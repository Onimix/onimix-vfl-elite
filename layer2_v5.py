#!/usr/bin/env python3
"""
ONIMIX VFL Layer 2 — 12-Layer Scoring Engine v5
Rebuilt with LIVE VFL API (sr:sport:202120001)
Team profiles from 11,822 fresh matches + ONIMIX scoring logic
"""
import requests, json, hashlib, time, os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

TG_TOKEN = "8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
TG_CHAT  = "1745848158"
BOOK_URL = "https://www.sportybet.com/api/ng/orders/share"
DEDUP_FILE = "/tmp/vfl_dedup_L2.json"
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

# ─── BUILD TEAM PROFILES FROM FRESH DATA ───
def build_team_profiles():
    """Build team-level stats from 7-day data"""
    try:
        with open("/home/user/vfl_fresh_7days.json") as f:
            matches = json.load(f)
    except:
        return {}
    
    teams = defaultdict(lambda: {
        "games": 0, "goals_scored": 0, "goals_conceded": 0,
        "o05": 0, "o15": 0, "o25": 0, "btts": 0,
        "home_games": 0, "home_o15": 0,
        "away_games": 0, "away_o15": 0,
        "recent_totals": [],
        "league": ""
    })
    
    for m in matches:
        score = m["score"].split(":")
        hg, ag = int(score[0]), int(score[1])
        total = hg + ag
        lg = m["league"]
        
        # Home team
        hk = f"{lg}|{m['home']}"
        teams[hk]["games"] += 1
        teams[hk]["goals_scored"] += hg
        teams[hk]["goals_conceded"] += ag
        teams[hk]["o05"] += 1 if total >= 1 else 0
        teams[hk]["o15"] += 1 if total >= 2 else 0
        teams[hk]["o25"] += 1 if total >= 3 else 0
        teams[hk]["btts"] += 1 if (hg >= 1 and ag >= 1) else 0
        teams[hk]["home_games"] += 1
        teams[hk]["home_o15"] += 1 if total >= 2 else 0
        teams[hk]["recent_totals"].append(total)
        teams[hk]["league"] = lg
        
        # Away team
        ak = f"{lg}|{m['away']}"
        teams[ak]["games"] += 1
        teams[ak]["goals_scored"] += ag
        teams[ak]["goals_conceded"] += hg
        teams[ak]["o05"] += 1 if total >= 1 else 0
        teams[ak]["o15"] += 1 if total >= 2 else 0
        teams[ak]["o25"] += 1 if total >= 3 else 0
        teams[ak]["btts"] += 1 if (hg >= 1 and ag >= 1) else 0
        teams[ak]["away_games"] += 1
        teams[ak]["away_o15"] += 1 if total >= 2 else 0
        teams[ak]["recent_totals"].append(total)
        teams[ak]["league"] = lg
    
    # Compute rates
    profiles = {}
    for key, t in teams.items():
        if t["games"] < 3:
            continue
        profiles[key] = {
            "games": t["games"],
            "avg_scored": round(t["goals_scored"] / t["games"], 2),
            "avg_conceded": round(t["goals_conceded"] / t["games"], 2),
            "o05_rate": round(t["o05"] / t["games"], 4),
            "o15_rate": round(t["o15"] / t["games"], 4),
            "o25_rate": round(t["o25"] / t["games"], 4),
            "btts_rate": round(t["btts"] / t["games"], 4),
            "home_o15": round(t["home_o15"] / max(t["home_games"], 1), 4),
            "away_o15": round(t["away_o15"] / max(t["away_games"], 1), 4),
            "recent_avg": round(sum(t["recent_totals"][-10:]) / min(len(t["recent_totals"]), 10), 2),
            "streak_o15": sum(1 for g in t["recent_totals"][-5:] if g >= 2),
            "league": t["league"]
        }
    return profiles

TEAM_PROFILES = build_team_profiles()

# ─── ELITE LOOKUP ───
ELITE_RAW = json.loads(open("/home/user/vfl_elite_lookup.json").read()) if os.path.exists("/home/user/vfl_elite_lookup.json") else {}
def build_elite_index():
    idx = {}
    for key, val in ELITE_RAW.items():
        parts = key.split("v", 1)
        if len(parts) == 2:
            idx[f"{val['lg']}|{parts[0]}|{parts[1]}"] = val
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

# ─── FETCH MATCHES ───
def fetch_matches():
    matches = []
    now_ms = int(time.time() * 1000)
    seen_ids = set()
    
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
                if kick_off > now_ms - 300000:
                    o15_odds = None
                    for mkt in e.get("markets", []):
                        if mkt.get("id") == "18" and mkt.get("specifier") == "total=1.5":
                            for out in mkt.get("outcomes", []):
                                if out.get("id") == "12" or out.get("desc") == "Over":
                                    o15_odds = out.get("odds")
                    matches.append({
                        "eventId": eid, "home": e.get("homeTeamName", ""),
                        "away": e.get("awayTeamName", ""), "kickoff": kick_off,
                        "league": flag, "league_id": lid,
                        "status": e.get("matchStatus", ""), "gameId": e.get("gameId", ""),
                        "o15_odds": o15_odds
                    })
            time.sleep(0.3)
        except Exception as ex:
            print(f"  Upcoming {flag}: {ex}")
    
    # Also grab live (early minutes)
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
            played = e.get("playedSeconds", "0:00")
            try:
                mins = int(played.split(":")[0])
                if mins > 5:
                    continue
            except:
                pass
            cat = e.get("sport", {}).get("category", {}).get("id", "")
            lid = None
            for l, (c, _, _) in LEAGUES.items():
                if c == cat:
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
                "eventId": eid, "home": e.get("homeTeamName", ""),
                "away": e.get("awayTeamName", ""), "kickoff": e.get("estimateStartTime", 0),
                "league": flag, "league_id": lid,
                "status": e.get("matchStatus", ""), "gameId": e.get("gameId", ""),
                "o15_odds": o15_odds
            })
    except:
        pass
    return matches

# ─── 12-LAYER ONIMIX SCORING ───
def score_12layer(m):
    lg = LEAGUE_NAMES.get(m["league_id"], "")
    home_key = f"{lg}|{m['home']}"
    away_key = f"{lg}|{m['away']}"
    
    hp = TEAM_PROFILES.get(home_key)
    ap = TEAM_PROFILES.get(away_key)
    
    if not hp or not ap:
        return None, {}
    
    score = 0
    layers = {}
    
    # Layer 1: O0.5 Safety Net
    avg_o05 = (hp["o05_rate"] + ap["o05_rate"]) / 2
    l1 = round(avg_o05 * 15, 1)
    score += l1
    layers["O0.5"] = l1
    
    # Layer 2: O1.5 Core
    avg_o15 = (hp["o15_rate"] + ap["o15_rate"]) / 2
    l2 = round(avg_o15 * 25, 1)
    score += l2
    layers["O1.5"] = l2
    
    # Layer 3: O2.5 Bonus
    avg_o25 = (hp["o25_rate"] + ap["o25_rate"]) / 2
    l3 = round(avg_o25 * 10, 1)
    score += l3
    layers["O2.5"] = l3
    
    # Layer 4: BTTS Power
    avg_btts = (hp["btts_rate"] + ap["btts_rate"]) / 2
    l4 = round(avg_btts * 12, 1)
    score += l4
    layers["BTTS"] = l4
    
    # Layer 5: Attack Strength
    combined_attack = hp["avg_scored"] + ap["avg_scored"]
    l5 = round(min(combined_attack / 4.0, 1.0) * 10, 1)
    score += l5
    layers["ATK"] = l5
    
    # Layer 6: Defense Weakness (higher = weaker defense = more goals)
    combined_concede = hp["avg_conceded"] + ap["avg_conceded"]
    l6 = round(min(combined_concede / 4.0, 1.0) * 8, 1)
    score += l6
    layers["DEF"] = l6
    
    # Layer 7: Home/Away Venue Factor
    venue_o15 = (hp["home_o15"] + ap["away_o15"]) / 2
    l7 = round(venue_o15 * 5, 1)
    score += l7
    layers["VEN"] = l7
    
    # Layer 8: Recent Trend (last 10 games avg goals)
    trend = (hp["recent_avg"] + ap["recent_avg"]) / 2
    l8 = round(min(trend / 3.5, 1.0) * 5, 1)
    score += l8
    layers["TRD"] = l8
    
    # Layer 9: Momentum (streak of O1.5 in last 5)
    streak = (hp["streak_o15"] + ap["streak_o15"]) / 2
    l9 = round((streak / 5.0) * 5, 1)
    score += l9
    layers["MOM"] = l9
    
    # Layer 10: ELITE Matchup Bonus
    mk = f"{lg}|{m['home']}|{m['away']}"
    if mk in ELITE:
        l10 = 5.0
    else:
        l10 = 0
    score += l10
    layers["ELT"] = l10
    
    # Layer 11: League Bonus (England & Germany higher scoring)
    if lg in ["England", "Germany", "France"]:
        l11 = 2.0
    else:
        l11 = 0
    score += l11
    layers["LGB"] = l11
    
    # Layer 12: Odds Confidence
    if m.get("o15_odds"):
        try:
            odds_val = float(m["o15_odds"])
            if odds_val < 1.3:
                l12 = 3.0
            elif odds_val < 1.5:
                l12 = 2.0
            elif odds_val < 1.8:
                l12 = 1.0
            else:
                l12 = 0
        except:
            l12 = 0
    else:
        l12 = 0
    score += l12
    layers["ODS"] = l12
    
    return round(score, 1), layers

# ─── BOOKING CODE ───
def get_booking_code(picks):
    if not picks:
        return None
    selections = [{"eventId": p["eventId"], "marketId": "18", "outcomeId": "12", "specifier": "total=1.5"} for p in picks[:10]]
    try:
        r = requests.post(BOOK_URL, json={"selections": selections}, headers={**HEADERS, "Content-Type": "application/json"}, timeout=15)
        data = r.json()
        return data.get("data", {}).get("code") or data.get("data", {}).get("shareCode")
    except:
        return None

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
    print(f"[L2 ONIMIX 12-Layer v5] {now.strftime('%H:%M:%S WAT')}")
    print(f"Team profiles: {len(TEAM_PROFILES)}")
    
    matches = fetch_matches()
    print(f"Matches: {len(matches)}")
    
    if not matches:
        print("No matches. Silent exit.")
        return
    
    # Score all matches
    scored = []
    for m in matches:
        score, layers = score_12layer(m)
        if score is not None:
            scored.append({**m, "score": score, "layers": layers})
    
    scored.sort(key=lambda x: -x["score"])
    
    # Tier classification (max possible ~105)
    ultra = [s for s in scored if s["score"] >= 75]
    premium = [s for s in scored if 60 <= s["score"] < 75]
    standard = [s for s in scored if 50 <= s["score"] < 60]
    
    picks = ultra + premium  # Only send ULTRA + PREMIUM
    print(f"Scored: {len(scored)} | ULTRA: {len(ultra)} | PREMIUM: {len(premium)} | STANDARD: {len(standard)}")
    
    if not picks:
        print("No qualifying picks. Silent exit.")
        return
    
    # Dedup
    seen = load_dedup()
    new_picks = []
    for p in picks:
        h = hashlib.md5(f"{p['eventId']}|{p['home']}|{p['away']}|L2".encode()).hexdigest()
        if h not in seen:
            new_picks.append(p)
            seen[h] = time.time()
    save_dedup(seen)
    
    if not new_picks:
        print("All picks already sent. Silent exit.")
        return
    
    booking = get_booking_code(new_picks)
    
    lines = [f"🧠 <b>ONIMIX 12-Layer Engine v5</b>", f"📅 {now.strftime('%d %b %Y • %H:%M WAT')}", ""]
    
    u_picks = [p for p in new_picks if p["score"] >= 75]
    p_picks = [p for p in new_picks if 60 <= p["score"] < 75]
    
    if u_picks:
        lines.append("🔴 <b>ULTRA (Score ≥75)</b>")
        for p in u_picks[:8]:
            kt = datetime.fromtimestamp(p["kickoff"]/1000, WAT).strftime("%H:%M")
            odds_str = f" @{p['o15_odds']}" if p.get("o15_odds") else ""
            lines.append(f"  🔥 {p['league']} {p['home']} vs {p['away']}")
            lines.append(f"     ⏰ {kt} | Score={p['score']:.0f}/105{odds_str}")
        lines.append("")
    
    if p_picks:
        lines.append("🟡 <b>PREMIUM (Score 60-74)</b>")
        for p in p_picks[:8]:
            kt = datetime.fromtimestamp(p["kickoff"]/1000, WAT).strftime("%H:%M")
            odds_str = f" @{p['o15_odds']}" if p.get("o15_odds") else ""
            lines.append(f"  ⚡ {p['league']} {p['home']} vs {p['away']}")
            lines.append(f"     ⏰ {kt} | Score={p['score']:.0f}/105{odds_str}")
        lines.append("")
    
    lines.append(f"📊 {len(u_picks)} ULTRA + {len(p_picks)} PREMIUM = {len(new_picks)} picks")
    if booking:
        lines.append(f"\n🎫 <b>BOOKING CODE:</b> <code>{booking}</code>")
        lines.append("👉 Paste on SportyBet to bet all at once!")
    lines.append(f"\n🤖 Layer 2 | {len(TEAM_PROFILES)} team profiles")
    
    msg = "\n".join(lines)
    print(f"\n{msg}\n")
    ok = send_telegram(msg)
    print(f"Telegram: {ok}")

if __name__ == "__main__":
    main()
