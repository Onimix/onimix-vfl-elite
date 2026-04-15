"""
VFL GOLD/SILVER SLIP PICKER v1.0
================================
Picks ONLY 3-5 leg accumulators from verified Gold (100%) and Silver (92.9%) matchups.
Strict odds range: 1.38-1.60 per leg.
Uses eventId probing + prematch JSON analysis.

Gold matchups (100% O1.5 in 14 days):
  Spain: CEL-FCB, GET-GIR, GIR-RMA, MAL-RMA, SEV-BIL
  Germany: BMG-WOB, DOR-BMG, HDH-BMG, KOE-WOB, SCF-HDH

Silver matchups (92.9% O1.5 in 14 days - 40 total):
  Spain: ALA-GIR, ALA-RMA, ATM-ELC, ATM-FCB, ATM-GIR, ATM-RSO, BIL-ESP,
         BIL-GIR, BIL-OVI, CEL-ELC, CEL-GIR, CEL-RMA, ELC-GIR, ESP-FCB,
         FCB-OVI, GET-RMA, GIR-SEV, MAL-GIR, OVI-GIR, RAY-GIR, RBB-FCB,
         RMA-OVI, RSO-GIR, SEV-GIR, VCF-GIR, VIL-FCB
  Germany: BMG-SGE, BMG-STP, DOR-KOE, DOR-SGE, DOR-WOB, HDH-KOE,
           HDH-SCF, HDH-SGE, HDH-STP, KOE-SCF, KOE-SGE, SCF-SGE,
           WOB-SGE, WOB-STP
"""
import json, time, urllib.request, ssl, hashlib
from datetime import datetime, timezone, timedelta

WAT = timezone(timedelta(hours=1))
TG_TOKEN = "8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow"
TG_CHAT = "1745848158"
SWEET = (1.38, 1.60)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}

# === MATCHUP DATABASE ===
GOLD = {
    'spain': [('CEL','FCB'),('GET','GIR'),('GIR','RMA'),('MAL','RMA'),('SEV','BIL')],
    'germany': [('BMG','WOB'),('DOR','BMG'),('HDH','BMG'),('KOE','WOB'),('SCF','HDH')]
}
SILVER = {
    'spain': [
        ('ALA','GIR'),('ALA','RMA'),('ATM','ELC'),('ATM','FCB'),('ATM','GIR'),
        ('ATM','RSO'),('BIL','ESP'),('BIL','GIR'),('BIL','OVI'),('CEL','ELC'),
        ('CEL','GIR'),('CEL','RMA'),('ELC','GIR'),('ESP','FCB'),('FCB','OVI'),
        ('GET','RMA'),('GIR','SEV'),('MAL','GIR'),('OVI','GIR'),('RAY','GIR'),
        ('RBB','FCB'),('RMA','OVI'),('RSO','GIR'),('SEV','GIR'),('VCF','GIR'),
        ('VIL','FCB')
    ],
    'germany': [
        ('BMG','SGE'),('BMG','STP'),('DOR','KOE'),('DOR','SGE'),('DOR','WOB'),
        ('HDH','KOE'),('HDH','SCF'),('HDH','SGE'),('HDH','STP'),('KOE','SCF'),
        ('KOE','SGE'),('SCF','SGE'),('WOB','SGE'),('WOB','STP')
    ]
}
TRAP = {
    ('ALA','VIL'),('CEL','VIL'),('ESP','RMA'),('RBB','ALA'),('VIL','ELC'),
    ('BMG','UNI'),('FCA','WOB'),('SGE','BMG'),('UNI','WOB')
}

LEAGUES = {
    'spain': {'catId':'sv:category:202120002','tId':'sv:league:2','catName':'Spain'},
    'germany': {'catId':'sv:category:202120004','tId':'sv:league:4','catName':'Germany'}
}

BASE = 'https://www.sportybet.com/api/ng/factsCenter'

def api(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode())
    except:
        return None

def tg_send(text, chat_id):
    try:
        data = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode()).get('ok', False)
    except Exception as e:
        print(f"  TG error: {e}")
        return False

def get_recent_results(league, hours=6):
    """Fetch recent results for a league."""
    cfg = LEAGUES[league]
    now = int(time.time() * 1000)
    start = now - (hours * 3600000)
    results = []
    for pn in range(1, 5):
        d = api(f"{BASE}/eventResultList?sportId=sr:sport:202120001"
                f"&categoryId={cfg['catId']}&tournamentId={cfg['tId']}"
                f"&pageNum={pn}&pageSize=100&startTime={start}&endTime={now}")
        if not d or d.get('bizCode') != 10000:
            break
        tours = d.get('data', {})
        if isinstance(tours, dict):
            tours = tours.get('tournaments', [])
        for t in tours:
            for ev in t.get('events', []):
                results.append(ev)
        if len(results) >= int(d.get('data', {}).get('totalNum', 0) if isinstance(d.get('data'), dict) else 0):
            break
    return results

def discover_upcoming(league, max_probe=80):
    """Discover upcoming events by probing eventIds ahead of last completed."""
    cfg = LEAGUES[league]
    results = get_recent_results(league, hours=4)
    if not results:
        return []
    
    # Get max eventId from results
    max_eid = 0
    for ev in results:
        eid = ev.get('eventId', '')
        try:
            num = int(str(eid).replace('sr:match:', ''))
            if num > max_eid:
                max_eid = num
        except:
            pass
    
    if max_eid == 0:
        return []
    
    upcoming = []
    misses = 0
    probe = max_eid + 1
    now_ms = int(time.time() * 1000)
    
    while misses < 15 and len(upcoming) < max_probe:
        eid = f"sr:match:{probe}"
        d = api(f"{BASE}/event?eventId={eid}&productId=3", timeout=8)
        probe += 1
        if not d or d.get('bizCode') != 10000:
            misses += 1
            continue
        
        ev = d.get('data', {})
        if not ev:
            misses += 1
            continue
        
        ms = ev.get('matchStatus', '')
        if ms not in ('Not start', 'not_started', '', None):
            misses = 0
            continue
        
        est = ev.get('estimateStartTime', 0)
        if est <= now_ms:
            misses = 0
            continue
        
        cat = ev.get('sport', {}).get('category', {}).get('name', '')
        if cat.lower() != cfg['catName'].lower():
            misses = 0
            continue
        
        upcoming.append(ev)
        misses = 0
        time.sleep(0.3)
    
    return upcoming

def analyze_prematch(event):
    """Section A: 6-market prematch JSON decoder. Returns score 0-14."""
    mkts = {}
    for m in event.get('markets', []):
        if isinstance(m, dict):
            mkts[(str(m.get('id', '')), m.get('specifier', ''))] = m
    
    score = 0
    odds = 0.0
    
    # Market 18 (O/U 1.5)
    for spec in ['total=1.5', '1.5']:
        m = mkts.get(('18', spec))
        if m:
            for o in m.get('outcomes', []):
                desc = o.get('desc', '').lower()
                if 'over' in desc:
                    p = float(o.get('probability', '0') or '0')
                    odds = float(o.get('odds', '0') or '0')
                    if p >= 0.72: score += 4
                    elif p >= 0.65: score += 3
                    elif p >= 0.55: score += 2
                    elif p >= 0.45: score += 1
            break
    
    # Market 18 (O/U 2.5)
    for spec in ['total=2.5', '2.5']:
        m = mkts.get(('18', spec))
        if m:
            for o in m.get('outcomes', []):
                if 'over' in o.get('desc', '').lower():
                    p = float(o.get('probability', '0') or '0')
                    if p >= 0.55: score += 3
                    elif p >= 0.45: score += 2
                    elif p >= 0.35: score += 1
            break
    
    # Market 19/20 (Home/Away totals)
    for mid in ['19', '20']:
        for spec in ['total=0.5', '0.5', '']:
            m = mkts.get((mid, spec))
            if m:
                for o in m.get('outcomes', []):
                    if 'over' in o.get('desc', '').lower():
                        p = float(o.get('probability', '0') or '0')
                        if p >= 0.70: score += 2
                        elif p >= 0.55: score += 1
                break
    
    # Market 29 (BTTS)
    m = mkts.get(('29', ''))
    if m:
        for o in m.get('outcomes', []):
            if 'yes' in o.get('desc', '').lower():
                p = float(o.get('probability', '0') or '0')
                if p >= 0.50: score += 2
                elif p >= 0.35: score += 1
    
    return score, odds

def classify_matchup(home, away):
    """Classify a matchup as GOLD, SILVER, or NONE."""
    pair = (home, away)
    if pair in TRAP:
        return 'TRAP', 0
    
    for lg in GOLD:
        if pair in GOLD[lg]:
            return 'GOLD', 100.0
    for lg in SILVER:
        if pair in SILVER[lg]:
            return 'SILVER', 92.9
    return 'NONE', 0

def book_slip(picks):
    """Generate SportyBet booking code for the slip."""
    outcomes = []
    for p in picks:
        eid = p.get('eventId', '')
        oid = p.get('outcomeId', '')
        if eid and oid:
            outcomes.append({
                "eventId": eid,
                "marketId": "18",
                "specifier": "total=1.5",
                "outcomeId": oid,
            })
    if not outcomes:
        return None
    
    payload = json.dumps({"selections": outcomes}).encode()
    try:
        req = urllib.request.Request(
            f"{BASE.replace('/factsCenter','')}/orders/share",
            data=payload,
            headers={**HEADERS, "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
            if d.get('bizCode') == 10000:
                return d.get('data', {}).get('shareCode')
    except:
        pass
    return None

def run():
    now = datetime.now(WAT)
    print("=" * 60)
    print("VFL GOLD/SILVER SLIP PICKER v1.0")
    print(f"Time: {now.strftime('%Y-%m-%d %H:%M WAT')}")
    print("=" * 60)
    
    # Discover upcoming matches
    all_candidates = []
    for lg in LEAGUES:
        print(f"\nDiscovering {lg.title()} upcoming...")
        upcoming = discover_upcoming(lg, max_probe=60)
        print(f"  Found {len(upcoming)} upcoming")
        
        for ev in upcoming:
            home = ev.get('homeTeamName', '')
            away = ev.get('awayTeamName', '')
            tier, hist_rate = classify_matchup(home, away)
            
            if tier == 'NONE' or tier == 'TRAP':
                continue
            
            sa_score, ou15_odds = analyze_prematch(ev)
            
            # STRICT: odds must be 1.38-1.60
            if ou15_odds < SWEET[0] or ou15_odds > SWEET[1]:
                print(f"  SKIP {home}v{away} — odds {ou15_odds:.2f} outside {SWEET[0]}-{SWEET[1]}")
                continue
            
            # STRICT: Section A must be >= 6/14
            if sa_score < 6:
                print(f"  SKIP {home}v{away} — SA={sa_score}/14 too low")
                continue
            
            # Get outcomeId for Over 1.5
            oid = ''
            for m in ev.get('markets', []):
                if str(m.get('id')) == '18' and 'total=1.5' in m.get('specifier', ''):
                    for o in m.get('outcomes', []):
                        if 'over' in o.get('desc', '').lower():
                            oid = str(o.get('id', ''))
            
            est = ev.get('estimateStartTime', 0)
            ko = datetime.fromtimestamp(est/1000, WAT).strftime('%H:%M') if est else '??:??'
            
            candidate = {
                'home': home,
                'away': away,
                'league': lg,
                'tier': tier,
                'hist_rate': hist_rate,
                'sa_score': sa_score,
                'odds': ou15_odds,
                'eventId': ev.get('eventId', ''),
                'gameId': ev.get('gameId', ''),
                'outcomeId': oid,
                'kickoff': ko,
                'est': est,
                'combined': sa_score + (14 if tier == 'GOLD' else 13),
            }
            all_candidates.append(candidate)
            flag = '🇪🇸' if lg == 'spain' else '🇩🇪'
            print(f"  ✅ {flag} {home}v{away} [{tier}] SA={sa_score} @{ou15_odds:.2f} KO={ko}")
    
    if not all_candidates:
        print("\n❌ No qualified Gold/Silver matchups found right now.")
        print("   VFL may be in maintenance or no ELITE fixtures in current rounds.")
        tg_send("🔍 VFL Slip Picker: No qualified Gold/Silver matchups right now. Will retry next scan.", TG_CHAT)
        return
    
    # Sort: GOLD first, then by combined score
    all_candidates.sort(key=lambda x: (0 if x['tier']=='GOLD' else 1, -x['combined'], -x['odds']))
    
    print(f"\n📊 Total qualified candidates: {len(all_candidates)}")
    
    # Build slips: 3-5 legs each, prioritizing Gold
    slips = []
    used = set()
    
    # SLIP 1: Best 3-leg (safest)
    slip1 = []
    for c in all_candidates:
        key = f"{c['home']}{c['away']}"
        if key not in used and len(slip1) < 3:
            slip1.append(c)
            used.add(key)
    if len(slip1) >= 3:
        odds1 = 1.0
        for s in slip1: odds1 *= s['odds']
        slips.append({'name': 'SAFE 3-LEG', 'picks': slip1, 'odds': odds1, 'legs': 3})
    
    # SLIP 2: Best 4-leg
    slip2 = []
    used2 = set()
    for c in all_candidates:
        key = f"{c['home']}{c['away']}"
        if key not in used2 and len(slip2) < 4:
            slip2.append(c)
            used2.add(key)
    if len(slip2) >= 4:
        odds2 = 1.0
        for s in slip2: odds2 *= s['odds']
        slips.append({'name': 'STANDARD 4-LEG', 'picks': slip2, 'odds': odds2, 'legs': 4})
    
    # SLIP 3: Best 5-leg (higher risk/reward)
    slip3 = []
    used3 = set()
    for c in all_candidates:
        key = f"{c['home']}{c['away']}"
        if key not in used3 and len(slip3) < 5:
            slip3.append(c)
            used3.add(key)
    if len(slip3) >= 5:
        odds3 = 1.0
        for s in slip3: odds3 *= s['odds']
        slips.append({'name': 'POWER 5-LEG', 'picks': slip3, 'odds': odds3, 'legs': 5})
    
    if not slips:
        print("❌ Not enough candidates for even a 3-leg slip")
        tg_send("🔍 VFL Slip Picker: Only found {len(all_candidates)} candidates — need at least 3 for a slip. Will retry.", TG_CHAT)
        return
    
    # Book codes
    for slip in slips:
        code = book_slip(slip['picks'])
        slip['code'] = code
    
    # Build Telegram message
    msg = f"🎯 VFL GOLD/SILVER SLIPS\n"
    msg += f"📅 {now.strftime('%Y-%m-%d %H:%M WAT')}\n"
    msg += f"{'='*35}\n\n"
    
    for slip in slips:
        msg += f"📋 {slip['name']} ({slip['odds']:.2f}x)\n"
        if slip.get('code'):
            msg += f"🎫 Code: {slip['code']}\n"
        msg += f"{'-'*30}\n"
        for i, p in enumerate(slip['picks'], 1):
            flag = '🇪🇸' if p['league'] == 'spain' else '🇩🇪'
            tier_icon = '🥇' if p['tier'] == 'GOLD' else '🥈'
            msg += f"{i}. {flag}{tier_icon} {p['home']} v {p['away']}\n"
            msg += f"   O1.5 @{p['odds']:.2f} | SA={p['sa_score']}/14 | {p['tier']} ({p['hist_rate']}%)\n"
            msg += f"   KO: {p['kickoff']}\n"
        msg += f"\n"
    
    msg += f"{'='*35}\n"
    msg += f"Gold = 100% hit (14/14 days)\n"
    msg += f"Silver = 92.9% hit (13/14 days)\n"
    msg += f"Odds range: {SWEET[0]}-{SWEET[1]} ONLY\n"
    msg += f"⚠️ Even 92.9% loses ~1 in 14\n"
    msg += f"ONIMIX TECH 🤖"
    
    # Send
    sent = tg_send(msg, TG_CHAT)
    print(f"\n{'='*60}")
    print(f"Telegram: {'✅ Sent' if sent else '❌ Failed'}")
    for slip in slips:
        print(f"  {slip['name']}: {slip['legs']} legs @ {slip['odds']:.2f}x | Code: {slip.get('code', 'N/A')}")
    print(f"{'='*60}")
    
    # Save picks for tracking
    save_data = {
        'timestamp': now.isoformat(),
        'slips': []
    }
    for slip in slips:
        save_data['slips'].append({
            'name': slip['name'],
            'odds': slip['odds'],
            'code': slip.get('code'),
            'picks': [{
                'home': p['home'], 'away': p['away'], 'league': p['league'],
                'tier': p['tier'], 'hist_rate': p['hist_rate'],
                'sa_score': p['sa_score'], 'odds': p['odds'],
                'eventId': p['eventId'], 'gameId': p['gameId'],
                'kickoff': p['kickoff'], 'status': 'pending'
            } for p in slip['picks']]
        })
    
    with open('/tmp/slip_picks.json', 'w') as f:
        json.dump(save_data, f, indent=2)
    print(f"\nPicks saved to /tmp/slip_picks.json")
    
    # Push to GitHub
    try:
        fname = f"data/slips_{now.strftime('%Y%m%d_%H%M')}.json"
        content = json.dumps(save_data, indent=2)
        import base64
        b64 = base64.b64encode(content.encode()).decode()
        gh_token = ''
        try:
            import subprocess
            r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
            gh_token = r.stdout.strip()
        except:
            pass
        if gh_token:
            payload = json.dumps({
                "message": f"Slip picks {now.strftime('%Y-%m-%d %H:%M')}",
                "content": b64
            }).encode()
            req = urllib.request.Request(
                f"https://api.github.com/repos/Onimix/onimix-vfl-elite/contents/{fname}",
                data=payload,
                headers={"Authorization": f"token {gh_token}", "Content-Type": "application/json"},
                method="PUT"
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                if r.status in (200, 201):
                    print(f"✅ Saved to GitHub: {fname}")
    except Exception as e:
        print(f"  GitHub save: {e}")
    
    return save_data

if __name__ == "__main__":
    run()
