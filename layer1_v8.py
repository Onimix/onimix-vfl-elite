#!/usr/bin/env python3
"""
ONIMIX VFL ELITE Scanner v8 — Layer 1
Rebuilt with LIVE VFL API (sr:sport:202120001)
690 ELITE matchups from 11,822 fresh matches
Hash-based dedup, prematch booking codes, Telegram delivery
"""
import requests, json, hashlib, time, os, sys
from datetime import datetime, timezone, timedelta

# ─── CONFIG ───
TG_TOKEN = "8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
TG_CHAT  = "1745848158"
BOOK_URL = "https://www.sportybet.com/api/ng/orders/share"
DEDUP_FILE = "/tmp/vfl_dedup_L1.json"
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

# ─── ELITE LOOKUP ───
ELITE_RAW = json.loads(open("/home/user/vfl_elite_lookup.json").read()) if os.path.exists("/home/user/vfl_elite_lookup.json") else {}

def build_elite_index():
    idx = {}
    for key, val in ELITE_RAW.items():
        parts = key.split("v", 1)
        if len(parts) == 2:
            lk = f"{val['lg']}|{parts[0]}|{parts[1]}"
            idx[lk] = val
    return idx

ELITE = build_elite_index()

# ─── DEDUP ───
def load_dedup():
    try:
        with open(DEDUP_FILE) as f:
            data = json.load(f)
        now = time.time()
        return {k: v for k, v in data.items() if now - v < DEDUP_TTL}
    except:
        return {}

def save_dedup(seen):
    with open(DEDUP_FILE, "w") as f:
        json.dump(seen, f)

def make_hash(pick):
    return hashlib.md5(f"{pick['eventId']}|{pick['home']}|{pick['away']}|L1".encode()).hexdigest()

# ─── FETCH UPCOMING + LIVE VFL MATCHES ───
def fetch_matches():
    matches = []
    now_ms = int(time.time() * 1000)
    seen_ids = set()
    
    # 1. Upcoming events (prematch)
    for lid, (cat_id, tourn_id, flag) in LEAGUES.items():
        try:
            url = "https://www.sportybet.com/api/ng/factsCenter/wapConfigurableUpcomingEvents"
            params = {"sportId": VFL_SPORT, "categoryId": cat_id, "tournamentId": tourn_id, "_t": now_ms}
            r = requests.get(url, params=params, headers=HEADERS, timeout=15)
            data = r.json()
            events = data.get("data", [])
            if isinstance(events, dict):
                events = events.get("tournaments", [{}])[0].get("events", []) if "tournaments" in events else []
            
            for e in events:
                eid = e.get("eventId", "")
                if eid in seen_ids:
                    continue
                seen_ids.add(eid)
                kick_off = e.get("estimateStartTime", 0)
                if kick_off > now_ms - 300000:  # Not older than 5 min
                    # Extract O1.5 odds from markets
                    o15_odds = None
                    for mkt in e.get("markets", []):
                        if mkt.get("id") == "18" and mkt.get("specifier") == "total=1.5":
                            for out in mkt.get("outcomes", []):
                                if out.get("id") == "12" or out.get("desc") == "Over":
                                    o15_odds = out.get("odds")
                    
                    matches.append({
                        "eventId": eid,
                        "home": e.get("homeTeamName", ""),
                        "away": e.get("awayTeamName", ""),
                        "kickoff": kick_off,
                        "league": flag,
                        "league_id": lid,
                        "status": e.get("matchStatus", ""),
                        "gameId": e.get("gameId", ""),
                        "o15_odds": o15_odds
                    })
            time.sleep(0.3)
        except Exception as ex:
            print(f"  Upcoming {flag} error: {ex}")
    
    # 2. Live events
    try:
        url = "https://www.sportybet.com/api/ng/factsCenter/wapConfigurableIndexLiveEvents"
        params = {"sportId": VFL_SPORT, "_t": now_ms}
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        data = r.json()
        events = data.get("data", [])
        if isinstance(events, dict):
            events = []
        
        for e in events:
            eid = e.get("eventId", "")
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            
            kick_off = e.get("estimateStartTime", 0)
            played = e.get("playedSeconds", "0:00")
            # Skip if >5 min played
            try:
                parts = played.split(":")
                mins_played = int(parts[0])
                if mins_played > 5:
                    continue
            except:
                pass
            
            # Determine league
            sport = e.get("sport", {})
            cat = sport.get("category", {})
            cat_id_val = cat.get("id", "")
            lid = None
            for l, (c, _, _) in LEAGUES.items():
                if c == cat_id_val:
                    lid = l
                    break
            if not lid:
                continue
            
            flag = LEAGUES[lid][2]
            
            o15_odds = None
            for mkt in e.get("markets", []):
                if mkt.get("id") == "18" and mkt.get("specifier") == "total=1.5":
                    for out in mkt.get("outcomes", []):
                        if out.get("id") == "12" or out.get("desc") == "Over":
                            o15_odds = out.get("odds")
            
            matches.append({
                "eventId": eid,
                "home": e.get("homeTeamName", ""),
                "away": e.get("awayTeamName", ""),
                "kickoff": kick_off,
                "league": flag,
                "league_id": lid,
                "status": e.get("matchStatus", ""),
                "gameId": e.get("gameId", ""),
                "o15_odds": o15_odds
            })
    except Exception as ex:
        print(f"  Live error: {ex}")
    
    return matches

# ─── SCORE ELITE MATCHES ───
def score_matches(matches):
    picks = []
    for m in matches:
        lg = LEAGUE_NAMES.get(m["league_id"], "")
        key = f"{lg}|{m['home']}|{m['away']}"
        
        if key in ELITE:
            stats = ELITE[key]
            o15_pct = stats["r"] * 100
            btts_pct = stats["b"] * 100
            games = stats["g"]
            
            if o15_pct >= 90:
                tier = "🔴 ULTRA"
            elif o15_pct >= 80:
                tier = "🟡 ELITE"
            else:
                continue
            
            picks.append({
                "eventId": m["eventId"],
                "home": m["home"],
                "away": m["away"],
                "league": m["league"],
                "kickoff": m["kickoff"],
                "o15_pct": o15_pct,
                "btts_pct": btts_pct,
                "games": games,
                "tier": tier,
                "gameId": m["gameId"],
                "o15_odds": m.get("o15_odds")
            })
    
    picks.sort(key=lambda x: -x["o15_pct"])
    return picks

# ─── BOOKING CODE ───
def get_booking_code(picks):
    if not picks:
        return None
    selections = []
    for p in picks[:10]:
        selections.append({
            "eventId": p["eventId"],
            "marketId": "18",
            "outcomeId": "12",
            "specifier": "total=1.5"
        })
    try:
        r = requests.post(BOOK_URL, json={"selections": selections},
                         headers={**HEADERS, "Content-Type": "application/json"}, timeout=15)
        data = r.json()
        return data.get("data", {}).get("code") or data.get("data", {}).get("shareCode")
    except:
        return None

# ─── TELEGRAM ───
def send_telegram(text):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                         json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"}, timeout=15)
        return r.json().get("ok", False)
    except:
        return False

# ─── MAIN ───
def main():
    now = datetime.now(WAT)
    print(f"[L1 VFL ELITE v8] {now.strftime('%H:%M:%S WAT')}")
    print(f"ELITE database: {len(ELITE)} matchups")
    
    matches = fetch_matches()
    print(f"Upcoming/live matches: {len(matches)}")
    
    if not matches:
        print("No matches found. Silent exit.")
        return
    
    picks = score_matches(matches)
    print(f"ELITE picks: {len(picks)}")
    
    if not picks:
        print("No ELITE matches in current round. Silent exit.")
        return
    
    # Dedup
    seen = load_dedup()
    new_picks = [p for p in picks if make_hash(p) not in seen]
    for p in new_picks:
        seen[make_hash(p)] = time.time()
    save_dedup(seen)
    print(f"New picks after dedup: {len(new_picks)}")
    
    if not new_picks:
        print("All picks already sent. Silent exit.")
        return
    
    booking = get_booking_code(new_picks)
    
    ultra = [p for p in new_picks if "ULTRA" in p["tier"]]
    elite = [p for p in new_picks if "ELITE" in p["tier"]]
    
    lines = [f"⚽ <b>ONIMIX VFL ELITE v8</b>", f"📅 {now.strftime('%d %b %Y • %H:%M WAT')}", ""]
    
    if ultra:
        lines.append("🔴 <b>ULTRA PICKS (≥90% O1.5)</b>")
        for p in ultra:
            kt = datetime.fromtimestamp(p["kickoff"]/1000, WAT).strftime("%H:%M")
            odds_str = f" @{p['o15_odds']}" if p.get("o15_odds") else ""
            lines.append(f"  🔥 {p['league']} {p['home']} vs {p['away']}")
            lines.append(f"     ⏰ {kt} | O1.5={p['o15_pct']:.0f}% | {p['games']}G{odds_str}")
        lines.append("")
    
    if elite:
        lines.append("🟡 <b>ELITE PICKS (80-89% O1.5)</b>")
        for p in elite:
            kt = datetime.fromtimestamp(p["kickoff"]/1000, WAT).strftime("%H:%M")
            odds_str = f" @{p['o15_odds']}" if p.get("o15_odds") else ""
            lines.append(f"  ⚡ {p['league']} {p['home']} vs {p['away']}")
            lines.append(f"     ⏰ {kt} | O1.5={p['o15_pct']:.0f}% | {p['games']}G{odds_str}")
        lines.append("")
    
    lines.append(f"📊 {len(ultra)} ULTRA + {len(elite)} ELITE = {len(new_picks)} picks")
    if booking:
        lines.append(f"\n🎫 <b>BOOKING CODE:</b> <code>{booking}</code>")
        lines.append("👉 Paste on SportyBet to bet all at once!")
    lines.append(f"\n🤖 Layer 1 | 690 ELITE from 11,822 matches")
    
    msg = "\n".join(lines)
    print(f"\n{msg}\n")
    ok = send_telegram(msg)
    print(f"Telegram sent: {ok}")

if __name__ == "__main__":
    main()
