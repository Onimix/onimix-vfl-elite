#!/usr/bin/env python3
"""
ONIMIX VFL ELITE — Mega Audit v4.4
=====================================
3-LAYER MEGA ACCUMULATOR ENGINE + AUTO-BOOKING
Layer 1: Proven Odds DB (odds_tracker history)
Layer 2: Recent Results Analyzer (team form + h2h)
Layer 3: Prematch JSON (live odds + SA scores)
AUTO-BOOKS each mega tier on SportyBet and sends booking codes to Telegram.

Author: ONIMIX TECH
Date: April 2026
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time
from datetime import datetime, timezone, timedelta

TELEGRAM_TOKEN = "8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow"
TELEGRAM_CHAT_ID = "1745848158"
GH_RAW = "https://raw.githubusercontent.com/Onimix/onimix-vfl-elite/main"
API_BASE = "https://www.sportybet.com/api/ng/factsCenter"
BOOKING_URL = "https://www.sportybet.com/api/ng/orders/share"

LEAGUES = {
    "Spain": "sv:league:2", "Germany": "sv:league:4",
    "England": "sv:league:1", "Italy": "sv:league:3", "France": "sv:league:5",
}

MEGA_MIN_ODDS = 1.35
MEGA_MAX_ODDS = 1.65
MEGA_MIN_SA = 7

MEGA_TIERS = [
    {"name": "🔥 MEGA 20K", "target": 20000, "min_legs": 10, "max_legs": 12},
    {"name": "💎 MEGA 40K", "target": 40000, "min_legs": 12, "max_legs": 14},
    {"name": "🚀 MEGA 60K", "target": 60000, "min_legs": 13, "max_legs": 15},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0",
    "Accept": "application/json", "Referer": "https://www.sportybet.com/ng/virtual",
}

# Layer 2: Result pages per league
RESULT_PAGES = {
    "Spain": list(range(4, 9)),
    "Germany": list(range(9, 14)),
    "England": list(range(1, 4)),
    "Italy": list(range(14, 17)),
    "France": list(range(17, 19)),
}


class MegaCorrection:
    def __init__(self):
        self.memory = []
        self.slot_history = {}
    def check(self, key, league, odds, sa):
        slot = key[:15]
        h = self.slot_history.get(slot, {"picks": 0, "fails": 0})
        if h.get("fails", 0) >= 3: return False, "Slot trapped"
        lp = [m for m in self.memory if m.get("league") == league]
        if len(lp) >= 5 and sum(1 for m in lp if m.get("result") == "WON") / len(lp) < 0.30:
            return False, f"League {league} poor"
        return True, "OK"


def api_get(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def api_post(url, payload, timeout=15):
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={
            **HEADERS, "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15)
    except: pass


def load_proven():
    try:
        req = urllib.request.Request(f"{GH_RAW}/data/proven_odds.json",
            headers={"User-Agent": "ONIMIX/4.4", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode()
            # Handle double-encoded JSON
            raw = raw.replace('\\n', '\n').replace('\\t', '\t')
            return json.loads(raw)
    except: return {}


def get_boost(odds, league, proven):
    """Layer 1: Check proven odds DB for historical hit rates."""
    if not proven: return 0, "No data"
    boost = 0; reasons = []
    # Fix: use correct keys (odds_buckets not by_odds_bucket)
    buckets = proven.get("odds_buckets", proven.get("by_odds_bucket", {}))
    for b, s in buckets.items():
        try:
            p = b.replace("[","").replace(")","").split("-")
            if float(p[0]) <= odds < float(p[1]):
                hr = s.get("hit_rate", 0)
                if s.get("total", 0) >= 3:
                    if hr >= 75: boost += 2; reasons.append(f"Proven {hr:.0f}%")
                    elif hr < 40: boost -= 3; reasons.append(f"Danger {hr:.0f}%")
                break
        except: continue
    # Fix: use correct keys (league_stats not by_league)
    leagues_data = proven.get("league_stats", proven.get("by_league", {}))
    for lg, stats in leagues_data.items():
        if league.lower() in lg.lower():
            hr = stats.get("hit_rate", 0)
            if stats.get("total", 0) >= 3 and hr >= 75:
                boost += 1; reasons.append(f"{league} proven")
            break
    return boost, " | ".join(reasons) if reasons else "Neutral"


# =====================
# LAYER 2: Recent Results Analyzer
# =====================

def fetch_recent_results(days=1):
    """Layer 2: Pull yesterday's + today's completed results from SportyBet API."""
    results = {}
    now = datetime.now(timezone.utc)
    for d in range(days + 1):
        day = now - timedelta(days=d)
        start_ts = int(day.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        end_ts = int(day.replace(hour=23, minute=59, second=59, microsecond=0).timestamp() * 1000)

        for league, pages in RESULT_PAGES.items():
            if league not in results:
                results[league] = []
            for page in pages[:2]:  # Limit to 2 pages per league for speed
                url = (f"{API_BASE}/eventResultList?pageNum={page}&pageSize=100"
                       f"&sportId=sr%3Asport%3A202120001&startTime={start_ts}&endTime={end_ts}")
                data = api_get(url, timeout=10)
                if "error" in data:
                    continue
                tournaments = data.get("data", {}).get("tournaments", [])
                for t in tournaments:
                    tname = t.get("name", "").lower()
                    if league.lower() not in tname:
                        continue
                    for evt in t.get("events", []):
                        home = evt.get("homeTeamName", "")
                        away = evt.get("awayTeamName", "")
                        score = evt.get("setScore", "0:0")
                        parts = score.split(":")
                        try:
                            hs, aws = int(parts[0]), int(parts[1])
                        except:
                            hs, aws = 0, 0
                        results[league].append({
                            "home": home, "away": away,
                            "hs": hs, "as": aws,
                            "total": hs + aws,
                            "over15": 1 if (hs + aws) >= 2 else 0,
                        })
                time.sleep(0.15)

    total = sum(len(v) for v in results.values())
    print(f"  📊 L2 fetched: {total} recent results across {len(results)} leagues")
    return results


def analyze_team_form(team, league, recent_results):
    """Check team's recent scoring form. Returns (form_score, reason)."""
    matches = recent_results.get(league, [])
    team_matches = []
    for m in matches:
        if team.lower() in m["home"].lower():
            team_matches.append(m["hs"])
        elif team.lower() in m["away"].lower():
            team_matches.append(m["as"])

    if len(team_matches) < 3:
        return 0, "insufficient"

    last5 = team_matches[-5:]
    blanks = sum(1 for g in last5 if g == 0)
    avg = sum(last5) / len(last5)

    if blanks >= 3:
        return -3, f"0-goal_streak({blanks}blanks)"
    elif blanks >= 2:
        return -1, f"low_scoring({blanks}blanks)"
    elif avg >= 1.5:
        return 2, f"hot({avg:.1f}avg)"
    elif avg >= 1.0:
        return 1, f"decent({avg:.1f}avg)"
    return 0, "neutral"


def analyze_matchup_history(home, away, league, recent_results):
    """Check if this exact matchup appeared recently."""
    matches = recent_results.get(league, [])
    h2h = []
    for m in matches:
        if (home.lower() in m["home"].lower() and away.lower() in m["away"].lower()) or \
           (home.lower() in m["away"].lower() and away.lower() in m["home"].lower()):
            h2h.append(m)

    if len(h2h) < 2:
        return 0, "no_h2h"

    o15_rate = sum(1 for m in h2h if m["over15"]) / len(h2h)
    if o15_rate >= 0.80:
        return 3, f"strong_h2h({o15_rate:.0%})"
    elif o15_rate <= 0.30:
        return -3, f"h2h_trap({o15_rate:.0%})"
    return 0, f"h2h_mixed({o15_rate:.0%})"


def l2_score(home, away, league, recent_results):
    """Combined Layer 2 score from team form + matchup history."""
    h_form, h_reason = analyze_team_form(home, league, recent_results)
    a_form, a_reason = analyze_team_form(away, league, recent_results)
    h2h, h2h_reason = analyze_matchup_history(home, away, league, recent_results)
    total = h_form + a_form + h2h
    reason = f"H:{h_reason} A:{a_reason} H2H:{h2h_reason}"
    return total, reason


# =====================
# LAYER 3: Prematch JSON (market parsing + SA score)
# =====================

def parse_markets(markets):
    """Layer 3: Parse prematch markets for O1.5 odds + SA score + booking data."""
    o15 = o25 = ho05 = ao05 = btts = 0; sa = 0
    o15_outcome_id = None
    o15_specifier = None
    for m in markets:
        mid = str(m.get("id", ""))
        specifier = m.get("specifier", "")
        for o in m.get("outcomes", []):
            d = str(o.get("desc", "")); v = float(o.get("odds", 0))
            oid = str(o.get("id", ""))
            if mid == "18" and d == "Over 1.5":
                o15 = v; o15_outcome_id = oid
                o15_specifier = specifier if specifier else "total=1.5"
            elif mid == "18" and d == "Over 2.5": o25 = v
            elif mid == "19" and d == "Over 0.5": ho05 = v
            elif mid == "20" and d == "Over 0.5": ao05 = v
            elif mid == "29" and d == "Yes": btts = v
    if o15 > 0:
        if o15 <= 1.60: sa += 3
        elif o15 <= 1.80: sa += 1
    if o25 > 0:
        if o25 <= 2.20: sa += 2
        elif o25 <= 2.80: sa += 1
    if ho05 > 0:
        if ho05 <= 1.40: sa += 2
        elif ho05 <= 1.60: sa += 1
    if ao05 > 0:
        if ao05 <= 1.40: sa += 2
        elif ao05 <= 1.60: sa += 1
    if btts > 0:
        if btts <= 1.80: sa += 2
        elif btts <= 2.20: sa += 1
    return {"o15": o15, "sa": min(sa, 14),
            "o15_outcome_id": o15_outcome_id, "o15_specifier": o15_specifier}


def generate_booking_code(selections):
    if not selections: return None
    payload = {"selections": selections}
    result = api_post(BOOKING_URL, payload)
    if "error" in result:
        result = api_post(BOOKING_URL, {"outcomes": selections})
        if "error" in result: return None
    data = result.get("data", result)
    if isinstance(data, dict):
        code = data.get("shareCode") or data.get("code") or data.get("betId")
        if code: return str(code)
    code = result.get("shareCode") or result.get("code")
    return str(code) if code else None


def book_mega(mega_legs):
    selections = []
    for leg in mega_legs:
        eid = leg.get("event_id", "")
        oid = leg.get("o15_outcome_id", "")
        spec = leg.get("o15_specifier", "total=1.5")
        if not eid or not oid: continue
        selections.append({"eventId": eid, "marketId": "18", "specifier": spec, "outcomeId": oid})
    if not selections: return None
    return generate_booking_code(selections)


def scan_all():
    """Layer 3: Scan all leagues for upcoming matches with prematch data."""
    cands = []
    for name, lid in LEAGUES.items():
        print(f"\n🔍 {name}...")
        data = api_get(f"{API_BASE}/commonThumbnailEvents?sportId=sr:sport:202120001&tournamentId={lid}")
        if "error" in data: continue
        evts = data.get("data", [{}])
        if not evts: continue
        evts = evts[0].get("events", [])
        upcoming = [e for e in evts if e.get("matchStatus") == "Not start"][:15]
        for evt in upcoming:
            eid = evt["eventId"]; h = evt.get("homeTeamName","?"); a = evt.get("awayTeamName","?")
            ed = api_get(f"{API_BASE}/event?eventId={eid}", 10)
            ev = ed.get("data", {})
            if not ev: continue
            p = parse_markets(ev.get("markets", []))
            if not (MEGA_MIN_ODDS <= p["o15"] <= MEGA_MAX_ODDS): continue
            if p["sa"] < MEGA_MIN_SA: continue
            print(f"  ✅ {h} vs {a} — {p['o15']:.2f} SA:{p['sa']}")
            cands.append({"event_id": eid, "league": name, "home": h, "away": a,
                         "match": f"{h} vs {a}", "o15": p["o15"], "sa": p["sa"],
                         "o15_outcome_id": p["o15_outcome_id"],
                         "o15_specifier": p["o15_specifier"],
                         "key": f"{name}_{h}_{a}"})
            time.sleep(0.2)
        time.sleep(0.3)
    return cands


def build_megas(cands, proven, correction, recent_results=None):
    """Build mega accumulators using all 3 layers."""
    scored = []
    for c in cands:
        # Layer 1: Proven odds boost
        boost, reason = get_boost(c["o15"], c["league"], proven)
        # Correction system check
        ok, msg = correction.check(c["key"], c["league"], c["o15"], c["sa"])
        if not ok:
            print(f"  🚫 Correction blocked {c['match']}: {msg}")
            continue
        # Layer 2: Recent results
        l2_adj, l2_reason = 0, "L2:disabled"
        if recent_results:
            l2_adj, l2_reason = l2_score(c["home"], c["away"], c["league"], recent_results)
        if l2_adj <= -4:
            print(f"  🚫 L2 REJECT {c['match']} — {l2_reason}")
            continue
        # Combined confidence (L1 + L2 + L3)
        conf = (c["sa"]/14*50) + max(0, 25-abs(c["o15"]-1.49)*100) + boost*5 + l2_adj*3
        combined_reason = f"L1:{reason} | L2:{l2_reason}"
        scored.append({**c, "confidence": round(max(0,min(100,conf)),1),
                       "boost": boost, "l2_adj": l2_adj,
                       "reason": combined_reason})
    scored.sort(key=lambda x: x["confidence"], reverse=True)
    if len(scored) < 10:
        print(f"⚠️ Only {len(scored)} candidates, need 10+ for mega")
        return [], scored

    megas = []
    for tier in MEGA_TIERS:
        best = None; best_diff = float('inf')
        for nl in range(tier["min_legs"], tier["max_legs"]+1):
            if nl > len(scored): continue
            sel = []; lc = {}
            for p in scored:
                lg = p["league"]
                if lc.get(lg,0) >= 4: continue
                sel.append(p); lc[lg] = lc.get(lg,0)+1
                if len(sel) == nl: break
            if len(sel) < nl: continue
            combo = 1.0
            for s in sel: combo *= s["o15"]
            diff = abs(combo - tier["target"])
            if diff < best_diff:
                best_diff = diff
                best = {"name": tier["name"], "legs": sel, "n": len(sel),
                       "odds": round(combo,2), "target": tier["target"],
                       "avg_conf": round(sum(s["confidence"] for s in sel)/len(sel),1),
                       "avg_sa": round(sum(s["sa"] for s in sel)/len(sel),1),
                       "ret_1k": round(1000*combo), "leagues": dict(lc)}
        if best:
            booking_code = book_mega(best["legs"])
            best["booking_code"] = booking_code
            if booking_code:
                print(f"  🎫 {best['name']} booked: {booking_code}")
            else:
                print(f"  ⚠️ {best['name']} booking failed — picks still valid")
            megas.append(best)
    return megas, scored


def format_msg(megas, total, l2_count=0):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    msg = f"🚀 *ONIMIX MEGA AUDIT v4.4*\n💎 *3-LAYER ENGINE + AUTO-BOOK*\n⏰ {now}\n{'='*35}\n\n"
    msg += f"🔍 *Scan:* 5 leagues, {total} candidates\n"
    msg += f"📊 *L2 results:* {l2_count} matches analyzed\n\n"
    if not megas:
        msg += f"⚠️ *Need 10+ candidates for mega, found {total}.*\nWill retry.\n"
        return msg
    booked_count = sum(1 for m in megas if m.get("booking_code"))
    for m in megas:
        msg += f"\n{m['name']}\n{'─'*30}\n"
        for i, l in enumerate(m["legs"],1):
            msg += f"{i}. {l['match']}\n   {l['league']} | O1.5 @ {l['o15']:.2f} | SA:{l['sa']}\n"
        msg += f"\n💰 *{m['odds']:,.0f}x*\n💵 ₦1,000 → *₦{m['ret_1k']:,}*\n"
        msg += f"📊 Conf: {m['avg_conf']:.0f}% | SA: {m['avg_sa']:.1f}\n"
        msg += f"🌍 {', '.join(m['leagues'].keys())}\n"
        if m.get("booking_code"):
            msg += f"🎫 *BOOKING CODE: {m['booking_code']}*\n"
            msg += f"📲 Open SportyBet → Load Code → Place Bet\n"
        else:
            msg += f"🎫 _Manual booking required (auto-book unavailable)_\n"
        msg += f"{'─'*30}\n"
    msg += f"\n🔒 *3-Layer Engine — L1:Proven + L2:Form + L3:Prematch*\n"
    msg += f"• Auto-booking enabled 🎫 ({booked_count}/{len(megas)} booked)\n"
    msg += f"⚠️ *Mega = high risk. Gamble responsibly.*"
    return msg


def run():
    print("="*60)
    print("🚀 ONIMIX MEGA AUDIT v4.4 — 3-LAYER ENGINE + AUTO-BOOK")
    print("="*60)
    start = time.time()
    correction = MegaCorrection()

    # Layer 1: Load proven odds
    print("\n📊 LAYER 1: Loading proven odds DB...")
    proven = load_proven()
    print(f"  ✅ Proven data: {len(proven)} keys loaded")

    # Layer 2: Fetch recent results
    print("\n📊 LAYER 2: Fetching recent results...")
    recent_results = fetch_recent_results(days=1)
    l2_count = sum(len(v) for v in recent_results.values())

    # Layer 3: Scan prematch data
    print("\n📊 LAYER 3: Scanning prematch markets...")
    cands = scan_all()
    print(f"\n📊 Total candidates: {len(cands)}")

    # Build megas with all 3 layers
    megas, scored = build_megas(cands, proven, correction, recent_results)
    booked = sum(1 for m in megas if m.get("booking_code"))
    print(f"📊 Megas: {len(megas)} | Booked: {booked}/{len(megas)}")

    msg = format_msg(megas, len(cands), l2_count)
    send_telegram(msg)
    elapsed = time.time() - start
    print(f"\n⏱️ Done in {elapsed:.1f}s")
    return {"status": "success", "version": "4.4", "method": "3-LAYER MEGA + AUTOBOOK",
            "candidates": len(cands), "megas": len(megas), "booked": booked,
            "l2_results": l2_count, "elapsed": round(elapsed,1)}

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
