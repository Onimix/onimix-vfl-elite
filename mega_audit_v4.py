#!/usr/bin/env python3
"""
ONIMIX VFL ELITE — Mega Audit v4.3
=====================================
PURE ODDS-BASED MEGA ACCUMULATOR + AUTO-BOOKING
Uses commonThumbnailEvents + individual event markets.
Correct parsing: id=18 exact desc, decimal odds.
AUTO-BOOKS each mega tier on SportyBet and sends booking codes to Telegram.

Author: ONIMIX TECH
Date: April 2026
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import time
from datetime import datetime, timezone

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
    """POST JSON to SportyBet API."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={
            **HEADERS,
            "Content-Type": "application/json",
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
            headers={"User-Agent": "ONIMIX/4.2", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except: return {}


def get_boost(odds, league, proven, home="", away="", sa=0):
    """Deep proven odds integration — uses ALL data from odds tracker.
    Checks: odds_buckets, league_stats, matchup_odds, sa_score_stats.
    Returns boost (-5 to +5) and reason string."""
    if not proven: return 0, "No proven data yet"
    boost = 0; reasons = []

    # 1. ODDS BUCKET CHECK (fixed key: "odds_buckets" not "by_odds_bucket")
    for b, s in proven.get("odds_buckets", {}).items():
        try:
            p = b.replace("[","").replace(")","").split("-")
            lo, hi = float(p[0]), float(p[1])
            if lo <= odds < hi:
                hr = s.get("hit_rate", 0) * 100 if s.get("hit_rate", 0) <= 1 else s.get("hit_rate", 0)
                total = s.get("total", 0)
                if total >= 3:
                    if hr >= 75: boost += 2; reasons.append(f"Odds bucket {hr:.0f}% ({total} settled)")
                    elif hr < 40: boost -= 3; reasons.append(f"⚠️ Danger bucket {hr:.0f}%")
                elif total >= 1:
                    if hr >= 70: boost += 1; reasons.append(f"Odds bucket early {hr:.0f}%")
                break
        except: continue

    # 2. LEAGUE STATS CHECK
    lg_key = league.lower()
    lg_stats = proven.get("league_stats", {}).get(lg_key, {})
    if lg_stats:
        lg_hr = lg_stats.get("hit_rate", 0) * 100 if lg_stats.get("hit_rate", 0) <= 1 else lg_stats.get("hit_rate", 0)
        lg_total = lg_stats.get("total", 0)
        if lg_total >= 5:
            if lg_hr >= 75: boost += 1; reasons.append(f"{league} league {lg_hr:.0f}%")
            elif lg_hr < 45: boost -= 2; reasons.append(f"⚠️ {league} league weak {lg_hr:.0f}%")

    # 3. MATCHUP CHECK (specific team pairing)
    if home and away:
        matchup_key = f"{lg_key}:{home} vs {away}"
        mu_stats = proven.get("matchup_odds", {}).get(matchup_key, {})
        if mu_stats:
            mu_hr = mu_stats.get("hit_rate", 0) * 100 if mu_stats.get("hit_rate", 0) <= 1 else mu_stats.get("hit_rate", 0)
            mu_total = mu_stats.get("total", 0)
            if mu_total >= 2:
                if mu_hr >= 80: boost += 2; reasons.append(f"Matchup proven {mu_hr:.0f}%")
                elif mu_hr < 30: boost -= 2; reasons.append(f"⚠️ Matchup dangerous {mu_hr:.0f}%")
            elif mu_total == 1 and mu_hr >= 100:
                boost += 1; reasons.append(f"Matchup 1/1 ✓")

    # 4. SA SCORE STATS CHECK
    sa_key = str(sa)
    sa_stats = proven.get("sa_score_stats", {}).get(sa_key, {})
    if sa_stats:
        sa_hr = sa_stats.get("hit_rate", 0) * 100 if sa_stats.get("hit_rate", 0) <= 1 else sa_stats.get("hit_rate", 0)
        sa_total = sa_stats.get("total", 0)
        if sa_total >= 3:
            if sa_hr >= 80: boost += 1; reasons.append(f"SA{sa} proven {sa_hr:.0f}%")
            elif sa_hr < 40: boost -= 1; reasons.append(f"⚠️ SA{sa} weak {sa_hr:.0f}%")

    # Cap boost
    boost = max(-5, min(5, boost))
    return boost, " | ".join(reasons) if reasons else "Neutral"


def parse_markets(markets):
    """Parse prematch markets. Extracts O1.5 odds + outcomeId/specifier for booking."""
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
                o15 = v
                o15_outcome_id = oid
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
    """Generate SportyBet booking code for a list of selections.
    Each selection needs: eventId, marketId, specifier, outcomeId.
    Returns the share/booking code or None on failure."""
    if not selections:
        return None

    payload = {"selections": selections}

    # Try SportyBet share endpoint
    result = api_post(BOOKING_URL, payload)
    if "error" in result:
        print(f"  ⚠️ Booking API error: {result['error']}")
        # Try alternate endpoint format
        alt_url = "https://www.sportybet.com/api/ng/orders/share"
        result = api_post(alt_url, {"outcomes": selections})
        if "error" in result:
            return None

    # Extract share code from response
    data = result.get("data", result)
    if isinstance(data, dict):
        code = data.get("shareCode") or data.get("code") or data.get("betId")
        if code:
            return str(code)

    # Try extracting from top-level
    code = result.get("shareCode") or result.get("code")
    if code:
        return str(code)

    print(f"  ℹ️ Booking response: {json.dumps(result)[:200]}")
    return None


def book_mega(mega_legs):
    """Book a mega accumulator on SportyBet. Returns booking code or None."""
    selections = []
    for leg in mega_legs:
        event_id = leg.get("event_id", "")
        outcome_id = leg.get("o15_outcome_id", "")
        specifier = leg.get("o15_specifier", "total=1.5")

        if not event_id or not outcome_id:
            print(f"  ⚠️ Missing booking data for {leg.get('match', '?')}")
            continue

        selections.append({
            "eventId": event_id,
            "marketId": "18",
            "specifier": specifier,
            "outcomeId": outcome_id,
        })

    if len(selections) < len(mega_legs):
        print(f"  ⚠️ Only {len(selections)}/{len(mega_legs)} legs have booking data")
        if not selections:
            return None

    code = generate_booking_code(selections)
    return code


def scan_all():
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


def build_megas(cands, proven, correction):
    scored = []
    for c in cands:
        boost, reason = get_boost(c["o15"], c["league"], proven, c.get("home",""), c.get("away",""), c.get("sa",0))
        ok, msg = correction.check(c["key"], c["league"], c["o15"], c["sa"])
        if not ok: continue
        conf = (c["sa"]/14*50) + max(0, 25-abs(c["o15"]-1.49)*100) + boost*5
        scored.append({**c, "confidence": round(max(0,min(100,conf)),1), "boost": boost, "reason": reason})
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
            # Generate booking code for this mega tier
            booking_code = book_mega(best["legs"])
            best["booking_code"] = booking_code
            if booking_code:
                print(f"  🎫 {best['name']} booked: {booking_code}")
            else:
                print(f"  ⚠️ {best['name']} booking failed — picks still valid")
            megas.append(best)
    return megas, scored


def format_msg(megas, total):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    msg = f"🚀 *ONIMIX MEGA AUDIT v4.3*\n💎 *ODDS-BASED ENGINE + AUTO-BOOK*\n⏰ {now}\n{'='*35}\n\n"
    msg += f"🔍 *Scan:* 5 leagues, {total} candidates\n\n"
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
        # Booking code section
        if m.get("booking_code"):
            msg += f"🎫 *BOOKING CODE: {m['booking_code']}*\n"
            msg += f"📲 Open SportyBet → Load Code → Place Bet\n"
        else:
            msg += f"🎫 _Manual booking required (auto-book unavailable)_\n"
        msg += f"{'─'*30}\n"
    msg += f"\n🔒 *Pure odds-based — no matchup dependency*\n"
    msg += f"• Auto-booking enabled 🎫 ({booked_count}/{len(megas)} booked)\n"
    msg += f"⚠️ *Mega = high risk. Gamble responsibly.*"
    return msg


def run():
    print("="*60)
    print("🚀 ONIMIX MEGA AUDIT v4.3 — ODDS-BASED + AUTO-BOOK")
    print("="*60)
    start = time.time()
    correction = MegaCorrection()
    proven = load_proven()
    proven_settled = proven.get("total_settled", 0)
    proven_hr = proven.get("overall_hit_rate", 0)
    if proven_settled:
        print(f"📊 Proven Odds DB: {proven_settled} settled, {proven_hr*100:.1f}% hit rate")
        print(f"   Leagues: {', '.join(proven.get('league_stats',{}).keys())}")
        print(f"   Odds buckets: {len(proven.get('odds_buckets',{}))}")
        print(f"   Matchups tracked: {len(proven.get('matchup_odds',{}))}")
    else:
        print("📊 No proven odds data yet — running without backing")
    cands = scan_all()
    print(f"\n📊 Total: {len(cands)}")
    megas, scored = build_megas(cands, proven, correction)
    booked = sum(1 for m in megas if m.get("booking_code"))
    print(f"📊 Megas: {len(megas)} | Booked: {booked}/{len(megas)}")
    msg = format_msg(megas, len(cands))
    send_telegram(msg)
    elapsed = time.time() - start
    print(f"\n⏱️ Done in {elapsed:.1f}s")
    return {"status": "success", "version": "4.3", "method": "ODDS-BASED MEGA + AUTOBOOK",
            "candidates": len(cands), "megas": len(megas), "booked": booked,
            "elapsed": round(elapsed,1)}

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
