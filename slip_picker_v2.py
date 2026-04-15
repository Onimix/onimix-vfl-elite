"""
VFL GOLD/SILVER SLIP PICKER v2.0
================================
ONIMIX AGENT ELITE — SELF-VERIFYING CORRECTION SYSTEM
5 Mandatory Rules:
  1. SLOT REPEAT TRAP — Same time block + prev day fixture + low scoring = SKIP
  2. FAILURE ROOT CAUSE ANALYSIS — Trace prev day pattern, classify traps
  3. MEMORY LEARNING — 2+ same failures → reduce confidence 40%
  4. CONFIRMATION FILTER — Flagged match needs 2+ positive signals
  5. SELF CHECK OUTPUT — Audit report after each batch

"You are not predicting matches. You are detecting structural football
simulation patterns." — ONIMIX ELITE DIRECTIVE
"""
import json, time, urllib.request, ssl, hashlib, os
from datetime import datetime, timezone, timedelta

WAT = timezone(timedelta(hours=1))
TG_TOKEN = "8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow"
TG_CHAT = "1745848158"
SWEET = (1.38, 1.60)
MEMORY_FILE = "/tmp/onimix_failure_memory.json"
PROVEN_ODDS_URL = 'https://raw.githubusercontent.com/Onimix/onimix-vfl-elite/main/data/proven_odds.json'

def load_proven_odds():
    """Load proven odds database from GitHub (built by Odds Tracker agent)."""
    try:
        req = urllib.request.Request(PROVEN_ODDS_URL, headers={
            'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            return json.loads(r.read().decode())
    except:
        return {}

def get_proven_odds_boost(odds_value, matchup_key, proven_data):
    """Check proven odds DB for confidence boost/penalty."""
    if not proven_data or proven_data.get('total_settled', 0) < 20:
        return 0, "insufficient data"
    boost = 0
    reasons = []
    buckets = proven_data.get('odds_buckets', {})
    for bk, bv in buckets.items():
        try:
            lo, hi = float(bk.split('-')[0]), float(bk.split('-')[1])
            if lo <= odds_value <= hi and bv.get('reliable', False):
                rate = bv.get('hit_rate', 0)
                if rate >= 0.80: boost += 2; reasons.append(f"@{bk} {rate*100:.0f}%")
                elif rate >= 0.70: boost += 1; reasons.append(f"@{bk} {rate*100:.0f}%")
                elif rate < 0.50: boost -= 2; reasons.append(f"@{bk} DANGER")
                break
        except: pass
    matchup_odds = proven_data.get('matchup_odds', {})
    if matchup_key in matchup_odds:
        mo = matchup_odds[matchup_key]
        if mo.get('reliable', False):
            mrate = mo.get('hit_rate', 0)
            if mrate >= 0.85: boost += 3; reasons.append(f"matchup {mrate*100:.0f}%")
            elif mrate >= 0.70: boost += 1; reasons.append(f"matchup {mrate*100:.0f}%")
            elif mrate < 0.50: boost -= 3; reasons.append(f"matchup TRAP {mrate*100:.0f}%")
    return boost, " | ".join(reasons) if reasons else "no data"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}

# === MATCHUP DATABASE ===
GOLD = {
    'spain': [('CEL','FCB'),('GET','GIR'),('GIR','RMA'),('MAL','RMA'),('SEV','BIL')],
    'germany': [('BMG','WOB'),('DOR','BMG'),('HDH','BMG'),('KOE','WOB'),('SCF','HDH')]
}
SILVER = {
    'spain': [
        ('ALA','GIR'),('ALA','RMA'),('ATM','ELC'),('ATM','FCB'),('ATM','GIR'),
        ('ATM','RSO'),('BIL','ESP'),('BIL','GIR'),('BIL','OVI'),('CEL','ELC'),
        ('CEL','GIR'),('CEL','RMA'),('ELC','GIR'),('ESP','FCB'),('FCB','OVI'),
        ('GET','RMA'),('GIR','SEV'),('MAL','GIR'),('OVI','GIR'),('RAY','GIR'),
        ('RBB','FCB'),('RMA','OVI'),('RSO','GIR'),('SEV','GIR'),('VCF','GIR'),
        ('VIL','FCB')
    ],
    'germany': [
        ('BMG','SGE'),('BMG','STP'),('DOR','KOE'),('DOR','SGE'),('DOR','WOB'),
        ('HDH','KOE'),('HDH','SCF'),('HDH','SGE'),('HDH','STP'),('KOE','SCF'),
        ('KOE','SGE'),('SCF','SGE'),('WOB','SGE'),('WOB','STP')
    ]
}
TRAP = {
    ('ALA','VIL'),('CEL','VIL'),('ESP','RMA'),('RBB','ALA'),('VIL','ELC'),
    ('BMG','UNI'),('FCA','WOB'),('SGE','BMG'),('UNI','WOB')
}

LEAGUES = {
    'spain': {'catId':'sv:category:202120002','tId':'sv:league:2','catName':'Spain'},
    'germany': {'catId':'sv:category:202120004','tId':'sv:league:4','catName':'Germany'}
}

BASE = 'https://www.sportybet.com/api/ng/factsCenter'

# ══════════════════════════════════════════════════════════════════════
# SELF-VERIFYING CORRECTION SYSTEM (ONIMIX AGENT ELITE)
# ══════════════════════════════════════════════════════════════════════

class CorrectionSystem:
    """
    Detects structural football simulation patterns.
    Never relies only on odds or team names.
    Prioritizes: Time slot repetition, Previous day score behavior, Structural goal pattern.
    """

    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = memory_file
        self.memory = self._load_memory()
        self.audit_log = []

    def _load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file) as f:
                    return json.load(f)
        except:
            pass
        return {"failures": [], "slot_patterns": {}, "matchup_failures": {}}

    def _save_memory(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"  Memory save error: {e}")

    def record_failure(self, home, away, league, kickoff_time, score, reason=""):
        """Record a failed pick into memory for future learning."""
        key = f"{home}v{away}"
        slot = kickoff_time[:5] if len(kickoff_time) >= 5 else kickoff_time
        entry = {
            "matchup": key,
            "league": league,
            "slot": slot,
            "score": score,
            "reason": reason,
            "timestamp": datetime.now(WAT).isoformat(),
            "date": datetime.now(WAT).strftime("%Y-%m-%d")
        }
        self.memory["failures"].append(entry)
        # Track per-matchup failure count
        if key not in self.memory["matchup_failures"]:
            self.memory["matchup_failures"][key] = []
        self.memory["matchup_failures"][key].append(entry)
        # Track slot patterns
        if slot not in self.memory["slot_patterns"]:
            self.memory["slot_patterns"][slot] = []
        self.memory["slot_patterns"][slot].append(entry)
        self._save_memory()

    def record_win(self, home, away, league, kickoff_time, score):
        """Record a successful pick (optional, for positive reinforcement)."""
        key = f"{home}v{away}"
        # Optionally reduce failure weight on wins
        pass

    # ── RULE 1: SLOT REPEAT TRAP ──────────────────────────────────────
    def check_slot_repeat_trap(self, home, away, kickoff_slot, yesterday_results):
        """
        Same time block (±10 min) + previous day fixture + low scoring = HARD SKIP.
        Returns (is_trapped, reason)
        """
        key = f"{home}v{away}"
        slot_min = self._slot_to_minutes(kickoff_slot)
        if slot_min is None:
            return False, ""

        for res in yesterday_results:
            res_home = res.get('home', '')
            res_away = res.get('away', '')
            res_key = f"{res_home}v{res_away}"
            res_slot = res.get('kickoff', '')
            res_goals = res.get('total_goals', 99)

            # Same fixture check
            if res_key != key:
                continue

            # Time block check (±10 min)
            res_min = self._slot_to_minutes(res_slot)
            if res_min is None:
                continue
            if abs(slot_min - res_min) > 10:
                continue

            # Low scoring check (≤1 goal)
            if res_goals <= 1:
                reason = (f"SLOT REPEAT TRAP: {key} at {kickoff_slot} — "
                         f"same fixture yesterday at {res_slot} scored {res_goals} goals")
                self._audit(key, "RULE1_SLOT_REPEAT", "HARD SKIP", reason)
                return True, reason

        return False, ""

    # ── RULE 2: FAILURE ROOT CAUSE ANALYSIS ───────────────────────────
    def analyze_failure_root_cause(self, home, away, kickoff_slot):
        """
        Trace previous day pattern and classify failure type.
        Returns (risk_level, classification, details)
        """
        key = f"{home}v{away}"
        recent_failures = self.memory.get("matchup_failures", {}).get(key, [])
        slot = kickoff_slot[:5] if len(kickoff_slot) >= 5 else kickoff_slot

        if not recent_failures:
            return "LOW", "NO_HISTORY", ""

        # Check for temporal pattern (same slot failures)
        slot_failures = [f for f in recent_failures
                        if abs(self._slot_to_minutes(f.get('slot','')) or 999
                              - (self._slot_to_minutes(slot) or 0)) <= 10]
        if len(slot_failures) >= 2:
            return "HIGH", "TEMPORAL_PATTERN_TRAP", (
                f"{key} failed {len(slot_failures)} times in slot ~{slot}: "
                f"scores={[f.get('score','?') for f in slot_failures]}")

        # Check for general matchup failure pattern
        last_7d = [f for f in recent_failures
                   if self._days_ago(f.get('timestamp', '')) <= 7]
        if len(last_7d) >= 2:
            return "MEDIUM", "RECURRING_FAILURE", (
                f"{key} failed {len(last_7d)} times in last 7 days")

        if len(recent_failures) >= 1:
            return "LOW", "SINGLE_FAILURE", (
                f"{key} had 1 failure: {recent_failures[-1].get('score','?')}")

        return "LOW", "CLEAN", ""

    # ── RULE 3: MEMORY LEARNING ───────────────────────────────────────
    def apply_memory_learning(self, home, away, base_confidence):
        """
        2+ same failures → reduce confidence 40%, require stronger signals.
        Returns (adjusted_confidence, penalty_applied, reason)
        """
        key = f"{home}v{away}"
        failures = self.memory.get("matchup_failures", {}).get(key, [])

        # Only count recent failures (last 14 days)
        recent = [f for f in failures if self._days_ago(f.get('timestamp', '')) <= 14]

        if len(recent) >= 3:
            # Heavy penalty: 60% reduction
            adj = base_confidence * 0.40
            reason = f"MEMORY: {key} failed {len(recent)}x in 14d → 60% penalty"
            self._audit(key, "RULE3_MEMORY", "HEAVY_PENALTY", reason)
            return adj, True, reason
        elif len(recent) >= 2:
            # Standard penalty: 40% reduction
            adj = base_confidence * 0.60
            reason = f"MEMORY: {key} failed {len(recent)}x in 14d → 40% penalty"
            self._audit(key, "RULE3_MEMORY", "STANDARD_PENALTY", reason)
            return adj, True, reason
        elif len(recent) == 1:
            # Light penalty: 15% reduction
            adj = base_confidence * 0.85
            reason = f"MEMORY: {key} failed 1x in 14d → 15% penalty"
            self._audit(key, "RULE3_MEMORY", "LIGHT_PENALTY", reason)
            return adj, True, reason

        return base_confidence, False, ""

    # ── RULE 4: CONFIRMATION FILTER ───────────────────────────────────
    def check_confirmation_filter(self, home, away, avg_goals, team_recent_goals,
                                   odds_movement, fixture_history_goals,
                                   is_flagged=False):
        """
        Flagged match needs 2+ of:
          1. avg goals ≥ 2.5
          2. team scored 3+ in recent matches
          3. odds dropped (movement < 0)
          4. high scoring fixture history (avg ≥ 2.0)

        Returns (passed, signals_met, signals_detail)
        """
        signals = []

        if avg_goals >= 2.5:
            signals.append(f"avg_goals={avg_goals:.1f}≥2.5")
        if team_recent_goals >= 3:
            signals.append(f"team_recent={team_recent_goals}≥3")
        if odds_movement < 0:
            signals.append(f"odds_drop={odds_movement:+.3f}")
        if fixture_history_goals >= 2.0:
            signals.append(f"fixture_avg={fixture_history_goals:.1f}≥2.0")

        key = f"{home}v{away}"
        if is_flagged:
            passed = len(signals) >= 2
            if not passed:
                self._audit(key, "RULE4_CONFIRMATION", "BLOCKED",
                           f"Only {len(signals)}/2 signals: {signals}")
            else:
                self._audit(key, "RULE4_CONFIRMATION", "PASSED",
                           f"{len(signals)} signals: {signals}")
            return passed, len(signals), signals
        else:
            # Unflagged matches pass but log signal count
            return True, len(signals), signals

    # ── RULE 5: SELF CHECK OUTPUT ─────────────────────────────────────
    def generate_audit_report(self, batch_picks, batch_name="SLIP"):
        """Generate audit report after each batch of picks."""
        report = []
        report.append(f"🔍 SELF-CHECK AUDIT — {batch_name}")
        report.append(f"📅 {datetime.now(WAT).strftime('%Y-%m-%d %H:%M WAT')}")
        report.append("=" * 40)

        total_memory_hits = 0
        total_slot_traps = 0
        total_confirmation_blocks = 0

        for log in self.audit_log:
            if log['rule'] == 'RULE1_SLOT_REPEAT':
                total_slot_traps += 1
            elif log['rule'] == 'RULE3_MEMORY':
                total_memory_hits += 1
            elif log['rule'] == 'RULE4_CONFIRMATION' and log['action'] == 'BLOCKED':
                total_confirmation_blocks += 1

        report.append(f"\n📊 CORRECTION STATS:")
        report.append(f"  Slot Repeat Traps: {total_slot_traps}")
        report.append(f"  Memory Penalties: {total_memory_hits}")
        report.append(f"  Confirmation Blocks: {total_confirmation_blocks}")
        report.append(f"  Total Corrections: {total_slot_traps + total_memory_hits + total_confirmation_blocks}")

        if self.audit_log:
            report.append(f"\n📋 DETAILED LOG:")
            for log in self.audit_log:
                report.append(f"  [{log['rule']}] {log['matchup']}: {log['action']} — {log['reason']}")

        report.append(f"\n🎯 FINAL PICKS: {len(batch_picks)}")
        for i, p in enumerate(batch_picks, 1):
            flag = '🇪🇸' if p.get('league') == 'spain' else '🇩🇪'
            report.append(f"  {i}. {flag} {p['home']}v{p['away']} [{p.get('tier','?')}] "
                         f"@{p.get('odds',0):.2f} SA={p.get('sa_score',0)}")

        if not batch_picks:
            report.append("  ⚠️ ALL CANDIDATES FILTERED — System detected structural risks")

        report.append(f"\n{'='*40}")
        report.append("ONIMIX AGENT ELITE 🤖")

        self.audit_log = []  # Reset for next batch
        return "\n".join(report)

    # ── HELPERS ────────────────────────────────────────────────────────
    def _slot_to_minutes(self, slot):
        """Convert HH:MM to minutes since midnight."""
        try:
            parts = str(slot).strip()[:5].split(':')
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return None

    def _days_ago(self, timestamp_str):
        """Calculate days since a timestamp."""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(WAT)
            return (now - dt).days
        except:
            return 999

    def _audit(self, matchup, rule, action, reason):
        self.audit_log.append({
            "matchup": matchup,
            "rule": rule,
            "action": action,
            "reason": reason,
            "time": datetime.now(WAT).strftime("%H:%M:%S")
        })

# ══════════════════════════════════════════════════════════════════════
# API & CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def api(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode())
    except:
        return None

def tg_send(text, chat_id):
    try:
        # Split long messages
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            data = json.dumps({"chat_id": chat_id, "text": chunk}).encode()
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

def get_recent_results(league, hours=6):
    """Fetch recent results for a league."""
    cfg = LEAGUES[league]
    now = int(time.time() * 1000)
    start = now - (hours * 3600000)
    results = []
    for pn in range(1, 5):
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
        if len(results) >= int(d.get('data', {}).get('totalNum', 0) if isinstance(d.get('data'), dict) else 0):
            break
    return results

def get_yesterday_results(league):
    """Get yesterday's full results for slot repeat detection."""
    return get_recent_results(league, hours=30)

def parse_result_goals(ev):
    """Extract total goals from a result event."""
    try:
        scores = ev.get('setScore', '') or ev.get('score', '')
        if ':' in str(scores):
            parts = str(scores).split(':')
            return int(parts[0]) + int(parts[1])
        # Try gameScore
        gs = ev.get('gameScore', '')
        if ':' in str(gs):
            parts = str(gs).split(':')
            return int(parts[0]) + int(parts[1])
    except:
        pass
    return None

def build_yesterday_lookup(league):
    """Build lookup of yesterday's results for slot repeat detection."""
    results = get_yesterday_results(league)
    lookup = []
    for ev in results:
        home = ev.get('homeTeamName', '')
        away = ev.get('awayTeamName', '')
        est = ev.get('estimateStartTime', 0)
        ko = ''
        if est:
            ko = datetime.fromtimestamp(est/1000, WAT).strftime('%H:%M')
        goals = parse_result_goals(ev)
        if home and away:
            lookup.append({
                'home': home, 'away': away,
                'kickoff': ko, 'total_goals': goals if goals is not None else 99
            })
    return lookup

def discover_upcoming(league, max_probe=80):
    """Discover upcoming events by probing eventIds ahead of last completed."""
    cfg = LEAGUES[league]
    results = get_recent_results(league, hours=4)
    if not results:
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
        time.sleep(0.3)

    return upcoming

def analyze_prematch(event):
    """Section A: 6-market prematch JSON decoder. Returns score 0-14."""
    mkts = {}
    for m in event.get('markets', []):
        if isinstance(m, dict):
            mkts[(str(m.get('id', '')), m.get('specifier', ''))] = m

    score = 0
    odds = 0.0

    # Market 18 (O/U 1.5)
    for spec in ['total=1.5', '1.5']:
        m = mkts.get(('18', spec))
        if m:
            for o in m.get('outcomes', []):
                desc = o.get('desc', '').lower()
                if 'over' in desc:
                    p = float(o.get('probability', '0') or '0')
                    odds = float(o.get('odds', '0') or '0')
                    if p >= 0.72: score += 4
                    elif p >= 0.65: score += 3
                    elif p >= 0.55: score += 2
                    elif p >= 0.45: score += 1
            break

    # Market 18 (O/U 2.5)
    for spec in ['total=2.5', '2.5']:
        m = mkts.get(('18', spec))
        if m:
            for o in m.get('outcomes', []):
                if 'over' in o.get('desc', '').lower():
                    p = float(o.get('probability', '0') or '0')
                    if p >= 0.55: score += 3
                    elif p >= 0.45: score += 2
                    elif p >= 0.35: score += 1
            break

    # Market 19/20 (Home/Away totals)
    for mid in ['19', '20']:
        for spec in ['total=0.5', '0.5', '']:
            m = mkts.get((mid, spec))
            if m:
                for o in m.get('outcomes', []):
                    if 'over' in o.get('desc', '').lower():
                        p = float(o.get('probability', '0') or '0')
                        if p >= 0.70: score += 2
                        elif p >= 0.55: score += 1
                break

    # Market 29 (BTTS)
    m = mkts.get(('29', ''))
    if m:
        for o in m.get('outcomes', []):
            if 'yes' in o.get('desc', '').lower():
                p = float(o.get('probability', '0') or '0')
                if p >= 0.50: score += 2
                elif p >= 0.35: score += 1

    return score, odds

def classify_matchup(home, away):
    """Classify a matchup as GOLD, SILVER, or NONE."""
    pair = (home, away)
    if pair in TRAP:
        return 'TRAP', 0
    for lg in GOLD:
        if pair in GOLD[lg]:
            return 'GOLD', 100.0
    for lg in SILVER:
        if pair in SILVER[lg]:
            return 'SILVER', 92.9
    return 'NONE', 0

def compute_avg_goals_from_results(home, away, results):
    """Compute avg goals for this matchup from recent results."""
    goals_list = []
    for ev in results:
        h = ev.get('homeTeamName', '')
        a = ev.get('awayTeamName', '')
        if h == home and a == away:
            g = parse_result_goals(ev)
            if g is not None:
                goals_list.append(g)
    return sum(goals_list) / len(goals_list) if goals_list else 0

def compute_team_recent_goals(team, results, last_n=5):
    """Count goals scored by a team in their last N matches."""
    total = 0
    count = 0
    for ev in results:
        h = ev.get('homeTeamName', '')
        a = ev.get('awayTeamName', '')
        g = parse_result_goals(ev)
        if g is None:
            continue
        scores_str = ev.get('setScore', '') or ev.get('score', '') or ev.get('gameScore', '')
        if ':' not in str(scores_str):
            continue
        parts = str(scores_str).split(':')
        try:
            hg, ag = int(parts[0]), int(parts[1])
        except:
            continue
        if h == team:
            total += hg
            count += 1
        elif a == team:
            total += ag
            count += 1
        if count >= last_n:
            break
    return total

def book_slip(picks):
    """Generate SportyBet booking code for the slip."""
    outcomes = []
    for p in picks:
        eid = p.get('eventId', '')
        oid = p.get('outcomeId', '')
        if eid and oid:
            outcomes.append({
                "eventId": eid, "marketId": "18",
                "specifier": "total=1.5", "outcomeId": oid,
            })
    if not outcomes:
        return None
    payload = json.dumps({"selections": outcomes}).encode()
    try:
        req = urllib.request.Request(
            f"{BASE.replace('/factsCenter','')}/orders/share",
            data=payload,
            headers={**HEADERS, "Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
            if d.get('bizCode') == 10000:
                return d.get('data', {}).get('shareCode')
    except:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════
# MAIN RUN — WITH CORRECTION SYSTEM
# ══════════════════════════════════════════════════════════════════════

def run():
    now = datetime.now(WAT)
    print("=" * 60)
    print("VFL GOLD/SILVER SLIP PICKER v2.0")
    print("ONIMIX AGENT ELITE — SELF-VERIFYING CORRECTION SYSTEM")
    print(f"Time: {now.strftime('%Y-%m-%d %H:%M WAT')}")
    print("=" * 60)

    # Initialize Correction System
    cs = CorrectionSystem()
    print("\n🛡️ Correction System loaded")

    # Load proven odds database
    proven_data = load_proven_odds()
    if proven_data and proven_data.get('total_settled', 0) > 0:
        print(f"📊 Proven Odds: {proven_data.get('total_settled',0)} settled, "
              f"{proven_data.get('overall_hit_pct','N/A')} hit rate")
    else:
        print("📊 Proven Odds: building database...")
    mem_count = len(cs.memory.get("failures", []))
    print(f"   Memory: {mem_count} recorded failures")

    # Pre-fetch yesterday's results for slot repeat detection
    yesterday_lookup = {}
    for lg in LEAGUES:
        yesterday_lookup[lg] = build_yesterday_lookup(lg)
        print(f"   Yesterday {lg}: {len(yesterday_lookup[lg])} results loaded")

    # Pre-fetch recent results for confirmation signals
    recent_results = {}
    for lg in LEAGUES:
        recent_results[lg] = get_recent_results(lg, hours=24)
        print(f"   Recent {lg}: {len(recent_results[lg])} results (24h)")

    # Discover upcoming matches
    all_candidates = []
    skipped_corrections = []

    for lg in LEAGUES:
        print(f"\n{'─'*40}")
        print(f"Discovering {lg.title()} upcoming...")
        upcoming = discover_upcoming(lg, max_probe=60)
        print(f"  Found {len(upcoming)} upcoming")

        for ev in upcoming:
            home = ev.get('homeTeamName', '')
            away = ev.get('awayTeamName', '')
            tier, hist_rate = classify_matchup(home, away)

            if tier == 'NONE' or tier == 'TRAP':
                continue

            sa_score, ou15_odds = analyze_prematch(ev)

            # STRICT: odds must be 1.38-1.60
            if ou15_odds < SWEET[0] or ou15_odds > SWEET[1]:
                print(f"  SKIP {home}v{away} — odds {ou15_odds:.2f} outside {SWEET[0]}-{SWEET[1]}")
                continue

            # STRICT: Section A must be >= 6/14
            if sa_score < 6:
                print(f"  SKIP {home}v{away} — SA={sa_score}/14 too low")
                continue

            est = ev.get('estimateStartTime', 0)
            ko = datetime.fromtimestamp(est/1000, WAT).strftime('%H:%M') if est else '??:??'

            # ═══════════════════════════════════════════════════
            # CORRECTION SYSTEM CHECKS (5 Rules)
            # ═══════════════════════════════════════════════════

            # RULE 1: Slot Repeat Trap
            is_trapped, trap_reason = cs.check_slot_repeat_trap(
                home, away, ko, yesterday_lookup.get(lg, []))
            if is_trapped:
                print(f"  🚫 RULE1 SKIP {home}v{away}: {trap_reason}")
                skipped_corrections.append({
                    'home': home, 'away': away, 'rule': 'SLOT_REPEAT', 'reason': trap_reason
                })
                continue

            # RULE 2: Failure Root Cause Analysis
            risk_level, classification, rca_detail = cs.analyze_failure_root_cause(home, away, ko)
            if risk_level == "HIGH":
                print(f"  🚫 RULE2 SKIP {home}v{away}: {classification} — {rca_detail}")
                skipped_corrections.append({
                    'home': home, 'away': away, 'rule': 'ROOT_CAUSE', 'reason': rca_detail
                })
                continue

            # RULE 3: Memory Learning — adjust confidence
            base_confidence = hist_rate / 100.0
            adj_confidence, penalty, mem_reason = cs.apply_memory_learning(
                home, away, base_confidence)
            if penalty:
                print(f"  ⚠️ RULE3 {home}v{away}: {mem_reason}")

            is_flagged = (risk_level == "MEDIUM" or penalty)

            # RULE 4: Confirmation Filter
            avg_goals = compute_avg_goals_from_results(
                home, away, recent_results.get(lg, []))
            team_goals = max(
                compute_team_recent_goals(home, recent_results.get(lg, []), 5),
                compute_team_recent_goals(away, recent_results.get(lg, []), 5)
            )
            # Simple odds movement = 0 (no historical odds tracking yet)
            odds_movement = 0
            fixture_avg = avg_goals

            passed, sig_count, sig_detail = cs.check_confirmation_filter(
                home, away,
                avg_goals=avg_goals,
                team_recent_goals=team_goals,
                odds_movement=odds_movement,
                fixture_history_goals=fixture_avg,
                is_flagged=is_flagged
            )

            if not passed:
                print(f"  🚫 RULE4 SKIP {home}v{away}: Failed confirmation ({sig_count}/2 signals)")
                skipped_corrections.append({
                    'home': home, 'away': away, 'rule': 'CONFIRMATION',
                    'reason': f"Only {sig_count}/2 signals: {sig_detail}"
                })
                continue

            # RULE 6: PROVEN ODDS CHECK
            matchup_key = f"{lg}:{home} vs {away}"
            po_boost, po_reason = get_proven_odds_boost(ou15_odds, matchup_key, proven_data)
            if po_boost <= -3:
                print(f"  🚫 RULE6 SKIP {home}v{away}: PROVEN TRAP — {po_reason}")
                skipped_corrections.append({
                    'home': home, 'away': away, 'rule': 'PROVEN_ODDS',
                    'reason': po_reason
                })
                continue

            # Get outcomeId for Over 1.5
            oid = ''
            for m in ev.get('markets', []):
                if str(m.get('id')) == '18' and 'total=1.5' in m.get('specifier', ''):
                    for o in m.get('outcomes', []):
                        if 'over' in o.get('desc', '').lower():
                            oid = str(o.get('id', ''))

            candidate = {
                'home': home, 'away': away, 'league': lg,
                'tier': tier, 'hist_rate': hist_rate, 'sa_score': sa_score,
                'odds': ou15_odds, 'eventId': ev.get('eventId', ''),
                'gameId': ev.get('gameId', ''), 'outcomeId': oid,
                'kickoff': ko, 'est': est,
                'adj_confidence': adj_confidence,
                'signals': sig_count,
                'combined': (sa_score * adj_confidence) + (14 if tier == 'GOLD' else 13) + po_boost,
                'proven_boost': po_boost,
            }
            all_candidates.append(candidate)
            flag = '🇪🇸' if lg == 'spain' else '🇩🇪'
            tier_icon = '🥇' if tier == 'GOLD' else '🥈'
            po_tag = f" PO={po_boost:+d}" if po_boost != 0 else ""
            print(f"  ✅ {flag}{tier_icon} {home}v{away} SA={sa_score} @{ou15_odds:.2f} "
                  f"conf={adj_confidence:.2f} sigs={sig_count}{po_tag} KO={ko}")

    if not all_candidates:
        print("\n❌ No qualified picks after correction system filtering.")
        audit = cs.generate_audit_report([], "SLIP PICKER v2.0")
        msg = ("🔍 VFL Slip Picker v2.0: No qualified picks after "
               f"correction filtering.\n{len(skipped_corrections)} candidates rejected.\n"
               "Will retry next scan.\n\n" + audit)
        tg_send(msg, TG_CHAT)
        return

    # Sort: GOLD first, then by adjusted combined score
    all_candidates.sort(key=lambda x: (
        0 if x['tier']=='GOLD' else 1,
        -x['combined'],
        -x['adj_confidence'],
        -x['odds']
    ))

    print(f"\n📊 Total qualified candidates: {len(all_candidates)}")
    print(f"   Corrected rejections: {len(skipped_corrections)}")

    # Build slips: 3-5 legs each
    slips = []
    # SLIP 1: SAFE 3-LEG
    slip1 = all_candidates[:3] if len(all_candidates) >= 3 else []
    if len(slip1) == 3:
        odds1 = 1.0
        for s in slip1: odds1 *= s['odds']
        slips.append({'name': 'SAFE 3-LEG', 'picks': slip1, 'odds': odds1, 'legs': 3})

    # SLIP 2: STANDARD 4-LEG
    slip2 = all_candidates[:4] if len(all_candidates) >= 4 else []
    if len(slip2) == 4:
        odds2 = 1.0
        for s in slip2: odds2 *= s['odds']
        slips.append({'name': 'STANDARD 4-LEG', 'picks': slip2, 'odds': odds2, 'legs': 4})

    # SLIP 3: POWER 5-LEG
    slip3 = all_candidates[:5] if len(all_candidates) >= 5 else []
    if len(slip3) == 5:
        odds3 = 1.0
        for s in slip3: odds3 *= s['odds']
        slips.append({'name': 'POWER 5-LEG', 'picks': slip3, 'odds': odds3, 'legs': 5})

    if not slips:
        print("❌ Not enough candidates for even a 3-leg slip")
        audit = cs.generate_audit_report(all_candidates, "SLIP PICKER v2.0")
        tg_send(f"🔍 Slip Picker v2.0: Only {len(all_candidates)} candidates — "
                f"need 3 minimum.\n\n{audit}", TG_CHAT)
        return

    # Book codes
    for slip in slips:
        code = book_slip(slip['picks'])
        slip['code'] = code

    # RULE 5: Generate Audit Report
    audit_report = cs.generate_audit_report(
        slips[0]['picks'] if slips else [], "SLIP PICKER v2.0")

    # Build Telegram message
    msg = f"🎯 VFL GOLD/SILVER SLIPS v2.0\n"
    msg += f"🛡️ CORRECTION SYSTEM ACTIVE\n"
    msg += f"📅 {now.strftime('%Y-%m-%d %H:%M WAT')}\n"
    msg += f"{'='*35}\n\n"

    for slip in slips:
        msg += f"📋 {slip['name']} ({slip['odds']:.2f}x)\n"
        if slip.get('code'):
            msg += f"🎫 Code: {slip['code']}\n"
        msg += f"{'-'*30}\n"
        for i, p in enumerate(slip['picks'], 1):
            flag = '🇪🇸' if p['league'] == 'spain' else '🇩🇪'
            tier_icon = '🥇' if p['tier'] == 'GOLD' else '🥈'
            msg += f"{i}. {flag}{tier_icon} {p['home']} v {p['away']}\n"
            msg += f"   O1.5 @{p['odds']:.2f} | SA={p['sa_score']}/14 | {p['tier']} ({p['hist_rate']}%)\n"
            msg += f"   Conf={p['adj_confidence']:.2f} | Sigs={p['signals']} | KO: {p['kickoff']}\n"
        msg += f"\n"

    msg += f"{'='*35}\n"
    msg += f"🛡️ Corrections: {len(skipped_corrections)} candidates rejected\n"
    msg += f"Odds range: {SWEET[0]}-{SWEET[1]} ONLY\n"
    msg += f"ONIMIX AGENT ELITE 🤖"

    sent = tg_send(msg, TG_CHAT)
    print(f"\n{'='*60}")
    print(f"Telegram picks: {'✅ Sent' if sent else '❌ Failed'}")

    # Send audit report separately
    tg_send(audit_report, TG_CHAT)
    print(f"Telegram audit: sent")

    # Save picks for tracking
    save_data = {
        'timestamp': now.isoformat(),
        'version': 'v2.0_correction',
        'corrections_applied': len(skipped_corrections),
        'skipped': skipped_corrections,
        'slips': [{
            'name': s['name'], 'odds': s['odds'], 'code': s.get('code'),
            'picks': [{
                'home': p['home'], 'away': p['away'], 'league': p['league'],
                'tier': p['tier'], 'hist_rate': p['hist_rate'],
                'sa_score': p['sa_score'], 'odds': p['odds'],
                'adj_confidence': p['adj_confidence'], 'signals': p['signals'],
                'eventId': p['eventId'], 'gameId': p['gameId'],
                'kickoff': p['kickoff'], 'status': 'pending'
            } for p in s['picks']]
        } for s in slips]
    }

    with open('/tmp/slip_picks_v2.json', 'w') as f:
        json.dump(save_data, f, indent=2)
    print(f"Picks saved to /tmp/slip_picks_v2.json")

    # Push to GitHub
    try:
        fname = f"data/slips_v2_{now.strftime('%Y%m%d_%H%M')}.json"
        content = json.dumps(save_data, indent=2)
        import base64
        b64 = base64.b64encode(content.encode()).decode()
        gh_token = ''
        try:
            import subprocess
            r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
            gh_token = r.stdout.strip()
        except:
            pass
        if gh_token:
            payload = json.dumps({"message": f"Slip v2.0 {now.strftime('%Y-%m-%d %H:%M')}", "content": b64}).encode()
            req = urllib.request.Request(
                f"https://api.github.com/repos/Onimix/onimix-vfl-elite/contents/{fname}",
                data=payload,
                headers={"Authorization": f"token {gh_token}", "Content-Type": "application/json"},
                method="PUT"
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status in (200, 201):
                    print(f"✅ Saved to GitHub: {fname}")
    except Exception as e:
        print(f"  GitHub save: {e}")

    return save_data

if __name__ == "__main__":
    run()
