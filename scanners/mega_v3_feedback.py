#!/usr/bin/env python3
"""ONIMIX VFL Mega Prematch Scanner v3 + FEEDBACK LOOP"""
import urllib.request, json, ssl, time, datetime, os
from collections import defaultdict

SPORT = 'sr:sport:202120001'
TGTOKEN = '8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8'
CHAT = '1745848158'
BOOK_URL = 'https://www.sportybet.com/api/ng/orders/share'
LIVE_URL = 'https://www.sportybet.com/api/ng/factsCenter/liveOrPrematchEvents'
ROUNDS_AHEAD = 10
MIN_ULTRA = 90; MIN_PREMIUM = 88; MIN_MEGA = 85
FEEDBACK_FILE = '/tmp/vfl_scanner_feedback.json'
PICKS_LOG = '/tmp/vfl_picks_log.json'
WAT_OFFSET = datetime.timedelta(hours=1)

ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

ELITE_RAW='{"England":{"AST vs ARS":97.6,"NEW vs LEE":95.2,"CHE vs NEW":95.1,"AST vs NEW":92.9,"BHA vs LEE":92.9,"CRY vs SUN":92.9,"CRY vs LEE":92.9,"CRY vs NEW":92.9,"MUN vs EVE":92.9,"NEW vs MCI":92.9,"ARS vs SUN":92.7,"CRY vs ARS":92.7,"AST vs BRE":90.5,"BOU vs CHE":90.5,"BOU vs SUN":90.5,"BOU vs LEE":90.5,"BOU vs ARS":90.5,"CHE vs LIV":90.5,"CHE vs MCI":90.5,"CHE vs BRE":90.5,"CRY vs MCI":90.5,"FOR vs LIV":90.5,"LIV vs BRE":90.5,"LIV vs MUN":90.5,"MCI vs EVE":90.5,"NEW vs CHE":90.5,"TOT vs LIV":90.5,"AST vs BOU":90.2,"MCI vs LIV":90.2,"MCI vs NEW":88.4,"AST vs WHU":88.1,"AST vs SUN":88.1,"BHA vs MCI":88.1,"CHE vs ARS":88.1,"CHE vs CRY":88.1,"CRY vs CHE":88.1,"FOR vs MUN":88.1,"LIV vs MCI":88.1,"LIV vs WOL":88.1,"MCI vs BRE":88.1,"MUN vs TOT":88.1,"NEW vs WHU":88.1,"NEW vs FOR":88.1,"NEW vs BOU":88.1,"TOT vs WHU":88.1,"WHU vs BRE":88.1,"ARS vs MCI":88.1,"CRY vs WHU":88.1,"AST vs TOT":87.8,"BOU vs NEW":87.8,"CHE vs WHU":87.8,"CHE vs BUR":87.8,"CRY vs BRE":87.8,"WHU vs NEW":87.8,"WOL vs BUR":87.8,"MUN vs SUN":86.0,"ARS vs TOT":85.7,"ARS vs EVE":85.7,"ARS vs LEE":85.7,"AST vs CHE":85.7,"AST vs MCI":85.7,"BOU vs WHU":85.7,"BRE vs SUN":85.7,"BRE vs BUR":85.7,"CHE vs SUN":85.7,"CRY vs BUR":85.7,"CRY vs TOT":85.7,"EVE vs MCI":85.7,"FOR vs NEW":85.7,"FOR vs BRE":85.7,"FUL vs BOU":85.7,"LIV vs WHU":85.7,"MUN vs LEE":85.7,"MUN vs LIV":85.7,"NEW vs EVE":85.7,"NEW vs FUL":85.7,"NEW vs TOT":85.7,"TOT vs NEW":85.7,"TOT vs CRY":85.7,"TOT vs FOR":85.7,"TOT vs MCI":85.7,"WHU vs CHE":85.7,"WOL vs NEW":85.7,"AST vs LIV":85.4,"BHA vs MUN":85.4,"FOR vs SUN":85.4,"MCI vs ARS":85.4,"ARS vs CRY":83.3,"ARS vs CHE":83.3,"AST vs WOL":83.3,"AST vs LEE":83.3,"BHA vs CRY":83.3,"BOU vs MCI":83.3,"BRE vs WHU":83.3,"CHE vs TOT":83.3,"CRY vs WOL":83.3,"FOR vs MCI":83.3,"FOR vs ARS":83.3,"LEE vs FOR":83.3,"LIV vs NEW":83.3,"MCI vs BUR":83.3,"MUN vs AST":83.3,"MUN vs WHU":83.3,"MUN vs FUL":83.3,"MUN vs FOR":83.3,"NEW vs AST":83.3,"NEW vs SUN":83.3,"NEW vs WOL":83.3,"NEW vs LIV":83.3,"NEW vs BUR":83.3,"TOT vs LEE":83.3,"TOT vs ARS":83.3,"WHU vs SUN":83.3,"WOL vs BOU":83.3,"WOL vs CRY":83.3,"WOL vs WHU":83.3,"BRE vs WOL":83.3,"CHE vs AST":83.3,"AST vs MUN":82.9,"CHE vs FUL":82.9,"CRY vs BOU":82.9,"CRY vs MUN":82.9,"EVE vs CHE":82.9,"FOR vs WHU":82.9,"LIV vs SUN":82.9,"MCI vs MUN":82.9,"CHE vs BHA":81.4,"AST vs BUR":81.0,"BHA vs CHE":81.0,"BHA vs WHU":81.0,"BOU vs TOT":81.0,"BOU vs EVE":81.0,"BOU vs FUL":81.0,"BOU vs FOR":81.0,"BRE vs LEE":81.0,"BUR vs NEW":81.0,"BUR vs CHE":81.0,"CHE vs BOU":81.0,"CRY vs BHA":81.0,"CRY vs AST":81.0,"CRY vs FUL":81.0,"CRY vs FOR":81.0,"FUL vs NEW":81.0,"LEE vs NEW":81.0,"LIV vs TOT":81.0,"LIV vs FUL":81.0,"MCI vs BOU":81.0,"MUN vs CRY":81.0,"TOT vs BRE":81.0,"TOT vs WOL":81.0,"TOT vs BUR":81.0,"WHU vs MCI":81.0,"LIV vs BOU":81.0,"BHA vs NEW":80.5,"BRE vs MUN":80.5,"FOR vs BUR":80.5,"LIV vs BUR":80.5,"MCI vs TOT":80.5},"France":{"REN vs LOR":92.9,"PSG vs NCE":92.7,"PSG vs AMO":92.7,"PSG vs LOR":90.7,"AUX vs LOR":90.5,"LYO vs AMO":90.5,"LEN vs PSG":90.2,"LIL vs PFC":90.2,"LIL vs LOR":90.2,"NAN vs MET":90.2,"TOU vs LYO":90.2,"LEN vs LOR":88.1,"LIL vs LYO":88.1,"LOR vs AMO":87.8,"LYO vs ANG":87.8,"TOU vs LOR":87.8,"AUX vs B29":85.7,"LOR vs PSG":85.7,"LYO vs STR":85.7,"NAN vs STR":85.7,"NCE vs AMO":85.7,"OLM vs MET":85.7,"OLM vs PFC":85.7,"PSG vs LYO":85.7,"PSG vs ANG":85.7,"PSG vs MET":85.7,"REN vs OLM":85.7,"TOU vs STR":85.7,"LOR vs MET":85.4,"NCE vs PFC":85.4,"NCE vs LOR":85.4,"PFC vs LEH":85.4,"PSG vs LEH":85.4,"STR vs LOR":85.4,"LYO vs MET":85.4,"AMO vs B29":83.3,"ANG vs LYO":83.3,"LEN vs NCE":83.3,"LIL vs NCE":83.3,"LOR vs ANG":83.3,"LOR vs TOU":83.3,"NAN vs AMO":83.3,"NAN vs B29":83.3,"OLM vs LOR":83.3,"OLM vs LIL":83.3,"REN vs AMO":83.3,"LIL vs REN":82.9,"NCE vs REN":82.9,"PFC vs REN":82.9,"STR vs PFC":82.9,"STR vs REN":82.9,"TOU vs MET":82.9,"ANG vs NCE":81.0,"AUX vs MET":81.0,"LEN vs MET":81.0,"LIL vs OLM":81.0,"LIL vs AMO":81.0,"LOR vs B29":81.0,"MET vs LYO":81.0,"PFC vs LIL":81.0,"PSG vs PFC":81.0,"PSG vs LIL":81.0,"REN vs PSG":81.0,"TOU vs AMO":81.0,"ANG vs AMO":81.0,"AUX vs AMO":80.5,"LEN vs LEH":80.5,"LEN vs AMO":80.5,"LIL vs MET":80.5,"LYO vs LOR":80.5,"LYO vs B29":80.5,"MET vs OLM":80.5,"NAN vs PFC":80.5,"NCE vs TOU":80.5,"OLM vs STR":80.5,"STR vs LYO":80.5,"OLM vs TOU":80.5},"Spain":{"SEV vs CEL":85.4,"CEL vs ALM":82.9,"CEL vs VIL":82.9,"CEL vs CAD":82.9,"GCF vs ATH":82.9,"RMA vs GCF":80.5,"RSO vs ALM":80.5},"Italy":{"GEN vs MON":90.2,"VER vs MON":87.8,"INT vs MON":87.8,"LAZ vs LEC":87.8,"NAP vs MON":87.5,"ROM vs LEC":87.5,"ROM vs MON":87.5,"VER vs LEC":87.5,"INT vs LEC":85.4,"LAZ vs MON":85.4,"NAP vs LEC":85.4,"JUV vs LEC":85.4,"GEN vs LEC":85.0,"MIL vs MON":85.0,"FIO vs MON":85.0,"COM vs MON":82.9,"INT vs COM":82.9,"LAZ vs SAL":82.9,"MIL vs LEC":82.9,"ATA vs MON":82.9,"NAP vs SAL":82.5,"ROM vs SAL":82.5,"FIO vs LEC":80.5,"GEN vs SAL":80.5,"JUV vs MON":80.5,"LAZ vs COM":80.5,"NAP vs COM":80.5,"ROM vs COM":80.5,"TOR vs MON":80.5,"VER vs SAL":80.5,"ATA vs LEC":80.5,"COM vs LEC":80.0,"INT vs SAL":80.0},"Germany":{"BAY vs KIE":94.1,"BVB vs KIE":94.1,"FCA vs KIE":91.2,"RBL vs KIE":91.2,"WOB vs KIE":91.2,"BMG vs KIE":91.2,"SCF vs KIE":91.2,"SGE vs KIE":91.2,"TSG vs KIE":91.2,"VFB vs KIE":91.2,"BAY vs BOC":88.2,"BVB vs BOC":88.2,"FCA vs BOC":88.2,"M05 vs KIE":88.2,"BAY vs HSV":88.2,"FCA vs HSV":87.8,"BVB vs HSV":87.8,"RBL vs BOC":85.3,"SCF vs BOC":85.3,"SGE vs BOC":85.3,"TSG vs BOC":85.3,"VFB vs BOC":85.3,"WOB vs BOC":85.3,"BMG vs BOC":85.3,"BAY vs SVD":85.3,"BVB vs SVD":85.3,"FCA vs SVD":85.3,"RBL vs HSV":85.3,"VFB vs HSV":85.4,"WOB vs HSV":85.3,"M05 vs BOC":85.3,"FCA vs BMU":84.8,"RBL vs HSV2":82.4,"SCF vs HSV":82.4,"SGE vs HSV":82.4,"TSG vs HSV":82.4,"BMG vs HSV":82.4,"BAY vs BMU":82.4,"BVB vs BMU":82.4,"RBL vs SVD":82.4,"SCF vs SVD":82.4,"SGE vs SVD":82.4,"TSG vs SVD":82.4,"VFB vs SVD":82.4,"WOB vs SVD":82.4,"BMG vs SVD":82.4,"M05 vs HSV":82.4,"M05 vs SVD":82.4,"VFB vs BMU":85.4,"FCA vs BMU2":82.4,"RBL vs KIE2":82.4,"RBL vs BMU":82.4,"SCF vs BMU":82.4,"SGE vs BMU":82.4,"TSG vs BMU":82.4,"WOB vs BMU":82.4,"BMG vs BMU":82.4,"M05 vs BMU":82.4,"BAY vs STP":82.4,"BVB vs STP":82.4,"FCA vs STP":82.4,"RBL vs STP":82.4,"SCF vs STP":82.4,"SGE vs STP":82.4,"TSG vs STP":82.4,"VFB vs STP":82.4,"WOB vs STP":82.4,"BMG vs STP":82.4,"M05 vs STP":82.4,"BAY vs FCU":80.6,"BVB vs FCU":80.6,"FCA vs FCU":80.6,"SGE vs FCU":80.6,"RBL vs FCU":80.6,"VFB vs FCU":80.6,"SCF vs FCU":80.6,"WOB vs FCU":80.6,"TSG vs FCU":80.6}}'
elite_data = json.loads(ELITE_RAW)
elite_flat = {}
for lg, mus in elite_data.items():
    for mu, rate in mus.items():
        elite_flat[mu] = (lg, rate)
print(f'ELITE: {len(elite_flat)} matchups')

# === FEEDBACK ===
_fb = {'bl':{},'pen':{},'cold':[]}
try:
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE) as f: _fb = json.load(f)
        print(f'Feedback: {len(_fb.get("bl",{}))}bl {len(_fb.get("pen",{}))}pen cold:{_fb.get("cold",[])}')
except: pass

def is_bl(mu):
    bl = _fb.get('bl',{})
    cur_hr = (datetime.datetime.utcnow() + WAT_OFFSET).hour
    return mu in bl and abs(bl[mu] - cur_hr) <= 1

def is_cold():
    cur_hr = (datetime.datetime.utcnow() + WAT_OFFSET).hour
    return cur_hr in _fb.get('cold', [])

def fetch_json(url, method='GET', data=None, retries=3):
    for attempt in range(retries):
        try:
            h = {**HDR}
            if data: h['Content-Type'] = 'application/json'; h['Accept'] = 'application/json'
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
                return json.loads(r.read().decode())
        except:
            if attempt == retries - 1: return None
            time.sleep(1)

def get_live_events():
    url = f"{LIVE_URL}?sportId={SPORT}&_t={int(time.time()*1000)}"
    data = fetch_json(url)
    if not data: return {}
    league_info = defaultdict(lambda: {'max_eid': 0, 'count': 0, 'ko': 0, 'events': []})
    tournaments = data.get('data', [])
    if isinstance(tournaments, dict): tournaments = tournaments.get('tournaments', [])
    for t in tournaments:
        for e in t.get('events', []):
            home = e.get('homeTeamName',''); away = e.get('awayTeamName','')
            # Detect league from team names
            h3 = home[:3].upper(); a3 = away[:3].upper()
            cat = None
            if h3 in {'ARS','AST','BRE','CHE','CRY','FOR','LIV','MUN','NEW','SUN','WOL','BUR','FUL','TOT','WHU','BOU','BHA','LEE','EVE','MCI'}: cat = 'England'
            elif h3 in {'ATM','BAR','BET','CEL','GIR','GET','MAL','OSA','RAY','RSO','SEV','VAL','VIL','ALA','CAD','ALM','GRA','LPA','ALC','ESP','RMA','ELC','LEV','VCF','BIL','FCB','OVI','RBB'}: cat = 'Spain'
            elif h3 in {'ATA','BFC','CAG','LEC','PAR','PIS','ROM','SAS','TOR','VER','COM','NAP','USC','ACM','LAZ','FIO','GEN','JUV','INT','UDI','MON'}: cat = 'Italy'
            elif h3 in {'BMU','BVB','HDH','LEV','MAI','SCF','SGE','STP','WOB','KOE','RBL','SVW','HSV','BMG','UNI','TSG','VFB','FCA','BAY','KIE'}: cat = 'Germany'
            elif h3 in {'ANG','LEN','LOR','NCE','OLM','PFC','PSG','REN','STR','NAN','LEH','B29','MET','AUX','LIL','LYO','TOU','AMO'}: cat = 'France'
            if not cat: continue
            eid_num = int(e['eventId'].replace('sr:match:', ''))
            ko = e.get('estimateStartTime', 0)
            league_info[cat]['max_eid'] = max(league_info[cat]['max_eid'], eid_num)
            league_info[cat]['count'] += 1
            league_info[cat]['ko'] = ko
            league_info[cat]['events'].append(e)
    return dict(league_info)

def probe_upcoming(league_info, rounds=ROUNDS_AHEAD):
    all_picks = []
    cold = is_cold()
    for lg in ['England','Spain','Italy','Germany','France']:
        info = league_info.get(lg)
        if not info: continue
        for rnd in range(1, rounds + 1):
            start_eid = info['max_eid'] + 1 + (rnd - 1) * info['count']
            sels = [{'eventId': f'sr:match:{start_eid+i}','marketId':18,'specifier':'total=1.5','outcomeId':'12'} for i in range(info['count'])]
            payload = json.dumps({"selections": sels, "sportId": SPORT}).encode()
            resp = fetch_json(BOOK_URL, data=payload)
            if not resp: break
            outcomes = resp.get('data',{}).get('outcomes',[])
            if not outcomes: break
            for oc in outcomes:
                home = oc.get('homeTeamName',''); away = oc.get('awayTeamName','')
                ko = oc.get('estimateStartTime',0); eid = oc.get('eventId','')
                mu = f"{home[:3].upper()} vs {away[:3].upper()}"
                o15_odds = None
                for mkt in oc.get('markets',[]):
                    if str(mkt.get('id'))=='18':
                        for out in mkt.get('outcomes',[]):
                            if str(out.get('id'))=='12': o15_odds = float(out.get('odds',0))
                # Check ELITE
                if mu in elite_flat:
                    _, rate = elite_flat[mu]
                else:
                    # Try league-based lookup
                    rate = elite_data.get(lg,{}).get(f"{home} vs {away}", 0)
                
                if rate >= MIN_MEGA:
                    # FEEDBACK: Skip blacklisted
                    if is_bl(mu):
                        print(f'  🚫 MEGA skip: {mu} (blacklisted)')
                        continue
                    # FEEDBACK: Cold hour = raise minimum to 88%
                    if cold and rate < MIN_PREMIUM:
                        continue
                    all_picks.append({
                        'eid':eid,'home':home,'away':away,'league':lg,
                        'o15_odds':o15_odds or 1.27,'elite_rate':rate,
                        'ko':ko,'round':rnd,'status':0
                    })
            time.sleep(0.2)
    return sorted(all_picks, key=lambda x: (x['ko'], -x['elite_rate']))

def scan_live_elite(league_info):
    early = []
    for lg, info in league_info.items():
        for e in info.get('events',[]):
            played = e.get('playedSeconds','0:00')
            try: mins = int(played.split(':')[0])
            except: mins = 99
            if mins > 20: continue
            home = e.get('homeTeamName',''); away = e.get('awayTeamName','')
            mu = f"{home[:3].upper()} vs {away[:3].upper()}"
            rate = 0
            if mu in elite_flat: _, rate = elite_flat[mu]
            else: rate = elite_data.get(lg,{}).get(f"{home} vs {away}", 0)
            if rate >= MIN_MEGA:
                if is_bl(mu): continue
                o15_odds = None
                for mkt in e.get('markets',[]):
                    if str(mkt.get('id'))=='18' and mkt.get('specifier')=='total=1.5':
                        for oc in mkt.get('outcomes',[]):
                            if str(oc.get('id'))=='12': o15_odds = float(oc.get('odds',0))
                early.append({
                    'eid':e['eventId'],'home':home,'away':away,'league':lg,
                    'o15_odds':o15_odds or 1.3,'elite_rate':rate,
                    'ko':e.get('estimateStartTime',0),'round':0,'status':1,
                    'minute':mins,'score':e.get('setScore','0:0')
                })
    return early

def create_booking_code(picks):
    sels = [{'eventId':p['eid'],'marketId':18,'specifier':'total=1.5','outcomeId':'12'} for p in picks]
    payload = json.dumps({"selections":sels,"sportId":SPORT}).encode()
    resp = fetch_json(BOOK_URL, data=payload)
    if resp and resp.get('data',{}).get('shareCode'):
        return resp['data']['shareCode'], resp['data'].get('shareURL','')
    return None, None

def send_tg(text):
    payload = json.dumps({"chat_id":CHAT,"text":text,"disable_web_page_preview":True}).encode()
    resp = fetch_json(f"https://api.telegram.org/bot{TGTOKEN}/sendMessage", data=payload)
    return resp and resp.get('ok')

def build_msg(tier_name, emoji, picks, code, share_url, combined):
    now_wat = (datetime.datetime.utcnow() + WAT_OFFSET).strftime('%H:%M')
    cold_tag = ' ❄️COLD-FILTERED' if is_cold() else ''
    lines = [
        f"{emoji} ONIMIX VFL {tier_name} ACCA v3",
        f"📅 {datetime.date.today().strftime('%d %b %Y')} | {now_wat} WAT{cold_tag}",
        f"🎯 {len(picks)} legs | {combined:,.0f}x odds",
        f"💰 N100 → N{100*combined:,.0f} | N500 → N{500*combined:,.0f}",
        ""
    ]
    ko_groups = {}
    for p in picks:
        if p['ko'] not in ko_groups: ko_groups[p['ko']] = []
        ko_groups[p['ko']].append(p)
    for ko_ts in sorted(ko_groups.keys()):
        ko_dt = datetime.datetime.utcfromtimestamp(ko_ts/1000) + WAT_OFFSET
        grp = ko_groups[ko_ts]
        tag = "LIVE" if any(p.get('status')==1 for p in grp) else "PRE"
        lines.append(f"⏰ {ko_dt.strftime('%H:%M')} WAT [{tag}]")
        for p in grp:
            icon = "🔥" if p['elite_rate']>=93 else "⭐" if p['elite_rate']>=90 else "✅"
            extra = f" [{p.get('score','')}, {p.get('minute',0)}']" if p.get('status')==1 else ""
            lines.append(f"  {icon} {p['league']}: {p['home']} v {p['away']} O1.5 @{p['o15_odds']:.2f} ({p['elite_rate']:.0f}%){extra}")
        lines.append("")
    if code:
        lines.append(f"🎟 Code: {code}")
        lines.append(f"🔗 {share_url}")
    lines.append("")
    lines.append("🤖 ONIMIX AI v3 | Feedback-enhanced | 73K DB")
    return '\n'.join(lines)

def log_picks(picks, layer='MEGA'):
    try:
        log = []
        if os.path.exists(PICKS_LOG):
            with open(PICKS_LOG) as f: log = json.load(f)
        now_wat = datetime.datetime.utcnow() + WAT_OFFSET
        for p in picks:
            mu = f"{p['home'][:3].upper()} vs {p['away'][:3].upper()}"
            log.append({'key':mu,'layer':layer,'hour':now_wat.hour,'date':now_wat.strftime('%Y-%m-%d'),'time':now_wat.strftime('%H:%M'),'rate':p['elite_rate'],'eid':p['eid']})
        with open(PICKS_LOG,'w') as f: json.dump(log[-500:],f)
    except: pass

def main():
    print("🚀 ONIMIX Mega v3 FEEDBACK starting...")
    league_info = get_live_events()
    if not league_info:
        print("❌ No live events"); return
    total_live = sum(i['count'] for i in league_info.values())
    print(f"✅ Live: {total_live} events, {len(league_info)} leagues")

    live_elite = scan_live_elite(league_info)
    print(f"✅ Live ELITE: {len(live_elite)}")
    
    upcoming = probe_upcoming(league_info)
    print(f"✅ Upcoming ELITE: {len(upcoming)}")
    
    all_picks = live_elite + upcoming
    seen = set(); unique = []
    for p in all_picks:
        if p['eid'] not in seen: seen.add(p['eid']); unique.append(p)
    print(f"✅ Unique: {len(unique)}")
    
    if not unique:
        send_tg("⚠️ Mega v3: No ELITE picks. Next scan in 30 min.")
        return

    tiers = [("ULTRA SAFE","🔒",MIN_ULTRA,15),("PREMIUM","⭐",MIN_PREMIUM,22),("MEGA","🚀",MIN_MEGA,40)]
    all_sent = []
    for tier_name, emoji, min_rate, max_picks in tiers:
        tp = [p for p in unique if p['elite_rate']>=min_rate][:max_picks]
        if not tp: continue
        combined = 1.0
        for p in tp: combined *= p['o15_odds']
        code, share_url = create_booking_code(tp)
        msg = build_msg(tier_name, emoji, tp, code, share_url, combined)
        sent = send_tg(msg)
        print(f"{'✅' if sent else '❌'} {tier_name}: {len(tp)} picks, {combined:,.0f}x, code={code}")
        all_sent.extend(tp)
        time.sleep(1)
    
    log_picks(all_sent, 'MEGA')
    print("\n🏁 Mega v3 complete!")

if __name__ == '__main__':
    main()
