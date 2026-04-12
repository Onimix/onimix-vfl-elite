import urllib.request,json,ssl,time,os,hashlib
from datetime import datetime,timezone,timedelta

TGTOKEN='8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8'
CHAT='1745848158'
SPORT='sr:sport:202120001'
AW=20; CYCLE=38
WAT=timezone(timedelta(hours=1))
BOOK_URL='https://www.sportybet.com/api/ng/orders/share'
FEEDBACK_FILE='/tmp/vfl_scanner_feedback.json'
PICKS_LOG='/tmp/vfl_picks_log.json'
DEDUP_FILE='/tmp/vfl_dedup_L1.json'

ctx=ssl.create_default_context()
ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

ENG_T=set('ARS,AST,BRE,CHE,CRY,FOR,LIV,MUN,NEW,SUN,WOL,BUR,FUL,TOT,WHU,BOU,BHA,LEE,EVE,MCI'.split(','))
ESP_T=set('ATM,BAR,BET,CEL,GIR,GET,MAL,OSA,RAY,RSO,SEV,VAL,VIL,ALA,CAD,ALM,GRA,LPA,ALC,ESP,RMA,ELC,LEV,VCF,BIL,FCB,OVI,RBB'.split(','))
ITA_T=set('ATA,BFC,CAG,LEC,PAR,PIS,ROM,SAS,TOR,VER,COM,NAP,USC,ACM,LAZ,FIO,GEN,JUV,INT,UDI,MON'.split(','))
GER_T=set('BMU,BVB,HDH,LEV,MAI,SCF,SGE,STP,WOB,KOE,RBL,SVW,HSV,BMG,UNI,TSG,VFB,FCA,BAY,KIE'.split(','))
FRA_T=set('ANG,LEN,LOR,NCE,OLM,PFC,PSG,REN,STR,NAN,LEH,B29,MET,AUX,LIL,LYO,TOU,AMO'.split(','))

ELITE_RAW='{"England":{"AST vs ARS":97.6,"NEW vs LEE":95.2,"CHE vs NEW":95.1,"AST vs NEW":92.9,"BHA vs LEE":92.9,"CRY vs SUN":92.9,"CRY vs LEE":92.9,"CRY vs NEW":92.9,"MUN vs EVE":92.9,"NEW vs MCI":92.9,"ARS vs SUN":92.7,"CRY vs ARS":92.7,"AST vs BRE":90.5,"BOU vs CHE":90.5,"BOU vs SUN":90.5,"BOU vs LEE":90.5,"BOU vs ARS":90.5,"CHE vs LIV":90.5,"CHE vs MCI":90.5,"CHE vs BRE":90.5,"CRY vs MCI":90.5,"FOR vs LIV":90.5,"LIV vs BRE":90.5,"LIV vs MUN":90.5,"MCI vs EVE":90.5,"NEW vs CHE":90.5,"TOT vs LIV":90.5,"AST vs BOU":90.2,"MCI vs LIV":90.2,"MCI vs NEW":88.4,"AST vs WHU":88.1,"AST vs SUN":88.1,"BHA vs MCI":88.1,"CHE vs ARS":88.1,"CHE vs CRY":88.1,"CRY vs CHE":88.1,"FOR vs MUN":88.1,"LIV vs MCI":88.1,"LIV vs WOL":88.1,"MCI vs BRE":88.1,"MUN vs TOT":88.1,"NEW vs WHU":88.1,"NEW vs FOR":88.1,"NEW vs BOU":88.1,"TOT vs WHU":88.1,"WHU vs BRE":88.1,"ARS vs MCI":88.1,"CRY vs WHU":88.1,"AST vs TOT":87.8,"BOU vs NEW":87.8,"CHE vs WHU":87.8,"CHE vs BUR":87.8,"CRY vs BRE":87.8,"WHU vs NEW":87.8,"WOL vs BUR":87.8,"MUN vs SUN":86.0,"ARS vs TOT":85.7,"ARS vs EVE":85.7,"ARS vs LEE":85.7,"AST vs CHE":85.7,"AST vs MCI":85.7,"BOU vs WHU":85.7,"BRE vs SUN":85.7,"BRE vs BUR":85.7,"CHE vs SUN":85.7,"CRY vs BUR":85.7,"CRY vs TOT":85.7,"EVE vs MCI":85.7,"FOR vs NEW":85.7,"FOR vs BRE":85.7,"FUL vs BOU":85.7,"LIV vs WHU":85.7,"MUN vs LEE":85.7,"MUN vs LIV":85.7,"NEW vs EVE":85.7,"NEW vs FUL":85.7,"NEW vs TOT":85.7,"TOT vs NEW":85.7,"TOT vs CRY":85.7,"TOT vs FOR":85.7,"TOT vs MCI":85.7,"WHU vs CHE":85.7,"WOL vs NEW":85.7,"AST vs LIV":85.4,"BHA vs MUN":85.4,"FOR vs SUN":85.4,"MCI vs ARS":85.4,"ARS vs CRY":83.3,"ARS vs CHE":83.3,"AST vs WOL":83.3,"AST vs LEE":83.3,"BHA vs CRY":83.3,"BOU vs MCI":83.3,"BRE vs WHU":83.3,"CHE vs TOT":83.3,"CRY vs WOL":83.3,"FOR vs MCI":83.3,"FOR vs ARS":83.3,"LEE vs FOR":83.3,"LIV vs NEW":83.3,"MCI vs BUR":83.3,"MUN vs AST":83.3,"MUN vs WHU":83.3,"MUN vs FUL":83.3,"MUN vs FOR":83.3,"NEW vs AST":83.3,"NEW vs SUN":83.3,"NEW vs WOL":83.3,"NEW vs LIV":83.3,"NEW vs BUR":83.3,"TOT vs LEE":83.3,"TOT vs ARS":83.3,"WHU vs SUN":83.3,"WOL vs BOU":83.3,"WOL vs CRY":83.3,"WOL vs WHU":83.3,"BRE vs WOL":83.3,"CHE vs AST":83.3,"AST vs MUN":82.9,"CHE vs FUL":82.9,"CRY vs BOU":82.9,"CRY vs MUN":82.9,"EVE vs CHE":82.9,"FOR vs WHU":82.9,"LIV vs SUN":82.9,"MCI vs MUN":82.9,"CHE vs BHA":81.4,"AST vs BUR":81.0,"BHA vs CHE":81.0,"BHA vs WHU":81.0,"BOU vs TOT":81.0,"BOU vs EVE":81.0,"BOU vs FUL":81.0,"BOU vs FOR":81.0,"BRE vs LEE":81.0,"BUR vs NEW":81.0,"BUR vs CHE":81.0,"CHE vs BOU":81.0,"CRY vs BHA":81.0,"CRY vs AST":81.0,"CRY vs FUL":81.0,"CRY vs FOR":81.0,"FUL vs NEW":81.0,"LEE vs NEW":81.0,"LIV vs TOT":81.0,"LIV vs FUL":81.0,"MCI vs BOU":81.0,"MUN vs CRY":81.0,"TOT vs BRE":81.0,"TOT vs WOL":81.0,"TOT vs BUR":81.0,"WHU vs MCI":81.0,"LIV vs BOU":81.0,"BHA vs NEW":80.5,"BRE vs MUN":80.5,"FOR vs BUR":80.5,"LIV vs BUR":80.5,"MCI vs TOT":80.5},"France":{"REN vs LOR":92.9,"PSG vs NCE":92.7,"PSG vs AMO":92.7,"PSG vs LOR":90.7,"AUX vs LOR":90.5,"LYO vs AMO":90.5,"LEN vs PSG":90.2,"LIL vs PFC":90.2,"LIL vs LOR":90.2,"NAN vs MET":90.2,"TOU vs LYO":90.2,"LEN vs LOR":88.1,"LIL vs LYO":88.1,"LOR vs AMO":87.8,"LYO vs ANG":87.8,"TOU vs LOR":87.8,"AUX vs B29":85.7,"LOR vs PSG":85.7,"LYO vs STR":85.7,"NAN vs STR":85.7,"NCE vs AMO":85.7,"OLM vs MET":85.7,"OLM vs PFC":85.7,"PSG vs LYO":85.7,"PSG vs ANG":85.7,"PSG vs MET":85.7,"REN vs OLM":85.7,"TOU vs STR":85.7,"LOR vs MET":85.4,"NCE vs PFC":85.4,"NCE vs LOR":85.4,"PFC vs LEH":85.4,"PSG vs LEH":85.4,"STR vs LOR":85.4,"LYO vs MET":85.4,"AMO vs B29":83.3,"ANG vs LYO":83.3,"LEN vs NCE":83.3,"LIL vs NCE":83.3,"LOR vs ANG":83.3,"LOR vs TOU":83.3,"NAN vs AMO":83.3,"NAN vs B29":83.3,"OLM vs LOR":83.3,"OLM vs LIL":83.3,"REN vs AMO":83.3,"LIL vs REN":82.9,"NCE vs REN":82.9,"PFC vs REN":82.9,"STR vs PFC":82.9,"STR vs REN":82.9,"TOU vs MET":82.9,"ANG vs NCE":81.0,"AUX vs MET":81.0,"LEN vs MET":81.0,"LIL vs OLM":81.0,"LIL vs AMO":81.0,"LOR vs B29":81.0,"MET vs LYO":81.0,"PFC vs LIL":81.0,"PSG vs PFC":81.0,"PSG vs LIL":81.0,"REN vs PSG":81.0,"TOU vs AMO":81.0,"ANG vs AMO":81.0,"AUX vs AMO":80.5,"LEN vs LEH":80.5,"LEN vs AMO":80.5,"LIL vs MET":80.5,"LYO vs LOR":80.5,"LYO vs B29":80.5,"MET vs OLM":80.5,"NAN vs PFC":80.5,"NCE vs TOU":80.5,"OLM vs STR":80.5,"STR vs LYO":80.5,"OLM vs TOU":80.5},"Spain":{"SEV vs CEL":85.4,"CEL vs ALM":82.9,"CEL vs VIL":82.9,"CEL vs CAD":82.9,"GCF vs ATH":82.9,"RMA vs GCF":80.5,"RSO vs ALM":80.5},"Italy":{"GEN vs MON":90.2,"VER vs MON":87.8,"INT vs MON":87.8,"LAZ vs LEC":87.8,"NAP vs MON":87.5,"ROM vs LEC":87.5,"ROM vs MON":87.5,"VER vs LEC":87.5,"INT vs LEC":85.4,"LAZ vs MON":85.4,"NAP vs LEC":85.4,"JUV vs LEC":85.4,"GEN vs LEC":85.0,"MIL vs MON":85.0,"FIO vs MON":85.0,"COM vs MON":82.9,"INT vs COM":82.9,"LAZ vs SAL":82.9,"MIL vs LEC":82.9,"ATA vs MON":82.9,"NAP vs SAL":82.5,"ROM vs SAL":82.5,"FIO vs LEC":80.5,"GEN vs SAL":80.5,"JUV vs MON":80.5,"LAZ vs COM":80.5,"NAP vs COM":80.5,"ROM vs COM":80.5,"TOR vs MON":80.5,"VER vs SAL":80.5,"ATA vs LEC":80.5,"COM vs LEC":80.0,"INT vs SAL":80.0},"Germany":{"BAY vs KIE":94.1,"BVB vs KIE":94.1,"FCA vs KIE":91.2,"RBL vs KIE":91.2,"WOB vs KIE":91.2,"BMG vs KIE":91.2,"SCF vs KIE":91.2,"SGE vs KIE":91.2,"TSG vs KIE":91.2,"VFB vs KIE":91.2,"BAY vs BOC":88.2,"BVB vs BOC":88.2,"FCA vs BOC":88.2,"M05 vs KIE":88.2,"BAY vs HSV":88.2,"FCA vs HSV":87.8,"BVB vs HSV":87.8,"RBL vs BOC":85.3,"SCF vs BOC":85.3,"SGE vs BOC":85.3,"TSG vs BOC":85.3,"VFB vs BOC":85.3,"WOB vs BOC":85.3,"BMG vs BOC":85.3,"BAY vs SVD":85.3,"BVB vs SVD":85.3,"FCA vs SVD":85.3,"RBL vs HSV":85.3,"VFB vs HSV":85.4,"WOB vs HSV":85.3,"M05 vs BOC":85.3,"FCA vs BMU":84.8,"RBL vs HSV2":82.4,"SCF vs HSV":82.4,"SGE vs HSV":82.4,"TSG vs HSV":82.4,"BMG vs HSV":82.4,"BAY vs BMU":82.4,"BVB vs BMU":82.4,"RBL vs SVD":82.4,"SCF vs SVD":82.4,"SGE vs SVD":82.4,"TSG vs SVD":82.4,"VFB vs SVD":82.4,"WOB vs SVD":82.4,"BMG vs SVD":82.4,"M05 vs HSV":82.4,"M05 vs SVD":82.4,"VFB vs BMU":85.4,"FCA vs BMU2":82.4,"RBL vs KIE2":82.4,"RBL vs BMU":82.4,"SCF vs BMU":82.4,"SGE vs BMU":82.4,"TSG vs BMU":82.4,"WOB vs BMU":82.4,"BMG vs BMU":82.4,"M05 vs BMU":82.4,"BAY vs STP":82.4,"BVB vs STP":82.4,"FCA vs STP":82.4,"RBL vs STP":82.4,"SCF vs STP":82.4,"SGE vs STP":82.4,"TSG vs STP":82.4,"VFB vs STP":82.4,"WOB vs STP":82.4,"BMG vs STP":82.4,"M05 vs STP":82.4,"BAY vs FCU":80.6,"BVB vs FCU":80.6,"FCA vs FCU":80.6,"SGE vs FCU":80.6,"RBL vs FCU":80.6,"VFB vs FCU":80.6,"SCF vs FCU":80.6,"WOB vs FCU":80.6,"TSG vs FCU":80.6}}'
elite=json.loads(ELITE_RAW)
elite_lookup=dict()
for league,matchups in elite.items():
    for mu,rate in matchups.items():
        elite_lookup[mu]=(league,rate)
print('ELITE: '+str(len(elite_lookup))+' matchups')

def get_league(home,away):
    h3=home[:3].upper(); a3=away[:3].upper()
    if h3 in ENG_T or a3 in ENG_T: return 'England'
    if h3 in ESP_T or a3 in ESP_T: return 'Spain'
    if h3 in ITA_T or a3 in ITA_T: return 'Italy'
    if h3 in GER_T or a3 in GER_T: return 'Germany'
    if h3 in FRA_T or a3 in FRA_T: return 'France'
    return None

def fetch(url,timeout=20):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','Referer':'https://www.sportybet.com/ng/virtual'})
    with urllib.request.urlopen(req,context=ctx,timeout=timeout) as r:
        return r.read().decode()

def fetch_json(url,data=None,retries=2):
    for attempt in range(retries):
        try:
            h={'User-Agent':'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36','Accept':'application/json'}
            if data: h['Content-Type']='application/json'; h['Referer']='https://www.sportybet.com/ng/virtual'; h['Origin']='https://www.sportybet.com'
            req=urllib.request.Request(url,data=data,headers=h,method='POST' if data else 'GET')
            with urllib.request.urlopen(req,context=ctx,timeout=15) as r:
                return json.loads(r.read().decode())
        except:
            if attempt<retries-1: time.sleep(0.5)
    return None

def send_tg(msg):
    d=json.dumps(dict(chat_id=CHAT,text=msg,parse_mode='HTML')).encode()
    req=urllib.request.Request('https://api.telegram.org/bot'+TGTOKEN+'/sendMessage',data=d,headers={'Content-Type':'application/json'},method='POST')
    try: urllib.request.urlopen(req,context=ctx,timeout=15); return True
    except: return False

def create_booking_code(selections):
    if not selections: return None, None
    payload={"selections":[{"eventId":s["eventId"],"marketId":"18","specifier":"total=1.5","outcomeId":"12","odds":s.get("odds","1.27")} for s in selections]}
    try:
        resp=fetch_json(BOOK_URL,data=json.dumps(payload).encode())
        if resp and resp.get('bizCode')==10000:
            return resp['data']['shareCode'],resp['data']['shareURL']
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
    keys=sorted([p.get('mu','') for p in picks])
    return hashlib.md5('|'.join(keys).encode()).hexdigest()

def is_duplicate(picks,dd):
    h=make_picks_hash(picks)
    now=time.time()
    # Same picks sent within last 30 min = duplicate
    if h==dd.get('last_hash','') and now-dd.get('last_time',0)<1800:
        return True
    return False

def filter_already_sent_eids(picks,dd):
    """Remove picks whose event IDs were already sent recently"""
    now=time.time()
    sent=dd.get('sent_eids',{})
    # Clean old entries (>60min)
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
_feedback = {'bl': {}, 'pen': {}, 'cold': []}
try:
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE) as _ff: _feedback = json.load(_ff)
        print('Feedback: '+str(len(_feedback.get('bl',{})))+' blacklisted, '+str(len(_feedback.get('pen',{})))+' penalized')
except: print('Feedback load failed')

def is_blacklisted(mu, hour):
    bl = _feedback.get('bl', {})
    return mu in bl and abs(bl[mu] - hour) <= 1

def get_penalty(mu, hour):
    pen = _feedback.get('pen', {})
    return 3 if mu in pen and abs(pen[mu] - hour) <= 1 else 0

def is_cold_hour(hour):
    return hour in _feedback.get('cold', [])

def log_picks(picks, layer):
    try:
        log = []
        if os.path.exists(PICKS_LOG):
            with open(PICKS_LOG) as f: log = json.load(f)
        now_wat = datetime.now(WAT)
        for p in picks:
            log.append({'key':p.get('mu',''),'layer':layer,'hour':now_wat.hour,
                        'date':now_wat.strftime('%Y-%m-%d'),'time':now_wat.strftime('%H:%M'),
                        'rate':p.get('rate',0),'eid':p.get('eventId','')})
        with open(PICKS_LOG,'w') as f: json.dump(log[-500:], f)
    except: pass

FLAG=dict(England='🏴',Spain='🇪🇸',Italy='🇮🇹',Germany='🇩🇪',France='🇫🇷')

now_ms=int(time.time()*1000)
now_s=datetime.now(WAT).strftime('%H:%M:%S')
cur_hour=datetime.now(WAT).hour
dd=load_dedup()
print('Layer 1 v7 DEDUP | AW:'+str(AW)+'min | '+now_s+' WAT')

try:
    api='https://www.sportybet.com/api/ng/factsCenter/liveOrPrematchEvents?sportId='+SPORT+'&_t='+str(now_ms)
    txt=fetch(api)
    resp=json.loads(txt)
    league_data=dict(); league_info=dict(); event_details=dict(); total_events=0
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
                if league is None: continue
                h3=home[:3].upper(); a3=away[:3].upper()
                mu=h3+' vs '+a3
                # STRICT FILTER: Skip matches already deep in play (>5 min)
                played=e.get('playedSeconds','0:00')
                try: played_min=int(played.split(':')[0])
                except: played_min=0
                if played_min>5:
                    continue  # Skip past/in-play matches
                over15_odds=None
                for m in e.get('markets',[]):
                    if m.get('desc')=='O/U' and m.get('specifier')=='total=1.5':
                        for o in m.get('outcomes',[]):
                            if o.get('id')=='12': over15_odds=o.get('odds')
                        break
                event_details[mu]={'eventId':eid,'home':home,'away':away,'odds':over15_odds,'est':est}
                if league not in league_info: league_info[league]={'max_eid':0,'count':0}
                if eid_num > league_info[league]['max_eid']: league_info[league]['max_eid']=eid_num
                league_info[league]['count']+=1
                if league not in league_data: league_data[league]=dict(max_est=0,matchups=[])
                if est>league_data[league]['max_est']:
                    league_data[league]['max_est']=est
                    league_data[league]['kick_s']=datetime.fromtimestamp(est/1000,tz=WAT).strftime('%H:%M')
                    league_data[league]['matchups']=[]
                if est==league_data[league]['max_est']:
                    league_data[league]['matchups'].append(mu)
    print('Scanned '+str(total_events)+' events (filtered to fresh only)')

    alerts=[]
    skipped_bl=0; skipped_cold=0
    for league,ld in league_data.items():
        next_est=ld['max_est']+CYCLE*60*1000
        mins_until=(next_est-now_ms)/60000.0
        next_kick_s=datetime.fromtimestamp(next_est/1000,tz=WAT).strftime('%H:%M')
        if mins_until<0 or mins_until>AW: continue
        for mu in ld['matchups']:
            if mu in elite_lookup:
                lg2,rate=elite_lookup[mu]
                if is_blacklisted(mu, cur_hour): skipped_bl+=1; continue
                if is_cold_hour(cur_hour) and rate < 88: skipped_cold+=1; continue
                ev=event_details.get(mu,{})
                penalty=get_penalty(mu, cur_hour)
                alerts.append(dict(league=league,mu=mu,rate=rate,kick=next_kick_s,
                    mins=round(mins_until,1),flag=FLAG.get(league,''),
                    eventId=ev.get('eventId',''),odds=ev.get('odds',''),
                    penalty=penalty))
    
    # DEDUP: Remove already-sent event IDs
    alerts=filter_already_sent_eids(alerts,dd)
    
    if skipped_bl or skipped_cold:
        print('Feedback: '+str(skipped_bl)+' blacklisted, '+str(skipped_cold)+' cold-skipped')
    print('Found '+str(len(alerts))+' NEW ELITE picks')

    if alerts:
        # DEDUP CHECK: Skip if exact same picks already sent recently
        if is_duplicate(alerts,dd):
            print('DEDUP: Same picks already sent recently - SKIP')
        else:
            alerts.sort(key=lambda x:-x['rate'])
            booking_sels=[{'eventId':a['eventId'],'odds':a['odds']} for a in alerts if a['eventId'] and a['odds']]
            book_code,book_url=create_booking_code(booking_sels)
            combo_odds=1.0
            for a in alerts:
                if a['odds']:
                    try: combo_odds*=float(a['odds'])
                    except: pass
            by_league=dict()
            for a in alerts:
                if a['league'] not in by_league: by_league[a['league']]=[]
                by_league[a['league']].append(a)
            lines=['<b>⚽ VFL ELITE ALERT v7</b>','🕐 '+now_s+' WAT','']
            for lg in sorted(by_league.keys()):
                picks=by_league[lg]
                kick=picks[0]['kick']; mins=picks[0]['mins']
                lines.append(FLAG.get(lg,'')+' <b>'+lg+'</b> - Kickoff: '+kick+' (~'+str(int(mins))+'min)')
                for p in picks:
                    odds_str=' @ '+str(p['odds']) if p['odds'] else ''
                    pen_str=' ⚠️-3' if p.get('penalty',0) > 0 else ''
                    lines.append('  '+p['mu']+' | <b>'+str(p['rate'])+'%</b>'+odds_str+pen_str)
                lines.append('')
            lines.append('✅ '+str(len(alerts))+' ELITE Over 1.5 picks')
            if combo_odds>1: lines.append('💰 Combined: <b>'+str(round(combo_odds,2))+'</b>')
            if book_code and book_url:
                lines.append('')
                lines.append('🎫 <b>ONE-TAP BET:</b>')
                lines.append('Code: <code>'+book_code+'</code>')
                lines.append('<a href="'+book_url+'">👉 TAP TO LOAD BETSLIP</a>')
            lines.append('')
            lines.append('🧠 v7 Dedup+Feedback')
            msg='\n'.join(lines)
            if len(msg)>4000:
                top=alerts[:10]
                lines=['<b>⚽ VFL ELITE (Top 10)</b> '+now_s+' WAT','']
                for a in top: lines.append(a['flag']+' '+a['mu']+' | '+str(a['rate'])+'% @'+str(a.get('odds','')))
                if book_code: lines.append('🎫 <code>'+book_code+'</code>'); lines.append('<a href="'+book_url+'">👉 BETSLIP</a>')
                msg='\n'.join(lines)
            if send_tg(msg):
                print('SENT '+str(len(alerts))+' alerts')
                mark_sent(alerts,dd)
            log_picks(alerts, 'L1')
    else:
        # NO "no picks" message - just exit silently to save credits
        print('No new ELITE picks - silent exit (no TG spam)')
except Exception as ex:
    print('Error: '+str(ex))
    import traceback; traceback.print_exc()

print('DONE - Layer 1 v7 DEDUP')
