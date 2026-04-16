"""
VFL ODDS TRACKER v1.0
======================
ONIMIX TECH — ALL-LEAGUE PREMATCH ODDS RECORDER & SETTLEMENT ENGINE

Tracks ALL 5 VFL leagues:
  - Spain, Germany, England, Italy, France
Records prematch O1.5 odds for EVERY match discovered.
After matches complete, settles results and tags WON/LOST.
Builds cumulative "proven odds" database — odds ranges that consistently deliver Over 1.5.
Saves to GitHub for reference during 30k mega audit predictions.

Run every 30 minutes via AutoGPT agent.
"""
import json, time, urllib.request, ssl, os, hashlib
from datetime import datetime, timezone, timedelta
from collections import defaultdict

WAT = timezone(timedelta(hours=1))
TG_TOKEN = "8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow"
TG_CHAT  = "1745848158"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}

BASE = 'https://www.sportybet.com/api/ng/factsCenter'

# === ALL 5 VFL LEAGUES ===
LEAGUES = {
    'spain':   {'catId': 'sv:category:202120002', 'tId': 'sv:league:2', 'catName': 'Spain'},
    'germany': {'catId': 'sv:category:202120004', 'tId': 'sv:league:4', 'catName': 'Germany'},
    'england': {'catId': 'sv:category:202120001', 'tId': 'sv:league:1', 'catName': 'England'},
    'italy':   {'catId': 'sv:category:202120003', 'tId': 'sv:league:3', 'catName': 'Italy'},
    'france':  {'catId': 'sv:category:202120005', 'tId': 'sv:league:5', 'catName': 'France'},
}

# Persistence files — GitHub-backed
ODDS_HISTORY_FILE  = '/tmp/odds_history.json'
PROVEN_ODDS_FILE   = '/tmp/proven_odds.json'
TRACKER_STATE_FILE = '/tmp/tracker_state.json'

# ══════════════════════════════════════════════════════════════════════
# API HELPERS
# ══════════════════════════════════════════════════════════════════════

def api(url, timeout=12):
    """Fetch API with error handling."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return None

def tg_send(text, chat_id=TG_CHAT):
    """Send message to Telegram (split if needed)."""
    try:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            data = json.dumps({"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                data=data, headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                pass
            time.sleep(0.3)
        return True
    except Exception as e:
        print(f"  TG error: {e}")
        return False

# ══════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

def load_json(path, default=None):
    """Load JSON from file or return default."""
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except:
        pass
    return default if default is not None else {}

def save_json(path, data):
    """Save JSON to file."""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"  Save error ({path}): {e}")

# ══════════════════════════════════════════════════════════════════════
# PHASE 1: DISCOVER UPCOMING MATCHES & RECORD PREMATCH ODDS
# ══════════════════════════════════════════════════════════════════════

def get_recent_results(league, hours=6):
    """Fetch recent completed results for a league."""
    cfg = LEAGUES[league]
    now = int(time.time() * 1000)
    start = now - (hours * 3600000)
    results = []
    for pn in range(1, 6):
        d = api(f"{BASE}/eventResultList?sportId=sr:sport:202120001"
                f"&categoryId={cfg['catId']}&tournamentId={cfg['tId']}"
                f"&pageNum={pn}&pageSize=100&startTime={start}&endTime={now}")
        if not d or d.get('bizCode') != 10000:
            break
        tours = d.get('data', {})
        if isinstance(tours, dict):
            tours = tours.get('tournaments', [])
        for t in tours:
            for ev in t.get('events', []):
                results.append(ev)
        total = 0
        if isinstance(d.get('data'), dict):
            total = int(d['data'].get('totalNum', 0))
        if len(results) >= total:
            break
    return results

def discover_upcoming(league, max_probe=80):
    """Discover upcoming events by probing eventIds."""
    cfg = LEAGUES[league]
    results = get_recent_results(league, hours=4)
    if not results:
        print(f"  [{league}] No recent results for probing")
        return []

    max_eid = 0
    for ev in results:
        eid = ev.get('eventId', '')
        try:
            num = int(str(eid).replace('sr:match:', ''))
            if num > max_eid:
                max_eid = num
        except:
            pass

    if max_eid == 0:
        return []

    upcoming = []
    misses = 0
    probe = max_eid + 1
    now_ms = int(time.time() * 1000)

    while misses < 15 and len(upcoming) < max_probe:
        eid = f"sr:match:{probe}"
        d = api(f"{BASE}/event?eventId={eid}&productId=3", timeout=8)
        probe += 1
        if not d or d.get('bizCode') != 10000:
            misses += 1
            continue

        ev = d.get('data', {})
        if not ev:
            misses += 1
            continue

        ms = ev.get('matchStatus', '')
        if ms not in ('Not start', 'not_started', '', None):
            misses = 0
            continue

        est = ev.get('estimateStartTime', 0)
        if est <= now_ms:
            misses = 0
            continue

        cat = ev.get('sport', {}).get('category', {}).get('name', '')
        if cat.lower() != cfg['catName'].lower():
            misses = 0
            continue

        upcoming.append(ev)
        misses = 0
        time.sleep(0.25)

    return upcoming

def extract_ou15_odds(event):
    """Extract Over 1.5 odds, probability, and outcomeId from prematch markets."""
    mkts = {}
    for m in event.get('markets', []):
        if isinstance(m, dict):
            mkts[(str(m.get('id', '')), m.get('specifier', ''))] = m

    ou15_odds = 0.0
    ou15_prob = 0.0
    ou15_outcome_id = ''
    ou25_odds = 0.0
    ou25_prob = 0.0
    btts_prob = 0.0
    home_over05_prob = 0.0
    away_over05_prob = 0.0

    # Market 18: O/U 1.5
    for spec in ['total=1.5', '1.5']:
        m = mkts.get(('18', spec))
        if m:
            for o in m.get('outcomes', []):
                desc = o.get('desc', '').lower()
                if 'over' in desc:
                    ou15_odds = float(o.get('odds', '0') or '0')
                    ou15_prob = float(o.get('probability', '0') or '0')
                    ou15_outcome_id = o.get('id', '')
            break

    # Market 18: O/U 2.5
    for spec in ['total=2.5', '2.5']:
        m = mkts.get(('18', spec))
        if m:
            for o in m.get('outcomes', []):
                if 'over' in o.get('desc', '').lower():
                    ou25_odds = float(o.get('odds', '0') or '0')
                    ou25_prob = float(o.get('probability', '0') or '0')
            break

    # Market 19 (Home Over 0.5), Market 20 (Away Over 0.5)
    for mid, store in [('19', 'home'), ('20', 'away')]:
        for spec in ['total=0.5', '0.5', '']:
            m = mkts.get((mid, spec))
            if m:
                for o in m.get('outcomes', []):
                    if 'over' in o.get('desc', '').lower():
                        p = float(o.get('probability', '0') or '0')
                        if store == 'home':
                            home_over05_prob = p
                        else:
                            away_over05_prob = p
                break

    # Market 29 (BTTS)
    m = mkts.get(('29', ''))
    if m:
        for o in m.get('outcomes', []):
            if 'yes' in o.get('desc', '').lower():
                btts_prob = float(o.get('probability', '0') or '0')

    # Section A score (0-14)
    sa_score = 0
    if ou15_prob >= 0.72: sa_score += 4
    elif ou15_prob >= 0.65: sa_score += 3
    elif ou15_prob >= 0.55: sa_score += 2
    elif ou15_prob >= 0.45: sa_score += 1

    if ou25_prob >= 0.55: sa_score += 3
    elif ou25_prob >= 0.45: sa_score += 2
    elif ou25_prob >= 0.35: sa_score += 1

    if home_over05_prob >= 0.70: sa_score += 2
    elif home_over05_prob >= 0.55: sa_score += 1
    if away_over05_prob >= 0.70: sa_score += 2
    elif away_over05_prob >= 0.55: sa_score += 1

    if btts_prob >= 0.50: sa_score += 2
    elif btts_prob >= 0.35: sa_score += 1

    return {
        'ou15_odds': ou15_odds,
        'ou15_prob': ou15_prob,
        'ou15_outcome_id': ou15_outcome_id,
        'ou25_odds': ou25_odds,
        'ou25_prob': ou25_prob,
        'btts_prob': btts_prob,
        'home_o05_prob': home_over05_prob,
        'away_o05_prob': away_over05_prob,
        'sa_score': sa_score,
    }

def record_prematch_odds(history, league, upcoming_events):
    """Record prematch odds for all discovered upcoming matches."""
    new_records = 0
    for ev in upcoming_events:
        eid = ev.get('eventId', '')
        if not eid:
            continue

        # Skip if already recorded
        if eid in history:
            continue

        home = ev.get('homeTeamName', '')
        away = ev.get('awayTeamName', '')
        est = ev.get('estimateStartTime', 0)

        odds_data = extract_ou15_odds(ev)

        if odds_data['ou15_odds'] <= 0:
            continue  # No odds available

        ko = datetime.fromtimestamp(est/1000, WAT).strftime('%Y-%m-%d %H:%M') if est else ''

        record = {
            'eventId': eid,
            'league': league,
            'home': home,
            'away': away,
            'matchup': f"{home} vs {away}",
            'kickoff': ko,
            'kickoff_ts': est,
            'recorded_at': datetime.now(WAT).isoformat(),
            # Prematch odds data
            'ou15_odds': odds_data['ou15_odds'],
            'ou15_prob': odds_data['ou15_prob'],
            'ou25_odds': odds_data['ou25_odds'],
            'ou25_prob': odds_data['ou25_prob'],
            'btts_prob': odds_data['btts_prob'],
            'home_o05_prob': odds_data['home_o05_prob'],
            'away_o05_prob': odds_data['away_o05_prob'],
            'sa_score': odds_data['sa_score'],
            # Settlement fields (filled later)
            'settled': False,
            'result': None,       # "WON" or "LOST"
            'home_goals': None,
            'away_goals': None,
            'total_goals': None,
            'settled_at': None,
        }

        history[eid] = record
        new_records += 1

    return new_records

# ══════════════════════════════════════════════════════════════════════
# PHASE 2: SETTLE COMPLETED MATCHES
# ══════════════════════════════════════════════════════════════════════

def settle_matches(history):
    """Check unsettled matches against results API and tag WON/LOST."""
    unsettled = {eid: rec for eid, rec in history.items()
                 if not rec.get('settled', False)}

    if not unsettled:
        return 0, 0

    now_ms = int(time.time() * 1000)
    settled_count = 0
    won_count = 0

    # Group unsettled by league
    by_league = defaultdict(list)
    for eid, rec in unsettled.items():
        # Only try to settle if kickoff was > 6 min ago (match should be done)
        if rec.get('kickoff_ts', 0) and (now_ms - rec['kickoff_ts']) > 6 * 60 * 1000:
            by_league[rec['league']].append((eid, rec))

    for league, records in by_league.items():
        if not records:
            continue

        # Find time range for results query
        min_ts = min(r[1]['kickoff_ts'] for r in records) - 600000
        max_ts = max(r[1]['kickoff_ts'] for r in records) + 600000

        # Fetch results in this time range
        cfg = LEAGUES.get(league)
        if not cfg:
            continue

        results = []
        for pn in range(1, 8):
            d = api(f"{BASE}/eventResultList?sportId=sr:sport:202120001"
                    f"&categoryId={cfg['catId']}&tournamentId={cfg['tId']}"
                    f"&pageNum={pn}&pageSize=100"
                    f"&startTime={min_ts}&endTime={max_ts}")
            if not d or d.get('bizCode') != 10000:
                break
            tours = d.get('data', {})
            if isinstance(tours, dict):
                tours = tours.get('tournaments', [])
            for t in tours:
                for ev in t.get('events', []):
                    results.append(ev)
            total = 0
            if isinstance(d.get('data'), dict):
                total = int(d['data'].get('totalNum', 0))
            if len(results) >= total:
                break

        # Build lookup: (home, away, approx_time) -> result
        result_lookup = {}
        for rev in results:
            rh = rev.get('homeTeamName', '')
            ra = rev.get('awayTeamName', '')
            rest = rev.get('estimateStartTime', 0)
            scores = rev.get('setScore', '') or rev.get('score', '') or rev.get('gameScore', '')
            if ':' in str(scores) and rh and ra:
                try:
                    parts = str(scores).split(':')
                    hg, ag = int(parts[0]), int(parts[1])
                    result_lookup[(rh, ra, rest)] = (hg, ag)
                except:
                    pass

        # Try to match unsettled records
        for eid, rec in records:
            home = rec['home']
            away = rec['away']
            kickoff_ts = rec['kickoff_ts']

            # Exact match first
            key = (home, away, kickoff_ts)
            if key in result_lookup:
                hg, ag = result_lookup[key]
            else:
                # Fuzzy time match (within 2 min)
                found = False
                for (rh, ra, rst), (hg2, ag2) in result_lookup.items():
                    if rh == home and ra == away and abs(rst - kickoff_ts) < 120000:
                        hg, ag = hg2, ag2
                        found = True
                        break
                if not found:
                    continue

            total = hg + ag
            won = total >= 2  # Over 1.5 = 2+ goals

            history[eid]['settled'] = True
            history[eid]['home_goals'] = hg
            history[eid]['away_goals'] = ag
            history[eid]['total_goals'] = total
            history[eid]['result'] = 'WON' if won else 'LOST'
            history[eid]['settled_at'] = datetime.now(WAT).isoformat()

            settled_count += 1
            if won:
                won_count += 1

    return settled_count, won_count

# ══════════════════════════════════════════════════════════════════════
# PHASE 3: BUILD PROVEN ODDS DATABASE
# ══════════════════════════════════════════════════════════════════════

def build_proven_odds(history):
    """
    Analyze all settled records to build proven odds database.
    Groups by odds range buckets and calculates hit rates.
    Also groups by (league, matchup, odds_range) for fine-grained insight.
    """
    settled = [rec for rec in history.values() if rec.get('settled')]

    if not settled:
        return {
            'last_updated': datetime.now(WAT).isoformat(),
            'total_settled': 0,
            'overall_hit_rate': 0,
            'odds_buckets': {},
            'league_stats': {},
            'matchup_odds': {},
            'sa_score_stats': {},
            'sweet_spot_analysis': {},
        }

    # === 1. ODDS BUCKETS (0.05 width) ===
    # Bucket: 1.20-1.24, 1.25-1.29, 1.30-1.34, 1.35-1.39, 1.40-1.44, etc.
    buckets = defaultdict(lambda: {'total': 0, 'won': 0})
    for rec in settled:
        odds = rec.get('ou15_odds', 0)
        if odds <= 0:
            continue
        bucket_low = round(int(odds * 20) / 20, 2)  # 0.05 width
        bucket_key = f"{bucket_low:.2f}-{bucket_low+0.04:.2f}"
        buckets[bucket_key]['total'] += 1
        if rec['result'] == 'WON':
            buckets[bucket_key]['won'] += 1

    odds_buckets = {}
    for bk in sorted(buckets.keys()):
        b = buckets[bk]
        rate = b['won'] / b['total'] if b['total'] > 0 else 0
        odds_buckets[bk] = {
            'total': b['total'],
            'won': b['won'],
            'lost': b['total'] - b['won'],
            'hit_rate': round(rate, 4),
            'hit_pct': f"{rate*100:.1f}%",
            'reliable': b['total'] >= 20,  # Need 20+ sample for reliability
        }

    # === 2. LEAGUE STATS ===
    league_stats = defaultdict(lambda: {'total': 0, 'won': 0})
    for rec in settled:
        lg = rec.get('league', 'unknown')
        league_stats[lg]['total'] += 1
        if rec['result'] == 'WON':
            league_stats[lg]['won'] += 1

    league_out = {}
    for lg in sorted(league_stats.keys()):
        s = league_stats[lg]
        rate = s['won'] / s['total'] if s['total'] > 0 else 0
        league_out[lg] = {
            'total': s['total'],
            'won': s['won'],
            'hit_rate': round(rate, 4),
            'hit_pct': f"{rate*100:.1f}%",
        }

    # === 3. MATCHUP + ODDS RANGE (for mega audit reference) ===
    matchup_odds = defaultdict(lambda: {'total': 0, 'won': 0, 'odds_sum': 0})
    for rec in settled:
        key = f"{rec['league']}:{rec['home']} vs {rec['away']}"
        odds = rec.get('ou15_odds', 0)
        if odds < 1.10:
            continue
        matchup_odds[key]['total'] += 1
        matchup_odds[key]['odds_sum'] += odds
        if rec['result'] == 'WON':
            matchup_odds[key]['won'] += 1

    matchup_out = {}
    for mk in sorted(matchup_odds.keys()):
        m = matchup_odds[mk]
        rate = m['won'] / m['total'] if m['total'] > 0 else 0
        avg_odds = m['odds_sum'] / m['total'] if m['total'] > 0 else 0
        matchup_out[mk] = {
            'total': m['total'],
            'won': m['won'],
            'hit_rate': round(rate, 4),
            'avg_odds': round(avg_odds, 3),
            'reliable': m['total'] >= 5,
        }

    # === 4. SA SCORE STATS (how SA score correlates with O1.5 hit rate) ===
    sa_stats = defaultdict(lambda: {'total': 0, 'won': 0})
    for rec in settled:
        sa = rec.get('sa_score', 0)
        sa_stats[sa]['total'] += 1
        if rec['result'] == 'WON':
            sa_stats[sa]['won'] += 1

    sa_out = {}
    for sa in sorted(sa_stats.keys()):
        s = sa_stats[sa]
        rate = s['won'] / s['total'] if s['total'] > 0 else 0
        sa_out[str(sa)] = {
            'total': s['total'],
            'won': s['won'],
            'hit_rate': round(rate, 4),
            'hit_pct': f"{rate*100:.1f}%",
        }

    # === 5. SWEET SPOT ANALYSIS (1.38-1.60 focus) ===
    sweet_total = 0
    sweet_won = 0
    non_sweet_total = 0
    non_sweet_won = 0
    for rec in settled:
        odds = rec.get('ou15_odds', 0)
        if 1.38 <= odds <= 1.60:
            sweet_total += 1
            if rec['result'] == 'WON':
                sweet_won += 1
        elif odds > 0:
            non_sweet_total += 1
            if rec['result'] == 'WON':
                non_sweet_won += 1

    sweet_rate = sweet_won / sweet_total if sweet_total > 0 else 0
    non_sweet_rate = non_sweet_won / non_sweet_total if non_sweet_total > 0 else 0

    overall_won = sum(1 for r in settled if r['result'] == 'WON')
    overall_rate = overall_won / len(settled) if settled else 0

    proven = {
        'last_updated': datetime.now(WAT).isoformat(),
        'total_settled': len(settled),
        'overall_hit_rate': round(overall_rate, 4),
        'overall_hit_pct': f"{overall_rate*100:.1f}%",
        'sweet_spot_analysis': {
            '1.38-1.60': {
                'total': sweet_total,
                'won': sweet_won,
                'hit_rate': round(sweet_rate, 4),
                'hit_pct': f"{sweet_rate*100:.1f}%",
            },
            'outside_sweet': {
                'total': non_sweet_total,
                'won': non_sweet_won,
                'hit_rate': round(non_sweet_rate, 4),
                'hit_pct': f"{non_sweet_rate*100:.1f}%",
            },
        },
        'odds_buckets': odds_buckets,
        'league_stats': league_out,
        'sa_score_stats': sa_out,
        'matchup_odds': matchup_out,
    }

    return proven

# ══════════════════════════════════════════════════════════════════════
# PHASE 4: TELEGRAM REPORTING
# ══════════════════════════════════════════════════════════════════════

def send_tracker_report(new_recorded, settled_count, won_count, proven, history):
    """Send tracking summary to Telegram."""
    now = datetime.now(WAT)
    total_in_history = len(history)
    total_settled = sum(1 for r in history.values() if r.get('settled'))
    total_unsettled = total_in_history - total_settled
    total_won = sum(1 for r in history.values() if r.get('result') == 'WON')

    msg = f"""📊 <b>VFL ODDS TRACKER v1.0</b>
🕐 {now.strftime('%Y-%m-%d %H:%M WAT')}

<b>This Run:</b>
• New odds recorded: {new_recorded}
• Matches settled: {settled_count} ({won_count} WON)

<b>Cumulative Database:</b>
• Total tracked: {total_in_history}
• Settled: {total_settled} | Pending: {total_unsettled}
• Overall O1.5 hit rate: {proven.get('overall_hit_pct', 'N/A')}"""

    # Sweet spot insight
    ss = proven.get('sweet_spot_analysis', {})
    sweet = ss.get('1.38-1.60', {})
    if sweet.get('total', 0) > 0:
        msg += f"""

<b>Sweet Spot (1.38-1.60):</b>
• {sweet['won']}/{sweet['total']} = {sweet['hit_pct']} hit rate"""

    # Top odds buckets
    buckets = proven.get('odds_buckets', {})
    if buckets:
        # Show top 5 most reliable buckets
        reliable = [(k, v) for k, v in buckets.items() if v.get('reliable')]
        reliable.sort(key=lambda x: x[1]['hit_rate'], reverse=True)
        if reliable:
            msg += "\n\n<b>🏆 Best Odds Ranges (20+ sample):</b>"
            for bk, bv in reliable[:5]:
                msg += f"\n• @{bk}: {bv['hit_pct']} ({bv['won']}/{bv['total']})"

    # League breakdown
    lg_stats = proven.get('league_stats', {})
    if lg_stats:
        msg += "\n\n<b>📋 By League:</b>"
        for lg, ls in lg_stats.items():
            msg += f"\n• {lg.title()}: {ls['hit_pct']} ({ls['won']}/{ls['total']})"

    msg += "\n\n🔄 Next scan in 30 min"
    tg_send(msg)

# ══════════════════════════════════════════════════════════════════════
# MAIN RUN
# ══════════════════════════════════════════════════════════════════════

def run():
    now = datetime.now(WAT)
    print("=" * 60)
    print("VFL ODDS TRACKER v1.0 — ALL-LEAGUE RECORDER")
    print(f"Time: {now.strftime('%Y-%m-%d %H:%M WAT')}")
    print("=" * 60)

    # Load state
    history = load_json(ODDS_HISTORY_FILE, {})
    print(f"\n📂 Loaded {len(history)} existing records")

    # === PHASE 1: DISCOVER & RECORD ===
    total_new = 0
    for league in LEAGUES:
        print(f"\n{'─'*40}")
        print(f"🔍 Scanning {league.title()}...")

        upcoming = discover_upcoming(league, max_probe=60)
        print(f"  Found {len(upcoming)} upcoming matches")

        new = record_prematch_odds(history, league, upcoming)
        total_new += new
        print(f"  Recorded {new} new prematch odds")
        time.sleep(0.5)

    print(f"\n✅ Phase 1 complete: {total_new} new records")

    # === PHASE 2: SETTLE ===
    print(f"\n{'─'*40}")
    print("⚖️ Settling completed matches...")
    settled_count, won_count = settle_matches(history)
    print(f"  Settled: {settled_count} ({won_count} WON)")

    # Save updated history
    save_json(ODDS_HISTORY_FILE, history)
    total_settled = sum(1 for r in history.values() if r.get('settled'))
    print(f"\n💾 History saved: {len(history)} total, {total_settled} settled")

    # === PHASE 3: BUILD PROVEN ODDS ===
    print(f"\n{'─'*40}")
    print("📊 Building proven odds database...")
    proven = build_proven_odds(history)
    save_json(PROVEN_ODDS_FILE, proven)
    print(f"  Overall hit rate: {proven.get('overall_hit_pct', 'N/A')}")
    print(f"  Odds buckets: {len(proven.get('odds_buckets', {}))}")
    print(f"  Matchups tracked: {len(proven.get('matchup_odds', {}))}")

    # === PHASE 4: REPORT ===
    if total_new > 0 or settled_count > 0:
        print(f"\n{'─'*40}")
        print("📤 Sending Telegram report...")
        send_tracker_report(total_new, settled_count, won_count, proven, history)

    print(f"\n{'='*60}")
    print("ODDS TRACKER RUN COMPLETE")
    print(f"{'='*60}")

    return {
        'new_recorded': total_new,
        'settled': settled_count,
        'won': won_count,
        'total_history': len(history),
        'proven_odds': proven,
    }


if __name__ == '__main__':
    run()
