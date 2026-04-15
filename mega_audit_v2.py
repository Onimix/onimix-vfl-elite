#!/usr/bin/env python3
"""
MEGA AUDIT v2.0 - Matchup-First Strategy
=========================================
Only picks from PROVEN Gold/Silver matchups (14-day verified).
Target: 20,000x combined odds with ~21% win probability.

Changes from v1:
- No more random picks - ONLY verified matchups
- Gold matchups: 100% Over 1.5 across 14 days (5 matchups)
- Silver matchups: 92.9% Over 1.5 across 14 days (40 matchups)
- Trap matchups blacklisted (9 matchups)
- Section A minimum raised from 8 to 6 (more lenient for proven matchups)
- Historical rate replaces Section B entirely
"""

import requests, json, time, math, hashlib, os, sys
from datetime import datetime, timedelta
import pytz

WAT = pytz.timezone('Africa/Lagos')
BASE = 'https://www.sportybet.com/api/ng/factsCenter'
SPORT = 'sr:sport:202120001'
BOT_TOKEN = '8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow'
CHAT_ID = '1745848158'
SWEET = (1.38, 1.60)
MIN_SA = 6
TARGET_ODDS = 20000

# ── MATCHUP DATABASE (verified April 1-14, 2026) ──────────────────────

GOLD = {
    'Spain:CEL vs FCB': 1.000,
    'Germany:BVB vs FCA': 1.000,
    'Germany:SCF vs TSG': 1.000,
    'Germany:SVW vs BMU': 1.000,
    'Germany:KOE vs HSV': 1.000,
}

SILVER = {
    'Spain:ATM vs VAL': 0.929, 'Spain:FCB vs RMA': 0.929,
    'Spain:FCB vs GRA': 0.929, 'Spain:SEV vs CEL': 0.929,
    'Spain:ATM vs CEL': 0.929, 'Spain:VAL vs VIL': 0.929,
    'Spain:SEV vs VIL': 0.929, 'Spain:ATM vs GRA': 0.929,
    'Spain:ESP vs ATM': 0.929, 'Spain:BET vs SEV': 0.929,
    'Spain:CEL vs SEV': 0.929, 'Spain:VAL vs ATM': 0.929,
    'Spain:GRA vs SEV': 0.929, 'Spain:VIL vs FCB': 0.929,
    'Spain:RMA vs BET': 0.929, 'Spain:CEL vs BET': 0.929,
    'Spain:BET vs VAL': 0.929, 'Spain:GRA vs CEL': 0.929,
    'Spain:VIL vs CEL': 0.929, 'Spain:ATM vs BET': 0.929,
    'Germany:FCA vs SCF': 0.929, 'Germany:BMU vs WOB': 0.929,
    'Germany:BVB vs KOE': 0.929, 'Germany:TSG vs BVB': 0.929,
    'Germany:FCA vs SVW': 0.929, 'Germany:KOE vs BVB': 0.929,
    'Germany:HSV vs BMU': 0.929, 'Germany:WOB vs SCF': 0.929,
    'Germany:BMU vs BVB': 0.929, 'Germany:TSG vs SVW': 0.929,
    'Germany:BVB vs SCF': 0.929, 'Germany:SCF vs KOE': 0.929,
    'Germany:SVW vs FCA': 0.929, 'Germany:HSV vs SCF': 0.929,
    'Germany:FCA vs KOE': 0.929, 'Germany:WOB vs BVB': 0.929,
    'Germany:SVW vs KOE': 0.929, 'Germany:BMU vs SCF': 0.929,
    'Germany:TSG vs KOE': 0.929, 'Germany:HSV vs BVB': 0.929,
}

TRAPS = {
    'Spain:OVI vs OSA', 'Spain:OSA vs OVI', 'Spain:GRA vs OVI',
    'Spain:SOC vs ESP', 'Spain:MAL vs SOC',
    'Germany:BMG vs SVW', 'Germany:SVW vs BMG',
    'Germany:BMG vs WOB', 'Germany:BMG vs HSV',
}

ALL_GOOD = {**GOLD, **SILVER}

LEAGUES = {
    'Spain':  {'catId': 'sv:category:202120002', 'tId': 'sv:league:2', 'mpr': 10},
    'Germany': {'catId': 'sv:category:202120004', 'tId': 'sv:league:4', 'mpr': 9},
}

# ── TEAM NAME MAPPING ─────────────────────────────────────────────────

ABBREV = {
    'CEL': ['Celta','Celta Vigo'], 'FCB': ['Barcelona','FC Barcelona'],
    'ATM': ['Atletico','Atletico Madrid','Atl. Madrid','Atl Madrid'],
    'VAL': ['Valencia','Valencia CF'], 'RMA': ['Real Madrid','R. Madrid'],
    'GRA': ['Granada','Granada CF'], 'SEV': ['Sevilla','Sevilla FC'],
    'VIL': ['Villarreal','Villarreal CF'], 'ESP': ['Espanyol','RCD Espanyol'],
    'BET': ['Betis','Real Betis'], 'SOC': ['Real Sociedad','R. Sociedad'],
    'MAL': ['Mallorca','RCD Mallorca'], 'OVI': ['Oviedo','Real Oviedo'],
    'OSA': ['Osasuna','CA Osasuna'], 'ATH': ['Athletic','Athletic Bilbao'],
    'GET': ['Getafe','Getafe CF'], 'LPA': ['Las Palmas'],
    'LEG': ['Leganes','CD Leganes'], 'RAY': ['Rayo','Rayo Vallecano'],
    'ALV': ['Alaves','Dep. Alaves'], 'BVB': ['Dortmund','Borussia Dortmund'],
    'FCA': ['Augsburg','FC Augsburg'], 'SCF': ['Freiburg','SC Freiburg'],
    'TSG': ['Hoffenheim','TSG Hoffenheim'], 'SVW': ['Bremen','Werder Bremen','SV Werder'],
    'BMU': ['Bayern','Bayern Munich','FC Bayern'], 'KOE': ['Koln','FC Koln','Cologne'],
    'HSV': ['Hamburg','Hamburger SV'], 'WOB': ['Wolfsburg','VfL Wolfsburg'],
    'BMG': ['Gladbach','Mgladbach','Monchengladbach'],
    'RBL': ['Leipzig','RB Leipzig'], 'UNB': ['Union Berlin'],
    'SGE': ['Frankfurt','Eintracht Frankfurt'], 'VFB': ['Stuttgart','VfB Stuttgart'],
    'BOC': ['Bochum','VfL Bochum'], 'FCH': ['Heidenheim'],
    'DSC': ['Darmstadt','SV Darmstadt'], 'MGD': ['Mainz','Mainz 05'],
}

def name_to_abbrev(name):
    nl = name.lower().strip()
    for abbr, variants in ABBREV.items():
        for v in variants:
            if v.lower() in nl or nl in v.lower():
                return abbr
    for abbr, variants in ABBREV.items():
        for v in variants:
            if nl.split()[0] == v.lower().split()[0]:
                return abbr
    return name.upper()[:3]

def classify(league, home, away):
    h, a = name_to_abbrev(home), name_to_abbrev(away)
    key = f"{league}:{h} vs {a}"
    if key in TRAPS:
        return 'TRAP', h, a, 0
    if key in GOLD:
        return 'GOLD', h, a, GOLD[key]
    if key in SILVER:
        return 'SILVER', h, a, SILVER[key]
    return 'SKIP', h, a, 0

# ── API HELPERS ────────────────────────────────────────────────────────

def fetch_results(league, hours=8):
    cfg = LEAGUES[league]
    now_ms = int(time.time()*1000)
    url = f"{BASE}/eventResultList"
    params = {
        'sportId': SPORT, 'categoryId': cfg['catId'], 'tournamentId': cfg['tId'],
        'pageNum': 1, 'pageSize': 100,
        'startTime': now_ms - hours*3600*1000, 'endTime': now_ms, '_t': now_ms
    }
    try:
        r = requests.get(url, params=params, timeout=30, headers={'User-Agent':'Mozilla/5.0'})
        data = r.json()
        evts = data.get('data',{}).get('tournaments',[])
        records = []
        for t in evts:
            records.extend(t.get('events',[]))
        if not records:
            records = data.get('data',{}).get('records',[])
        return records
    except:
        return []

def fetch_detail(eid):
    try:
        r = requests.get(f"{BASE}/event",
            params={'sportId': SPORT, 'eventId': eid, '_t': int(time.time()*1000)},
            timeout=15, headers={'User-Agent':'Mozilla/5.0'})
        return r.json().get('data')
    except:
        return None

def score_section_a(detail):
    if not detail:
        return 0, {}, None, None
    ou15_odds = ou15_oid = None
    mkts = {}
    for m in detail.get('markets', []):
        mid = str(m.get('id',''))
        for o in m.get('outcomes', []):
            spec = str(o.get('specifier',''))
            desc = o.get('desc','').lower()
            odds_val = float(o.get('odds',0))
            if mid == '18' and '1.5' in spec:
                if 'over' in desc: ou15_odds, ou15_oid = odds_val, o.get('id')
                elif 'under' in desc: mkts['u15'] = odds_val
            elif mid == '29' and 'yes' in desc: mkts['btts'] = odds_val
            elif mid == '68' and '0.5' in spec and 'over' in desc: mkts['fh'] = odds_val
            elif mid == '19' and '0.5' in spec and 'over' in desc: mkts['ho'] = odds_val
            elif mid == '20' and '0.5' in spec and 'over' in desc: mkts['ao'] = odds_val

    sa, sigs = 0, {}
    if ou15_odds and SWEET[0] <= ou15_odds <= SWEET[1]:
        sa += 3; sigs['ou15'] = f'O1.5@{ou15_odds}'
    if mkts.get('u15',0) > 2.0: sa += 2; sigs['u15'] = f'U1.5@{mkts["u15"]}'
    if mkts.get('btts',0) and mkts['btts'] < 2.0: sa += 2; sigs['btts'] = f'BTTS@{mkts["btts"]}'
    if mkts.get('fh',0) and mkts['fh'] < 1.5: sa += 2; sigs['fh'] = f'FH@{mkts["fh"]}'
    if mkts.get('ho',0) and mkts['ho'] < 1.7: sa += 2; sigs['ho'] = f'HO@{mkts["ho"]}'
    if mkts.get('ao',0) and mkts['ao'] < 1.7: sa += 2; sigs['ao'] = f'AO@{mkts["ao"]}'
    if ou15_odds and ou15_odds < 1.50 and mkts.get('btts',9) < 1.7: sa += 1; sigs['x'] = 'EXTREME'
    return min(sa, 14), sigs, ou15_odds, ou15_oid

# ── DISCOVERY ──────────────────────────────────────────────────────────

def discover_upcoming(hours_ahead=4):
    print("Discovering upcoming matches...")
    all_upcoming = []
    for league, cfg in LEAGUES.items():
        results = fetch_results(league, hours=10)
        if not results:
            print(f"  {league}: no recent results")
            continue
        max_eid = 0
        for ev in results:
            eid = ev.get('eventId','')
            if ':' in str(eid):
                try:
                    n = int(str(eid).split(':')[-1])
                    if n > max_eid: max_eid = n
                except: pass
        if not max_eid:
            print(f"  {league}: no eventId pattern")
            continue
        print(f"  {league}: max eid={max_eid}, probing ahead...")
        pid = max_eid + 1
        misses = found = 0
        now = datetime.now(WAT)
        cutoff = now + timedelta(hours=hours_ahead)
        while misses < 40 and found < 200:
            d = fetch_detail(f"sr:match:{pid}")
            if d:
                misses = 0
                cat = d.get('categoryId','')
                if str(cat) == str(cfg['catId']) and d.get('matchStatus','') in ('Not start','not_started',0,'0',None,''):
                    st = d.get('estimateStartTime',0)
                    dt = datetime.fromtimestamp(st/1000, WAT) if st else now
                    if now - timedelta(minutes=5) <= dt <= cutoff:
                        found += 1
                        all_upcoming.append({
                            'league': league, 'eventId': f"sr:match:{pid}",
                            'home': d.get('homeTeamName',''), 'away': d.get('awayTeamName',''),
                            'start': dt, 'detail': d
                        })
            else:
                misses += 1
            pid += 1
            time.sleep(0.03)
        print(f"  {league}: {found} upcoming")
    return all_upcoming

# ── MAIN PIPELINE ──────────────────────────────────────────────────────

def run_mega_audit():
    print("="*60)
    print("MEGA AUDIT v2.0 - MATCHUP-FIRST STRATEGY")
    print(f"Time: {datetime.now(WAT).strftime('%Y-%m-%d %H:%M WAT')}")
    print("="*60)

    upcoming = discover_upcoming(hours_ahead=4)
    if not upcoming:
        print("\nNo upcoming matches found. VFL may be in maintenance.")
        return None

    # Filter through matchup database
    candidates = []
    for m in upcoming:
        tier, h, a, rate = classify(m['league'], m['home'], m['away'])
        if tier in ('GOLD', 'SILVER'):
            sa, sigs, odds, oid = score_section_a(m['detail'])
            if odds and SWEET[0] <= odds <= SWEET[1] and sa >= MIN_SA:
                combined = sa * 0.6 + (rate * 14) * 0.4
                candidates.append({
                    **m, 'tier': tier, 'h': h, 'a': a, 'rate': rate,
                    'sa': sa, 'odds': odds, 'oid': oid, 'combined': combined, 'sigs': sigs
                })
            else:
                r = []
                if not odds: r.append('no odds')
                elif odds < SWEET[0]: r.append(f'odds {odds}<{SWEET[0]}')
                elif odds > SWEET[1]: r.append(f'odds {odds}>{SWEET[1]}')
                if sa < MIN_SA: r.append(f'SA={sa}<{MIN_SA}')
                print(f"  SKIP {tier} {h}v{a}: {','.join(r)}")
        elif tier == 'TRAP':
            print(f"  BLACKLISTED: {h}v{a}")

    candidates.sort(key=lambda x: (0 if x['tier']=='GOLD' else 1, -x['combined']))

    # Select top N for target odds
    if not candidates:
        print("\nNo qualified candidates from proven matchups.")
        return None

    avg = sum(c['odds'] for c in candidates)/len(candidates)
    need = math.ceil(math.log(TARGET_ODDS)/math.log(avg))
    pick_n = min(need, len(candidates))
    selected = candidates[:pick_n]

    total_odds = 1.0
    win_prob = 1.0
    for s in selected:
        total_odds *= s['odds']
        win_prob *= s['rate']

    print(f"\n{'='*60}")
    print(f"SELECTED {len(selected)} PICKS | {total_odds:,.0f}x | Win prob: {win_prob*100:.1f}%")
    print(f"{'='*60}")
    for i, c in enumerate(selected):
        print(f"{i+1}. [{c['tier']}] {c['league']}: {c['h']} vs {c['a']} | {c['odds']} | SA:{c['sa']} | {c['start'].strftime('%H:%M')}")

    # Build booking code
    selections = []
    for s in selected:
        selections.append({
            "sportId": SPORT,
            "eventId": str(s['eventId']),
            "marketId": "18",
            "specifier": "total=1.5",
            "outcomeId": str(s['oid'])
        })

    booking_code = None
    if selections:
        try:
            payload = {"selections": selections}
            r = requests.post('https://www.sportybet.com/api/ng/orders/share',
                json=payload, timeout=20,
                headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/json'})
            bd = r.json()
            booking_code = bd.get('data',{}).get('shareCode') or bd.get('data',{}).get('code')
            print(f"\nBooking Code: {booking_code}")
        except Exception as e:
            print(f"Booking failed: {e}")

    # Send to Telegram
    lines = [f"🏆 MEGA AUDIT v2.0 — {len(selected)} PICKS"]
    lines.append(f"💰 Combined: {total_odds:,.0f}x | Win: {win_prob*100:.1f}%")
    lines.append("")
    for i, c in enumerate(selected):
        icon = "🔴" if c['tier'] == 'GOLD' else "🟡"
        lines.append(f"{icon} {c['league']}: {c['h']} vs {c['a']} — O1.5 @{c['odds']} (SA:{c['sa']}, {c['rate']*100:.0f}%)")
    if booking_code:
        lines.append(f"\n📋 Code: {booking_code}")
    lines.append(f"\n⏰ {datetime.now(WAT).strftime('%H:%M WAT %Y-%m-%d')}")

    msg = "\n".join(lines)
    try:
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json={'chat_id': CHAT_ID, 'text': msg})
    except:
        pass

    return {
        'picks': len(selected),
        'total_odds': total_odds,
        'win_prob': win_prob,
        'booking_code': booking_code,
        'selected': [{
            'league': s['league'], 'home': s['home'], 'away': s['away'],
            'h': s['h'], 'a': s['a'], 'tier': s['tier'], 'rate': s['rate'],
            'sa': s['sa'], 'odds': s['odds'], 'eventId': s['eventId'],
            'start': s['start'].isoformat()
        } for s in selected]
    }

if __name__ == '__main__':
    result = run_mega_audit()
    if result:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("No picks generated. Will retry when matches are available.")
