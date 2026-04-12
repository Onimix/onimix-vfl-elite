"""
ONIMIX VFL Feedback Engine v2 - Resilient
- Works with results API when available
- Falls back to live API data analysis
- Builds blacklist + penalty from cross-day patterns
- Exports scanner-ready feedback JSON
"""
import urllib.request, json, ssl, time
from datetime import datetime, timezone, timedelta
from collections import defaultdict

SPORT = 'sr:sport:202120001'
RESULTS_URL = 'https://www.sportybet.com/api/ng/factsCenter/eventResultList'
LIVE_URL = 'https://www.sportybet.com/api/ng/factsCenter/liveOrPrematchEvents'
WAT = timezone(timedelta(hours=1))
FEEDBACK_FILE = '/tmp/vfl_feedback.json'
SCANNER_FILE = '/tmp/vfl_scanner_feedback.json'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ENG_T=set('ARS,AST,BRE,CHE,CRY,FOR,LIV,MUN,NEW,SUN,WOL,BUR,FUL,TOT,WHU,BOU,BHA,LEE,EVE,MCI'.split(','))
ESP_T=set('ATM,BAR,BET,CEL,GIR,GET,MAL,OSA,RAY,RSO,SEV,VAL,VIL,ALA,CAD,ALM,GRA,LPA,ALC,ESP,RMA,ELC,LEV,VCF,BIL,FCB,OVI,RBB'.split(','))
ITA_T=set('ATA,BFC,CAG,LEC,PAR,PIS,ROM,SAS,TOR,VER,COM,NAP,USC,ACM,LAZ,FIO,GEN,JUV,INT,UDI,MON'.split(','))
GER_T=set('BMU,BVB,HDH,LEV,MAI,SCF,SGE,STP,WOB,KOE,RBL,SVW,HSV,BMG,UNI,TSG,VFB,FCA,BAY,KIE'.split(','))
FRA_T=set('ANG,LEN,LOR,NCE,OLM,PFC,PSG,REN,STR,NAN,LEH,B29,MET,AUX,LIL,LYO,TOU,AMO'.split(','))

def get_league(h,a):
    h3=h[:3].upper(); a3=a[:3].upper()
    if h3 in ENG_T or a3 in ENG_T: return 'England'
    if h3 in ESP_T or a3 in ESP_T: return 'Spain'
    if h3 in ITA_T or a3 in ITA_T: return 'Italy'
    if h3 in GER_T or a3 in GER_T: return 'Germany'
    if h3 in FRA_T or a3 in FRA_T: return 'France'
    return None

def mk(h,a): return h[:3].upper()+' vs '+a[:3].upper()

def fetch_url(url, t=15):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36','Referer':'https://www.sportybet.com/ng/virtual','Origin':'https://www.sportybet.com','Accept':'application/json'})
    with urllib.request.urlopen(req, context=ctx, timeout=t) as r:
        return json.loads(r.read().decode())

def try_results_api(pages=5):
    """Try to fetch results - returns empty list if API is down"""
    results = []
    now_ms = int(time.time()*1000)
    for p in range(1, pages+1):
        try:
            url = f"{RESULTS_URL}?pageNum={p}&pageSize=100&sportId={SPORT}&_t={now_ms+p}"
            data = fetch_url(url, t=10)
            if data.get('bizCode')==10000:
                evts = data.get('data',{}).get('list',[])
                if not evts: break
                results.extend(evts)
            else: break
        except:
            break
        time.sleep(0.3)
    return results

def get_live_finished():
    """Get matches from live API that are near-finished (70+ min) to approximate results"""
    now_ms = int(time.time()*1000)
    try:
        url = f"{LIVE_URL}?sportId={SPORT}&_t={now_ms}"
        data = fetch_url(url, t=15)
        if data.get('bizCode')!=10000: return []
        tournaments = data.get('data',[])
        if isinstance(tournaments, dict): tournaments = tournaments.get('tournaments',[])
        finished = []
        for t in tournaments:
            for e in t.get('events',[]):
                played = e.get('playedSeconds','0:00')
                try: mins = int(played.split(':')[0])
                except: mins = 0
                if mins >= 70:  # Near-finished, score is final
                    finished.append(e)
        return finished
    except:
        return []

def parse_events(events, source='results'):
    """Parse events into standardized records"""
    parsed = []
    for e in events:
        home = e.get('homeTeamName','?')
        away = e.get('awayTeamName','?')
        league = get_league(home, away)
        if not league: continue
        key = mk(home, away)
        scores = e.get('setScore','').split(':')
        if len(scores)!=2: continue
        try: hg,ag = int(scores[0]),int(scores[1])
        except: continue
        tg = hg+ag
        ko = e.get('estimateStartTime',0)
        if isinstance(ko,str): ko=int(ko)
        dt = datetime.fromtimestamp(ko/1000, tz=WAT) if ko>0 else None
        parsed.append({
            'key':key, 'league':league, 'hg':hg, 'ag':ag, 'tg':tg,
            'o15':tg>=2, 'score':f'{hg}:{ag}',
            'date':dt.strftime('%Y-%m-%d') if dt else 'unknown',
            'hour':dt.hour if dt else -1,
            'source':source
        })
    return parsed

def load_previous_feedback():
    """Load previous feedback file to accumulate knowledge"""
    try:
        with open(FEEDBACK_FILE) as f:
            return json.load(f)
    except:
        return None

def run_feedback():
    now = datetime.now(WAT)
    today = now.strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    print(f'🔄 Feedback Engine v2 | {now.strftime("%H:%M:%S")} WAT')
    print(f'   Today={today} Yesterday={yesterday}')

    # Load ELITE lookup
    ELITE_RAW='{"England":{"AST vs ARS":97.6,"NEW vs LEE":95.2,"CHE vs NEW":95.1,"AST vs NEW":92.9,"BHA vs LEE":92.9,"CRY vs SUN":92.9,"CRY vs LEE":92.9,"CRY vs NEW":92.9,"MUN vs EVE":92.9,"NEW vs MCI":92.9,"ARS vs SUN":92.7,"CRY vs ARS":92.7,"AST vs BRE":90.5,"BOU vs CHE":90.5,"BOU vs SUN":90.5,"BOU vs LEE":90.5,"BOU vs ARS":90.5,"CHE vs LIV":90.5,"CHE vs MCI":90.5,"CHE vs BRE":90.5,"CRY vs MCI":90.5,"FOR vs LIV":90.5,"LIV vs BRE":90.5,"LIV vs MUN":90.5,"MCI vs EVE":90.5,"NEW vs CHE":90.5,"TOT vs LIV":90.5,"AST vs BOU":90.2,"MCI vs LIV":90.2,"MCI vs NEW":88.4,"AST vs WHU":88.1,"AST vs SUN":88.1,"BHA vs MCI":88.1,"CHE vs ARS":88.1,"CHE vs CRY":88.1,"CRY vs CHE":88.1,"FOR vs MUN":88.1,"LIV vs MCI":88.1,"LIV vs WOL":88.1,"MCI vs BRE":88.1,"MUN vs TOT":88.1,"NEW vs WHU":88.1,"NEW vs FOR":88.1,"NEW vs BOU":88.1,"TOT vs WHU":88.1,"WHU vs BRE":88.1,"ARS vs MCI":88.1,"CRY vs WHU":88.1,"AST vs TOT":87.8,"BOU vs NEW":87.8,"CHE vs WHU":87.8,"CHE vs BUR":87.8,"CRY vs BRE":87.8,"WHU vs NEW":87.8,"WOL vs BUR":87.8,"MUN vs SUN":86.0,"ARS vs TOT":85.7,"ARS vs EVE":85.7,"ARS vs LEE":85.7,"AST vs CHE":85.7,"AST vs MCI":85.7,"BOU vs WHU":85.7,"BRE vs SUN":85.7,"BRE vs BUR":85.7,"CHE vs SUN":85.7,"CRY vs BUR":85.7,"CRY vs TOT":85.7,"EVE vs MCI":85.7,"FOR vs NEW":85.7,"FOR vs BRE":85.7,"FUL vs BOU":85.7,"LIV vs WHU":85.7,"MUN vs LEE":85.7,"MUN vs LIV":85.7,"NEW vs EVE":85.7,"NEW vs FUL":85.7,"NEW vs TOT":85.7,"TOT vs NEW":85.7,"TOT vs CRY":85.7,"TOT vs FOR":85.7,"TOT vs MCI":85.7,"WHU vs CHE":85.7,"WOL vs NEW":85.7,"AST vs LIV":85.4,"BHA vs MUN":85.4,"FOR vs SUN":85.4,"MCI vs ARS":85.4,"ARS vs CRY":83.3,"ARS vs CHE":83.3,"AST vs WOL":83.3,"AST vs LEE":83.3,"BHA vs CRY":83.3,"BOU vs MCI":83.3,"BRE vs WHU":83.3,"CHE vs TOT":83.3,"CRY vs WOL":83.3,"FOR vs MCI":83.3,"FOR vs ARS":83.3,"LEE vs FOR":83.3,"LIV vs NEW":83.3,"MCI vs BUR":83.3,"MUN vs AST":83.3,"MUN vs WHU":83.3,"MUN vs FUL":83.3,"MUN vs FOR":83.3,"NEW vs AST":83.3,"NEW vs SUN":83.3,"NEW vs WOL":83.3,"NEW vs LIV":83.3,"NEW vs BUR":83.3,"TOT vs LEE":83.3,"TOT vs ARS":83.3,"WHU vs SUN":83.3,"WOL vs BOU":83.3,"WOL vs CRY":83.3,"WOL vs WHU":83.3,"BRE vs WOL":83.3,"CHE vs AST":83.3,"AST vs MUN":82.9,"CHE vs FUL":82.9,"CRY vs BOU":82.9,"CRY vs MUN":82.9,"EVE vs CHE":82.9,"FOR vs WHU":82.9,"LIV vs SUN":82.9,"MCI vs MUN":82.9,"CHE vs BHA":81.4,"AST vs BUR":81.0,"BHA vs CHE":81.0,"BHA vs WHU":81.0,"BOU vs TOT":81.0,"BOU vs EVE":81.0,"BOU vs FUL":81.0,"BOU vs FOR":81.0,"BRE vs LEE":81.0,"BUR vs NEW":81.0,"BUR vs CHE":81.0,"CHE vs BOU":81.0,"CRY vs BHA":81.0,"CRY vs AST":81.0,"CRY vs FUL":81.0,"CRY vs FOR":81.0,"FUL vs NEW":81.0,"LEE vs NEW":81.0,"LIV vs TOT":81.0,"LIV vs FUL":81.0,"MCI vs BOU":81.0,"MUN vs CRY":81.0,"TOT vs BRE":81.0,"TOT vs WOL":81.0,"TOT vs BUR":81.0,"WHU vs MCI":81.0,"LIV vs BOU":81.0,"BHA vs NEW":80.5,"BRE vs MUN":80.5,"FOR vs BUR":80.5,"LIV vs BUR":80.5,"MCI vs TOT":80.5},"France":{"REN vs LOR":92.9,"PSG vs NCE":92.7,"PSG vs AMO":92.7,"PSG vs LOR":90.7,"AUX vs LOR":90.5,"LYO vs AMO":90.5,"LEN vs PSG":90.2,"LIL vs PFC":90.2,"LIL vs LOR":90.2,"NAN vs MET":90.2,"TOU vs LYO":90.2,"LEN vs LOR":88.1,"LIL vs LYO":88.1,"LOR vs AMO":87.8,"LYO vs ANG":87.8,"TOU vs LOR":87.8,"AUX vs B29":85.7,"LOR vs PSG":85.7,"LYO vs STR":85.7,"NAN vs STR":85.7,"NCE vs AMO":85.7,"OLM vs MET":85.7,"OLM vs PFC":85.7,"PSG vs LYO":85.7,"PSG vs ANG":85.7,"PSG vs MET":85.7,"REN vs OLM":85.7,"TOU vs STR":85.7,"LOR vs MET":85.4,"NCE vs PFC":85.4,"NCE vs LOR":85.4,"PFC vs LEH":85.4,"PSG vs LEH":85.4,"STR vs LOR":85.4,"LYO vs MET":85.4,"AMO vs B29":83.3,"ANG vs LYO":83.3,"LEN vs NCE":83.3,"LIL vs NCE":83.3,"LOR vs ANG":83.3,"LOR vs TOU":83.3,"NAN vs AMO":83.3,"NAN vs B29":83.3,"OLM vs LOR":83.3,"OLM vs LIL":83.3,"REN vs AMO":83.3,"LIL vs REN":82.9,"NCE vs REN":82.9,"PFC vs REN":82.9,"STR vs PFC":82.9,"STR vs REN":82.9,"TOU vs MET":82.9,"ANG vs NCE":81.0,"AUX vs MET":81.0,"LEN vs MET":81.0,"LIL vs OLM":81.0,"LIL vs AMO":81.0,"LOR vs B29":81.0,"MET vs LYO":81.0,"PFC vs LIL":81.0,"PSG vs PFC":81.0,"PSG vs LIL":81.0,"REN vs PSG":81.0,"TOU vs AMO":81.0,"ANG vs AMO":81.0,"AUX vs AMO":80.5,"LEN vs LEH":80.5,"LEN vs AMO":80.5,"LIL vs MET":80.5,"LYO vs LOR":80.5,"LYO vs B29":80.5,"MET vs OLM":80.5,"NAN vs PFC":80.5,"NCE vs TOU":80.5,"OLM vs STR":80.5,"STR vs LYO":80.5,"OLM vs TOU":80.5},"Spain":{"SEV vs CEL":85.4,"CEL vs ALM":82.9,"CEL vs VIL":82.9,"CEL vs CAD":82.9,"GCF vs ATH":82.9,"RMA vs GCF":80.5,"RSO vs ALM":80.5},"Italy":{"GEN vs MON":90.2,"VER vs MON":87.8,"INT vs MON":87.8,"LAZ vs LEC":87.8,"NAP vs MON":87.5,"ROM vs LEC":87.5,"ROM vs MON":87.5,"VER vs LEC":87.5,"INT vs LEC":85.4,"LAZ vs MON":85.4,"NAP vs LEC":85.4,"JUV vs LEC":85.4,"GEN vs LEC":85.0,"MIL vs MON":85.0,"FIO vs MON":85.0,"COM vs MON":82.9,"INT vs COM":82.9,"LAZ vs SAL":82.9,"MIL vs LEC":82.9,"ATA vs MON":82.9,"NAP vs SAL":82.5,"ROM vs SAL":82.5,"FIO vs LEC":80.5,"GEN vs SAL":80.5,"JUV vs MON":80.5,"LAZ vs COM":80.5,"NAP vs COM":80.5,"ROM vs COM":80.5,"TOR vs MON":80.5,"VER vs SAL":80.5,"ATA vs LEC":80.5,"COM vs LEC":80.0,"INT vs SAL":80.0},"Germany":{"BAY vs KIE":94.1,"BVB vs KIE":94.1,"FCA vs KIE":91.2,"RBL vs KIE":91.2,"WOB vs KIE":91.2,"BMG vs KIE":91.2,"SCF vs KIE":91.2,"SGE vs KIE":91.2,"TSG vs KIE":91.2,"VFB vs KIE":91.2,"BAY vs BOC":88.2,"BVB vs BOC":88.2,"FCA vs BOC":88.2,"M05 vs KIE":88.2,"BAY vs HSV":88.2,"FCA vs HSV":87.8,"BVB vs HSV":87.8,"RBL vs BOC":85.3,"SCF vs BOC":85.3,"SGE vs BOC":85.3,"TSG vs BOC":85.3,"VFB vs BOC":85.3,"WOB vs BOC":85.3,"BMG vs BOC":85.3,"BAY vs SVD":85.3,"BVB vs SVD":85.3,"FCA vs SVD":85.3,"RBL vs HSV":85.3,"VFB vs HSV":85.4,"WOB vs HSV":85.3,"M05 vs BOC":85.3,"FCA vs BMU":84.8,"RBL vs HSV2":82.4,"SCF vs HSV":82.4,"SGE vs HSV":82.4,"TSG vs HSV":82.4,"BMG vs HSV":82.4,"BAY vs BMU":82.4,"BVB vs BMU":82.4,"RBL vs SVD":82.4,"SCF vs SVD":82.4,"SGE vs SVD":82.4,"TSG vs SVD":82.4,"VFB vs SVD":82.4,"WOB vs SVD":82.4,"BMG vs SVD":82.4,"M05 vs HSV":82.4,"M05 vs SVD":82.4,"VFB vs BMU":85.4,"FCA vs BMU2":82.4,"RBL vs KIE2":82.4,"RBL vs BMU":82.4,"SCF vs BMU":82.4,"SGE vs BMU":82.4,"TSG vs BMU":82.4,"WOB vs BMU":82.4,"BMG vs BMU":82.4,"M05 vs BMU":82.4,"BAY vs STP":82.4,"BVB vs STP":82.4,"FCA vs STP":82.4,"RBL vs STP":82.4,"SCF vs STP":82.4,"SGE vs STP":82.4,"TSG vs STP":82.4,"VFB vs STP":82.4,"WOB vs STP":82.4,"BMG vs STP":82.4,"M05 vs STP":82.4,"BAY vs FCU":80.6,"BVB vs FCU":80.6,"FCA vs FCU":80.6,"SGE vs FCU":80.6,"RBL vs FCU":80.6,"VFB vs FCU":80.6,"SCF vs FCU":80.6,"WOB vs FCU":80.6,"TSG vs FCU":80.6}}'
    elite = json.loads(ELITE_RAW)
    elite_lookup = {}
    for lg, mus in elite.items():
        for mu, rate in mus.items():
            elite_lookup[mu] = (lg, rate)

    # Try results API first
    print('\n[1] Trying results API...')
    results = try_results_api(pages=5)
    
    # Also get near-finished live matches
    print('[2] Getting live finished matches...')
    live_fin = get_live_finished()
    
    all_parsed = []
    if results:
        print(f'  Results API: {len(results)} events')
        all_parsed.extend(parse_events(results, 'results'))
    if live_fin:
        print(f'  Live finished: {len(live_fin)} events')
        all_parsed.extend(parse_events(live_fin, 'live'))
    
    # Load previous feedback to merge
    prev = load_previous_feedback()
    if prev and prev.get('accumulated_results'):
        prev_count = len(prev['accumulated_results'])
        # Merge previous results (avoid duplicates by key+hour+date)
        existing_keys = set()
        for r in all_parsed:
            existing_keys.add(f"{r['key']}|{r['date']}|{r['hour']}")
        for pr in prev['accumulated_results']:
            pk = f"{pr['key']}|{pr['date']}|{pr['hour']}"
            if pk not in existing_keys:
                all_parsed.append(pr)
                existing_keys.add(pk)
        print(f'  Merged {prev_count} previous results → total {len(all_parsed)}')
    
    # Separate by day
    today_data = [r for r in all_parsed if r['date']==today]
    yesterday_data = [r for r in all_parsed if r['date']==yesterday]
    
    print(f'\n  Today: {len(today_data)} | Yesterday: {len(yesterday_data)}')
    
    # Filter ELITE
    today_elite = [r for r in today_data if r['key'] in elite_lookup]
    today_hit = [r for r in today_elite if r['o15']]
    today_miss = [r for r in today_elite if not r['o15']]
    
    yday_elite = [r for r in yesterday_data if r['key'] in elite_lookup]
    yday_hit = [r for r in yday_elite if r['o15']]
    
    print(f'\n[3] ELITE Performance:')
    if today_elite:
        print(f'  Today: {len(today_hit)}/{len(today_elite)} = {len(today_hit)/len(today_elite)*100:.1f}%')
    if yday_elite:
        print(f'  Yesterday: {len(yday_hit)}/{len(yday_elite)} = {len(yday_hit)/len(yday_elite)*100:.1f}%')
    
    # Analyze failures
    print(f'\n[4] Failed ELITE Analysis:')
    blacklist = {}
    penalties = {}
    
    for miss in today_miss:
        key = miss['key']
        hour = miss['hour']
        rate = elite_lookup.get(key, (None, None))[1]
        
        # Same matchup, same time yesterday
        yday_same = [y for y in yesterday_data if y['key']==key and abs(y['hour']-hour)<=1]
        yday_all = [y for y in yesterday_data if y['key']==key]
        
        pattern = 'UNKNOWN'; risk = 'low'
        
        if yday_same:
            same_hit = sum(1 for y in yday_same if y['o15'])
            if same_hit == 0:
                pattern = 'TIME_KILLER'; risk = 'high'
            elif same_hit < len(yday_same) * 0.5:
                pattern = 'TIME_WEAK'; risk = 'medium'
            else:
                pattern = 'FLUKE'; risk = 'low'
        elif yday_all:
            all_hit = sum(1 for y in yday_all if y['o15'])
            if all_hit < len(yday_all) * 0.5:
                pattern = 'MATCHUP_DRY'; risk = 'high'
            else:
                pattern = 'TIME_SPECIFIC'; risk = 'medium'
        
        slot = f'{key}@{hour}'
        if risk == 'high':
            blacklist[slot] = {'mu':key,'hr':hour,'why':pattern,'sc':miss['score'],'elite':rate}
        elif risk == 'medium':
            penalties[slot] = {'mu':key,'hr':hour,'why':pattern,'pen':3}
        
        yd_info = ''
        if yday_same:
            yd_info = f" Yday: {','.join(y['score']+('✅' if y['o15'] else '❌') for y in yday_same)}"
        elif yday_all:
            yd_info = f" Yday: {','.join(y['score']+'@'+str(y['hour'])+'h' for y in yday_all[:3])}"
        
        print(f'  ❌ {key} {miss["score"]} hr:{hour} E:{rate}% → {pattern}({risk}){yd_info}')
    
    # Check for dry-at-same-time patterns across days
    for r in today_data:
        if r['key'] in elite_lookup and r['tg'] <= 1:
            slot = f"{r['key']}@{r['hour']}"
            yday_dry = [y for y in yesterday_data if y['key']==r['key'] and abs(y['hour']-r['hour'])<=2 and y['tg']<=1]
            if yday_dry and slot not in blacklist:
                rate = elite_lookup.get(r['key'],(None,None))[1]
                blacklist[slot] = {'mu':r['key'],'hr':r['hour'],'why':'DRY_BOTH_DAYS','sc':r['score'],'elite':rate}
    
    # Hour analysis
    print(f'\n[5] Hour-by-hour (ELITE):')
    hour_stats = defaultdict(lambda:{'t':0,'h':0})
    for r in today_elite:
        hour_stats[r['hour']]['t'] += 1
        if r['o15']: hour_stats[r['hour']]['h'] += 1
    
    cold_hours = []
    for h in sorted(hour_stats.keys()):
        s = hour_stats[h]
        rate = s['h']/s['t']*100
        icon = '🔥' if rate>=85 else ('⚠️' if rate>=70 else '❄️')
        print(f'  {icon} {h:02d}h: {s["h"]}/{s["t"]} = {rate:.0f}%')
        if rate < 70 and s['t'] >= 3:
            cold_hours.append(h)
    
    # Summary
    print(f'\n{"="*50}')
    print(f'  📋 FEEDBACK SUMMARY')
    print(f'{"="*50}')
    print(f'  🚫 Blacklist (SKIP): {len(blacklist)}')
    for k,v in blacklist.items():
        print(f'    {v["mu"]} @{v["hr"]}h — {v["why"]}')
    print(f'  ⚠️ Penalty (-3pts): {len(penalties)}')
    for k,v in penalties.items():
        print(f'    {v["mu"]} @{v["hr"]}h — {v["why"]}')
    if cold_hours:
        print(f'  ❄️ Cold hours: {cold_hours}')
    
    # Save
    feedback = {
        'ts': now.isoformat(),
        'today': today, 'yesterday': yesterday,
        'stats': {
            'today_elite': len(today_elite),
            'today_hit': len(today_hit),
            'today_miss': len(today_miss),
            'rate': round(len(today_hit)/max(1,len(today_elite))*100, 1)
        },
        'blacklist': blacklist,
        'penalties': penalties,
        'cold_hours': cold_hours,
        'accumulated_results': all_parsed[-2000:]  # Keep last 2000 for next run
    }
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback, f, default=str)
    
    # Compact scanner version
    scanner = {
        'bl': {v['mu']: v['hr'] for v in blacklist.values()},
        'pen': {v['mu']: v['hr'] for v in penalties.values()},
        'cold': cold_hours,
        'ts': now.isoformat()
    }
    with open(SCANNER_FILE, 'w') as f:
        json.dump(scanner, f)
    
    print(f'\n✅ Saved feedback → {FEEDBACK_FILE}')
    print(f'✅ Scanner data → {SCANNER_FILE}')
    return feedback

if __name__ == '__main__':
    run_feedback()
