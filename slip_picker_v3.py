#!/usr/bin/env python3
"""
ONIMIX VFL ELITE — Slip Picker v3.2
====================================
PURE ODDS-BASED PREDICTION ENGINE + AUTO-BOOKING
Uses commonThumbnailEvents for discovery + individual event detail for markets.
Correct market parsing: id=18 + exact desc match. Odds already decimal.
AUTO-BOOKS each slip on SportyBet and sends booking codes to Telegram.

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
    "Spain":   {"league_id": "sv:league:2"},
    "Germany": {"league_id": "sv:league:4"},
    "England": {"league_id": "sv:league:1"},
    "Italy":   {"league_id": "sv:league:3"},
    "France":  {"league_id": "sv:league:5"},
}

MIN_ODDS = 1.38
MAX_ODDS = 1.60
MIN_SA_SCORE = 8

SLIP_CONFIGS = [
    {"name": "🟢 SAFE 3-LEG", "legs": 3, "min_confidence": 45},
    {"name": "🟡 STANDARD 4-LEG", "legs": 4, "min_confidence": 40},
    {"name": "🔴 POWER 5-LEG", "legs": 5, "min_confidence": 35},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0",
    "Accept": "application/json",
    "Referer": "https://www.sportybet.com/ng/virtual",
}


class CorrectionSystem:
    def __init__(self):
        self.memory = []
        self.slot_history = {}

    def rule1_slot_repeat_trap(self, match_key):
        slot = match_key[:15]
        h = self.slot_history.get(slot, {"picks": 0, "fails": 0})
        if h["fails"] >= 2 and h["picks"] >= 3:
            return False, f"Slot {slot} trapped"
        return True, "OK"

    def rule2_failure_root_cause(self, odds_value):
        fails = [m for m in self.memory[-20:] if m.get("result") == "LOST"]
        if len(fails) >= 3:
            avg = sum(f.get("odds", 1.5) for f in fails) / len(fails)
            if abs(odds_value - avg) < 0.03:
                return False, f"Odds {odds_value:.2f} matches failure pattern"
        return True, "OK"

    def rule3_memory_learning(self, league):
        lp = [m for m in self.memory if m.get("league") == league]
        if len(lp) >= 5:
            wins = sum(1 for m in lp if m.get("result") == "WON")
            if wins / len(lp) < 0.40:
                return False, f"League {league} win rate too low"
        return True, "OK"

    def rule4_confirmation_filter(self, sa_score, odds_value, proven_boost):
        c = 0
        if sa_score >= 10: c += 1
        if MIN_ODDS <= odds_value <= MAX_ODDS: c += 1
        if proven_boost > 0: c += 1
        if sa_score >= 8: c += 1
        if c < 2:
            return False, f"Only {c} confirmations"
        return True, f"{c} confirmations"

    def rule5_self_check(self, pick):
        flags = 0
        if pick.get("odds", 0) < 1.30: flags += 1
        if pick.get("odds", 0) > 1.80: flags += 1
        if pick.get("sa_score", 0) < 6: flags += 1
        if flags >= 2:
            return False, f"{flags} red flags"
        return True, "OK"

    def run_all(self, match_key, league, odds_val, sa_score, proven_boost, pick):
        results = [
            self.rule1_slot_repeat_trap(match_key),
            self.rule2_failure_root_cause(odds_val),
            self.rule3_memory_learning(league),
            self.rule4_confirmation_filter(sa_score, odds_val, proven_boost),
            self.rule5_self_check(pick),
        ]
        passed = all(r[0] for r in results)
        blocked = [f"R{i+1}: {r[1]}" for i, r in enumerate(results) if not r[0]]
        return passed, blocked


def api_get(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
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


def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=15)
        return True
    except:
        return False


def load_proven_odds():
    try:
        url = f"{GH_RAW}/data/proven_odds.json"
        req = urllib.request.Request(url, headers={"User-Agent": "ONIMIX/3.2", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except:
        return {}


def get_proven_boost(odds_value, league, proven_data):
    if not proven_data:
        return 0, "No data"
    boost = 0
    reasons = []
    for bucket, stats in proven_data.get("by_odds_bucket", {}).items():
        try:
            parts = bucket.replace("[","").replace(")","").split("-")
            lo, hi = float(parts[0]), float(parts[1])
            if lo <= odds_value < hi:
                hr = stats.get("hit_rate", 0)
                ct = stats.get("total", 0)
                if ct >= 3 and hr >= 75:
                    boost += 3; reasons.append(f"Proven {hr:.0f}%")
                elif ct >= 3 and hr < 40:
                    boost -= 3; reasons.append(f"Danger {hr:.0f}%")
                break
        except: continue
    for lg, stats in proven_data.get("by_league", {}).items():
        if league.lower() in lg.lower():
            hr = stats.get("hit_rate", 0)
            if stats.get("total", 0) >= 3 and hr >= 75:
                boost += 2; reasons.append(f"{league} proven")
            break
    return boost, " | ".join(reasons) if reasons else "Neutral"


def parse_markets(markets):
    """Parse prematch markets correctly. Key: market id=18 has multiple lines.
    Also extracts outcomeId for Over 1.5 for booking purposes."""
    o15 = o25 = home_o05 = away_o05 = btts = 0
    o15_outcome_id = None
    o15_specifier = None
    sa = 0
    for m in markets:
        mid = str(m.get("id", ""))
        specifier = m.get("specifier", "")
        for o in m.get("outcomes", []):
            desc = str(o.get("desc", ""))
            val = float(o.get("odds", 0))
            oid = str(o.get("id", ""))
            if mid == "18" and desc == "Over 1.5":
                o15 = val
                o15_outcome_id = oid
                o15_specifier = specifier if specifier else "total=1.5"
            elif mid == "18" and desc == "Over 2.5": o25 = val
            elif mid == "19" and desc == "Over 0.5": home_o05 = val
            elif mid == "20" and desc == "Over 0.5": away_o05 = val
            elif mid == "29" and desc == "Yes": btts = val
    if o15 > 0:
        if o15 <= 1.60: sa += 3
        elif o15 <= 1.80: sa += 1
    if o25 > 0:
        if o25 <= 2.20: sa += 2
        elif o25 <= 2.80: sa += 1
    if home_o05 > 0:
        if home_o05 <= 1.40: sa += 2
        elif home_o05 <= 1.60: sa += 1
    if away_o05 > 0:
        if away_o05 <= 1.40: sa += 2
        elif away_o05 <= 1.60: sa += 1
    if btts > 0:
        if btts <= 1.80: sa += 2
        elif btts <= 2.20: sa += 1
    return {
        "o15": o15, "o25": o25, "home_o05": home_o05, "away_o05": away_o05,
        "btts": btts, "sa_score": min(sa, 14),
        "o15_outcome_id": o15_outcome_id,
        "o15_specifier": o15_specifier,
    }


def discover_upcoming(league_name, league_id):
    """Use commonThumbnailEvents to find upcoming matches, then fetch details."""
    candidates = []
    url = f"{API_BASE}/commonThumbnailEvents?sportId=sr:sport:202120001&tournamentId={league_id}"
    data = api_get(url)
    if "error" in data:
        return candidates
    events = data.get("data", [{}])
    if not events:
        return candidates
    events = events[0].get("events", [])
    upcoming = [e for e in events if e.get("matchStatus") == "Not start"][:15]
    print(f"  {league_name}: {len(upcoming)} upcoming matches")

    for evt in upcoming:
        eid = evt["eventId"]
        home = evt.get("homeTeamName", "?")
        away = evt.get("awayTeamName", "?")
        game_id = evt.get("gameId", "")
        edata = api_get(f"{API_BASE}/event?eventId={eid}", timeout=10)
        event = edata.get("data", {})
        if not event:
            continue
        parsed = parse_markets(event.get("markets", []))
        o15 = parsed["o15"]
        sa = parsed["sa_score"]
        if not (MIN_ODDS <= o15 <= MAX_ODDS):
            continue
        if sa < MIN_SA_SCORE:
            continue
        print(f"    ✅ {home} vs {away} — O1.5: {o15:.2f}, SA: {sa}")
        candidates.append({
            "event_id": eid, "game_id": game_id, "league": league_name,
            "home": home, "away": away, "match": f"{home} vs {away}",
            "o15_odds": o15, "sa_score": sa,
            "o25": parsed["o25"], "btts": parsed["btts"],
            "o15_outcome_id": parsed["o15_outcome_id"],
            "o15_specifier": parsed["o15_specifier"],
            "match_key": f"{league_name}_{home}_{away}",
        })
        time.sleep(0.2)
    return candidates


def select_and_score(candidates, proven_data, correction):
    scored = []
    for c in candidates:
        boost, reason = get_proven_boost(c["o15_odds"], c["league"], proven_data)
        conf = (c["sa_score"]/14*50) + max(0, 25 - abs(c["o15_odds"]-1.49)*100) + (boost*5)
        conf = max(0, min(100, conf))
        pick = {"match": c["match"], "league": c["league"], "odds": c["o15_odds"],
                "sa_score": c["sa_score"], "confidence": conf, "proven_boost": boost}
        passed, blocked = correction.run_all(c["match_key"], c["league"], c["o15_odds"], c["sa_score"], boost, pick)
        if not passed:
            continue
        scored.append({**c, "confidence": round(conf, 1), "proven_boost": boost, "proven_reason": reason})
    scored.sort(key=lambda x: x["confidence"], reverse=True)
    return scored


def generate_booking_code(selections):
    """Generate SportyBet booking code for a list of selections.
    Each selection needs: eventId, marketId, specifier, outcomeId.
    Returns the share/booking code or None on failure."""
    if not selections:
        return None

    payload = {
        "selections": selections
    }

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


def book_slip(slip_legs):
    """Book a slip on SportyBet. Returns booking code or None."""
    selections = []
    for leg in slip_legs:
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

    if len(selections) < len(slip_legs):
        print(f"  ⚠️ Only {len(selections)}/{len(slip_legs)} legs have booking data")
        if not selections:
            return None

    code = generate_booking_code(selections)
    return code


def build_slips(scored):
    slips = []
    for cfg in SLIP_CONFIGS:
        n = cfg["legs"]
        eligible = [p for p in scored if p["confidence"] >= cfg["min_confidence"]]
        if len(eligible) < n:
            eligible = sorted(scored, key=lambda x: x["confidence"], reverse=True)
        selected = []
        lcount = {}
        for p in eligible:
            lg = p["league"]
            if lcount.get(lg, 0) >= 2: continue
            selected.append(p)
            lcount[lg] = lcount.get(lg, 0) + 1
            if len(selected) == n: break
        if len(selected) < n:
            for p in eligible:
                if p not in selected:
                    selected.append(p)
                    if len(selected) == n: break
        if len(selected) < n: continue
        combo = 1.0
        for s in selected: combo *= s["o15_odds"]

        # Generate booking code for this slip
        booking_code = book_slip(selected)
        if booking_code:
            print(f"  🎫 {cfg['name']} booked: {booking_code}")
        else:
            print(f"  ⚠️ {cfg['name']} booking failed — picks still valid")

        slips.append({
            "name": cfg["name"], "legs": selected, "num_legs": len(selected),
            "combined_odds": round(combo, 2),
            "avg_confidence": round(sum(s["confidence"] for s in selected)/len(selected), 1),
            "avg_sa": round(sum(s["sa_score"] for s in selected)/len(selected), 1),
            "potential_1k": round(1000 * combo),
            "booking_code": booking_code,
        })
    return slips


def format_message(slips, stats):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    msg = f"🎯 *ONIMIX VFL ELITE v3.2*\n📊 *ODDS-BASED ENGINE + AUTO-BOOK*\n⏰ {now}\n{'='*35}\n\n"
    msg += f"🔍 *Scan:* {stats['leagues']} leagues, {stats['scanned']} matches\n"
    msg += f"🎯 *Sweet spot:* {stats['candidates']} | After filter: {stats['scored']}\n\n"
    if not slips:
        msg += "⚠️ *No qualifying slips this cycle.* Will retry next scan.\n"
        return msg
    for slip in slips:
        msg += f"\n{slip['name']}\n{'─'*30}\n"
        for i, leg in enumerate(slip["legs"], 1):
            msg += f"{i}. {leg['match']}\n"
            msg += f"   🏆 {leg['league']} | O1.5 @ {leg['o15_odds']:.2f}\n"
            msg += f"   📊 SA: {leg['sa_score']} | Conf: {leg['confidence']:.0f}%\n"
        msg += f"\n💰 Combined: *{slip['combined_odds']:.2f}x*\n"
        msg += f"💵 ₦1,000 → ₦{slip['potential_1k']:,}\n"
        msg += f"📊 Avg Conf: {slip['avg_confidence']:.0f}% | SA: {slip['avg_sa']:.1f}\n"
        # Booking code section
        if slip.get("booking_code"):
            msg += f"🎫 *BOOKING CODE: {slip['booking_code']}*\n"
            msg += f"📲 Open SportyBet → Load Code → Place Bet\n"
        else:
            msg += f"🎫 _Manual booking required (auto-book unavailable)_\n"
        msg += f"{'─'*30}\n"
    msg += f"\n🔒 *Pure odds-based — zero matchup dependency*\n"
    msg += f"• Sweet spot: {MIN_ODDS}-{MAX_ODDS} | SA ≥ {MIN_SA_SCORE}\n"
    msg += f"• Proven odds DB + 5-rule correction ✅\n"
    msg += f"• Auto-booking enabled 🎫\n"
    msg += f"\n⚠️ *Gamble responsibly.*"
    return msg


def run():
    print("="*60)
    print("🎯 ONIMIX VFL ELITE v3.2 — ODDS-BASED + AUTO-BOOK")
    print("="*60)
    start = time.time()
    correction = CorrectionSystem()
    proven = load_proven_odds()
    all_cands = []
    total_scanned = 0
    for name, cfg in LEAGUES.items():
        print(f"\n🔍 Scanning {name}...")
        cands = discover_upcoming(name, cfg["league_id"])
        all_cands.extend(cands)
        total_scanned += 15
        time.sleep(0.3)
    print(f"\n📊 Sweet spot candidates: {len(all_cands)}")
    scored = select_and_score(all_cands, proven, correction)
    print(f"📊 After scoring: {len(scored)}")
    slips = build_slips(scored)
    print(f"📊 Slips: {len(slips)}")
    booked = sum(1 for s in slips if s.get("booking_code"))
    print(f"🎫 Booked: {booked}/{len(slips)} slips")
    stats = {"leagues": len(LEAGUES), "scanned": total_scanned, "candidates": len(all_cands), "scored": len(scored)}
    msg = format_message(slips, stats)
    send_telegram(msg)
    elapsed = time.time() - start
    print(f"\n⏱️ Done in {elapsed:.1f}s")
    return {"status": "success", "version": "3.2", "method": "ODDS-BASED+AUTOBOOK",
            "stats": stats, "slips_count": len(slips), "booked_count": booked,
            "slips": slips, "scored_picks": scored, "elapsed": round(elapsed, 1)}

if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, default=str))
