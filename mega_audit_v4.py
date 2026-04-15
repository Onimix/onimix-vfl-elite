#!/usr/bin/env python3
"""
ONIMIX VFL ELITE — Mega Audit v4.1
=====================================
PURE ODDS-BASED MEGA ACCUMULATOR (FIXED)
Uses commonThumbnailEvents + individual event markets.
Correct parsing: id=18 exact desc, decimal odds.

Author: ONIMIX TECH
Date: April 2026
"""

import json
import urllib.request
import urllib.parse
import time
from datetime import datetime, timezone

TELEGRAM_TOKEN = "8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow"
TELEGRAM_CHAT_ID = "1745848158"
GH_RAW = "https://raw.githubusercontent.com/Onimix/onimix-vfl-elite/main"
API_BASE = "https://www.sportybet.com/api/ng/factsCenter"

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


def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15)
    except: pass


def load_proven():
    try:
        req = urllib.request.Request(f"{GH_RAW}/data/proven_odds.json",
            headers={"User-Agent": "ONIMIX/4.1", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except: return {}


def get_boost(odds, league, proven):
    if not proven: return 0, "No data"
    boost = 0; reasons = []
    for b, s in proven.get("by_odds_bucket", {}).items():
        try:
            p = b.replace("[","").replace(")","").split("-")
            if float(p[0]) <= odds < float(p[1]):
                hr = s.get("hit_rate", 0)
                if s.get("total", 0) >= 3:
                    if hr >= 75: boost += 2; reasons.append(f"Proven {hr:.0f}%")
                    elif hr < 40: boost -= 3; reasons.append(f"Danger {hr:.0f}%")
                break
        except: continue
    return boost, " | ".join(reasons) if reasons else "Neutral"


def parse_markets(markets):
    o15 = o25 = ho05 = ao05 = btts = 0; sa = 0
    for m in markets:
        mid = str(m.get("id", ""))
        for o in m.get("outcomes", []):
            d = str(o.get("desc", "")); v = float(o.get("odds", 0))
            if mid == "18" and d == "Over 1.5": o15 = v
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
    return {"o15": o15, "sa": min(sa, 14)}


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
                         "key": f"{name}_{h}_{a}"})
            time.sleep(0.2)
        time.sleep(0.3)
    return cands


def build_megas(cands, proven, correction):
    scored = []
    for c in cands:
        boost, reason = get_boost(c["o15"], c["league"], proven)
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
        if best: megas.append(best)
    return megas, scored


def format_msg(megas, total):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    msg = f"🚀 *ONIMIX MEGA AUDIT v4.1*\n💎 *ODDS-BASED ENGINE*\n⏰ {now}\n{'='*35}\n\n"
    msg += f"🔍 *Scan:* 5 leagues, {total} candidates\n\n"
    if not megas:
        msg += f"⚠️ *Need 10+ candidates for mega, found {total}.*\nWill retry.\n"
        return msg
    for m in megas:
        msg += f"\n{m['name']}\n{'─'*30}\n"
        for i, l in enumerate(m["legs"],1):
            msg += f"{i}. {l['match']}\n   {l['league']} | O1.5 @ {l['o15']:.2f} | SA:{l['sa']}\n"
        msg += f"\n💰 *{m['odds']:,.0f}x*\n💵 ₦1,000 → *₦{m['ret_1k']:,}*\n"
        msg += f"📊 Conf: {m['avg_conf']:.0f}% | SA: {m['avg_sa']:.1f}\n"
        msg += f"🌍 {', '.join(m['leagues'].keys())}\n{'─'*30}\n"
    msg += f"\n🔒 *Pure odds-based — no matchup dependency*\n⚠️ *Mega = high risk. Gamble responsibly.*"
    return msg


def run():
    print("="*60)
    print("🚀 ONIMIX MEGA AUDIT v4.1 — ODDS-BASED")
    print("="*60)
    start = time.time()
    correction = MegaCorrection()
    proven = load_proven()
    cands = scan_all()
    print(f"\n📊 Total: {len(cands)}")
    megas, scored = build_megas(cands, proven, correction)
    print(f"📊 Megas: {len(megas)}")
    msg = format_msg(megas, len(cands))
    send_telegram(msg)
    elapsed = time.time() - start
    print(f"\n⏱️ Done in {elapsed:.1f}s")
    return {"status": "success", "version": "4.1", "method": "ODDS-BASED MEGA",
            "candidates": len(cands), "megas": len(megas), "elapsed": round(elapsed,1)}

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
