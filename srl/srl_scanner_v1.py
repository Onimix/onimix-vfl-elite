"""
ONIMIX SRL ELITE Scanner v1
============================
Team-Pair Scoring Model for Simulated Reality League
- Scans upcoming SRL matches
- Scores each match based on team O1.5 profiles from 1518+ historical results
- Sends ELITE picks to Telegram with SportyBet booking codes
- Focus: Over 1.5 Goals market ONLY (SRL only, no eFootball)

Scoring Logic:
- Base: (home_o15_rate + away_o15_rate) / 2
- Bonus: +5 if both teams 80%+ O1.5
- Bonus: +3 if combined avg goals >= 5.0
- Bonus: +2 if tournament is Premier League SRL (highest O1.5 league)
- Penalty: -5 if either team < 65% O1.5
- Penalty: -3 if combined avg goals < 4.0

Tiers:
- ULTRA: score >= 85 (both teams elite + high scoring)
- PREMIUM: score >= 75 
- STANDARD: score >= 65

Dedup: hash-based, 30-min window, event ID tracking
"""
import requests, json, time, datetime, hashlib, os
from collections import defaultdict

BASE = 'https://www.sportybet.com/api/ng'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.sportybet.com/ng/m/virtual'
}
TG_TOKEN = '8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8'
CHAT_ID = '1745848158'
DEDUP_FILE = '/tmp/srl_scanner_dedup.json'

# ===== EMBEDDED TEAM PROFILES (from 1518 SRL matches) =====
TEAM_PROFILES = {
    "Liverpool SRL": {"o15_rate": 0.925, "avg_total": 3.15, "tournament": "Premier League SRL", "games": 40},
    "Bournemouth SRL": {"o15_rate": 0.900, "avg_total": 3.17, "tournament": "Premier League SRL", "games": 40},
    "Brighton SRL": {"o15_rate": 0.897, "avg_total": 3.26, "tournament": "Premier League SRL", "games": 39},
    "Crystal Palace SRL": {"o15_rate": 0.897, "avg_total": 2.82, "tournament": "Premier League SRL", "games": 39},
    "Kocaelispor Srl": {"o15_rate": 0.897, "avg_total": 3.17, "tournament": "Turkey Super Lig SRL", "games": 29},
    "UD Las Palmas Srl": {"o15_rate": 0.889, "avg_total": 2.89, "tournament": "LaLiga SRL", "games": 9},
    "Valladolid SRL": {"o15_rate": 0.875, "avg_total": 2.75, "tournament": "LaLiga SRL", "games": 8},
    "Tottenham SRL": {"o15_rate": 0.872, "avg_total": 3.21, "tournament": "Premier League SRL", "games": 39},
    "Trabzonspor SRL": {"o15_rate": 0.865, "avg_total": 2.97, "tournament": "Turkey Super Lig SRL", "games": 37},
    "Leicester SRL": {"o15_rate": 0.857, "avg_total": 3.86, "tournament": "Premier League SRL", "games": 7},
    "Southampton SRL": {"o15_rate": 0.857, "avg_total": 3.71, "tournament": "Premier League SRL", "games": 7},
    "Ipswich Town Srl": {"o15_rate": 0.857, "avg_total": 2.29, "tournament": "Premier League SRL", "games": 7},
    "Barcelona SRL": {"o15_rate": 0.850, "avg_total": 4.05, "tournament": "LaLiga SRL", "games": 40},
    "Celta SRL": {"o15_rate": 0.846, "avg_total": 2.72, "tournament": "LaLiga SRL", "games": 39},
    "Kasimpasa SRL": {"o15_rate": 0.842, "avg_total": 3.21, "tournament": "Turkey Super Lig SRL", "games": 38},
    "Gaziantep SRL": {"o15_rate": 0.833, "avg_total": 2.83, "tournament": "Turkey Super Lig SRL", "games": 36},
    "Aston Villa SRL": {"o15_rate": 0.825, "avg_total": 2.75, "tournament": "Premier League SRL", "games": 40},
    "Wolves SRL": {"o15_rate": 0.821, "avg_total": 2.92, "tournament": "Premier League SRL", "games": 39},
    "Roma SRL": {"o15_rate": 0.821, "avg_total": 2.85, "tournament": "Serie A SRL", "games": 39},
    "Nottingham Forest SRL": {"o15_rate": 0.821, "avg_total": 2.87, "tournament": "Premier League SRL", "games": 39},
    "Brentford SRL": {"o15_rate": 0.821, "avg_total": 2.72, "tournament": "Premier League SRL", "games": 39},
    "Inter SRL": {"o15_rate": 0.821, "avg_total": 2.51, "tournament": "Serie A SRL", "games": 39},
    "Rizespor SRL": {"o15_rate": 0.816, "avg_total": 2.82, "tournament": "Turkey Super Lig SRL", "games": 38},
    "Sunderland AFC Srl": {"o15_rate": 0.813, "avg_total": 2.47, "tournament": "Premier League SRL", "games": 32},
    "Leeds United SRL": {"o15_rate": 0.806, "avg_total": 3.06, "tournament": "Premier League SRL", "games": 31},
    "Galatasaray SRL": {"o15_rate": 0.806, "avg_total": 2.83, "tournament": "Turkey Super Lig SRL", "games": 36},
    "Fulham SRL": {"o15_rate": 0.800, "avg_total": 2.98, "tournament": "Premier League SRL", "games": 40},
    "Eyupspor Srl": {"o15_rate": 0.800, "avg_total": 2.86, "tournament": "Turkey Super Lig SRL", "games": 35},
    "Fenerbahce SRL": {"o15_rate": 0.795, "avg_total": 3.00, "tournament": "Turkey Super Lig SRL", "games": 39},
    "Atalanta SRL": {"o15_rate": 0.775, "avg_total": 2.70, "tournament": "Serie A SRL", "games": 40},
    "Juventus SRL": {"o15_rate": 0.769, "avg_total": 2.82, "tournament": "Serie A SRL", "games": 39},
    "Arsenal SRL": {"o15_rate": 0.775, "avg_total": 2.95, "tournament": "Premier League SRL", "games": 40},
    "Girona FC SRL": {"o15_rate": 0.769, "avg_total": 2.56, "tournament": "LaLiga SRL", "games": 39},
    "Valencia SRL": {"o15_rate": 0.763, "avg_total": 2.39, "tournament": "LaLiga SRL", "games": 38},
    "Villarreal SRL": {"o15_rate": 0.756, "avg_total": 2.88, "tournament": "LaLiga SRL", "games": 41},
    "Espanyol SRL": {"o15_rate": 0.750, "avg_total": 2.40, "tournament": "LaLiga SRL", "games": 40},
    "Udinese SRL": {"o15_rate": 0.756, "avg_total": 2.68, "tournament": "Serie A SRL", "games": 41},
    "Bologna SRL": {"o15_rate": 0.750, "avg_total": 2.45, "tournament": "Serie A SRL", "games": 40},
    "Betis SRL": {"o15_rate": 0.744, "avg_total": 2.59, "tournament": "LaLiga SRL", "games": 39},
    "Milan SRL": {"o15_rate": 0.744, "avg_total": 2.77, "tournament": "Serie A SRL", "games": 39},
    "Torino SRL": {"o15_rate": 0.744, "avg_total": 2.69, "tournament": "Serie A SRL", "games": 39},
    "Man City SRL": {"o15_rate": 0.775, "avg_total": 2.70, "tournament": "Premier League SRL", "games": 40},
    "Chelsea SRL": {"o15_rate": 0.775, "avg_total": 2.98, "tournament": "Premier League SRL", "games": 40},
    "West Ham SRL": {"o15_rate": 0.775, "avg_total": 2.78, "tournament": "Premier League SRL", "games": 40},
    "Everton SRL": {"o15_rate": 0.750, "avg_total": 2.50, "tournament": "Premier League SRL", "games": 40},
    "Newcastle SRL": {"o15_rate": 0.725, "avg_total": 2.43, "tournament": "Premier League SRL", "games": 40},
    "Man Utd SRL": {"o15_rate": 0.750, "avg_total": 2.73, "tournament": "Premier League SRL", "games": 40},
    "Real Madrid SRL": {"o15_rate": 0.725, "avg_total": 2.98, "tournament": "LaLiga SRL", "games": 40},
    "Napoli SRL": {"o15_rate": 0.700, "avg_total": 2.30, "tournament": "Serie A SRL", "games": 40},
    "Lazio SRL": {"o15_rate": 0.692, "avg_total": 2.23, "tournament": "Serie A SRL", "games": 39},
    "Fiorentina SRL": {"o15_rate": 0.711, "avg_total": 2.53, "tournament": "Serie A SRL", "games": 38},
    "Goztepe SRL": {"o15_rate": 0.757, "avg_total": 2.78, "tournament": "Turkey Super Lig SRL", "games": 37},
    "Alanyaspor SRL": {"o15_rate": 0.757, "avg_total": 2.49, "tournament": "Turkey Super Lig SRL", "games": 37},
    "Samsunspor Srl": {"o15_rate": 0.750, "avg_total": 2.78, "tournament": "Turkey Super Lig SRL", "games": 36},
    "Besiktas SRL": {"o15_rate": 0.744, "avg_total": 2.85, "tournament": "Turkey Super Lig SRL", "games": 39},
    "Antalyaspor SRL": {"o15_rate": 0.750, "avg_total": 2.61, "tournament": "Turkey Super Lig SRL", "games": 36},
    "Sivasspor SRL": {"o15_rate": 0.730, "avg_total": 2.54, "tournament": "Turkey Super Lig SRL", "games": 37},
}

# ===== DEDUP =====
def load_dedup():
    try:
        with open(DEDUP_FILE) as f: return json.load(f)
    except: return {'last_hash': '', 'last_time': 0, 'sent_eids': {}}

def save_dedup(dd):
    with open(DEDUP_FILE, 'w') as f: json.dump(dd, f)

def make_hash(picks):
    key = '|'.join(sorted(f"{p['eventId']}" for p in picks))
    return hashlib.md5(key.encode()).hexdigest()

def is_duplicate(picks, dd):
    h = make_hash(picks)
    if h == dd.get('last_hash', '') and time.time() - dd.get('last_time', 0) < 1800:
        return True
    return False

def filter_sent(picks, dd):
    now = time.time()
    # Clean old entries (1hr TTL)
    dd['sent_eids'] = {k: v for k, v in dd.get('sent_eids', {}).items() if now - v < 3600}
    return [p for p in picks if p['eventId'] not in dd.get('sent_eids', {})]

def mark_sent(picks, dd):
    now = time.time()
    dd['last_hash'] = make_hash(picks)
    dd['last_time'] = now
    for p in picks:
        dd.setdefault('sent_eids', {})[p['eventId']] = now
    save_dedup(dd)

# ===== SCORING =====
def score_match(home_name, away_name):
    """Score a match based on team profiles. Returns (score, details)"""
    home_p = None
    away_p = None
    
    # Fuzzy match team names (SRL names may vary slightly)
    for name, prof in TEAM_PROFILES.items():
        name_clean = name.replace(' SRL', '').replace(' Srl', '').lower().strip()
        home_clean = home_name.replace(' SRL', '').replace(' Srl', '').lower().strip()
        away_clean = away_name.replace(' SRL', '').replace(' Srl', '').lower().strip()
        
        if name_clean == home_clean or name_clean in home_clean or home_clean in name_clean:
            home_p = prof
        if name_clean == away_clean or name_clean in away_clean or away_clean in name_clean:
            away_p = prof
    
    if not home_p or not away_p:
        return 0, "Unknown team(s)"
    
    # Base score: average of both teams' O1.5 rates (0-100)
    base = (home_p['o15_rate'] + away_p['o15_rate']) / 2 * 100
    
    score = base
    details = []
    
    # Both teams 80%+ O1.5
    if home_p['o15_rate'] >= 0.80 and away_p['o15_rate'] >= 0.80:
        score += 5
        details.append("Both ELITE")
    
    # High combined avg goals
    combined_avg = home_p['avg_total'] + away_p['avg_total']
    if combined_avg >= 6.0:
        score += 3
        details.append(f"High scoring ({combined_avg:.1f})")
    elif combined_avg < 5.0:
        score -= 3
        details.append(f"Low scoring ({combined_avg:.1f})")
    
    # Premier League SRL bonus (highest O1.5 league at 82%)
    if home_p.get('tournament') == 'Premier League SRL':
        score += 2
        details.append("PL bonus")
    
    # Low O1.5 penalty
    if home_p['o15_rate'] < 0.65 or away_p['o15_rate'] < 0.65:
        score -= 5
        details.append("Weak team")
    
    # Sample size confidence
    min_games = min(home_p.get('games', 0), away_p.get('games', 0))
    if min_games < 10:
        score -= 2
        details.append(f"Low sample ({min_games}g)")
    
    return round(score, 1), ' | '.join(details) if details else 'Standard'

# ===== FETCH UPCOMING =====
def fetch_upcoming():
    events = []
    try:
        url = f'{BASE}/factsCenter/wapConfigurableUpcomingEvents?sportId=sr:sport:1&categoryId=sr:category:2123'
        r = requests.get(url, timeout=15, headers=HEADERS)
        if r.status_code == 200:
            data = r.json().get('data', [])
            if isinstance(data, list):
                for ev in data:
                    if isinstance(ev, dict) and ev.get('eventId'):
                        events.append(ev)
    except Exception as e:
        print(f'[WARN] fetch error: {e}')
    return events

# ===== BOOKING CODE =====
def get_booking_code(picks):
    """Generate SportyBet booking code for Over 1.5 selections"""
    selections = []
    for p in picks:
        selections.append({
            "eventId": p['eventId'],
            "marketId": "18",       # Over/Under
            "specifier": "total=1.5",
            "outcomeId": "12"       # Over
        })
    
    try:
        r = requests.post(f'{BASE}/orders/share',
            json={"selections": selections},
            headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            code = data.get('data', {}).get('shareCode', '')
            if code:
                return code
    except:
        pass
    return None

# ===== TELEGRAM =====
def tg_send(msg):
    try:
        requests.post(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
            json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}, timeout=10)
    except:
        pass

# ===== MAIN =====
dd = load_dedup()
now = datetime.datetime.now()
print(f'[{now.isoformat()}] ONIMIX SRL ELITE Scanner v1 starting...')

upcoming = fetch_upcoming()
print(f'Upcoming SRL events: {len(upcoming)}')

if not upcoming:
    print('No upcoming events. Silent exit.')
    exit(0)

# Score all matches
scored = []
for ev in upcoming:
    home = ev.get('homeTeamName', '?')
    away = ev.get('awayTeamName', '?')
    eid = ev.get('eventId', '')
    est = ev.get('estimateStartTime', 0)
    tourn = ev.get('sport', {}).get('category', {}).get('tournament', {}).get('name', '?')
    
    s, details = score_match(home, away)
    
    if s >= 65:  # Minimum threshold
        scored.append({
            'eventId': eid,
            'home': home,
            'away': away,
            'score': s,
            'details': details,
            'tournament': tourn,
            'kickoff': datetime.datetime.fromtimestamp(est/1000).strftime('%H:%M') if est else '?'
        })

scored.sort(key=lambda x: x['score'], reverse=True)

print(f'Qualified picks: {len(scored)}')
for p in scored:
    tier = 'ULTRA' if p['score'] >= 85 else 'PREMIUM' if p['score'] >= 75 else 'STANDARD'
    print(f'  [{tier}] {p["home"]} vs {p["away"]} | Score: {p["score"]} | {p["details"]}')

if not scored:
    print('No qualified picks. Silent exit.')
    exit(0)

# Filter already sent
scored = filter_sent(scored, dd)
if not scored:
    print('All picks already sent. Silent exit.')
    exit(0)

# Check dedup
if is_duplicate(scored, dd):
    print('Duplicate batch. Silent exit.')
    exit(0)

# Build tiers
ultra = [p for p in scored if p['score'] >= 85]
premium = [p for p in scored if 75 <= p['score'] < 85]
standard = [p for p in scored if 65 <= p['score'] < 75]

# Build message
msg = f'🏆 <b>ONIMIX SRL ELITE Scanner</b>\n'
msg += f'⏰ {now.strftime("%H:%M")} | 📊 {len(scored)} picks\n\n'

if ultra:
    msg += f'🔴 <b>ULTRA TIER ({len(ultra)} picks)</b>\n'
    for p in ultra:
        msg += f'⚡ {p["home"]} vs {p["away"]}\n'
        msg += f'   📊 Score: {p["score"]} | {p["details"]}\n'
        msg += f'   ⏰ {p["kickoff"]} | {p["tournament"]}\n\n'

if premium:
    msg += f'🟡 <b>PREMIUM TIER ({len(premium)} picks)</b>\n'
    for p in premium:
        msg += f'✅ {p["home"]} vs {p["away"]}\n'
        msg += f'   📊 Score: {p["score"]} | {p["details"]}\n'
        msg += f'   ⏰ {p["kickoff"]} | {p["tournament"]}\n\n'

if standard:
    msg += f'🟢 <b>STANDARD ({len(standard)} picks)</b>\n'
    for p in standard[:5]:  # Limit standard picks
        msg += f'📌 {p["home"]} vs {p["away"]} | {p["score"]}\n'
    msg += '\n'

# Get booking codes
if ultra:
    code = get_booking_code(ultra)
    if code:
        msg += f'🎫 <b>ULTRA Booking:</b> <code>{code}</code>\n'

all_qualified = ultra + premium
if len(all_qualified) >= 2:
    code = get_booking_code(all_qualified)
    if code:
        msg += f'🎫 <b>ULTRA+PREMIUM Booking:</b> <code>{code}</code>\n'

if scored:
    code = get_booking_code(scored[:10])
    if code:
        msg += f'🎫 <b>MEGA (all picks) Booking:</b> <code>{code}</code>\n'

msg += f'\n💡 Model: 1518 SRL matches analyzed'
msg += f'\n⚙️ eFootball excluded (human-controlled)'

tg_send(msg)
mark_sent(scored, dd)
print(f'\n✅ Sent {len(scored)} picks to Telegram')
print('=== DONE ===')
