#!/usr/bin/env python3
"""
MEGA AUDIT v3.0 - ONIMIX AGENT ELITE CORRECTION SYSTEM
=======================================================
Matchup-First Strategy + Self-Verifying Correction System.
Target: 20,000x combined odds with structural pattern detection.

5 Mandatory Rules:
  1. SLOT REPEAT TRAP — Same time block + prev day fixture + low scoring = SKIP
  2. FAILURE ROOT CAUSE ANALYSIS — Trace prev day pattern, classify traps
  3. MEMORY LEARNING — 2+ same failures → reduce confidence 40%
  4. CONFIRMATION FILTER — Flagged match needs 2+ positive signals
  5. SELF CHECK OUTPUT — Audit report after each batch

"You are not predicting matches. You are detecting structural football
simulation patterns." — ONIMIX ELITE DIRECTIVE
"""

import json, time, math, hashlib, os, sys, ssl, urllib.request
from datetime import datetime, timezone, timedelta

WAT = timezone(timedelta(hours=1))
BASE = 'https://www.sportybet.com/api/ng/factsCenter'
SPORT = 'sr:sport:202120001'
BOT_TOKEN = '8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow'
CHAT_ID = '1745848158'
SWEET = (1.38, 1.60)
MIN_SA = 6
TARGET_ODDS = 20000
MEMORY_FILE = "/tmp/onimix_failure_memory.json"
PROVEN_ODDS_URL = f'https://raw.githubusercontent.com/Onimix/onimix-vfl-elite/main/data/proven_odds.json'

# ══════════════════════════════════════════════════════════════════════
# PROVEN ODDS INTEGRATION (from Odds Tracker v1.0)
# ══════════════════════════════════════════════════════════════════════

def load_proven_odds():
    """Load proven odds database from GitHub (built by Odds Tracker agent)."""
    try:
        req = urllib.request.Request(PROVEN_ODDS_URL, headers={
            'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            data = json.loads(r.read().decode())
        return data
    except:
        return {}

def get_proven_odds_boost(odds_value, matchup_key, proven_data):
    """
    Check if this odds value and matchup have a proven track record.
    Returns (boost, reason):
      boost > 0: confidence boost (proven winner)
      boost < 0: confidence penalty (proven loser)
      boost = 0: no data
    """
    if not proven_data or proven_data.get('total_settled', 0) < 20:
        return 0, "insufficient data"

    boost = 0
    reasons = []

    # Check odds bucket hit rate
    buckets = proven_data.get('odds_buckets', {})
    for bk, bv in buckets.items():
        try:
            lo = float(bk.split('-')[0])
            hi = float(bk.split('-')[1])
            if lo <= odds_value <= hi and bv.get('reliable', False):
                rate = bv.get('hit_rate', 0)
                if rate >= 0.80:
                    boost += 2
                    reasons.append(f"odds@{bk} {rate*100:.0f}% hit")
                elif rate >= 0.70:
                    boost += 1
                    reasons.append(f"odds@{bk} {rate*100:.0f}% hit")
                elif rate < 0.50:
                    boost -= 2
                    reasons.append(f"odds@{bk} DANGER {rate*100:.0f}%")
                break
        except:
            pass

    # Check matchup-specific odds performance
    matchup_odds = proven_data.get('matchup_odds', {})
    if matchup_key in matchup_odds:
        mo = matchup_odds[matchup_key]
        if mo.get('reliable', False):
            mrate = mo.get('hit_rate', 0)
            if mrate >= 0.85:
                boost += 3
                reasons.append(f"matchup {mrate*100:.0f}% proven")
            elif mrate >= 0.70:
                boost += 1
                reasons.append(f"matchup {mrate*100:.0f}% OK")
            elif mrate < 0.50:
                boost -= 3
                reasons.append(f"matchup {mrate*100:.0f}% TRAP")

    # Check SA score correlation
    sa_stats = proven_data.get('sa_score_stats', {})

    reason = " | ".join(reasons) if reasons else "no proven data"
    return boost, reason

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ── MATCHUP DATABASE (verified April 1-14, 2026) ──────────────────────

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

# ══════════════════════════════════════════════════════════════════════
# CORRECTION SYSTEM (same as slip_picker_v2.py for consistency)
# ══════════════════════════════════════════════════════════════════════

class CorrectionSystem:
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
        except:
            pass

    def record_failure(self, home, away, league, kickoff_time, score, reason=""):
        key = f"{home}v{away}"
        slot = kickoff_time[:5] if len(kickoff_time) >= 5 else kickoff_time
        entry = {
            "matchup": key, "league": league, "slot": slot, "score": score,
            "reason": reason, "timestamp": datetime.now(WAT).isoformat(),
            "date": datetime.now(WAT).strftime("%Y-%m-%d")
        }
        self.memory["failures"].append(entry)
        if key not in self.memory["matchup_failures"]:
            self.memory["matchup_failures"][key] = []
        self.memory["matchup_failures"][key].append(entry)
        if slot not in self.memory["slot_patterns"]:
            self.memory["slot_patterns"][slot] = []
        self.memory["slot_patterns"][slot].append(entry)
        self._save_memory()

    def check_slot_repeat_trap(self, home, away, kickoff_slot, yesterday_results):
        key = f"{home}v{away}"
        slot_min = self._slot_to_minutes(kickoff_slot)
        if slot_min is None:
            return False, ""
        for res in yesterday_results:
            if f"{res.get('home','')}v{res.get('away','')}" != key:
                continue
            res_min = self._slot_to_minutes(res.get('kickoff', ''))
            if res_min is None:
                continue
            if abs(slot_min - res_min) > 10:
                continue
            if res.get('total_goals', 99) <= 1:
                reason = (f"SLOT REPEAT: {key}@{kickoff_slot} — "
                         f"yesterday@{res.get('kickoff','')} scored {res.get('total_goals',0)}")
                self._audit(key, "RULE1", "HARD SKIP", reason)
                return True, reason
        return False, ""

    def analyze_failure_root_cause(self, home, away, kickoff_slot):
        key = f"{home}v{away}"
        recent = self.memory.get("matchup_failures", {}).get(key, [])
        slot = kickoff_slot[:5]
        if not recent:
            return "LOW", "CLEAN", ""
        slot_fails = [f for f in recent
                     if abs((self._slot_to_minutes(f.get('slot','')) or 999)
                           - (self._slot_to_minutes(slot) or 0)) <= 10]
        if len(slot_fails) >= 2:
            return "HIGH", "TEMPORAL_PATTERN_TRAP", (
                f"{key} failed {len(slot_fails)}x in slot ~{slot}")
        last7 = [f for f in recent if self._days_ago(f.get('timestamp','')) <= 7]
        if len(last7) >= 2:
            return "MEDIUM", "RECURRING_FAILURE", f"{key} failed {len(last7)}x in 7d"
        if recent:
            return "LOW", "SINGLE_FAILURE", f"{key} had 1 prior failure"
        return "LOW", "CLEAN", ""

    def apply_memory_learning(self, home, away, base_confidence):
        key = f"{home}v{away}"
        failures = self.memory.get("matchup_failures", {}).get(key, [])
        recent = [f for f in failures if self._days_ago(f.get('timestamp','')) <= 14]
        if len(recent) >= 3:
            adj = base_confidence * 0.40
            r = f"MEMORY: {key} {len(recent)}x/14d → 60% cut"
            self._audit(key, "RULE3", "HEAVY", r)
            return adj, True, r
        elif len(recent) >= 2:
            adj = base_confidence * 0.60
            r = f"MEMORY: {key} {len(recent)}x/14d → 40% cut"
            self._audit(key, "RULE3", "STANDARD", r)
            return adj, True, r
        elif len(recent) == 1:
            adj = base_confidence * 0.85
            r = f"MEMORY: {key} 1x/14d → 15% cut"
            self._audit(key, "RULE3", "LIGHT", r)
            return adj, True, r
        return base_confidence, False, ""

    def check_confirmation_filter(self, home, away, avg_goals, team_recent_goals,
                                   odds_movement, fixture_history_goals, is_flagged=False):
        signals = []
        if avg_goals >= 2.5:
            signals.append(f"avg={avg_goals:.1f}")
        if team_recent_goals >= 3:
            signals.append(f"team={team_recent_goals}")
        if odds_movement < 0:
            signals.append(f"drop={odds_movement:+.3f}")
        if fixture_history_goals >= 2.0:
            signals.append(f"fix={fixture_history_goals:.1f}")
        key = f"{home}v{away}"
        if is_flagged:
            passed = len(signals) >= 2
            self._audit(key, "RULE4", "PASSED" if passed else "BLOCKED",
                       f"{len(signals)} sigs: {signals}")
            return passed, len(signals), signals
        return True, len(signals), signals

    def generate_audit_report(self, batch_picks, batch_name="MEGA"):
        rpt = [f"🔍 SELF-CHECK AUDIT — {batch_name}",
               f"📅 {datetime.now(WAT).strftime('%Y-%m-%d %H:%M WAT')}",
               "=" * 40]
        s1 = sum(1 for l in self.audit_log if l['rule'] == 'RULE1')
        s3 = sum(1 for l in self.audit_log if l['rule'] == 'RULE3')
        s4 = sum(1 for l in self.audit_log if l['rule'] == 'RULE4' and l['action'] == 'BLOCKED')
        rpt.append(f"\n📊 CORRECTIONS: Slot={s1} Memory={s3} Confirm={s4} Total={s1+s3+s4}")
        if self.audit_log:
            rpt.append("\n📋 LOG:")
            for l in self.audit_log:
                rpt.append(f"  [{l['rule']}] {l['matchup']}: {l['action']} — {l['reason']}")
        rpt.append(f"\n🎯 FINAL: {len(batch_picks)} picks")
        for i, p in enumerate(batch_picks, 1):
            fl = '🇪🇸' if p.get('league','') == 'spain' else '🇩🇪'
            rpt.append(f"  {i}. {fl} {p.get('home','')}v{p.get('away','')} "
                       f"[{p.get('tier','?')}] @{p.get('odds',0):.2f}")
        if not batch_picks:
            rpt.append("  ⚠️ ALL FILTERED — structural risks detected")
        rpt.extend(["", "=" * 40, "ONIMIX AGENT ELITE 🤖"])
        self.audit_log = []
        return "\n".join(rpt)

    def _slot_to_minutes(self, slot):
        try:
            p = str(slot).strip()[:5].split(':')
            return int(p[0]) * 60 + int(p[1])
        except:
            return None

    def _days_ago(self, ts):
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            return (datetime.now(WAT) - dt).days
        except:
            return 999

    def _audit(self, matchup, rule, action, reason):
        self.audit_log.append({"matchup": matchup, "rule": rule,
                               "action": action, "reason": reason,
                               "time": datetime.now(WAT).strftime("%H:%M:%S")})

# ══════════════════════════════════════════════════════════════════════
# API HELPERS
# ══════════════════════════════════════════════════════════════════════

def api(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode())
    except:
        return None

def tg_send(text):
    try:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            data = json.dumps({"chat_id": CHAT_ID, "text": chunk}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                pass
            time.sleep(0.3)
        return True
    except Exception as e:
        print(f"TG error: {e}")
        return False

def get_recent_results(league, hours=6):
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
    return results

def parse_result_goals(ev):
    try:
        for key in ['setScore', 'score', 'gameScore']:
            s = ev.get(key, '')
            if ':' in str(s):
                p = str(s).split(':')
                return int(p[0]) + int(p[1])
    except:
        pass
    return None

def build_yesterday_lookup(league):
    results = get_recent_results(league, hours=30)
    lookup = []
    for ev in results:
        h, a = ev.get('homeTeamName',''), ev.get('awayTeamName','')
        est = ev.get('estimateStartTime', 0)
        ko = datetime.fromtimestamp(est/1000, WAT).strftime('%H:%M') if est else ''
        goals = parse_result_goals(ev)
        if h and a:
            lookup.append({'home': h, 'away': a, 'kickoff': ko,
                          'total_goals': goals if goals is not None else 99})
    return lookup

def compute_avg_goals(home, away, results):
    gl = []
    for ev in results:
        if ev.get('homeTeamName','') == home and ev.get('awayTeamName','') == away:
            g = parse_result_goals(ev)
            if g is not None:
                gl.append(g)
    return sum(gl)/len(gl) if gl else 0

def compute_team_goals(team, results, n=5):
    total = count = 0
    for ev in results:
        h, a = ev.get('homeTeamName',''), ev.get('awayTeamName','')
        s = ev.get('setScore','') or ev.get('score','') or ev.get('gameScore','')
        if ':' not in str(s): continue
        try:
            hg, ag = [int(x) for x in str(s).split(':')]
        except: continue
        if h == team: total += hg; count += 1
        elif a == team: total += ag; count += 1
        if count >= n: break
    return total

def discover_upcoming(league, max_probe=80):
    cfg = LEAGUES[league]
    results = get_recent_results(league, hours=4)
    if not results:
        return []
    max_eid = 0
    for ev in results:
        try:
            n = int(str(ev.get('eventId','')).replace('sr:match:',''))
            if n > max_eid: max_eid = n
        except: pass
    if not max_eid:
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
            misses += 1; continue
        ev = d.get('data', {})
        if not ev:
            misses += 1; continue
        ms = ev.get('matchStatus', '')
        if ms not in ('Not start','not_started','',None):
            misses = 0; continue
        est = ev.get('estimateStartTime', 0)
        if est <= now_ms:
            misses = 0; continue
        cat = ev.get('sport',{}).get('category',{}).get('name','')
        if cat.lower() != cfg['catName'].lower():
            misses = 0; continue
        upcoming.append(ev)
        misses = 0
        time.sleep(0.3)
    return upcoming

def classify_matchup(home, away):
    pair = (home, away)
    if pair in TRAP: return 'TRAP', 0
    for lg in GOLD:
        if pair in GOLD[lg]: return 'GOLD', 100.0
    for lg in SILVER:
        if pair in SILVER[lg]: return 'SILVER', 92.9
    return 'NONE', 0

def analyze_prematch(event):
    mkts = {}
    for m in event.get('markets', []):
        if isinstance(m, dict):
            mkts[(str(m.get('id','')), m.get('specifier',''))] = m
    score = 0; odds = 0.0
    for spec in ['total=1.5','1.5']:
        m = mkts.get(('18', spec))
        if m:
            for o in m.get('outcomes', []):
                if 'over' in o.get('desc','').lower():
                    p = float(o.get('probability','0') or '0')
                    odds = float(o.get('odds','0') or '0')
                    if p >= 0.72: score += 4
                    elif p >= 0.65: score += 3
                    elif p >= 0.55: score += 2
                    elif p >= 0.45: score += 1
            break
    for spec in ['total=2.5','2.5']:
        m = mkts.get(('18', spec))
        if m:
            for o in m.get('outcomes', []):
                if 'over' in o.get('desc','').lower():
                    p = float(o.get('probability','0') or '0')
                    if p >= 0.55: score += 3
                    elif p >= 0.45: score += 2
                    elif p >= 0.35: score += 1
            break
    for mid in ['19','20']:
        for spec in ['total=0.5','0.5','']:
            m = mkts.get((mid, spec))
            if m:
                for o in m.get('outcomes', []):
                    if 'over' in o.get('desc','').lower():
                        p = float(o.get('probability','0') or '0')
                        if p >= 0.70: score += 2
                        elif p >= 0.55: score += 1
                break
    m = mkts.get(('29',''))
    if m:
        for o in m.get('outcomes', []):
            if 'yes' in o.get('desc','').lower():
                p = float(o.get('probability','0') or '0')
                if p >= 0.50: score += 2
                elif p >= 0.35: score += 1
    return score, odds

# ══════════════════════════════════════════════════════════════════════
# MAIN MEGA AUDIT PIPELINE WITH CORRECTION SYSTEM
# ══════════════════════════════════════════════════════════════════════

def run_mega_audit():
    now = datetime.now(WAT)
    print("=" * 60)
    print("MEGA AUDIT v3.0 — ONIMIX AGENT ELITE")
    print("SELF-VERIFYING CORRECTION SYSTEM ACTIVE")
    print(f"Time: {now.strftime('%Y-%m-%d %H:%M WAT')}")
    print("=" * 60)

    cs = CorrectionSystem()
    print(f"\n🛡️ Correction System: {len(cs.memory.get('failures',[]))} failures in memory")

    # Load proven odds database from Odds Tracker
    proven_data = load_proven_odds()
    if proven_data and proven_data.get('total_settled', 0) > 0:
        print(f"📊 Proven Odds loaded: {proven_data.get('total_settled',0)} settled, "
              f"{proven_data.get('overall_hit_pct','N/A')} hit rate")
    else:
        print("📊 Proven Odds: no data yet (tracker building database)")

    # Pre-fetch yesterday & recent results
    yesterday = {}
    recent = {}
    for lg in LEAGUES:
        yesterday[lg] = build_yesterday_lookup(lg)
        recent[lg] = get_recent_results(lg, hours=24)
        print(f"  {lg}: {len(yesterday[lg])} yesterday, {len(recent[lg])} recent")

    # Discover upcoming
    all_upcoming = []
    for lg in LEAGUES:
        print(f"\nDiscovering {lg.title()}...")
        up = discover_upcoming(lg, max_probe=60)
        print(f"  Found {len(up)} upcoming")
        for ev in up:
            all_upcoming.append({'league': lg, 'event': ev})

    if not all_upcoming:
        print("\nNo upcoming matches. VFL may be in maintenance.")
        tg_send("🏆 Mega Audit v3.0: No upcoming matches. Will retry.")
        return None

    # Filter through matchup database + correction system
    candidates = []
    skipped = []

    for item in all_upcoming:
        lg = item['league']
        ev = item['event']
        home = ev.get('homeTeamName', '')
        away = ev.get('awayTeamName', '')
        tier, hist_rate = classify_matchup(home, away)

        if tier in ('NONE', 'TRAP'):
            continue

        sa, odds = analyze_prematch(ev)

        if odds < SWEET[0] or odds > SWEET[1]:
            continue
        if sa < MIN_SA:
            continue

        est = ev.get('estimateStartTime', 0)
        ko = datetime.fromtimestamp(est/1000, WAT).strftime('%H:%M') if est else '??:??'

        # ═══ CORRECTION RULES ═══

        # RULE 1: Slot Repeat Trap
        trapped, trap_r = cs.check_slot_repeat_trap(home, away, ko, yesterday.get(lg, []))
        if trapped:
            print(f"  🚫 R1 {home}v{away}: {trap_r}")
            skipped.append({'match': f"{home}v{away}", 'rule': 'SLOT_REPEAT', 'reason': trap_r})
            continue

        # RULE 2: Root Cause Analysis
        risk, cls, rca = cs.analyze_failure_root_cause(home, away, ko)
        if risk == "HIGH":
            print(f"  🚫 R2 {home}v{away}: {cls}")
            skipped.append({'match': f"{home}v{away}", 'rule': 'ROOT_CAUSE', 'reason': rca})
            continue

        # RULE 3: Memory Learning
        base_conf = hist_rate / 100.0
        adj_conf, penalty, mem_r = cs.apply_memory_learning(home, away, base_conf)
        is_flagged = (risk == "MEDIUM" or penalty)

        # RULE 4: Confirmation Filter
        avg_g = compute_avg_goals(home, away, recent.get(lg, []))
        team_g = max(compute_team_goals(home, recent.get(lg,[]),5),
                     compute_team_goals(away, recent.get(lg,[]),5))
        passed, sigs, sig_d = cs.check_confirmation_filter(
            home, away, avg_g, team_g, 0, avg_g, is_flagged)
        if not passed:
            print(f"  🚫 R4 {home}v{away}: {sigs}/2 signals")
            skipped.append({'match': f"{home}v{away}", 'rule': 'CONFIRMATION',
                           'reason': f"{sigs}/2: {sig_d}"})
            continue

        # RULE 6: PROVEN ODDS CHECK (from Odds Tracker database)
        matchup_key = f"{lg}:{home} vs {away}"
        po_boost, po_reason = get_proven_odds_boost(odds, matchup_key, proven_data)
        if po_boost <= -3:
            print(f"  🚫 R6 {home}v{away}: PROVEN TRAP — {po_reason}")
            skipped.append({'match': f"{home}v{away}", 'rule': 'PROVEN_ODDS',
                           'reason': po_reason})
            continue

        # Get outcomeId
        oid = ''
        for m in ev.get('markets', []):
            if str(m.get('id')) == '18' and 'total=1.5' in m.get('specifier',''):
                for o in m.get('outcomes', []):
                    if 'over' in o.get('desc','').lower():
                        oid = str(o.get('id',''))

        # Combined score now includes proven odds boost
        combined = (sa * adj_conf) + (14 if tier == 'GOLD' else 13) + po_boost
        candidates.append({
            'home': home, 'away': away, 'league': lg,
            'tier': tier, 'hist_rate': hist_rate, 'sa_score': sa,
            'odds': odds, 'eventId': ev.get('eventId',''),
            'outcomeId': oid, 'kickoff': ko, 'est': est,
            'adj_confidence': adj_conf, 'signals': sigs,
            'combined': combined, 'proven_boost': po_boost,
            'proven_reason': po_reason
        })
        fl = '🇪🇸' if lg == 'spain' else '🇩🇪'
        po_tag = f" PO={po_boost:+d}" if po_boost != 0 else ""
        print(f"  ✅ {fl} {home}v{away} [{tier}] SA={sa} @{odds:.2f} conf={adj_conf:.2f}{po_tag}")

    if not candidates:
        print("\nNo qualified candidates after corrections.")
        audit = cs.generate_audit_report([], "MEGA AUDIT v3.0")
        tg_send(f"🏆 Mega Audit v3.0: 0 qualified picks.\n"
                f"{len(skipped)} rejected by corrections.\n\n{audit}")
        return None

    # Sort by combined score
    candidates.sort(key=lambda x: (
        0 if x['tier']=='GOLD' else 1, -x['combined'], -x['adj_confidence']))

    # Select picks to hit TARGET_ODDS
    avg_odds = sum(c['odds'] for c in candidates) / len(candidates)
    need = max(3, math.ceil(math.log(TARGET_ODDS) / math.log(avg_odds)))
    selected = candidates[:min(need, len(candidates))]

    total_odds = 1.0
    win_prob = 1.0
    for s in selected:
        total_odds *= s['odds']
        win_prob *= (s['adj_confidence'])

    print(f"\n{'='*60}")
    print(f"SELECTED {len(selected)} PICKS | {total_odds:,.0f}x | Win: {win_prob*100:.1f}%")
    for i, c in enumerate(selected, 1):
        print(f"  {i}. [{c['tier']}] {c['league']}: {c['home']}v{c['away']} "
              f"@{c['odds']} SA={c['sa_score']} conf={c['adj_confidence']:.2f}")

    # Book
    selections = []
    for s in selected:
        if s['eventId'] and s['outcomeId']:
            selections.append({
                "eventId": str(s['eventId']), "marketId": "18",
                "specifier": "total=1.5", "outcomeId": str(s['outcomeId'])
            })
    booking_code = None
    if selections:
        try:
            payload = json.dumps({"selections": selections}).encode()
            req = urllib.request.Request(
                f"{BASE.replace('/factsCenter','')}/orders/share",
                data=payload,
                headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                bd = json.loads(r.read().decode())
                booking_code = bd.get('data',{}).get('shareCode') or bd.get('data',{}).get('code')
        except:
            pass

    # RULE 5: Audit Report
    audit = cs.generate_audit_report(selected, "MEGA AUDIT v3.0")

    # Telegram
    msg = [f"🏆 MEGA AUDIT v3.0 — ELITE CORRECTION",
           f"🛡️ {len(skipped)} candidates filtered by corrections",
           f"💰 {len(selected)} picks | {total_odds:,.0f}x | Win: {win_prob*100:.1f}%", ""]
    for i, c in enumerate(selected, 1):
        fl = "🇪🇸" if c['league'] == 'spain' else "🇩🇪"
        ico = "🥇" if c['tier'] == 'GOLD' else "🥈"
        msg.append(f"{i}. {fl}{ico} {c['home']} v {c['away']}")
        msg.append(f"   O1.5 @{c['odds']:.2f} | SA={c['sa_score']} | "
                   f"Conf={c['adj_confidence']:.2f} | {c['tier']} | KO:{c['kickoff']}")
    if booking_code:
        msg.append(f"\n📋 Code: {booking_code}")
    msg.extend(["", f"Odds: {SWEET[0]}-{SWEET[1]} STRICT",
                f"⏰ {now.strftime('%H:%M WAT %Y-%m-%d')}",
                "ONIMIX AGENT ELITE 🤖"])
    tg_send("\n".join(msg))
    tg_send(audit)

    # Save
    result = {
        'timestamp': now.isoformat(), 'version': 'v3.0_correction',
        'total_odds': total_odds, 'win_prob': win_prob,
        'booking_code': booking_code, 'corrections': len(skipped),
        'skipped': skipped,
        'picks': [{
            'home': s['home'], 'away': s['away'], 'league': s['league'],
            'tier': s['tier'], 'odds': s['odds'], 'sa_score': s['sa_score'],
            'adj_confidence': s['adj_confidence'], 'signals': s['signals'],
            'eventId': s['eventId'], 'kickoff': s['kickoff'], 'status': 'pending'
        } for s in selected]
    }
    with open('/tmp/mega_audit_v3.json', 'w') as f:
        json.dump(result, f, indent=2)

    # Push to GitHub
    try:
        fname = f"data/mega_v3_{now.strftime('%Y%m%d_%H%M')}.json"
        import base64
        b64 = base64.b64encode(json.dumps(result, indent=2).encode()).decode()
        gh_token = ''
        try:
            import subprocess
            r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
            gh_token = r.stdout.strip()
        except: pass
        if gh_token:
            pl = json.dumps({"message": f"Mega v3.0 {now.strftime('%Y-%m-%d %H:%M')}", "content": b64}).encode()
            req = urllib.request.Request(
                f"https://api.github.com/repos/Onimix/onimix-vfl-elite/contents/{fname}",
                data=pl, headers={"Authorization": f"token {gh_token}",
                "Content-Type": "application/json"}, method="PUT")
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status in (200, 201):
                    print(f"✅ GitHub: {fname}")
    except Exception as e:
        print(f"GitHub: {e}")

    return result

if __name__ == '__main__':
    result = run_mega_audit()
    if result:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("No picks. Will retry when matches available.")
