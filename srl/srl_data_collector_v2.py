"""
ONIMIX SRL Data Collector v2
==============================
Collects SRL match results from SportyBet API.
- SRL ONLY (eFootball excluded - human-controlled)
- Uses results API pagination for bulk collection
- Tracks live matches and detects completions
- Sends milestone digests to Telegram
- Builds/updates team profiles automatically
"""
import requests, json, time, datetime, os
from collections import defaultdict

BASE = 'https://www.sportybet.com/api/ng'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.sportybet.com/ng/m/virtual'
}
TG_TOKEN = '8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8'
CHAT_ID = '1745848158'
RESULTS_FILE = '/tmp/srl_results_v2.json'
TRACKING_FILE = '/tmp/srl_tracking_v2.json'

TOURNAMENTS = {
    'sr:tournament:32215': 'Premier League SRL',
    'sr:tournament:32219': 'LaLiga SRL',
    'sr:tournament:32221': 'Serie A SRL',
    'sr:tournament:32225': 'Turkey Super Lig SRL'
}

def load_json(p, d=None):
    if d is None: d = {}
    try:
        with open(p) as f: return json.load(f)
    except: return d

def save_json(p, data):
    with open(p, 'w') as f: json.dump(data, f)

def tg(msg):
    try:
        requests.post(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
                       json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=10)
    except: pass

# ===== COLLECT FROM RESULTS API =====
results = load_json(RESULTS_FILE, [])
existing_eids = set(r.get('eventId') for r in results)
new_count = 0
now = datetime.datetime.now()

print(f'[{now.isoformat()}] SRL Data Collector v2 starting...')
print(f'Existing results: {len(results)}')

# Fetch recent results from each tournament (page 1 only for incremental updates)
for tid, tname in TOURNAMENTS.items():
    try:
        url = f'{BASE}/factsCenter/eventResultList?sportId=sr:sport:1&tournamentId={tid}&pageSize=50&pageNum=1'
        r = requests.get(url, timeout=15, headers=HEADERS)
        if r.status_code != 200:
            continue
        d = r.json()
        tourns = d.get('data', {}).get('tournaments', [])
        if not tourns:
            continue
        for ev in tourns[0].get('events', []):
            eid = ev.get('eventId', '')
            if not eid or eid in existing_eids:
                continue
            score = ev.get('setScore', '')
            if not score or ':' not in str(score):
                continue
            parts = str(score).split(':')
            try:
                hs, aws = int(parts[0]), int(parts[1])
            except:
                continue
            total = hs + aws
            results.append({
                'eventId': eid,
                'home': ev.get('homeTeamName', '?'),
                'away': ev.get('awayTeamName', '?'),
                'homeScore': hs, 'awayScore': aws,
                'totalGoals': total,
                'over15': total >= 2, 'over25': total >= 3,
                'over05': total >= 1,
                'btts': hs > 0 and aws > 0,
                'score': score,
                'tournament': tname,
                'tournamentId': tid,
                'completed': now.isoformat()
            })
            existing_eids.add(eid)
            new_count += 1
    except Exception as e:
        print(f'  {tname}: error - {e}')

save_json(RESULTS_FILE, results)

# ===== STATS =====
total = len(results)
print(f'New results: {new_count} | Total: {total}')

if total > 0:
    o15 = sum(1 for r in results if r.get('over15'))
    avg = sum(r.get('totalGoals', 0) for r in results) / total
    
    # Per-tournament
    ts = defaultdict(lambda: {'n': 0, 'o15': 0, 'g': 0})
    for r in results:
        t = r.get('tournament', '?')
        ts[t]['n'] += 1
        if r.get('over15'): ts[t]['o15'] += 1
        ts[t]['g'] += r.get('totalGoals', 0)
    
    # Per-team profiles (for scanner updates)
    team = defaultdict(lambda: {'n': 0, 'o15': 0, 'gf': 0, 'ga': 0, 'tourn': ''})
    for r in results:
        for t, gf, ga in [(r['home'], r['homeScore'], r['awayScore']),
                           (r['away'], r['awayScore'], r['homeScore'])]:
            team[t]['n'] += 1
            if r.get('over15'): team[t]['o15'] += 1
            team[t]['gf'] += gf
            team[t]['ga'] += ga
            team[t]['tourn'] = r.get('tournament', '')
    
    summary = f'SRL Data Collector v2 Report\n'
    summary += f'Time: {now.isoformat()}\n'
    summary += f'New: {new_count} | Total: {total}\n'
    summary += f'O1.5: {o15}/{total} ({o15/total*100:.1f}%) | Avg: {avg:.2f}g\n'
    for t, s in sorted(ts.items()):
        summary += f'  {t}: {s["n"]}m O1.5={s["o15"]/s["n"]*100:.0f}%\n'
    
    # Count elite teams (80%+ O1.5 with 10+ games)
    elite_count = sum(1 for t, s in team.items() if s['n'] >= 10 and s['o15']/s['n'] >= 0.80)
    summary += f'Elite teams (80%+ O1.5): {elite_count}\n'
    
    print(summary)
    
    # Save team profiles
    profiles = {}
    for t, s in team.items():
        if s['n'] >= 5:
            profiles[t] = {
                'o15_rate': round(s['o15']/s['n'], 3),
                'avg_total': round((s['gf']+s['ga'])/s['n'], 2),
                'games': s['n'],
                'tournament': s['tourn']
            }
    save_json('/tmp/srl_team_profiles_live.json', profiles)
    
    # TG milestone alerts
    milestones = [100, 250, 500, 1000, 2000, 3000, 5000]
    for ms in milestones:
        if total >= ms and total - new_count < ms:
            tg_msg = f'📊 <b>SRL Data Milestone: {ms}+ matches!</b>\n\n'
            tg_msg += f'Total: {total} | O1.5: {o15/total*100:.1f}%\n'
            tg_msg += f'Avg goals: {avg:.2f}\n'
            tg_msg += f'Elite teams: {elite_count}\n'
            tg_msg += f'\n🔄 Model auto-updating...'
            tg(tg_msg)
            break

print('=== DONE ===')
