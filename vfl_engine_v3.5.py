"""
VFL Engine v3.5 — ONIMIX TECH
Failure Monitoring + Learning System
Section A: Pre-match JSON Probability Decoder (6 markets)
Section B: Yesterday Same-Slot Energy Cards (restored via gameId tracking)
"""

import requests, json, time, hashlib, os
import concurrent.futures
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.sportybet.com/ng/sport/vFootball'
}

TG_TOKEN = '8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow'
TG_API = 'https://api.telegram.org/bot' + TG_TOKEN
TG_CHAT = '1745848158'

SPORT = 'sr:sport:202120001'
SWEET = (1.38, 1.60)

LEAGUES = {
    'spain': {'name': 'Spain VFL', 'catName': 'Spain'},
    'germany': {'name': 'Germany VFL', 'catName': 'Germany'},
}

# ── PERSISTENCE: prediction tracking + blacklist ──
TRACK_FILE = '/tmp/vfl_predictions.json'
BLACKLIST_FILE = '/tmp/vfl_blacklist.json'

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_predictions():
    """Load tracked predictions: {gameId: {match, verdict, odds, pct, timestamp}}"""
    return load_json(TRACK_FILE)

def save_predictions(preds):
    save_json(TRACK_FILE, preds)

def load_blacklist():
    """Load blacklist: {matchup_key: {fails, last_fail, reason}}"""
    return load_json(BLACKLIST_FILE)

def save_blacklist(bl):
    save_json(BLACKLIST_FILE, bl)

def matchup_key(home, away):
    """Canonical key for a matchup (order-independent)."""
    h = (home or '').strip().lower()
    a = (away or '').strip().lower()
    return '|'.join(sorted([h, a]))

# ── DISCOVERY ──
def discover_all():
    """Get ALL upcoming VFL events from commonThumbnailEvents."""
    r = requests.get('https://www.sportybet.com/api/ng/factsCenter/commonThumbnailEvents', params={
        'sportId': SPORT, 'productId': 3,
    }, headers=HEADERS, timeout=15)
    d = r.json()
    if d.get('bizCode') != 10000:
        print("  warning: Discovery failed: %s" % d.get('message',''))
        return {}
    by_league = defaultdict(list)
    for tour in d.get('data', []):
        cn = tour.get('categoryName', '')
        by_league[cn].extend(tour.get('events', []))
    return by_league

def event_detail(game_id):
    """Fetch full event detail using numeric gameId."""
    try:
        r = requests.get('https://www.sportybet.com/api/ng/factsCenter/event', params={
            'gameId': str(game_id), 'productId': 3
        }, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        if d.get('bizCode') != 10000:
            return None
        ev = d.get('data')
        if not ev:
            return None
        ms = ev.get('matchStatus')
        if ms and ms not in ('Not start', 'not_started', 0, '0', None):
            return None
        if ev.get('status') not in (0, '0'):
            return None
        return ev
    except:
        return None

def event_result(game_id):
    """Fetch event to check if ended and get score."""
    try:
        r = requests.get('https://www.sportybet.com/api/ng/factsCenter/event', params={
            'gameId': str(game_id), 'productId': 3
        }, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None
        d = r.json()
        if d.get('bizCode') != 10000:
            return None
        return d.get('data')
    except:
        return None

# ── FAILURE MONITOR ──
def check_past_predictions():
    """Check results of previously predicted matches. Returns analysis."""
    preds = load_predictions()
    blacklist = load_blacklist()
    if not preds:
        return {'checked': 0, 'won': 0, 'lost': 0, 'pending': 0, 'new_blacklist': []}

    checked, won, lost, pending = 0, 0, 0, 0
    new_blacklist_entries = []
    keys_to_remove = []

    # Only check predictions from last 24 hours
    cutoff = time.time() - 86400
    gids_to_check = [gid for gid, info in preds.items()
                     if info.get('timestamp', 0) > cutoff and info.get('status') != 'settled']

    print("  Checking %d pending predictions..." % len(gids_to_check))

    def fetch_result(gid):
        return (gid, event_result(gid))

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        results = list(ex.map(lambda g: fetch_result(g), gids_to_check))

    for gid, ev in results:
        if ev is None:
            pending += 1
            continue

        ms = ev.get('matchStatus')
        status = ev.get('status')

        if ms != 'Ended' and status not in (3, '3'):
            pending += 1
            continue

        checked += 1
        score = ev.get('setScore', '')
        try:
            parts = str(score).split(':')
            total_goals = int(parts[0]) + int(parts[1])
        except:
            total_goals = -1
            pending += 1
            continue

        pred_info = preds[gid]
        pred_info['actual_score'] = score
        pred_info['total_goals'] = total_goals
        pred_info['status'] = 'settled'

        if total_goals >= 2:
            won += 1
            pred_info['result'] = 'WON'
        else:
            lost += 1
            pred_info['result'] = 'LOST'
            # Add to blacklist
            home = pred_info.get('home', '')
            away = pred_info.get('away', '')
            mk = matchup_key(home, away)
            if mk not in blacklist:
                blacklist[mk] = {'fails': 0, 'history': []}
            blacklist[mk]['fails'] += 1
            blacklist[mk]['last_fail'] = time.time()
            blacklist[mk]['history'].append({
                'score': score,
                'verdict': pred_info.get('verdict', ''),
                'pct': pred_info.get('pct', 0),
                'odds': pred_info.get('odds', 0),
                'time': time.time(),
                'reason': analyze_failure(pred_info, total_goals)
            })
            new_blacklist_entries.append({
                'match': '%s v %s' % (home, away),
                'score': score,
                'verdict': pred_info.get('verdict'),
                'reason': analyze_failure(pred_info, total_goals),
            })

    # Remove predictions older than 48 hours
    old_cutoff = time.time() - 172800
    for gid, info in list(preds.items()):
        if info.get('timestamp', 0) < old_cutoff:
            keys_to_remove.append(gid)
    for k in keys_to_remove:
        del preds[k]

    save_predictions(preds)
    save_blacklist(blacklist)

    return {
        'checked': checked,
        'won': won,
        'lost': lost,
        'pending': pending,
        'new_blacklist': new_blacklist_entries,
        'win_rate': round(won / checked * 100, 1) if checked > 0 else 0,
    }

def analyze_failure(pred_info, total_goals):
    """Analyze why a prediction failed."""
    reasons = []
    pct = pred_info.get('pct', 0)
    odds = pred_info.get('odds', 0)
    sig = pred_info.get('signals', {})

    if total_goals == 0:
        reasons.append("0-0 dead match")
    elif total_goals == 1:
        reasons.append("Only 1 goal scored")

    if pct < 60:
        reasons.append("Low confidence (%d%%)" % pct)

    cs_o15 = sig.get('cs_o15', 0)
    if cs_o15 < 0.50:
        reasons.append("Weak CS signal (%.0f%%)" % (cs_o15 * 100))

    fp11 = sig.get('fp11', 0)
    if fp11 > 0.10:
        reasons.append("1:1 fingerprint detected (%.1f%%)" % (fp11 * 100))

    ou15_prob = sig.get('ou15_prob', 0)
    if ou15_prob < 0.60:
        reasons.append("Low O1.5 prob (%.0f%%)" % (ou15_prob * 100))

    gg_prob = sig.get('gg_prob', 0)
    if gg_prob < 0.35:
        reasons.append("Low GG prob (%.0f%%)" % (gg_prob * 100))

    return '; '.join(reasons) if reasons else 'Unknown'

def is_blacklisted(home, away, blacklist):
    """Check if matchup is blacklisted (failed 2+ times recently)."""
    mk = matchup_key(home, away)
    entry = blacklist.get(mk)
    if not entry:
        return False, ''
    fails = entry.get('fails', 0)
    last_fail = entry.get('last_fail', 0)
    # Blacklist decays after 7 days
    if time.time() - last_fail > 604800:
        return False, ''
    if fails >= 2:
        return True, 'Failed %d times (last: %s)' % (fails, entry.get('history', [{}])[-1].get('reason', '?'))
    return False, ''

def sum_score(desc):
    """Parse correct score description like '2:1' to total goals."""
    try:
        parts = desc.replace(' ','').split(':')
        return int(parts[0]) + int(parts[1])
    except:
        return 0

# ── SECTION A ──
def sec_a(event):
    """Section A: decode 6 markets in order: CS(45) > HG(23) > AG(24) > OU(18) > FH(68) > GG(29)."""
    mkts = event.get('markets', [])
    cs, hg, ag, ou, fhou, gg = None, None, None, {}, {}, None

    for m in mkts:
        mid = str(m.get('id', ''))
        spec = m.get('specifier', '')
        parsed = {}
        for o in m.get('outcomes', []):
            try:
                if o.get('isActive') not in (1, '1', True):
                    continue
                parsed[o['desc']] = {
                    'odds': float(o.get('odds', 0)),
                    'prob': float(o.get('probability', 0)),
                    'id': o.get('id', ''),
                    'act': o.get('isActive', 0),
                }
            except:
                pass
        if mid == '45': cs = parsed
        elif mid == '23': hg = parsed
        elif mid == '24': ag = parsed
        elif mid == '18':
            key = spec.replace('total=', '') if 'total=' in spec else spec
            ou[key] = parsed
        elif mid == '68':
            key = spec.replace('total=', '') if 'total=' in spec else spec
            fhou[key] = parsed
        elif mid == '29': gg = parsed

    sc, mx, sig = 0, 0, {}

    # Market 45: Correct Score
    if cs:
        mx += 3
        o15p = sum(v['prob'] for d, v in cs.items() if sum_score(d) >= 2)
        fp11 = next((v['prob'] for d, v in cs.items() if d.replace(' ', '') == '1:1'), 0)
        sig['cs_o15'] = round(o15p, 4)
        sig['fp11'] = round(fp11, 4)
        if o15p > 0.55: sc += 3
        elif o15p > 0.45: sc += 2
        elif o15p > 0.35: sc += 1

    # Market 23: Home Goals
    if hg:
        mx += 2
        h1p = sum(v['prob'] for d, v in hg.items() if d not in ('0',))
        sig['hg_1plus'] = round(h1p, 4)
        if h1p > 0.70: sc += 2
        elif h1p > 0.55: sc += 1

    # Market 24: Away Goals
    if ag:
        mx += 2
        a1p = sum(v['prob'] for d, v in ag.items() if d not in ('0',))
        sig['ag_1plus'] = round(a1p, 4)
        if a1p > 0.70: sc += 2
        elif a1p > 0.55: sc += 1

    # Market 18: Over/Under totals
    ou15 = ou.get('1.5', {})
    ou15_over = ou15.get('Over 1.5', {})
    ou15_odds = ou15_over.get('odds', 0)
    ou15_prob = ou15_over.get('prob', 0)
    ou15_oid = ou15_over.get('id', '')

    if ou15:
        mx += 3
        sig['ou15_prob'] = round(ou15_prob, 4)
        sig['ou15_odds'] = ou15_odds
        if ou15_prob > 0.70: sc += 3
        elif ou15_prob > 0.55: sc += 2
        elif ou15_prob > 0.40: sc += 1

    # Market 68: 1st Half O/U
    fh05 = fhou.get('0.5', {})
    fh05_over = fh05.get('Over 0.5', {})
    if fh05:
        mx += 2
        fhp = fh05_over.get('prob', 0)
        sig['fh05_prob'] = round(fhp, 4)
        if fhp > 0.75: sc += 2
        elif fhp > 0.60: sc += 1

    # Market 29: GG/NG
    if gg:
        mx += 2
        ggp = gg.get('Yes', {}).get('prob', 0)
        sig['gg_prob'] = round(ggp, 4)
        if ggp > 0.55: sc += 2
        elif ggp > 0.40: sc += 1

    pct = round(sc / mx * 100) if mx > 0 else 0
    sweet = SWEET[0] <= ou15_odds <= SWEET[1] if ou15_odds > 0 else False
    fp11 = sig.get('fp11', 0) > 0.10

    # Confidence tier per user rules
    top_cs_prob = max((v['prob'] for d, v in (cs or {}).items()), default=0)
    if top_cs_prob > 0.12:
        conf = 'HIGH'
    elif top_cs_prob > 0.08:
        conf = 'MEDIUM'
    else:
        conf = 'LOW'

    return {
        'sc': sc, 'mx': mx, 'pct': pct,
        'ou15_odds': ou15_odds, 'ou15_prob': ou15_prob, 'ou15_oid': ou15_oid,
        'sweet': sweet, 'fp11': fp11, 'sig': sig, 'conf': conf,
    }

# ── ANALYSIS ──
def analyze(event, blacklist):
    """Combine Section A + blacklist check."""
    a = sec_a(event)
    hn = event.get('homeTeamName') or '?'
    an = event.get('awayTeamName') or '?'
    cpct = a['pct']

    # Verdict thresholds
    if cpct >= 70:
        verdict = 'LOCK'
    elif cpct >= 50:
        verdict = 'PICK'
    elif cpct >= 35:
        verdict = 'CONSIDER'
    else:
        verdict = 'SKIP'

    # HARD 1.38 FILTER — below is a trap
    if a['ou15_odds'] > 0 and a['ou15_odds'] < SWEET[0]:
        verdict = 'SKIP'

    # No odds = can't book
    if a['ou15_odds'] <= 0:
        verdict = 'SKIP'

    # 1:1 fingerprint penalty: downgrade if detected
    if a['fp11'] and verdict in ('LOCK', 'PICK'):
        verdict = 'PICK' if verdict == 'LOCK' else 'CONSIDER'

    # BLACKLIST CHECK — learning from past failures
    bl_hit, bl_reason = is_blacklisted(hn, an, blacklist)
    if bl_hit and verdict in ('LOCK', 'PICK', 'CONSIDER'):
        verdict = 'SKIP'

    return {
        'match': '%s v %s' % (hn, an),
        'home': hn,
        'away': an,
        'eid': event.get('eventId', ''),
        'gid': str(event.get('gameId', '')),
        'start': event.get('estimateStartTime', 0),
        'a': a,
        'cpct': cpct,
        'verdict': verdict,
        'ou15_odds': a['ou15_odds'],
        'ou15_oid': a['ou15_oid'],
        'sweet': a['sweet'],
        'fp11': a['fp11'],
        'conf': a['conf'],
        'bl_hit': bl_hit,
        'bl_reason': bl_reason,
    }

# ── BOOKING CODE ──
def gen_booking(picks):
    if not picks:
        return None
    outcomes = []
    for p in picks:
        oid = p.get('ou15_oid')
        eid = p.get('eid')
        if not oid or not eid:
            continue
        outcomes.append({
            "eventId": eid,
            "marketId": "18",
            "specifier": "total=1.5",
            "outcomeId": str(oid),
        })
    if not outcomes:
        return None
    payload = {"selections": outcomes}
    print("    Booking: %d selections" % len(outcomes))
    try:
        r = requests.post(
            'https://www.sportybet.com/api/ng/orders/share',
            json=payload, headers={**HEADERS, 'Content-Type': 'application/json'}, timeout=15
        )
        d = r.json()
        if d.get('bizCode') == 10000:
            code = d.get('data', {}).get('shareCode')
            if code:
                return code
        print("    Booking response: %s" % json.dumps(d)[:200])
    except Exception as e:
        print("    Booking failed: %s" % e)
    return None

# ── TELEGRAM ──
def tg_send(text, chat_id=None):
    cid = chat_id or TG_CHAT
    try:
        r = requests.post('%s/sendMessage' % TG_API, json={
            'chat_id': cid, 'text': text,
            'parse_mode': 'HTML', 'disable_web_page_preview': True,
        }, timeout=15)
        d = r.json()
        if d.get('ok'):
            return True
        print("  TG error: %s" % d.get('description', ''))
    except Exception as e:
        print("  TG send failed: %s" % e)
    return False

def format_section(picks, icon, label, code, total_odds):
    if not picks:
        return []
    lines = ["%s <b>%s (%d sel | %.0fx odds)</b>" % (icon, label, len(picks), total_odds), ""]
    by_time = defaultdict(list)
    for p in picks:
        by_time[p.get('start', 0)].append(p)
    for t in sorted(by_time.keys()):
        dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
        lines.append("<b>%s UTC</b>" % dt.strftime('%H:%M'))
        for p in by_time[t]:
            sw = ' [S]' if p['sweet'] else ''
            fp = ' [1:1]' if p['fp11'] else ''
            conf = p.get('conf', '')
            lines.append("  %s %s — O1.5 @%.2f %s%s%s" % (icon, p['match'], p['ou15_odds'], conf, sw, fp))
        lines.append("")
    lines.append("<b>ODDS: %.0fx</b>" % total_odds)
    if code:
        lines.append("<b>CODE: %s</b>" % code)
        lines.append("sportybet.com/ng/share/%s" % code)
    else:
        lines.append("Code: manual entry required")
    return lines

# ── MAIN SCANNER ──
def run():
    scan_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print("=" * 60)
    print("VFL ENGINE v3.5 — ONIMIX TECH")
    print("Failure Monitor + Learning System")
    print(scan_time)
    print("=" * 60)

    # ── PHASE 0: Check past predictions ──
    print("\n[PHASE 0] Checking past predictions...")
    monitor = check_past_predictions()
    if monitor['checked'] > 0:
        print("  Results: %d checked | %d won | %d lost | %.1f%% win rate" % (
            monitor['checked'], monitor['won'], monitor['lost'], monitor['win_rate']))
        if monitor['new_blacklist']:
            print("  NEW BLACKLIST entries:")
            for bl in monitor['new_blacklist']:
                print("    X %s | %s | %s" % (bl['match'], bl['score'], bl['reason']))
    else:
        print("  No settled predictions to check yet")
    print("  Pending: %d matches still awaiting results" % monitor['pending'])

    # Load blacklist for this scan
    blacklist = load_blacklist()
    bl_count = sum(1 for v in blacklist.values() if v.get('fails', 0) >= 2)
    print("  Active blacklist: %d matchups" % bl_count)

    # ── PHASE 1: Discover events ──
    print("\n[PHASE 1] Discovering all upcoming VFL events...")
    all_upcoming = discover_all()

    all_results = []

    for lk, cfg in LEAGUES.items():
        cat_name = cfg['catName']
        events = all_upcoming.get(cat_name, [])
        print("\n  %s: %d upcoming matches" % (cfg['name'], len(events)))

        if not events:
            continue

        rounds = sorted(set(e['estimateStartTime'] for e in events))
        for t in rounds[:5]:
            dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
            n = sum(1 for e in events if e['estimateStartTime'] == t)
            print("    %s UTC (%d matches)" % (dt.strftime('%H:%M'), n))
        if len(rounds) > 5:
            print("    ... +%d more rounds" % (len(rounds) - 5))

        game_ids = [e.get('gameId') for e in events if e.get('gameId')]
        print("  Fetching %d event details..." % len(game_ids))

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
            details = list(ex.map(event_detail, game_ids))

        valid = [d for d in details if d is not None]
        print("  Got %d valid events" % len(valid))

        for ev in valid:
            r = analyze(ev, blacklist)
            emoji = {'LOCK': 'L', 'PICK': 'P', 'CONSIDER': '?', 'SKIP': 'X'}[r['verdict']]
            bl = ' [BL]' if r['bl_hit'] else ''
            print("  [%s] %s: A:%d%% O1.5@%.2f %s%s" % (
                emoji, r['match'], r['a']['pct'], r['ou15_odds'],
                r['conf'], bl
            ))
            all_results.append(r)

    # ── PHASE 2: Sort and filter ──
    locks = [r for r in all_results if r['verdict'] == 'LOCK']
    picks = [r for r in all_results if r['verdict'] == 'PICK']
    cons = [r for r in all_results if r['verdict'] == 'CONSIDER']
    skips = [r for r in all_results if r['verdict'] == 'SKIP']
    bl_skips = [r for r in all_results if r['bl_hit']]

    print("\n" + "=" * 60)
    print("L:%d P:%d ?:%d X:%d | Blacklisted:%d" % (
        len(locks), len(picks), len(cons), len(skips), len(bl_skips)))

    bookable = locks + picks
    if not bookable:
        print("No bookable picks found")
        msg = "VFL Scan %s\nNo bookable picks across %d matches." % (scan_time, len(all_results))
        if monitor['checked'] > 0:
            msg += "\n\nMonitor: %d/%d won (%.1f%%)" % (monitor['won'], monitor['checked'], monitor['win_rate'])
        tg_send(msg, TG_CHAT)
        return

    locks.sort(key=lambda x: (x['sweet'], x['cpct']), reverse=True)
    picks.sort(key=lambda x: (x['sweet'], x['cpct']), reverse=True)

    lock_odds = 1.0
    for p in locks:
        lock_odds *= p['ou15_odds']
    pick_odds = 1.0
    for p in picks:
        pick_odds *= p['ou15_odds']

    print("\nLOCK ACCA: %d @ %.1fx" % (len(locks), lock_odds))
    print("PICK ACCA: %d @ %.1fx" % (len(picks), pick_odds))

    # ── PHASE 3: Generate booking codes ──
    lock_code = None
    pick_code = None

    if locks:
        print("\nGenerating LOCK booking code...")
        lock_code = gen_booking(locks)
        if lock_code:
            print("  LOCK Code: %s" % lock_code)

    if picks:
        print("Generating PICK booking code...")
        pick_code = gen_booking(picks)
        if pick_code:
            print("  PICK Code: %s" % pick_code)

    # ── PHASE 4: Track predictions for future monitoring ──
    preds = load_predictions()
    for p in bookable:
        gid = p['gid']
        preds[gid] = {
            'match': p['match'],
            'home': p['home'],
            'away': p['away'],
            'verdict': p['verdict'],
            'pct': p['cpct'],
            'odds': p['ou15_odds'],
            'signals': p['a']['sig'],
            'conf': p['conf'],
            'timestamp': time.time(),
            'status': 'pending',
        }
    save_predictions(preds)
    print("\nTracking %d predictions for monitoring" % len(bookable))

    # ── PHASE 5: Telegram delivery ──
    total_sel = len(locks) + len(picks)
    lines = [
        "<b>VFL MEGA — ONIMIX ELITE v3.5</b>",
        scan_time,
        "%d selections from %d analyzed" % (total_sel, len(all_results)),
        "L:%d | P:%d" % (len(locks), len(picks)),
    ]

    # Add monitor stats if available
    if monitor['checked'] > 0:
        lines.append("")
        lines.append("<b>MONITOR:</b> %d/%d won (%.1f%%)" % (
            monitor['won'], monitor['checked'], monitor['win_rate']))
        if monitor['new_blacklist']:
            for bl in monitor['new_blacklist'][:3]:
                lines.append("  X %s %s" % (bl['match'], bl['score']))

    lines.append("")

    if locks:
        lines.extend(format_section(locks, 'L', 'LOCK ACCUMULATOR', lock_code, lock_odds))
        lines.append("")

    if picks:
        lines.extend(format_section(picks, 'P', 'PICK ACCUMULATOR', pick_code, pick_odds))
        lines.append("")

    if bl_skips:
        lines.append("<i>Blacklisted: %d matches skipped (failed before)</i>" % len(bl_skips))

    lines.extend([
        "",
        "<i>Engine v3.5 | Monitor Active | ONIMIX TECH</i>",
    ])

    msg = '\n'.join(lines)

    if len(msg) > 4000:
        if locks:
            lock_msg = '\n'.join([
                "<b>VFL MEGA — ONIMIX ELITE (1/2)</b>",
                scan_time, "",
            ] + format_section(locks, 'L', 'LOCK ACCUMULATOR', lock_code, lock_odds))
            tg_send(lock_msg, TG_CHAT)
        if picks:
            pick_msg = '\n'.join([
                "<b>VFL MEGA — ONIMIX ELITE (2/2)</b>",
                scan_time, "",
            ] + format_section(picks, 'P', 'PICK ACCUMULATOR', pick_code, pick_odds) + [
                "", "<i>Engine v3.5 | Monitor Active | ONIMIX TECH</i>",
            ])
            tg_send(pick_msg, TG_CHAT)
    else:
        tg_send(msg, TG_CHAT)

    print("\nScan complete!")

if __name__ == '__main__':
    run()
