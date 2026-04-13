"""
VFL Quick Scanner v3.4 — ONIMIX TECH
Uses NEW SportyBet API structure (sv: categories, gameId-based events)
Section A: Pre-match JSON Probability Decoder (6 markets)
Section B: Disabled temporarily (results API changed)
"""

import requests, json, time, hashlib, math
import concurrent.futures
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.sportybet.com/ng/sport/vFootball'
}

TG_TOKEN = '8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow'
TG_API = 'https://api.telegram.org/bot' + TG_TOKEN
TG_CHAT = '1745848158'

SPORT = 'sr:sport:202120001'
SWEET = (1.38, 1.60)

LEAGUES = {
    'spain': {
        'name': 'Spain VFL',
        'catId': 'sv:category:202120002',
        'tourId': 'sv:league:2',
        'catName': 'Spain',
    },
    'germany': {
        'name': 'Germany VFL',
        'catId': 'sv:category:202120004',
        'tourId': 'sv:league:4',
        'catName': 'Germany',
    },
}

# ── DISCOVERY (NEW API) ──
def discover_all():
    """Get ALL upcoming VFL events from commonThumbnailEvents."""
    r = requests.get('https://www.sportybet.com/api/ng/factsCenter/commonThumbnailEvents', params={
        'sportId': SPORT, 'productId': 3,
    }, headers=HEADERS, timeout=15)
    d = r.json()
    if d.get('bizCode') != 10000:
        print("  ⚠️ Discovery failed: %s" % d.get('message',''))
        return {}
    
    by_league = defaultdict(list)
    for tour in d.get('data', []):
        for ev in tour.get('events', []):
            cat_name = ev.get('sport',{}).get('category',{}).get('name','')
            by_league[cat_name].append(ev)
    return by_league

def event_detail(game_id):
    """Fetch full event detail using numeric gameId."""
    try:
        r = requests.get('https://www.sportybet.com/api/ng/factsCenter/event', params={
            'gameId': str(game_id), 'productId': 3
        }, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        if d.get('bizCode') != 10000:
            return None
        ev = d.get('data')
        if not ev:
            return None
        # Check matchStatus
        ms = ev.get('matchStatus')
        if ms and ms not in ('Not start', 'not_started', 0, '0', None):
            return None
        # Check status
        if ev.get('status') not in (0, '0'):
            return None
        return ev
    except:
        return None

def sum_score(desc):
    """Parse correct score description like '2:1' to total goals."""
    try:
        parts = desc.replace(' ','').split(':')
        return int(parts[0]) + int(parts[1])
    except:
        return 0

# ── SECTION A ──
def sec_a(event):
    """Section A: decode 6 markets in order: CS(45) → HG(23) → AG(24) → OU(18) → FH(68) → GG(29)."""
    mkts = event.get('markets', [])
    cs, hg, ag, ou, fhou, gg = None, None, None, {}, {}, None
    
    for m in mkts:
        mid = str(m.get('id', ''))
        spec = m.get('specifier', '')
        parsed = {}
        for o in m.get('outcomes', []):
            try:
                if o.get('isActive') not in (1, '1', True):
                    continue
                parsed[o['desc']] = {
                    'odds': float(o.get('odds', 0)),
                    'prob': float(o.get('probability', 0)),
                    'id': o.get('id', ''),
                    'act': o.get('isActive', 0),
                }
            except:
                pass
        if mid == '45': cs = parsed
        elif mid == '23': hg = parsed
        elif mid == '24': ag = parsed
        elif mid == '18':
            key = spec.replace('total=', '') if 'total=' in spec else spec
            ou[key] = parsed
        elif mid == '68':
            key = spec.replace('total=', '') if 'total=' in spec else spec
            fhou[key] = parsed
        elif mid == '29': gg = parsed
    
    sc, mx, sig = 0, 0, {}
    
    # Market 45: Correct Score
    if cs:
        mx += 3
        o15p = sum(v['prob'] for d, v in cs.items() if sum_score(d) >= 2)
        fp11 = next((v['prob'] for d, v in cs.items() if d.replace(' ', '') == '1:1'), 0)
        sig['cs_o15'] = round(o15p, 4)
        sig['fp11'] = round(fp11, 4)
        if o15p > 0.55: sc += 3
        elif o15p > 0.45: sc += 2
        elif o15p > 0.35: sc += 1
    
    # Market 23: Home Goals
    if hg:
        mx += 2
        h1p = sum(v['prob'] for d, v in hg.items() if d not in ('0',))
        sig['hg_1plus'] = round(h1p, 4)
        if h1p > 0.70: sc += 2
        elif h1p > 0.55: sc += 1
    
    # Market 24: Away Goals
    if ag:
        mx += 2
        a1p = sum(v['prob'] for d, v in ag.items() if d not in ('0',))
        sig['ag_1plus'] = round(a1p, 4)
        if a1p > 0.70: sc += 2
        elif a1p > 0.55: sc += 1
    
    # Market 18: Over/Under totals
    ou15 = ou.get('1.5', {})
    ou15_over = ou15.get('Over 1.5', {})
    ou15_odds = ou15_over.get('odds', 0)
    ou15_prob = ou15_over.get('prob', 0)
    ou15_oid = ou15_over.get('id', '')
    
    if ou15:
        mx += 3
        sig['ou15_prob'] = round(ou15_prob, 4)
        sig['ou15_odds'] = ou15_odds
        if ou15_prob > 0.70: sc += 3
        elif ou15_prob > 0.55: sc += 2
        elif ou15_prob > 0.40: sc += 1
    
    # Market 68: 1st Half O/U
    fh05 = fhou.get('0.5', {})
    fh05_over = fh05.get('Over 0.5', {})
    if fh05:
        mx += 2
        fhp = fh05_over.get('prob', 0)
        sig['fh05_prob'] = round(fhp, 4)
        if fhp > 0.75: sc += 2
        elif fhp > 0.60: sc += 1
    
    # Market 29: GG/NG
    if gg:
        mx += 2
        ggp = gg.get('Yes', {}).get('prob', 0)
        sig['gg_prob'] = round(ggp, 4)
        if ggp > 0.55: sc += 2
        elif ggp > 0.40: sc += 1
    
    pct = round(sc / mx * 100) if mx > 0 else 0
    sweet = SWEET[0] <= ou15_odds <= SWEET[1] if ou15_odds > 0 else False
    fp11 = sig.get('fp11', 0) > 0.10
    
    return {
        'sc': sc, 'mx': mx, 'pct': pct,
        'ou15_odds': ou15_odds, 'ou15_prob': ou15_prob, 'ou15_oid': ou15_oid,
        'sweet': sweet, 'fp11': fp11, 'sig': sig,
        'gid': event.get('sport', {}).get('category', {}).get('tournament', {}).get('id', ''),
    }

# ── ANALYSIS ──
def analyze(event):
    """Combine Section A analysis. Section B disabled pending results API update."""
    a = sec_a(event)
    hn = event.get('homeTeamName', '?')
    an = event.get('awayTeamName', '?')
    
    # Combined: Section A only (max 14 from A)
    cpct = a['pct']
    
    # Verdict thresholds (adjusted for A-only: use A score directly)
    if cpct >= 70:
        verdict = 'LOCK'
    elif cpct >= 50:
        verdict = 'PICK'
    elif cpct >= 35:
        verdict = 'CONSIDER'
    else:
        verdict = 'SKIP'
    
    # HARD 1.38 FILTER — below is a trap
    if a['ou15_odds'] > 0 and a['ou15_odds'] < SWEET[0]:
        verdict = 'SKIP'
    
    # No odds = can't book
    if a['ou15_odds'] <= 0:
        verdict = 'SKIP'
    
    return {
        'match': '%s v %s' % (hn, an),
        'eid': event.get('eventId', ''),
        'gid': event.get('gameId', ''),
        'start': event.get('estimateStartTime', 0),
        'a': a,
        'cpct': cpct,
        'verdict': verdict,
        'ou15_odds': a['ou15_odds'],
        'ou15_oid': a['ou15_oid'],
        'sweet': a['sweet'],
        'fp11': a['fp11'],
    }

# ── BOOKING CODE ──
def gen_booking(picks):
    if not picks:
        return None
    outcomes = []
    for p in picks:
        oid = p.get('ou15_oid')
        eid = p.get('eid')
        if not oid or not eid:
            continue
        outcomes.append({
            "eventId": eid,
            "marketId": "18",
            "specifier": "total=1.5",
            "outcomeId": str(oid),
        })
    if not outcomes:
        return None
    
    payload = {"selections": outcomes}
    print("    📦 Booking: %d selections" % len(outcomes))
    try:
        r = requests.post(
            'https://www.sportybet.com/api/ng/orders/share',
            json=payload, headers={**HEADERS, 'Content-Type': 'application/json'}, timeout=15
        )
        d = r.json()
        if d.get('bizCode') == 10000:
            code = d.get('data', {}).get('shareCode')
            if code:
                return code
        print("    ⚠️ Booking response: %s" % json.dumps(d)[:200])
    except Exception as e:
        print("    ⚠️ Booking failed: %s" % e)
    return None

# ── TELEGRAM ──
def tg_send(text, chat_id=None):
    cid = chat_id or TG_CHAT
    try:
        r = requests.post('%s/sendMessage' % TG_API, json={
            'chat_id': cid,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
        }, timeout=15)
        d = r.json()
        if d.get('ok'):
            return True
        print("  ⚠️ TG error: %s" % d.get('description', ''))
    except Exception as e:
        print("  ⚠️ TG send failed: %s" % e)
    return False

def format_section(picks, icon, label, code, total_odds):
    if not picks:
        return []
    lines = ["%s <b>%s (%d selections | %.0fx odds)</b>" % (icon, label, len(picks), total_odds), ""]
    by_time = defaultdict(list)
    for p in picks:
        by_time[p.get('start', 0)].append(p)
    for t in sorted(by_time.keys()):
        dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
        lines.append("⏰ <b>%s UTC</b>" % dt.strftime('%H:%M'))
        for p in by_time[t]:
            sw = ' 💎' if p['sweet'] else ''
            fp = ' 🔍' if p['fp11'] else ''
            lines.append("  %s %s — O1.5 @%.2f%s%s" % (icon, p['match'], p['ou15_odds'], sw, fp))
            lines.append("      A:%d%% C:%d%%" % (p['a']['pct'], p['cpct']))
        lines.append("")
    lines.append("💰 <b>ODDS: %.0fx</b>" % total_odds)
    if code:
        lines.append("📋 <b>CODE: %s</b>" % code)
        lines.append("🔗 sportybet.com/ng/share/%s" % code)
    else:
        lines.append("📋 Code: manual entry required")
    return lines

# ── MAIN SCANNER ──
def run():
    scan_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print("=" * 60)
    print("🏆 VFL ENGINE v3.4 — ONIMIX TECH")
    print("📅 %s" % scan_time)
    print("=" * 60)
    
    # Discover all upcoming events
    print("\n🔍 Discovering all upcoming VFL events...")
    all_upcoming = discover_all()
    
    all_results = []
    
    for lk, cfg in LEAGUES.items():
        cat_name = cfg['catName']
        events = all_upcoming.get(cat_name, [])
        print("\n📋 %s: %d upcoming matches" % (cfg['name'], len(events)))
        
        if not events:
            continue
        
        # Show rounds
        rounds = sorted(set(e['estimateStartTime'] for e in events))
        for t in rounds[:5]:
            dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
            n = sum(1 for e in events if e['estimateStartTime'] == t)
            print("  ⏰ %s UTC (%d matches)" % (dt.strftime('%H:%M'), n))
        if len(rounds) > 5:
            print("  ... +%d more rounds" % (len(rounds) - 5))
        
        # Fetch full event details using gameId
        game_ids = [e.get('gameId') for e in events if e.get('gameId')]
        print("  📥 Fetching %d event details..." % len(game_ids))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
            details = list(ex.map(event_detail, game_ids))
        
        valid = [d for d in details if d is not None]
        print("  ✅ Got %d valid events" % len(valid))
        
        # Analyze each
        for ev in valid:
            r = analyze(ev)
            emoji = {'LOCK': '🔒', 'PICK': '✅', 'CONSIDER': '🤔', 'SKIP': '❌'}[r['verdict']]
            sw = '💎' if r['sweet'] else ''
            fp = '🔍' if r['fp11'] else ''
            print("  %s %s: %s A:%d%% O1.5@%.2f %s%s" % (
                emoji, r['match'], r['verdict'], r['a']['pct'], r['ou15_odds'], sw, fp
            ))
            all_results.append(r)
    
    # Summary
    locks = [r for r in all_results if r['verdict'] == 'LOCK']
    picks = [r for r in all_results if r['verdict'] == 'PICK']
    cons = [r for r in all_results if r['verdict'] == 'CONSIDER']
    skips = [r for r in all_results if r['verdict'] == 'SKIP']
    
    print("\n" + "=" * 60)
    print("📊 🔒%d ✅%d 🤔%d ❌%d" % (len(locks), len(picks), len(cons), len(skips)))
    
    bookable = locks + picks
    if not bookable:
        print("⚠️ No bookable picks found")
        tg_send("⚠️ VFL Scan %s\nNo bookable picks across %d matches.\nNext scan coming." % (scan_time, len(all_results)), TG_CHAT)
        return
    
    # Sort by confidence
    locks.sort(key=lambda x: (x['sweet'], x['cpct']), reverse=True)
    picks.sort(key=lambda x: (x['sweet'], x['cpct']), reverse=True)
    
    # Calculate odds
    lock_odds = 1.0
    for p in locks:
        lock_odds *= p['ou15_odds']
    pick_odds = 1.0
    for p in picks:
        pick_odds *= p['ou15_odds']
    
    print("\n🎰 LOCK ACCA: %d @ %.1fx" % (len(locks), lock_odds))
    print("🎰 PICK ACCA: %d @ %.1fx" % (len(picks), pick_odds))
    
    # Generate booking codes
    lock_code = None
    pick_code = None
    
    if locks:
        print("\n📋 Generating LOCK booking code...")
        lock_code = gen_booking(locks)
        if lock_code:
            print("  ✅ LOCK Code: %s" % lock_code)
    
    if picks:
        print("📋 Generating PICK booking code...")
        pick_code = gen_booking(picks)
        if pick_code:
            print("  ✅ PICK Code: %s" % pick_code)
    
    # Build Telegram message
    total_sel = len(locks) + len(picks)
    lines = [
        "🏆 <b>VFL MEGA — ONIMIX ELITE</b>",
        "📅 %s" % scan_time,
        "🎯 %d total selections from %d analyzed" % (total_sel, len(all_results)),
        "🔒 %d LOCKs | ✅ %d PICKs" % (len(locks), len(picks)),
        "",
    ]
    
    if locks:
        lines.extend(format_section(locks, '🔒', 'LOCK ACCUMULATOR', lock_code, lock_odds))
        lines.append("")
    
    if picks:
        lines.extend(format_section(picks, '✅', 'PICK ACCUMULATOR', pick_code, pick_odds))
        lines.append("")
    
    lines.extend([
        "⚡ <i>Engine v3.4 | Section A | New API</i>",
        "🤖 <i>ONIMIX TECH — Automated VFL Intelligence</i>",
    ])
    
    msg = '\n'.join(lines)
    
    # Send to Telegram (split if too long)
    if len(msg) > 4000:
        # Split into lock + pick messages
        if locks:
            lock_msg = '\n'.join([
                "🏆 <b>VFL MEGA — ONIMIX ELITE (1/2)</b>",
                "📅 %s" % scan_time,
                "",
            ] + format_section(locks, '🔒', 'LOCK ACCUMULATOR', lock_code, lock_odds))
            ok1 = tg_send(lock_msg, TG_CHAT)
            print("  📤 LOCK msg: %s" % ('sent' if ok1 else 'FAILED'))
        
        if picks:
            pick_msg = '\n'.join([
                "🏆 <b>VFL MEGA — ONIMIX ELITE (2/2)</b>",
                "📅 %s" % scan_time,
                "",
            ] + format_section(picks, '✅', 'PICK ACCUMULATOR', pick_code, pick_odds) + [
                "",
                "⚡ <i>Engine v3.4 | Section A | New API</i>",
                "🤖 <i>ONIMIX TECH — Automated VFL Intelligence</i>",
            ])
            ok2 = tg_send(pick_msg, TG_CHAT)
            print("  📤 PICK msg: %s" % ('sent' if ok2 else 'FAILED'))
    else:
        ok = tg_send(msg, TG_CHAT)
        print("\n✅ Telegram: %s" % ('sent!' if ok else 'FAILED'))
    
    print("\n🏁 Scan complete!")

if __name__ == '__main__':
    run()
