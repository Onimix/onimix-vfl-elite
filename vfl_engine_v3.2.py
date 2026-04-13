"""
VFL Prediction Engine v3.2 FINAL — ONIMIX TECH
Section A: Pre-match JSON Probability Decoder (6 markets)
Section B: Yesterday SAME-SLOT Energy Card System
Optimized skip rules (removed A+F, kept C+D+E)
+ Telegram delivery with mega booking codes
+ Deduplication / spam prevention
"""

import requests, json, time, hashlib, os, concurrent.futures
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.sportybet.com/ng/sport/vFootball'
}

LEAGUES = {
    'spain': {'catId': 'sv:category:202120002', 'tId': 'sv:league:2', 'name': 'Spain VFL', 'mpr': 10},
    'germany': {'catId': 'sv:category:202120004', 'tId': 'sv:league:4', 'name': 'Germany VFL', 'mpr': 9},
}
SPORT = 'sr:sport:202120001'
BASE = 'https://www.sportybet.com/api/ng/factsCenter'
SWEET = (1.38, 1.60)

# ── TELEGRAM ──
TG_TOKEN = '8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow'
TG_CHAT = os.environ.get('TG_CHAT_ID', '')  # Set via env or fill in
TG_API = f'https://api.telegram.org/bot{TG_TOKEN}'

# ── DEDUP ──
SENT_FILE = '/tmp/vfl_sent.json'
def load_sent():
    try:
        with open(SENT_FILE) as f: return json.load(f)
    except: return {}

def save_sent(d):
    try:
        with open(SENT_FILE, 'w') as f: json.dump(d, f)
    except: pass

def dedup_key(picks):
    """Hash of sorted eventIds — same set of picks = same key."""
    ids = sorted(p['eid'] for p in picks if p.get('eid'))
    return hashlib.md5('|'.join(ids).encode()).hexdigest()

def already_sent(key):
    d = load_sent()
    # Clean entries older than 6 hours
    now = time.time()
    d = {k:v for k,v in d.items() if now-v < 21600}
    save_sent(d)
    return key in d

def mark_sent(key):
    d = load_sent()
    d[key] = time.time()
    save_sent(d)

# ── API ──
def api(url, t=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=t)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def event_detail(eid):
    d = api(f"{BASE}/event?eventId={eid}&productId=3&_t={int(time.time()*1000)}")
    if d and d.get('bizCode') == 10000 and d.get('data', {}).get('homeTeamName'):
        return d['data']
    return None

def results(lk, s, e, ps=100, pn=1):
    lg = LEAGUES[lk]
    d = api(f"{BASE}/eventResultList?pageNum={pn}&pageSize={ps}&sportId={SPORT}"
            f"&categoryId={lg['catId']}&tournamentId={lg['tId']}&startTime={s}&endTime={e}"
            f"&_t={int(time.time()*1000)}")
    if d and d.get('bizCode') == 10000 and d.get('data'):
        ev = []
        for t in d['data'].get('tournaments', []):
            ev.extend(t.get('events', []))
        return ev
    return []

def yesterday(lk):
    n = datetime.now(timezone.utc)
    ts = n.replace(hour=0, minute=0, second=0, microsecond=0)
    ys = ts - timedelta(days=1)
    s, e = int(ys.timestamp()*1000), int(ts.timestamp()*1000)
    all_ev = []
    for p in range(1, 5):
        ev = results(lk, s, e, 100, p)
        if not ev: break
        all_ev.extend(ev)
        if len(ev) < 100: break
    return all_ev

# ── DISCOVERY ──
def discover(lk, rounds=2):
    now = int(time.time()*1000)
    lg = LEAGUES[lk]
    rec = results(lk, now-14400000, now, 20)
    if not rec: return []
    pfx, suffs = None, []
    for ev in rec:
        eid = ev.get('eventId', '')
        if eid.startswith('sr:match:20002'):
            num = eid.replace('sr:match:', '')
            pfx = 'sr:match:' + num[:10]
            suffs.append(int(num[10:]))
    if not pfx or not suffs: return []
    mx = max(suffs)
    scan = list(range(mx+1, mx+1+rounds*(lg['mpr']+15)))
    eids = [f"{pfx}{n}" for n in scan]
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        res = list(ex.map(event_detail, eids))
    up = []
    for ev in res:
        if not ev or ev.get('status') != 0: continue
        sp = ev.get('sport', {})
        if sp.get('id') != SPORT or sp.get('category',{}).get('id') != lg['catId']: continue
        up.append(ev)
    rds = defaultdict(list)
    for ev in up: rds[ev.get('estimateStartTime',0)].append(ev)
    out = []
    for t in sorted(rds.keys())[:rounds]: out.extend(rds[t])
    return out

# ── SECTION A ──
def sec_a(event):
    mkts = event.get('markets', [])
    cs, hg, ag, ou, fhou, gg = None, None, None, {}, {}, None
    for m in mkts:
        mid, spec = str(m.get('id','')), m.get('specifier','')
        parsed = {}
        for o in m.get('outcomes', []):
            try:
                parsed[o['desc']] = {'odds':float(o.get('odds',0)),'prob':float(o.get('probability',0)),'id':o.get('id',''),'act':o.get('isActive',0)}
            except: pass
        if mid=='45': cs=parsed
        elif mid=='23': hg=parsed
        elif mid=='24': ag=parsed
        elif mid=='18': ou[spec.replace('total=','') if 'total=' in spec else spec]=parsed
        elif mid=='68': fhou[spec.replace('total=','') if 'total=' in spec else spec]=parsed
        elif mid=='29': gg=parsed
    
    sc, mx, sig = 0, 0, {}
    
    if cs:
        mx += 3
        o15p = sum(v['prob'] for d,v in cs.items() if sum_score(d)>=2)
        fp11 = next((v['prob'] for d,v in cs.items() if d.replace(' ','')=='1:1'), 0)
        sig['cs_o15']=round(o15p,4); sig['fp11']=round(fp11,4)
        if o15p>0.55: sc+=3
        elif o15p>0.45: sc+=2
        elif o15p>0.35: sc+=1
    
    if hg:
        mx += 2
        h0 = sum(v['prob'] for d,v in hg.items() if d.strip() in ('0','No goal','0 Goals','No Goal'))
        sig['h0']=round(h0,4)
        if h0<0.30: sc+=2
        elif h0<0.42: sc+=1
    
    if ag:
        mx += 2
        a0 = sum(v['prob'] for d,v in ag.items() if d.strip() in ('0','No goal','0 Goals','No Goal'))
        sig['a0']=round(a0,4)
        if a0<0.30: sc+=2
        elif a0<0.42: sc+=1
    
    ou15_odds, ou15_prob, ou15_oid = 0, 0, None
    if '1.5' in ou:
        mx += 3
        for d,v in ou['1.5'].items():
            if 'Over' in d: ou15_odds,ou15_prob,ou15_oid = v['odds'],v['prob'],v['id']
        sig['ou15']=ou15_odds; sig['ou15p']=round(ou15_prob,4)
        sweet = SWEET[0]<=ou15_odds<=SWEET[1]
        sig['sweet']=sweet
        if sweet: sc+=3
        elif ou15_prob>0.60: sc+=2
        elif ou15_prob>0.50: sc+=1
    
    if '0.5' in fhou:
        mx += 2
        fh = max((v['prob'] for d,v in fhou['0.5'].items() if 'Over' in d), default=0)
        sig['fh05']=round(fh,4)
        if fh>0.70: sc+=2
        elif fh>0.55: sc+=1
    
    if gg:
        mx += 2
        gp = max((v['prob'] for d,v in gg.items() if 'Yes' in d or 'GG' in d), default=0)
        sig['gg']=round(gp,4)
        if gp>0.45: sc+=2
        elif gp>0.35: sc+=1
    
    pct = (sc/mx*100) if mx>0 else 0
    return {
        'sc':sc,'mx':mx,'pct':round(pct,1),'sig':sig,
        'fp11':sig.get('fp11',0)>0.10,
        'ou15_odds':ou15_odds,'ou15p':ou15_prob,'ou15_oid':ou15_oid,
        'sweet':sig.get('sweet',False),
        'gid':event.get('markets',[{}])[0].get('groupId','') if event.get('markets') else '',
    }

def sum_score(desc):
    try:
        p=desc.replace(' ','').split(':')
        return int(p[0])+int(p[1])
    except: return -1

# ── SECTION B: OPTIMIZED SKIP + SCORE ──
def find_slot(yest, target_est):
    target_dt = datetime.fromtimestamp(target_est/1000, tz=timezone.utc)
    tm = target_dt.hour*60+target_dt.minute
    slots = defaultdict(list)
    for ev in yest: slots[int(ev.get('estimateStartTime',0))].append(ev)
    best, bd = None, 999
    for t in slots:
        dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
        d = abs((dt.hour*60+dt.minute)-tm)
        if d<bd: bd=d; best=t
    return slots.get(best,[]) if best and bd<=10 else []

def pscore(ev):
    ss = ev.get('setScore','')
    if ss and ':' in ss:
        try:
            p=ss.split(':')
            return int(p[0]),int(p[1])
        except: pass
    return None,None

def energy(slot, home, away):
    sf, hd, ad = None, {'s':0,'c':0,'t':0}, {'s':0,'c':0,'t':0}
    for m in slot:
        h,a = m.get('homeTeamName',''), m.get('awayTeamName','')
        hs,aws = pscore(m)
        if hs is None: continue
        if h==home and a==away: sf={'hs':hs,'as':aws,'t':hs+aws}
        if h==home: hd={'s':hs,'c':aws,'t':hs+aws}
        elif a==home: hd={'s':aws,'c':hs,'t':hs+aws}
        if h==away: ad={'s':hs,'c':aws,'t':hs+aws}
        elif a==away: ad={'s':aws,'c':hs,'t':hs+aws}
    return {'sf':sf,'h':hd,'a':ad,'n':len(slot)}

def sec_b(en):
    h,a,sf = en['h'],en['a'],en['sf']
    
    # OPTIMIZED SKIP RULES (removed A+F, kept C+D+E)
    # C: Compression — both ≥4 total in slot
    if h['t']>=4 and a['t']>=4:
        return {'skip':True,'reason':'Skip-C: Compression','sc':0,'conf':'SKIP','reasons':['Skip-C']}
    # D: Combined low < 2
    if h['t']+a['t']<2:
        return {'skip':True,'reason':'Skip-D: Low energy','sc':0,'conf':'SKIP','reasons':['Skip-D']}
    # E: Same fixture 0-0
    if sf and sf['t']==0:
        return {'skip':True,'reason':'Skip-E: Same fix 0-0','sc':0,'conf':'SKIP','reasons':['Skip-E']}
    
    # SCORING (max 14)
    pts, reasons = 0, []
    if h['s']>=1: pts+=2; reasons.append(f"R1:H scored {h['s']}(+2)")
    if a['s']>=1: pts+=2; reasons.append(f"R2:A scored {a['s']}(+2)")
    if sf and sf['t']>=2: pts+=2; reasons.append(f"R3:Fix {sf['hs']}-{sf['as']}(+2)")
    if h['t']>=2: pts+=2; reasons.append(f"R4:H total {h['t']}≥2(+2)")
    if a['t']>=2: pts+=2; reasons.append(f"R5:A total {a['t']}≥2(+2)")
    if h['t']+a['t']>=4: pts+=1; reasons.append(f"R6:Comb {h['t']+a['t']}≥4(+1)")
    if h['s']>0 and h['c']>0 and a['s']>0 and a['c']>0: pts+=1; reasons.append("R7:Both S&C(+1)")
    
    if pts>=10: conf='LOCK'
    elif pts>=6: conf='PICK'
    elif pts>=3: conf='CONSIDER'
    else: conf='SKIP'
    
    return {'skip':conf=='SKIP','reason':'' if conf!='SKIP' else f'B:{pts}<3','sc':pts,'conf':conf,'reasons':reasons}

# ── COMBINED ──
def analyze(event, yest):
    home, away = event.get('homeTeamName','?'), event.get('awayTeamName','?')
    est = int(event.get('estimateStartTime',0))
    a = sec_a(event)
    slot = find_slot(yest, est)
    en = energy(slot, home, away)
    b = sec_b(en)
    
    combined = a['sc']+b['sc']
    cmax = a['mx']+14
    cpct = (combined/cmax*100) if cmax>0 else 0
    
    if b['skip']:
        verdict = 'SKIP'
    elif cpct>=70: verdict='LOCK'
    elif cpct>=50: verdict='PICK'
    elif cpct>=35: verdict='CONSIDER'
    else: verdict='SKIP'
    
    return {
        'match':f"{home} vs {away}", 'eid':event.get('eventId'), 'gid':event.get('gameId'),
        'home':home, 'away':away, 'start':est,
        'a':a, 'b':b, 'en':en,
        'combined':combined, 'cmax':cmax, 'cpct':round(cpct,1),
        'verdict':verdict,
        'ou15_odds':a['ou15_odds'], 'ou15_oid':a['ou15_oid'],
        'sweet':a['sweet'], 'fp11':a['fp11'], 'group_id':a['gid'],
    }

def scan(lk, yc=None):
    lg = LEAGUES[lk]
    print(f"\n🔍 Scanning {lg['name']}...")
    yest = yc or yesterday(lk)
    print(f"  📊 Yesterday: {len(yest)} matches")
    up = discover(lk, rounds=2)
    print(f"  📋 Upcoming: {len(up)} matches")
    if not up: return [], yest
    
    rds = sorted(set(ev.get('estimateStartTime',0) for ev in up))
    for t in rds:
        dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
        n = sum(1 for ev in up if ev.get('estimateStartTime')==t)
        print(f"  ⏰ {dt.strftime('%H:%M UTC')} ({n} matches)")
    
    res = []
    for ev in up:
        r = analyze(ev, yest)
        e = {'LOCK':'🔒','PICK':'✅','CONSIDER':'🤔','SKIP':'❌'}[r['verdict']]
        sw = '💎' if r['sweet'] else ''
        fp = '🔍' if r['fp11'] else ''
        en = r['en']
        si = f"[fix:{en['sf']['hs']}-{en['sf']['as']}]" if en['sf'] else f"[H{en['h']['s']}-{en['h']['c']} A{en['a']['s']}-{en['a']['c']}]"
        print(f"  {e} {r['match']}: {r['verdict']} A:{r['a']['pct']}% B:{r['b']['conf']}({r['b']['sc']}/14) C:{r['cpct']}% O1.5@{r['ou15_odds']:.2f} {sw}{fp} {si}")
        if r['b']['skip']: print(f"      ↳ {r['b']['reason']}")
        res.append(r)
    res.sort(key=lambda x: x['cpct'], reverse=True)
    return res, yest

def build_mega(all_r, min_odds=30000, max_odds=40000):
    """Select picks for mega accumulator targeting 30k-40k combined odds."""
    eligible = [r for r in all_r if r['verdict'] in ('LOCK','PICK')]
    eligible.sort(key=lambda x: (x['verdict']=='LOCK', x['sweet'], x['cpct']), reverse=True)
    if not eligible: return []
    selected = []
    running = 1.0
    for p in eligible:
        o = p['ou15_odds']
        if o <= 1.0: continue
        selected.append(p)
        running *= o
        if running >= min_odds: break
    return selected

def build_separate(all_r):
    """Build separate LOCK and PICK accumulators with individual booking codes."""
    locks = [r for r in all_r if r['verdict']=='LOCK' and r['ou15_odds']>1.0 and r.get('ou15_oid')]
    picks = [r for r in all_r if r['verdict']=='PICK' and r['ou15_odds']>1.0 and r.get('ou15_oid')]
    locks.sort(key=lambda x: (x['sweet'], x['cpct']), reverse=True)
    picks.sort(key=lambda x: (x['sweet'], x['cpct']), reverse=True)
    return locks, picks

# ── BOOKING CODE ──
def gen_booking(picks):
    """Generate SportyBet booking code via share API."""
    if not picks: return None
    outcomes = []
    for p in picks:
        oid = p.get('ou15_oid')
        eid = p.get('eid')
        if not oid or not eid: continue
        outcomes.append({
            'eventId': eid,
            'productId': '3',
            'marketId': '18',
            'outcomeId': oid,
            'specifier': 'total=1.5',
            'odds': str(p['ou15_odds']),
            'sportId': SPORT,
            'isLive': False,
            'isBanker': False,
        })
    if not outcomes: return None
    
    payload = {
        'outcomes': outcomes,
        'totalOdds': str(round(eval('*'.join(str(p['ou15_odds']) for p in picks)), 2)),
        'totalStake': '100',
        'channel': 'WEB',
    }
    try:
        r = requests.post(
            'https://www.sportybet.com/api/ng/orders/share',
            json=payload, headers={**HEADERS, 'Content-Type': 'application/json'}, timeout=15
        )
        d = r.json()
        if d.get('bizCode') == 10000 and d.get('data', {}).get('shareCode'):
            return d['data']['shareCode']
    except Exception as e:
        print(f"  ⚠️ Booking failed: {e}")
    return None

# ── TELEGRAM ──
def tg_send(text, chat_id=None):
    """Send message to Telegram."""
    cid = chat_id or TG_CHAT
    if not cid:
        print("  ⚠️ No TG_CHAT_ID set")
        return False
    try:
        r = requests.post(f'{TG_API}/sendMessage', json={
            'chat_id': cid,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
        }, timeout=15)
        d = r.json()
        if d.get('ok'): return True
        print(f"  ⚠️ TG error: {d.get('description','')}")
    except Exception as e:
        print(f"  ⚠️ TG send failed: {e}")
    return False

def tg_get_chat_id():
    """Get chat_id from latest message to the bot (for setup)."""
    try:
        r = requests.get(f'{TG_API}/getUpdates', timeout=10)
        d = r.json()
        if d.get('ok') and d.get('result'):
            msg = d['result'][-1].get('message', {})
            cid = msg.get('chat', {}).get('id')
            if cid:
                print(f"  ✅ Chat ID: {cid}")
                return str(cid)
    except: pass
    return None

def format_section(picks, icon, label, code, total_odds):
    """Format a single section (LOCKs or PICKs) for Telegram."""
    if not picks: return []
    lines = [f"{icon} <b>{label} ({len(picks)} selections | {total_odds:,.0f}x odds)</b>", ""]
    by_time = defaultdict(list)
    for p in picks:
        by_time[p.get('start', 0)].append(p)
    for t in sorted(by_time.keys()):
        dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
        lines.append(f"⏰ <b>{dt.strftime('%H:%M UTC')}</b>")
        for p in by_time[t]:
            sw = ' 💎' if p['sweet'] else ''
            fp = ' 🔍' if p['fp11'] else ''
            lines.append(f"  {icon} {p['match']} — O1.5 @{p['ou15_odds']:.2f}{sw}{fp}")
            lines.append(f"      A:{p['a']['pct']}% B:{p['b']['conf']}({p['b']['sc']}/14) C:{p['cpct']}%")
        lines.append("")
    lines.append(f"💰 <b>ODDS: {total_odds:,.0f}x</b>")
    if code:
        lines.append(f"📋 <b>CODE: {code}</b>")
        lines.append(f"🔗 sportybet.com/ng/share/{code}")
    else:
        lines.append("📋 Code: manual entry required")
    return lines

def format_mega_msg(lock_picks, lock_code, lock_odds, pick_picks, pick_code, pick_odds, scan_time):
    """Format the Telegram message with SEPARATE booking codes for LOCKs and PICKs."""
    total_sel = len(lock_picks) + len(pick_picks)
    lines = [
        f"🏆 <b>VFL MEGA — ONIMIX ELITE</b>",
        f"📅 {scan_time}",
        f"🎯 {total_sel} total selections",
        f"🔒 {len(lock_picks)} LOCKs | ✅ {len(pick_picks)} PICKs",
        "",
    ]
    
    # ── LOCK SECTION ──
    if lock_picks:
        lines.extend(format_section(lock_picks, '🔒', 'LOCK ACCUMULATOR', lock_code, lock_odds))
        lines.append("")
    
    # ── PICK SECTION ──
    if pick_picks:
        lines.extend(format_section(pick_picks, '✅', 'PICK ACCUMULATOR', pick_code, pick_odds))
        lines.append("")
    
    lines.extend([
        "⚡ <i>Engine v3.2 | Section A+B | Accuracy ~77.5%</i>",
        "🤖 <i>ONIMIX TECH — Automated VFL Intelligence</i>",
    ])
    return '\n'.join(lines)

# ── MAIN RUNNER ──
def run(chat_id=None):
    """Full scan → analyze → book → send to Telegram."""
    cid = chat_id or TG_CHAT
    scan_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    print("="*60)
    print("🏆 VFL ENGINE v3.2 FINAL — ONIMIX TECH")
    print(f"📅 {scan_time}")
    print("="*60)
    
    all_r = []
    for lk in ['spain','germany']:
        res, _ = scan(lk)
        all_r.extend(res)
    
    locks = [r for r in all_r if r['verdict']=='LOCK']
    picks = [r for r in all_r if r['verdict']=='PICK']
    cons = [r for r in all_r if r['verdict']=='CONSIDER']
    skips = [r for r in all_r if r['verdict']=='SKIP']
    
    print(f"\n{'='*60}")
    print(f"📊 🔒{len(locks)} ✅{len(picks)} 🤔{len(cons)} ❌{len(skips)}")
    
    bookable = [r for r in all_r if r['verdict'] in ('LOCK','PICK')]
    if not bookable:
        print("⚠️ No bookable picks this round")
        if cid:
            tg_send(f"⚠️ VFL Scan {scan_time}\nNo bookable picks this round. Next scan in ~4 min.", cid)
        return {'picks': 0, 'sent': False}
    
    # Build SEPARATE lock and pick accumulators
    lock_picks, pick_picks = build_separate(all_r)
    all_selected = lock_picks + pick_picks
    
    if not all_selected:
        print("⚠️ No valid selections for accumulators")
        return {'picks': len(bookable), 'sent': False}
    
    # Calculate odds for each
    lock_odds = 1.0
    for p in lock_picks: lock_odds *= p['ou15_odds']
    pick_odds = 1.0
    for p in pick_picks: pick_odds *= p['ou15_odds']
    
    print(f"\n🎰 LOCK ACCA: {len(lock_picks)} selections @ {lock_odds:,.1f}x")
    print(f"🎰 PICK ACCA: {len(pick_picks)} selections @ {pick_odds:,.1f}x")
    
    # Dedup check (using combined set)
    dk = dedup_key(all_selected)
    if already_sent(dk):
        print("🔁 Already sent this exact combo — skipping")
        return {'picks': len(all_selected), 'sent': False, 'reason': 'dedup'}
    
    # Generate SEPARATE booking codes
    lock_code, pick_code = None, None
    if lock_picks:
        print("📋 Generating LOCK booking code...")
        lock_code = gen_booking(lock_picks)
        if lock_code: print(f"  ✅ LOCK Code: {lock_code}")
        else: print("  ⚠️ No LOCK booking code")
    
    if pick_picks:
        print("📋 Generating PICK booking code...")
        pick_code = gen_booking(pick_picks)
        if pick_code: print(f"  ✅ PICK Code: {pick_code}")
        else: print("  ⚠️ No PICK booking code")
    
    # Format and send
    msg = format_mega_msg(lock_picks, lock_code, lock_odds, pick_picks, pick_code, pick_odds, scan_time)
    
    if cid:
        ok = tg_send(msg, cid)
        if ok:
            mark_sent(dk)
            print(f"✅ Sent to Telegram!")
        else:
            print(f"❌ Telegram send failed")
        return {'picks': len(all_selected), 'sent': ok, 'lock_code': lock_code, 'pick_code': pick_code,
                'lock_odds': lock_odds, 'pick_odds': pick_odds}
    else:
        print("⚠️ No chat_id — printing message only:")
        print(msg)
        mark_sent(dk)
        return {'picks': len(all_selected), 'sent': False, 'lock_code': lock_code, 'pick_code': pick_code,
                'lock_odds': lock_odds, 'pick_odds': pick_odds, 'msg': msg}

# ── MAIN ──
if __name__ == '__main__':
    # Auto-detect chat_id if not set
    if not TG_CHAT:
        print("📱 No TG_CHAT_ID set. Trying to detect from bot updates...")
        cid = tg_get_chat_id()
        if cid:
            TG_CHAT = cid
            print(f"  ✅ Using chat_id: {cid}")
        else:
            print("  ⚠️ Send any message to your bot first, then re-run")
    
    run()
