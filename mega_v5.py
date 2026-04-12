#!/usr/bin/env python3
"""
ONIMIX VFL MEGA Accumulator v5
Combines Layer 1 (ELITE) + Layer 2 (12-Layer) for 3-tier accumulators
Only sends TOP picks with highest combined confidence
"""
import requests, json, hashlib, time, os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

TG_TOKEN = "8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
TG_CHAT  = "1745848158"
BOOK_URL = "https://www.sportybet.com/api/ng/orders/share"
DEDUP_FILE = "/tmp/vfl_dedup_MEGA.json"
DEDUP_TTL  = 3600
WAT = timezone(timedelta(hours=1))
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

VFL_SPORT = "sr:sport:202120001"
LEAGUES = {
    1: ("sv:category:202120001", "sv:league:1", "🏴 ENG"),
    2: ("sv:category:202120002", "sv:league:2", "🇪🇸 ESP"),
    3: ("sv:category:202120003", "sv:league:3", "🇮🇹 ITA"),
    4: ("sv:category:202120004", "sv:league:4", "🇩🇪 GER"),
    5: ("sv:category:202120005", "sv:league:5", "🇫🇷 FRA"),
}
LEAGUE_NAMES = {1: "England", 2: "Spain", 3: "Italy", 4: "Germany", 5: "France"}

# Load ELITE lookup
ELITE_RAW = json.loads(open("/home/user/vfl_elite_lookup.json").read()) if os.path.exists("/home/user/vfl_elite_lookup.json") else {}
def build_elite_index():
    idx = {}
    for key, val in ELITE_RAW.items():
        parts = key.split("v", 1)
        if len(parts) == 2:
            idx[f"{val['lg']}|{parts[0]}|{parts[1]}"] = val
    return idx
ELITE = build_elite_index()

# Load team profiles
def build_team_profiles():
    try:
        with open("/home/user/vfl_fresh_7days.json") as f:
            matches = json.load(f)
    except:
        return {}
    teams = defaultdict(lambda: {"games":0,"gs":0,"gc":0,"o05":0,"o15":0,"o25":0,"btts":0,"ho15":0,"hg":0,"ao15":0,"ag":0,"rec":[],"lg":""})
    for m in matches:
        s = m["score"].split(":")
        hg, ag = int(s[0]), int(s[1])
        t = hg + ag
        lg = m["league"]
        for tk, gs, gc, is_h in [(f"{lg}|{m['home']}", hg, ag, True), (f"{lg}|{m['away']}", ag, hg, False)]:
            teams[tk]["games"] += 1; teams[tk]["gs"] += gs; teams[tk]["gc"] += gc
            teams[tk]["o05"] += 1 if t>=1 else 0; teams[tk]["o15"] += 1 if t>=2 else 0
            teams[tk]["o25"] += 1 if t>=3 else 0; teams[tk]["btts"] += 1 if (hg>=1 and ag>=1) else 0
            if is_h: teams[tk]["hg"] += 1; teams[tk]["ho15"] += 1 if t>=2 else 0
            else: teams[tk]["ag"] += 1; teams[tk]["ao15"] += 1 if t>=2 else 0
            teams[tk]["rec"].append(t); teams[tk]["lg"] = lg
    profiles = {}
    for k, t in teams.items():
        if t["games"] < 3: continue
        profiles[k] = {
            "g": t["games"], "as": round(t["gs"]/t["games"],2), "ac": round(t["gc"]/t["games"],2),
            "o15r": round(t["o15"]/t["games"],4), "o25r": round(t["o25"]/t["games"],4),
            "btts": round(t["btts"]/t["games"],4),
            "ho15": round(t["ho15"]/max(t["hg"],1),4), "ao15": round(t["ao15"]/max(t["ag"],1),4),
            "ravg": round(sum(t["rec"][-10:])/min(len(t["rec"]),10),2),
            "stk": sum(1 for g in t["rec"][-5:] if g>=2)
        }
    return profiles
TP = build_team_profiles()

def load_dedup():
    try:
        with open(DEDUP_FILE) as f: data = json.load(f)
        now = time.time()
        return {k:v for k,v in data.items() if now-v < DEDUP_TTL}
    except: return {}

def save_dedup(s):
    with open(DEDUP_FILE, "w") as f: json.dump(s, f)

def fetch_matches():
    matches = []; now_ms = int(time.time()*1000); seen = set()
    for lid, (cat_id, tourn_id, flag) in LEAGUES.items():
        try:
            r = requests.get("https://www.sportybet.com/api/ng/factsCenter/wapConfigurableUpcomingEvents",
                params={"sportId":VFL_SPORT,"categoryId":cat_id,"tournamentId":tourn_id,"_t":now_ms}, headers=HEADERS, timeout=15)
            events = r.json().get("data", [])
            if isinstance(events, dict): events = []
            for e in events:
                eid = e.get("eventId","")
                if eid in seen: continue
                seen.add(eid)
                ko = e.get("estimateStartTime",0)
                if ko > now_ms - 300000:
                    o15_odds = None
                    for mkt in e.get("markets",[]):
                        if mkt.get("id")=="18" and mkt.get("specifier")=="total=1.5":
                            for out in mkt.get("outcomes",[]):
                                if out.get("id")=="12" or out.get("desc")=="Over": o15_odds = out.get("odds")
                    matches.append({"eventId":eid,"home":e.get("homeTeamName",""),"away":e.get("awayTeamName",""),
                        "kickoff":ko,"league":flag,"league_id":lid,"gameId":e.get("gameId",""),"o15_odds":o15_odds})
            time.sleep(0.3)
        except: pass
    return matches

def mega_score(m):
    """Combined ELITE + 12-Layer mega score (0-100)"""
    lg = LEAGUE_NAMES.get(m["league_id"],"")
    mk = f"{lg}|{m['home']}|{m['away']}"
    hk, ak = f"{lg}|{m['home']}", f"{lg}|{m['away']}"
    hp, ap = TP.get(hk), TP.get(ak)
    
    if not hp or not ap:
        return None
    
    score = 0
    
    # ELITE component (0-30)
    if mk in ELITE:
        er = ELITE[mk]["r"]
        score += er * 30
    else:
        avg_o15 = (hp["o15r"] + ap["o15r"]) / 2
        score += avg_o15 * 20
    
    # Attack power (0-15)
    atk = (hp["as"] + ap["as"]) / 2
    score += min(atk / 2.5, 1.0) * 15
    
    # O1.5 consistency (0-15)
    o15_avg = (hp["o15r"] + ap["o15r"]) / 2
    score += o15_avg * 15
    
    # BTTS factor (0-10)
    btts = (hp["btts"] + ap["btts"]) / 2
    score += btts * 10
    
    # Venue factor (0-10)
    venue = (hp["ho15"] + ap["ao15"]) / 2
    score += venue * 10
    
    # Momentum (0-10)
    mom = (hp["stk"] + ap["stk"]) / 10
    score += mom * 10
    
    # Odds confidence (0-10)
    if m.get("o15_odds"):
        try:
            odds = float(m["o15_odds"])
            if odds < 1.3: score += 10
            elif odds < 1.5: score += 7
            elif odds < 1.8: score += 4
        except: pass
    
    return round(score, 1)

def get_booking_code(picks):
    if not picks: return None
    sels = [{"eventId":p["eventId"],"marketId":"18","outcomeId":"12","specifier":"total=1.5"} for p in picks[:10]]
    try:
        r = requests.post(BOOK_URL, json={"selections":sels}, headers={**HEADERS,"Content-Type":"application/json"}, timeout=15)
        d = r.json()
        return d.get("data",{}).get("code") or d.get("data",{}).get("shareCode")
    except: return None

def send_telegram(text):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id":TG_CHAT,"text":text,"parse_mode":"HTML"}, timeout=15)
        return r.json().get("ok",False)
    except: return False

def main():
    now = datetime.now(WAT)
    print(f"[MEGA v5] {now.strftime('%H:%M:%S WAT')}")
    
    matches = fetch_matches()
    print(f"Matches: {len(matches)}")
    if not matches: return
    
    scored = []
    for m in matches:
        s = mega_score(m)
        if s is not None:
            scored.append({**m, "mega_score": s})
    scored.sort(key=lambda x: -x["mega_score"])
    
    # 3 Tiers
    t1 = [s for s in scored if s["mega_score"] >= 80]  # ULTRA MEGA
    t2 = [s for s in scored if 65 <= s["mega_score"] < 80]  # MEGA
    t3 = [s for s in scored if 50 <= s["mega_score"] < 65]  # STRONG
    
    print(f"ULTRA MEGA: {len(t1)} | MEGA: {len(t2)} | STRONG: {len(t3)}")
    
    # Build accumulators
    accas = []
    
    # Acca 1: ULTRA MEGA (top 3-5, highest confidence)
    if len(t1) >= 3:
        accas.append(("🔴 ULTRA MEGA", t1[:5]))
    elif len(t1) >= 2 and len(t2) >= 1:
        accas.append(("🔴 ULTRA MEGA", (t1 + t2[:2])[:5]))
    
    # Acca 2: MEGA MIX (5-7 picks from t1+t2)
    mega_pool = t1 + t2
    if len(mega_pool) >= 5:
        accas.append(("🟡 MEGA MIX", mega_pool[:7]))
    
    # Acca 3: FULL HOUSE (top 10)
    full_pool = t1 + t2 + t3
    if len(full_pool) >= 8:
        accas.append(("🟢 FULL HOUSE", full_pool[:10]))
    
    if not accas:
        print("Not enough qualifying picks for accumulator. Silent exit.")
        return
    
    # Dedup
    seen = load_dedup()
    all_event_ids = set()
    for _, picks in accas:
        for p in picks:
            all_event_ids.add(p["eventId"])
    
    acca_hash = hashlib.md5("|".join(sorted(all_event_ids)).encode()).hexdigest()
    if acca_hash in seen:
        print("Accumulator already sent. Silent exit.")
        return
    seen[acca_hash] = time.time()
    save_dedup(seen)
    
    # Build message
    lines = [f"🎯 <b>ONIMIX VFL MEGA v5</b>", f"📅 {now.strftime('%d %b %Y • %H:%M WAT')}", ""]
    
    for tier_name, picks in accas:
        booking = get_booking_code(picks)
        
        # Calculate combined odds
        total_odds = 1.0
        for p in picks:
            if p.get("o15_odds"):
                try: total_odds *= float(p["o15_odds"])
                except: pass
        
        lines.append(f"{tier_name} ({len(picks)} picks)")
        for p in picks:
            kt = datetime.fromtimestamp(p["kickoff"]/1000, WAT).strftime("%H:%M")
            odds_str = f"@{p['o15_odds']}" if p.get("o15_odds") else ""
            lines.append(f"  • {p['league']} {p['home']} vs {p['away']} ⏰{kt} {odds_str}")
        
        if total_odds > 1:
            lines.append(f"  💰 Combined odds: <b>{total_odds:.2f}</b>")
        if booking:
            lines.append(f"  🎫 Code: <code>{booking}</code>")
        lines.append("")
    
    lines.append(f"🤖 Mega Engine | {len(ELITE)} ELITE + {len(TP)} profiles")
    
    msg = "\n".join(lines)
    print(f"\n{msg}\n")
    ok = send_telegram(msg)
    print(f"Telegram: {ok}")

if __name__ == "__main__":
    main()
