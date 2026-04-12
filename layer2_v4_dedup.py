"""VFL LAYER 2 v4 - ONIMIX 12-Layer Engine + FEEDBACK + DEDUP"""
import urllib.request, json, ssl, time, os, hashlib
from datetime import datetime, timezone, timedelta

TGTOKEN = '8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8'
CHAT = '1745848158'
SPORT = 'sr:sport:202120001'
AW = 20; CYCLE = 38
WAT = timezone(timedelta(hours=1))
BOOK_URL = 'https://www.sportybet.com/api/ng/orders/share'
FEEDBACK_FILE = '/tmp/vfl_scanner_feedback.json'
PICKS_LOG = '/tmp/vfl_picks_log.json'
DEDUP_FILE = '/tmp/vfl_dedup_L2.json'

ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

ENG_T=set('ARS,AST,BRE,CHE,CRY,FOR,LIV,MUN,NEW,SUN,WOL,BUR,FUL,TOT,WHU,BOU,BHA,LEE,EVE,MCI'.split(','))
ESP_T=set('ATM,BAR,BET,CEL,GIR,GET,MAL,OSA,RAY,RSO,SEV,VAL,VIL,ALA,CAD,ALM,GRA,LPA,ALC,ESP,RMA,ELC,LEV,VCF,BIL,FCB,OVI,RBB'.split(','))
ITA_T=set('ATA,BFC,CAG,LEC,PAR,PIS,ROM,SAS,TOR,VER,COM,NAP,USC,ACM,LAZ,FIO,GEN,JUV,INT,UDI,MON'.split(','))
GER_T=set('BMU,BVB,HDH,LEV,MAI,SCF,SGE,STP,WOB,KOE,RBL,SVW,HSV,BMG,UNI,TSG,VFB,FCA,BAY,KIE'.split(','))
FRA_T=set('ANG,LEN,LOR,NCE,OLM,PFC,PSG,REN,STR,NAN,LEH,B29,MET,AUX,LIL,LYO,TOU,AMO'.split(','))
FLAG = {'England':'🏴','Spain':'🇪🇸','Italy':'🇮🇹','Germany':'🇩🇪','France':'🇫🇷'}

ELITE_RAW='{"England":{"AST vs ARS":97.6,"NEW vs LEE":95.2,"CHE vs NEW":95.1,"AST vs NEW":92.9,"BHA vs LEE":92.9,"CRY vs SUN":92.9,"CRY vs LEE":92.9,"CRY vs NEW":92.9,"MUN vs EVE":92.9,"NEW vs MCI":92.9,"ARS vs SUN":92.7,"CRY vs ARS":92.7,"AST vs BRE":90.5,"BOU vs CHE":90.5,"BOU vs SUN":90.5,"BOU vs LEE":90.5,"BOU vs ARS":90.5,"CHE vs LIV":90.5,"CHE vs MCI":90.5,"CHE vs BRE":90.5,"CRY vs MCI":90.5,"FOR vs LIV":90.5,"LIV vs BRE":90.5,"LIV vs MUN":90.5,"MCI vs EVE":90.5,"NEW vs CHE":90.5,"TOT vs LIV":90.5,"AST vs BOU":90.2,"MCI vs LIV":90.2,"MCI vs NEW":88.4,"AST vs WHU":88.1,"AST vs SUN":88.1,"BHA vs MCI":88.1,"CHE vs ARS":88.1,"CHE vs CRY":88.1,"CRY vs CHE":88.1,"FOR vs MUN":88.1,"LIV vs MCI":88.1,"LIV vs WOL":88.1,"MCI vs BRE":88.1,"MUN vs TOT":88.1,"NEW vs WHU":88.1,"NEW vs FOR":88.1,"NEW vs BOU":88.1,"TOT vs WHU":88.1,"WHU vs BRE":88.1,"ARS vs MCI":88.1,"CRY vs WHU":88.1,"AST vs TOT":87.8,"BOU vs NEW":87.8,"CHE vs WHU":87.8,"CHE vs BUR":87.8,"CRY vs BRE":87.8,"WHU vs NEW":87.8,"WOL vs BUR":87.8,"MUN vs SUN":86.0,"ARS vs TOT":85.7,"ARS vs EVE":85.7,"ARS vs LEE":85.7,"AST vs CHE":85.7,"AST vs MCI":85.7,"BOU vs WHU":85.7,"BRE vs SUN":85.7,"BRE vs BUR":85.7,"CHE vs SUN":85.7,"CRY vs BUR":85.7,"CRY vs TOT":85.7,"EVE vs MCI":85.7,"FOR vs NEW":85.7,"FOR vs BRE":85.7,"FUL vs BOU":85.7,"LIV vs WHU":85.7,"MUN vs LEE":85.7,"MUN vs LIV":85.7,"NEW vs EVE":85.7,"NEW vs FUL":85.7,"NEW vs TOT":85.7,"TOT vs NEW":85.7,"TOT vs CRY":85.7,"TOT vs FOR":85.7,"TOT vs MCI":85.7,"WHU vs CHE":85.7,"WOL vs NEW":85.7,"AST vs LIV":85.4,"BHA vs MUN":85.4,"FOR vs SUN":85.4,"MCI vs ARS":85.4,"ARS vs CRY":83.3,"ARS vs CHE":83.3,"AST vs WOL":83.3,"AST vs LEE":83.3,"BHA vs CRY":83.3,"BOU vs MCI":83.3,"BRE vs WHU":83.3,"CHE vs TOT":83.3,"CRY vs WOL":83.3,"FOR vs MCI":83.3,"FOR vs ARS":83.3,"LEE vs FOR":83.3,"LIV vs NEW":83.3,"MCI vs BUR":83.3,"MUN vs AST":83.3,"MUN vs WHU":83.3,"MUN vs FUL":83.3,"MUN vs FOR":83.3,"NEW vs AST":83.3,"NEW vs SUN":83.3,"NEW vs WOL":83.3,"NEW vs LIV":83.3,"NEW vs BUR":83.3,"TOT vs LEE":83.3,"TOT vs ARS":83.3,"WHU vs SUN":83.3,"WOL vs BOU":83.3,"WOL vs CRY":83.3,"WOL vs WHU":83.3,"BRE vs WOL":83.3,"CHE vs AST":83.3,"AST vs MUN":82.9,"CHE vs FUL":82.9,"CRY vs BOU":82.9,"CRY vs MUN":82.9,"EVE vs CHE":82.9,"FOR vs WHU":82.9,"LIV vs SUN":82.9,"MCI vs MUN":82.9,"CHE vs BHA":81.4,"AST vs BUR":81.0,"BHA vs CHE":81.0,"BHA vs WHU":81.0,"BOU vs TOT":81.0,"BOU vs EVE":81.0,"BOU vs FUL":81.0,"BOU vs FOR":81.0,"BRE vs LEE":81.0,"BUR vs NEW":81.0,"BUR vs CHE":81.0,"CHE vs BOU":81.0,"CRY vs BHA":81.0,"CRY vs AST":81.0,"CRY vs FUL":81.0,"CRY vs FOR":81.0,"FUL vs NEW":81.0,"LEE vs NEW":81.0,"LIV vs TOT":81.0,"LIV vs FUL":81.0,"MCI vs BOU":81.0,"MUN vs CRY":81.0,"TOT vs BRE":81.0,"TOT vs WOL":81.0,"TOT vs BUR":81.0,"WHU vs MCI":81.0,"LIV vs BOU":81.0,"BHA vs NEW":80.5,"BRE vs MUN":80.5,"FOR vs BUR":80.5,"LIV vs BUR":80.5,"MCI vs TOT":80.5},"France":{"REN vs LOR":92.9,"PSG vs NCE":92.7,"PSG vs AMO":92.7,"PSG vs LOR":90.7,"AUX vs LOR":90.5,"LYO vs AMO":90.5,"LEN vs PSG":90.2,"LIL vs PFC":90.2,"LIL vs LOR":90.2,"NAN vs MET":90.2,"TOU vs LYO":90.2,"LEN vs LOR":88.1,"LIL vs LYO":88.1,"LOR vs AMO":87.8,"LYO vs ANG":87.8,"TOU vs LOR":87.8,"AUX vs B29":85.7,"LOR vs PSG":85.7,"LYO vs STR":85.7,"NAN vs STR":85.7,"NCE vs AMO":85.7,"OLM vs MET":85.7,"OLM vs PFC":85.7,"PSG vs LYO":85.7,"PSG vs ANG":85.7,"PSG vs MET":85.7,"REN vs OLM":85.7,"TOU vs STR":85.7,"LOR vs MET":85.4,"NCE vs PFC":85.4,"NCE vs LOR":85.4,"PFC vs LEH":85.4,"PSG vs LEH":85.4,"STR vs LOR":85.4,"LYO vs MET":85.4,"AMO vs B29":83.3,"ANG vs LYO":83.3,"LEN vs NCE":83.3,"LIL vs NCE":83.3,"LOR vs ANG":83.3,"LOR vs TOU":83.3,"NAN vs AMO":83.3,"NAN vs B29":83.3,"OLM vs LOR":83.3,"OLM vs LIL":83.3,"REN vs AMO":83.3,"LIL vs REN":82.9,"NCE vs REN":82.9,"PFC vs REN":82.9,"STR vs PFC":82.9,"STR vs REN":82.9,"TOU vs MET":82.9,"ANG vs NCE":81.0,"AUX vs MET":81.0,"LEN vs MET":81.0,"LIL vs OLM":81.0,"LIL vs AMO":81.0,"LOR vs B29":81.0,"MET vs LYO":81.0,"PFC vs LIL":81.0,"PSG vs PFC":81.0,"PSG vs LIL":81.0,"REN vs PSG":81.0,"TOU vs AMO":81.0,"ANG vs AMO":81.0,"AUX vs AMO":80.5,"LEN vs LEH":80.5,"LEN vs AMO":80.5,"LIL vs MET":80.5,"LYO vs LOR":80.5,"LYO vs B29":80.5,"MET vs OLM":80.5,"NAN vs PFC":80.5,"NCE vs TOU":80.5,"OLM vs STR":80.5,"STR vs LYO":80.5,"OLM vs TOU":80.5},"Spain":{"SEV vs CEL":85.4,"CEL vs ALM":82.9,"CEL vs VIL":82.9,"CEL vs CAD":82.9,"GCF vs ATH":82.9,"RMA vs GCF":80.5,"RSO vs ALM":80.5},"Italy":{"GEN vs MON":90.2,"VER vs MON":87.8,"INT vs MON":87.8,"LAZ vs LEC":87.8,"NAP vs MON":87.5,"ROM vs LEC":87.5,"ROM vs MON":87.5,"VER vs LEC":87.5,"INT vs LEC":85.4,"LAZ vs MON":85.4,"NAP vs LEC":85.4,"JUV vs LEC":85.4,"GEN vs LEC":85.0,"MIL vs MON":85.0,"FIO vs MON":85.0,"COM vs MON":82.9,"INT vs COM":82.9,"LAZ vs SAL":82.9,"MIL vs LEC":82.9,"ATA vs MON":82.9,"NAP vs SAL":82.5,"ROM vs SAL":82.5,"FIO vs LEC":80.5,"GEN vs SAL":80.5,"JUV vs MON":80.5,"LAZ vs COM":80.5,"NAP vs COM":80.5,"ROM vs COM":80.5,"TOR vs MON":80.5,"VER vs SAL":80.5,"ATA vs LEC":80.5,"COM vs LEC":80.0,"INT vs SAL":80.0},"Germany":{"BAY vs KIE":94.1,"BVB vs KIE":94.1,"FCA vs KIE":91.2,"RBL vs KIE":91.2,"WOB vs KIE":91.2,"BMG vs KIE":91.2,"SCF vs KIE":91.2,"SGE vs KIE":91.2,"TSG vs KIE":91.2,"VFB vs KIE":91.2,"BAY vs BOC":88.2,"BVB vs BOC":88.2,"FCA vs BOC":88.2,"M05 vs KIE":88.2,"BAY vs HSV":88.2,"FCA vs HSV":87.8,"BVB vs HSV":87.8,"RBL vs BOC":85.3,"SCF vs BOC":85.3,"SGE vs BOC":85.3,"TSG vs BOC":85.3,"VFB vs BOC":85.3,"WOB vs BOC":85.3,"BMG vs BOC":85.3,"BAY vs SVD":85.3,"BVB vs SVD":85.3,"FCA vs SVD":85.3,"RBL vs HSV":85.3,"VFB vs HSV":85.4,"WOB vs HSV":85.3,"M05 vs BOC":85.3,"FCA vs BMU":84.8,"RBL vs HSV2":82.4,"SCF vs HSV":82.4,"SGE vs HSV":82.4,"TSG vs HSV":82.4,"BMG vs HSV":82.4,"BAY vs BMU":82.4,"BVB vs BMU":82.4,"RBL vs SVD":82.4,"SCF vs SVD":82.4,"SGE vs SVD":82.4,"TSG vs SVD":82.4,"VFB vs SVD":82.4,"WOB vs SVD":82.4,"BMG vs SVD":82.4,"M05 vs HSV":82.4,"M05 vs SVD":82.4,"VFB vs BMU":85.4,"FCA vs BMU2":82.4,"RBL vs KIE2":82.4,"RBL vs BMU":82.4,"SCF vs BMU":82.4,"SGE vs BMU":82.4,"TSG vs BMU":82.4,"WOB vs BMU":82.4,"BMG vs BMU":82.4,"M05 vs BMU":82.4,"BAY vs STP":82.4,"BVB vs STP":82.4,"FCA vs STP":82.4,"RBL vs STP":82.4,"SCF vs STP":82.4,"SGE vs STP":82.4,"TSG vs STP":82.4,"VFB vs STP":82.4,"WOB vs STP":82.4,"BMG vs STP":82.4,"M05 vs STP":82.4,"BAY vs FCU":80.6,"BVB vs FCU":80.6,"FCA vs FCU":80.6,"SGE vs FCU":80.6,"RBL vs FCU":80.6,"VFB vs FCU":80.6,"SCF vs FCU":80.6,"WOB vs FCU":80.6,"TSG vs FCU":80.6}}'
elite=json.loads(ELITE_RAW)
elite_lookup = {}
for lg, matchups in elite.items():
    for mu, rate in matchups.items():
        elite_lookup[mu] = (lg, rate)
print('ELITE: ' + str(len(elite_lookup)))

def get_league(h,a):
    h3=h[:3].upper(); a3=a[:3].upper()
    if h3 in ENG_T or a3 in ENG_T: return 'England'
    if h3 in ESP_T or a3 in ESP_T: return 'Spain'
    if h3 in ITA_T or a3 in ITA_T: return 'Italy'
    if h3 in GER_T or a3 in GER_T: return 'Germany'
    if h3 in FRA_T or a3 in FRA_T: return 'France'
    return None

def mk(h,a): return h[:3].upper()+' vs '+a[:3].upper()

def fetch(url,t=20):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','Referer':'https://www.sportybet.com/ng/virtual'})
    with urllib.request.urlopen(req,context=ctx,timeout=t) as r: return r.read().decode()

def fetch_json(url,data=None,retries=2):
    for a in range(retries):
        try:
            h={'User-Agent':'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36','Accept':'application/json'}
            if data: h['Content-Type']='application/json'; h['Referer']='https://www.sportybet.com/ng/virtual'; h['Origin']='https://www.sportybet.com'
            req=urllib.request.Request(url,data=data,headers=h,method='POST' if data else 'GET')
            with urllib.request.urlopen(req,context=ctx,timeout=15) as r: return json.loads(r.read().decode())
        except:
            if a<retries-1: time.sleep(0.5)
    return None

def send_tg(msg):
    d=json.dumps({'chat_id':CHAT,'text':msg,'parse_mode':'HTML'}).encode()
    req=urllib.request.Request('https://api.telegram.org/bot'+TGTOKEN+'/sendMessage',data=d,headers={'Content-Type':'application/json'},method='POST')
    try: urllib.request.urlopen(req,context=ctx,timeout=15); return True
    except: return False

def create_booking_code(sels):
    if not sels: return None,None
    payload={"selections":[{"eventId":s["eventId"],"marketId":"18","specifier":"total=1.5","outcomeId":"12","odds":s.get("odds","1.27")} for s in sels]}
    try:
        resp=fetch_json(BOOK_URL,data=json.dumps(payload).encode())
        if resp and resp.get('bizCode')==10000: return resp['data']['shareCode'],resp['data']['shareURL']
    except: pass
    return None,None

# === DEDUPLICATION ===
def load_dedup():
    try:
        if os.path.exists(DEDUP_FILE):
            with open(DEDUP_FILE) as f: return json.load(f)
    except: pass
    return {'last_hash':'','last_time':0,'sent_eids':{}}

def save_dedup(dd):
    try:
        with open(DEDUP_FILE,'w') as f: json.dump(dd,f)
    except: pass

def make_picks_hash(picks):
    keys=sorted([p.get('key','') for p in picks])
    return hashlib.md5('|'.join(keys).encode()).hexdigest()

def is_duplicate(picks,dd):
    h=make_picks_hash(picks)
    now=time.time()
    if h==dd.get('last_hash','') and now-dd.get('last_time',0)<1800:
        return True
    return False

def filter_already_sent_eids(picks,dd):
    now=time.time()
    sent=dd.get('sent_eids',{})
    sent={k:v for k,v in sent.items() if now-v<3600}
    dd['sent_eids']=sent
    return [p for p in picks if p.get('eventId','') not in sent]

def mark_sent(picks,dd):
    h=make_picks_hash(picks)
    now=time.time()
    dd['last_hash']=h
    dd['last_time']=now
    for p in picks:
        eid=p.get('eventId','')
        if eid: dd['sent_eids'][eid]=now
    save_dedup(dd)

# === FEEDBACK ===
_fb={'bl':{},'pen':{},'cold':[]}
try:
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE) as f: _fb=json.load(f)
        print('Feedback: '+str(len(_fb.get('bl',{})))+'bl '+str(len(_fb.get('pen',{})))+'pen cold:'+str(_fb.get('cold',[])))
except: pass

def is_bl(mu,hr):
    bl=_fb.get('bl',{})
    return mu in bl and abs(bl[mu]-hr)<=1

def get_pen(mu,hr):
    pen=_fb.get('pen',{})
    return 3 if mu in pen and abs(pen[mu]-hr)<=1 else 0

def is_cold(hr): return hr in _fb.get('cold',[])

def log_picks(picks,layer):
    try:
        log=[]
        if os.path.exists(PICKS_LOG):
            with open(PICKS_LOG) as f: log=json.load(f)
        now_wat=datetime.now(WAT)
        for p in picks:
            log.append({'key':p.get('key',''),'layer':layer,'hour':now_wat.hour,'date':now_wat.strftime('%Y-%m-%d'),'time':now_wat.strftime('%H:%M'),'score':p.get('score',0)})
        with open(PICKS_LOG,'w') as f: json.dump(log[-500:],f)
    except: pass

def score_12layer(key, hist_data, live_score=None):
    hist=hist_data.get(key,[])
    elite_rate=elite_lookup.get(key,(None,None))[1]
    n=len(hist)
    cur_hr=datetime.now(WAT).hour
    if is_bl(key, cur_hr): return 0,'BLACKLISTED',0,0,0
    if n>=3:
        o05_pct=sum(1 for m in hist if m['tg']>=1)/n*100
        o15_pct=sum(1 for m in hist if m['o15'])/n*100
        btts_pct=sum(1 for m in hist if m['btts'])/n*100
        zz_pct=sum(1 for m in hist if m['zz'])/n*100
        avg_goals=sum(m['tg'] for m in hist)/n
        r3_over=sum(1 for m in hist[-3:] if m['o15'])
        prev=hist[-1]
    elif elite_rate is not None:
        o15_pct=elite_rate; o05_pct=min(98,elite_rate+15)
        btts_pct=elite_rate*0.7; zz_pct=max(0,100-o05_pct)
        avg_goals=1.5+(elite_rate-70)*0.03
        r3_over=2 if elite_rate>80 else 1; n=10
        prev=live_score if live_score else {'tg':2,'hg':1,'ag':1}
    else: return 0,'SKIP',0,0,0
    if o05_pct<90 or o15_pct<60 or zz_pct>10: return 0,'SKIP',0,0,0
    if r3_over<=1 and n>=3: return 0,'SKIP',0,0,0
    score=0
    if o05_pct>90: score+=2
    if o15_pct>75: score+=3
    elif o15_pct>60: score+=2
    over_trend=r3_over>=2 if n>=3 else (elite_rate and elite_rate>80)
    if over_trend: score+=1
    if btts_pct>65: score+=2
    elif btts_pct>50: score+=1
    if o15_pct>65: score+=1
    if btts_pct>55: score+=1
    if zz_pct<5: score+=1
    prev_tg=prev.get('tg',0) if prev else 0
    if prev_tg>=3: score+=1
    if prev and prev.get('tg',0)>=2: score+=1
    if avg_goals>2.0: score+=1
    if o15_pct>88: score-=1
    if elite_rate:
        if elite_rate>=90: score+=2
        elif elite_rate>=80: score+=1
    penalty=get_pen(key, cur_hr)
    if penalty>0: score-=penalty
    if is_cold(cur_hr) and score<9:
        return score,'COLD_SKIP',round(o15_pct,1),round(btts_pct,1),round(avg_goals,1)
    if score>=11: cat='LOCK_IT'
    elif score>=9: cat='PICK_IT'
    elif score>=7: cat='CONSIDER'
    else: cat='LOW'
    return score,cat,round(o15_pct,1),round(btts_pct,1),round(avg_goals,1)

print('='*50)
print('  LAYER 2 v4 - 12-Layer + FEEDBACK + DEDUP')
print('='*50)
now_ms=int(time.time()*1000)
now_s=datetime.now(WAT).strftime('%H:%M:%S')
cur_hr=datetime.now(WAT).hour
dd=load_dedup()
print('Time: '+now_s+' WAT | Hour: '+str(cur_hr))

# Fetch results
print('\n[1] Fetching results...')
matchup_history={}
for attempt in range(3):
    try:
        url='https://www.sportybet.com/api/ng/factsCenter/eventResultList?pageNum=1&pageSize=50&sportId='+SPORT+'&_t='+str(now_ms+attempt)
        txt=fetch(url,timeout=10)
        resp=json.loads(txt)
        if resp.get('bizCode')==10000:
            events=resp.get('data',{}).get('list',[])
            for e in events:
                home=e.get('homeTeamName','?'); away=e.get('awayTeamName','?')
                league=get_league(home,away)
                if not league: continue
                key=mk(home,away)
                scores=e.get('setScore','').split(':')
                if len(scores)==2:
                    try: hg,ag=int(scores[0]),int(scores[1])
                    except: continue
                    if key not in matchup_history: matchup_history[key]=[]
                    matchup_history[key].append({'tg':hg+ag,'hg':hg,'ag':ag,'o15':hg+ag>=2,'btts':hg>0 and ag>0,'zz':hg+ag==0,'league':league})
            print('  Loaded '+str(len(events))+' results')
            break
    except:
        time.sleep(1)
if not matchup_history:
    print('  Results API down - using ELITE fallback only')

# Scan live
print('\n[2] Scanning live events...')
try:
    api='https://www.sportybet.com/api/ng/factsCenter/liveOrPrematchEvents?sportId='+SPORT+'&_t='+str(now_ms)
    txt=fetch(api)
    resp=json.loads(txt)
    league_data={}; league_info={}; event_details={}; live_scores={}; total_events=0
    if resp.get('bizCode')==10000:
        tournaments=resp.get('data',[])
        if isinstance(tournaments,dict): tournaments=tournaments.get('tournaments',[])
        for t in tournaments:
            for e in t.get('events',[]):
                total_events+=1
                est=e.get('estimateStartTime',0)
                if isinstance(est,str): est=int(est)
                eid=e.get('eventId','')
                eid_num=int(eid.replace('sr:match:','')) if 'sr:match:' in eid else 0
                home=e.get('homeTeamName','?'); away=e.get('awayTeamName','?')
                league=get_league(home,away)
                if not league: continue
                key=mk(home,away)
                # STRICT FILTER: Skip matches already deep in play (>5 min)
                played=e.get('playedSeconds','0:00')
                try: played_min=int(played.split(':')[0])
                except: played_min=0
                if played_min>5: continue  # Skip past/in-play matches
                ss=e.get('setScore','')
                if ss and ':' in ss:
                    try:
                        sh,sa=ss.split(':')
                        live_scores[key]={'hg':int(sh),'ag':int(sa),'tg':int(sh)+int(sa)}
                    except: pass
                o15_odds=None
                for m in e.get('markets',[]):
                    if m.get('desc')=='O/U' and m.get('specifier')=='total=1.5':
                        for o in m.get('outcomes',[]):
                            if o.get('id')=='12': o15_odds=o.get('odds')
                        break
                event_details[key]={'eventId':eid,'home':home,'away':away,'odds':o15_odds,'est':est,'league':league}
                if league not in league_info: league_info[league]={'max_eid':0,'count':0}
                if eid_num>league_info[league]['max_eid']: league_info[league]['max_eid']=eid_num
                league_info[league]['count']+=1
                if league not in league_data: league_data[league]={'max_est':0,'matchups':[]}
                if est>league_data[league]['max_est']:
                    league_data[league]['max_est']=est
                    league_data[league]['kick_s']=datetime.fromtimestamp(est/1000,tz=WAT).strftime('%H:%M')
                    league_data[league]['matchups']=[]
                if est==league_data[league]['max_est']:
                    league_data[league]['matchups'].append(key)
    print('  '+str(total_events)+' events scanned (filtered to fresh only)')

    # Score
    print('\n[3] Scoring next round...')
    picks=[]; skipped=0
    for league,ld in league_data.items():
        next_est=ld['max_est']+CYCLE*60*1000
        mins_until=(next_est-now_ms)/60000.0
        next_kick=datetime.fromtimestamp(next_est/1000,tz=WAT).strftime('%H:%M')
        if mins_until<0 or mins_until>AW: continue
        for key in ld['matchups']:
            live=live_scores.get(key)
            sc,cat,o15p,btp,avg=score_12layer(key,matchup_history,live)
            if cat=='BLACKLISTED': skipped+=1; continue
            if cat=='COLD_SKIP': skipped+=1; continue
            if cat in ('LOCK_IT','PICK_IT','CONSIDER'):
                ev=event_details.get(key,{})
                er=elite_lookup.get(key,(None,None))[1]
                momentum=live.get('tg',0)>=3 if live else False
                prev_str=str(live.get('hg','?'))+':'+str(live.get('ag','?')) if live else '?:?'
                picks.append({'key':key,'league':league,'score':sc,'category':cat,'o15_pct':o15p,'btts_pct':btp,'avg_goals':avg,'prev_score':prev_str,'momentum':momentum,'elite_rate':er,'kick':next_kick,'mins':round(mins_until,1),'eventId':ev.get('eventId',''),'odds':ev.get('odds',''),'flag':FLAG.get(league,'')})
    if skipped: print('  Feedback skipped: '+str(skipped))

    # DEDUP: Remove already-sent event IDs
    picks=filter_already_sent_eids(picks,dd)
    print('  Qualified (after dedup): '+str(len(picks)))

    # Prematch probe
    print('\n[4] Probing prematch...')
    prematch_picks=[]
    if league_info:
        for lg,info in league_info.items():
            for rnd in range(1,6):
                start_eid=info['max_eid']+1+(rnd-1)*info['count']
                sels=[{'eventId':'sr:match:'+str(start_eid+i),'marketId':18,'specifier':'total=1.5','outcomeId':'12'} for i in range(info['count'])]
                payload=json.dumps({"selections":sels,"sportId":SPORT}).encode()
                resp2=fetch_json(BOOK_URL,data=payload)
                if not resp2: break
                outcomes=resp2.get('data',{}).get('outcomes',[])
                if not outcomes: break
                for oc in outcomes:
                    home=oc.get('homeTeamName',''); away=oc.get('awayTeamName','')
                    eid=oc.get('eventId',''); ko=oc.get('estimateStartTime',0)
                    key=mk(home,away)
                    o15_odds=None
                    for mkt in oc.get('markets',[]):
                        if str(mkt.get('id'))=='18':
                            for out in mkt.get('outcomes',[]):
                                if str(out.get('id'))=='12': o15_odds=out.get('odds')
                    sc,ct,o15p,btp,avg=score_12layer(key,matchup_history)
                    if ct in ('LOCK_IT','PICK_IT','CONSIDER'):
                        prematch_picks.append({'key':key,'league':lg,'score':sc,'category':ct,'eventId':eid,'odds':str(o15_odds) if o15_odds else '1.27','ko_est':ko,'round':rnd})
                time.sleep(0.3)
        # DEDUP: Filter prematch too
        prematch_picks=filter_already_sent_eids(prematch_picks,dd)
        prematch_picks.sort(key=lambda x:(0 if x['category']=='LOCK_IT' else 1,-x['score']))
        print('  Found '+str(len(prematch_picks))+' prematch (after dedup)')

    # Send
    print('\n[5] Sending...')
    if picks:
        # DEDUP CHECK: Skip if exact same picks already sent recently
        if is_duplicate(picks,dd):
            print('  DEDUP: Same picks already sent recently - SKIP')
        else:
            picks.sort(key=lambda x:(0 if x['category']=='LOCK_IT' else 1,-x['score']))
            combo=1.0
            for p in picks:
                if p['odds']:
                    try: combo*=float(p['odds'])
                    except: pass
            bk_sels=[{'eventId':p['eventId'],'odds':p['odds']} for p in picks if p['eventId'] and p['odds']]
            book_code,book_url=create_booking_code(bk_sels)
            if not book_code and prematch_picks:
                pm_sels=[{'eventId':p['eventId'],'odds':p['odds']} for p in prematch_picks[:15]]
                book_code,book_url=create_booking_code(pm_sels)
            by_lg={}
            for p in picks:
                if p['league'] not in by_lg: by_lg[p['league']]=[]
                by_lg[p['league']].append(p)
            lines=['<b>🧠 LAYER 2 v4 - 12-Layer+DEDUP</b>','🕒 '+now_s+' WAT | Over 1.5','']
            if skipped: lines.append('🧠 Feedback: '+str(skipped)+' skipped'); lines.append('')
            for lg in sorted(by_lg.keys()):
                lp=by_lg[lg]
                lines.append(FLAG.get(lg,'')+' <b>'+lg+'</b> - '+lp[0]['kick']+' (~'+str(int(lp[0]['mins']))+'min)')
                for p in lp:
                    ic='🔒' if p['category']=='LOCK_IT' else ('🎯' if p['category']=='PICK_IT' else '💡')
                    o_str=' @'+str(p['odds']) if p['odds'] else ''
                    m_str='🔥' if p['momentum'] else ''
                    e_str='⭐' if p['elite_rate'] and p['elite_rate']>=90 else ''
                    lines.append('  '+ic+' '+p['key']+' ['+str(p['score'])+'pts]'+o_str+' '+m_str+e_str)
                    lines.append('    O1.5:'+str(p['o15_pct'])+'% BTTS:'+str(p['btts_pct'])+'% Avg:'+str(p['avg_goals'])+'g')
                lines.append('')
            lines.append('✅ '+str(len(picks))+' picks | Odds: <b>'+str(round(combo,2))+'</b>')
            if book_code and book_url:
                lines.append(''); lines.append('🎫 <b>ONE-TAP BET (L2):</b>')
                lines.append('Code: <code>'+book_code+'</code>')
                lines.append('<a href="'+book_url+'">👉 TAP TO LOAD BETSLIP</a>')
            lines.append(''); lines.append('🧠 v4 Dedup+Feedback')
            msg='\n'.join(lines)
            if len(msg)>4000:
                top=picks[:8]
                lines=['<b>🧠 L2 Top 8</b> '+now_s+' WAT','']
                for p in top: lines.append(p['flag']+' '+p['key']+' ['+str(p['score'])+'] @'+str(p.get('odds','')))
                if book_code: lines.append('🎫 <code>'+book_code+'</code>'); lines.append('<a href="'+book_url+'">👉 BETSLIP</a>')
                msg='\n'.join(lines)
            if send_tg(msg):
                print('  SENT '+str(len(picks))+' picks')
                mark_sent(picks,dd)
            log_picks(picks,'L2')
    elif prematch_picks:
        # DEDUP CHECK for prematch
        if is_duplicate(prematch_picks,dd):
            print('  DEDUP: Same prematch already sent - SKIP')
        else:
            print('  No live - delivering prematch')
            top_pm=prematch_picks[:20]
            combo=1.0
            for p in top_pm:
                try: combo*=float(p['odds'])
                except: pass
            pm_sels=[{'eventId':p['eventId'],'odds':p['odds']} for p in top_pm]
            book_code,book_url=create_booking_code(pm_sels)
            by_lg={}
            for p in top_pm:
                if p['league'] not in by_lg: by_lg[p['league']]=[]
                by_lg[p['league']].append(p)
            lines=['<b>🧠 L2 PREMATCH v4</b>','🕒 '+now_s+' WAT','']
            for lg in sorted(by_lg.keys()):
                lp=by_lg[lg]
                lines.append(FLAG.get(lg,'')+' <b>'+lg+'</b>')
                for p in lp:
                    ic='🔒' if p['category']=='LOCK_IT' else '🎯'
                    ko_str=''
                    if p.get('ko_est'): ko_str=' ⏰'+datetime.fromtimestamp(p['ko_est']/1000,tz=WAT).strftime('%H:%M')
                    lines.append('  '+ic+' '+p['key']+' ['+str(p['score'])+'pts] @'+p['odds']+ko_str)
                lines.append('')
            lines.append('✅ '+str(len(top_pm))+' picks | Odds: <b>'+str(round(combo,2))+'</b>')
            if book_code and book_url:
                lines.append(''); lines.append('🎫 <b>ONE-TAP BET (L2):</b>')
                lines.append('Code: <code>'+book_code+'</code>')
                lines.append('<a href="'+book_url+'">👉 TAP TO LOAD BETSLIP</a>')
            lines.append(''); lines.append('🧠 v4 Dedup+Feedback Prematch')
            msg='\n'.join(lines)
            if len(msg)>4000:
                lines=['<b>🧠 L2 PRE Top 8</b> '+now_s,'']
                for p in top_pm[:8]: lines.append(FLAG.get(p['league'],'')+' '+p['key']+' @'+p['odds'])
                if book_code: lines.append('🎫 <code>'+book_code+'</code>')
                msg='\n'.join(lines)
            if send_tg(msg):
                print('  SENT '+str(len(top_pm))+' prematch')
                mark_sent(top_pm,dd)
            log_picks(top_pm,'L2')
    else:
        # NO "no picks" message - just exit silently to save credits
        print('  No qualified picks - silent exit (no TG spam)')

except Exception as ex:
    print('ERROR: '+str(ex))
    import traceback; traceback.print_exc()

print('\nLAYER 2 v4 DEDUP DONE')
