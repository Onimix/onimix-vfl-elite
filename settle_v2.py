#!/usr/bin/env python3
"""
VFL Settlement Engine v2 — All 5 Leagues
Runs after every agent cycle to settle predictions from state.json
"""
import json, urllib.request, time, os, sys

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO  = "Qalaxy/vfl-engine"
STATE_FILE   = "data/state.json"

LEAGUES = [
    ("sv:category:202120001", "sv:league:1", "England"),
    ("sv:category:202120002", "sv:league:2", "Spain"),
    ("sv:category:202120003", "sv:league:3", "Italy"),
    ("sv:category:202120004", "sv:league:4", "Germany"),
    ("sv:category:202120005", "sv:league:5", "France"),
]

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"predictions": {}}

def save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def fetch_results(earliest_ms, latest_ms):
    all_finished = []
    for cat_id, league_id, name in LEAGUES:
        for page in range(1, 6):
            url = (
                f"https://www.sportybet.com/api/ng/factsCenter/eventResultList"
                f"?sportId=sr:sport:202120001&categoryId={cat_id}"
                f"&tournamentId={league_id}&pageNum={page}&pageSize=100"
                f"&startTime={earliest_ms - 3600000}&endTime={latest_ms + 7200000}"
            )
            try:
                with urllib.request.urlopen(url, timeout=10) as r:
                    data = json.loads(r.read())
                tournaments = data.get("data", {}).get("tournaments", [])
                if not tournaments:
                    break
                events = tournaments[0].get("events", [])
                finished = [
                    (e["homeTeamName"], e["awayTeamName"], e["setScore"])
                    for e in events if e.get("matchStatus") == "End"
                ]
                all_finished.extend(finished)
                if len(events) < 100:
                    break
            except Exception as ex:
                break
    return all_finished

def settle():
    state = load_state()
    predictions = state.get("predictions", {})

    pending = [(p.get("start", 0), pid, p)
               for pid, p in predictions.items()
               if p.get("status") != "settled"]

    if not pending:
        print("✅ No pending predictions to settle.")
        return

    earliest_ms = min(s for s, _, _ in pending)
    latest_ms   = max(s for s, _, _ in pending)
    print(f"🔍 Settling {len(pending)} predictions across 5 leagues...")

    finished = fetch_results(earliest_ms, latest_ms)
    print(f"   Found {len(finished)} finished matches from API")

    settled_count = 0
    for _, pred_id, pred in pending:
        ph, pa = pred.get("home", ""), pred.get("away", "")
        for ah, aa, score in finished:
            if ph == ah and pa == aa:
                h, a = map(int, score.split(":"))
                total = h + a
                result = "WON" if total >= 2 else "LOST"
                pred.update({
                    "actual_score": score,
                    "total_goals": total,
                    "status": "settled",
                    "settled_at": time.time(),
                    "result": result
                })
                sym = "✅" if result == "WON" else "❌"
                print(f"  {sym} {ph} v {pa}: {score} → {result}")
                settled_count += 1
                break

    save_state(state)

    won  = sum(1 for p in predictions.values() if p.get("result") == "WON")
    lost = sum(1 for p in predictions.values() if p.get("result") == "LOST")
    pend = sum(1 for p in predictions.values() if p.get("status") != "settled")

    print(f"\n📊 SETTLEMENT COMPLETE: {settled_count} new")
    print(f"   ✅ Won:     {won}")
    print(f"   ❌ Lost:    {lost}")
    print(f"   ⏳ Pending: {pend}")
    if won + lost > 0:
        print(f"   📈 Win Rate: {won/(won+lost)*100:.1f}% ({won}/{won+lost})")

if __name__ == "__main__":
    settle()
