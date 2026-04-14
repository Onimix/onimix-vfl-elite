"""
MEGA GRAND AUDIT v3 — ALL 5 VFL LEAGUES  
Target: 30k-60k combined odds
Strategy: LOCK tier (odds ≥1.38) + ELITE-LOW tier (odds 1.13-1.37 with top signals)
Deep: 6-market prematch JSON + 3-day historical data
"""
import requests, json, time, math, datetime as dt

BASE = "https://www.sportybet.com/api/ng/factsCenter"
THUMB = f"{BASE}/commonThumbnailEvents"
DETAIL = f"{BASE}/event"
RESULTS = f"{BASE}/eventResultList"
BOOK = "https://www.sportybet.com/api/ng/orders/share"
TG_TOKEN = "8548617749:AAENDPXnXb0Rcr453me-7rIMfE6E28nS_Ow"
TG_CHAT = "1745848158"
SPORT = "sr:sport:202120001"

LEAGUES = {
    "sv:category:202120001": "England",
    "sv:category:202120002": "Spain",
    "sv:category:202120003": "Italy",
    "sv:category:202120004": "Germany",
    "sv:category:202120005": "France",
}
FLAGS = {"England":"🏴","Spain":"🇪🇸","Italy":"🇮🇹","Germany":"🇩🇪","France":"🇫🇷"}

HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.sportybet.com/ng/sport/vFootball/live_list",
}

def api(url, params=None, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=HDRS, timeout=20)
            r.raise_for_status()
            return r.json().get("data", r.json())
        except Exception as e:
            if i == retries - 1: return None
            time.sleep(1.5)

def fetch_upcoming():
    now_ms = int(time.time() * 1000)
    data = api(THUMB, {"sportId": SPORT, "_t": now_ms})
    if not data: return []
    events = []
    for lg in (data if isinstance(data, list) else data.get("tournaments", [])):
        if not isinstance(lg, dict): continue
        for ev in lg.get("events", []):
            est = ev.get("estimateStartTime", 0)
            if est <= now_ms or ev.get("matchStatus","") not in ("Not start","not_started",""): continue
            cat_id = ""
            sp = ev.get("sport",{})
            if isinstance(sp, dict):
                c = sp.get("category",{})
                if isinstance(c, dict): cat_id = c.get("id","")
            league = LEAGUES.get(cat_id)
            if not league: continue
            events.append({"gameId":ev.get("gameId",""),"eventId":ev.get("eventId",""),
                          "home":ev.get("homeTeamName",""),"away":ev.get("awayTeamName",""),
                          "league":league,"cat_id":cat_id,"kickoff":est,
                          "kickoff_str":dt.datetime.fromtimestamp(est/1000).strftime("%H:%M") if est else "?"})
    print(f"📡 {len(events)} upcoming events")
    for l in LEAGUES.values():
        c = sum(1 for e in events if e["league"]==l)
        if c: print(f"   {FLAGS.get(l,'')} {l}: {c}")
    return events

def fetch_history(days=3):
    history = {l: [] for l in LEAGUES.values()}
    now = dt.datetime.now()
    for d_off in range(1, days+1):
        target = now - dt.timedelta(days=d_off)
        s_ms = int(target.replace(hour=0,minute=0,second=0,microsecond=0).timestamp()*1000)
        e_ms = int(target.replace(hour=23,minute=59,second=59,microsecond=0).timestamp()*1000)
        for page in range(1, 21):
            data = api(RESULTS, {"pageNum":page,"pageSize":100,"sportId":SPORT,"startTime":s_ms,"endTime":e_ms,"_t":int(time.time()*1000)})
            if not data: break
            tournaments = data.get("tournaments",[]) if isinstance(data,dict) else data if isinstance(data,list) else []
            if not tournaments: break
            count = 0
            for t in tournaments:
                if not isinstance(t,dict): continue
                for ev in t.get("events",[]):
                    league = None
                    sp = ev.get("sport",{})
                    if isinstance(sp,dict):
                        ct = sp.get("category",{})
                        if isinstance(ct,dict): league = LEAGUES.get(ct.get("id",""))
                    if not league: continue
                    scores = ev.get("regularTimeScore",[])
                    goals = 0
                    if isinstance(scores,list):
                        for s in scores:
                            if isinstance(s,str) and ":" in s:
                                p = s.split(":")
                                try: goals += int(p[0])+int(p[1])
                                except: pass
                    count += 1
                    history[league].append({"home":ev.get("homeTeamName",""),"away":ev.get("awayTeamName",""),"goals":goals,"over15":goals>=2})
            if count==0: break
            time.sleep(0.25)
        time.sleep(0.3)
    total = sum(len(v) for v in history.values())
    print(f"\n📊 History: {total} matches ({days} days)")
    for l, ms in history.items():
        if ms:
            r = sum(1 for m in ms if m["over15"])/len(ms)*100
            print(f"   {FLAGS.get(l,'')} {l}: {len(ms)} ({r:.0f}% O1.5)")
    return history

def section_a(detail):
    if not detail: return 0, 1.0, {}
    mkts = {}
    for m in detail.get("markets",[]):
        if isinstance(m,dict): mkts[(str(m.get("id","")),m.get("specifier",""))] = m
    score = 0; odds = 1.0; sigs = {}
    
    m = mkts.get(("18","total=1.5"))
    if m:
        for o in m.get("outcomes",[]):
            if "over" in o.get("desc","").lower():
                p = float(o.get("probability","0") or "0")
                odds = float(o.get("odds","1") or "1")
                sigs["ou"] = f"{p:.0%}@{odds:.2f}"
                if p>=0.75: score+=4
                elif p>=0.65: score+=3
                elif p>=0.55: score+=2
                elif p>=0.45: score+=1
    
    m = mkts.get(("19","total=0.5"))
    if m:
        for o in m.get("outcomes",[]):
            if "over" in o.get("desc","").lower():
                p = float(o.get("probability","0") or "0"); sigs["hg"]=f"{p:.0%}"
                if p>=0.70: score+=2
                elif p>=0.55: score+=1
    
    m = mkts.get(("20","total=0.5"))
    if m:
        for o in m.get("outcomes",[]):
            if "over" in o.get("desc","").lower():
                p = float(o.get("probability","0") or "0"); sigs["ag"]=f"{p:.0%}"
                if p>=0.70: score+=2
                elif p>=0.55: score+=1
    
    for spec in ["","total=0.5"]:
        m = mkts.get(("29",spec))
        if m:
            for o in m.get("outcomes",[]):
                if "yes" in o.get("desc","").lower():
                    p = float(o.get("probability","0") or "0"); sigs["btts"]=f"{p:.0%}"
                    if p>=0.55: score+=2
                    elif p>=0.40: score+=1
            break
    
    m = mkts.get(("45",""))
    if m:
        hi = sum(float(o.get("probability","0") or "0") for o in m.get("outcomes",[])
                 if ":" in o.get("desc","") and sum(int(x) for x in o["desc"].split(":") if x.isdigit())>=2)
        sigs["cs2+"]=f"{hi:.0%}"
        if hi>=0.70: score+=2
        elif hi>=0.55: score+=1
    
    m = mkts.get(("68","total=0.5"))
    if m:
        for o in m.get("outcomes",[]):
            if "over" in o.get("desc","").lower():
                p = float(o.get("probability","0") or "0"); sigs["fh"]=f"{p:.0%}"
                if p>=0.65: score+=2
                elif p>=0.50: score+=1
    return score, odds, sigs

def section_b(home, away, league, history):
    ms = history.get(league,[]); 
    if not ms: return 0, {}
    score = 0; sigs = {}
    h2h = [m for m in ms if (m["home"]==home and m["away"]==away) or (m["home"]==away and m["away"]==home)]
    if h2h:
        r = sum(1 for m in h2h if m["over15"])/len(h2h)
        sigs["h2h"]=f"{sum(1 for m in h2h if m['over15'])}/{len(h2h)}"
        if r>=0.80: score+=4
        elif r>=0.60: score+=3
        elif r>=0.40: score+=2
    hm = [m for m in ms if m["home"]==home]
    if hm:
        r = sum(1 for m in hm if m["over15"])/len(hm); sigs["hf"]=f"{r:.0%}"
        if r>=0.75: score+=3
        elif r>=0.55: score+=2
        elif r>=0.40: score+=1
    am = [m for m in ms if m["away"]==away]
    if am:
        r = sum(1 for m in am if m["over15"])/len(am); sigs["af"]=f"{r:.0%}"
        if r>=0.75: score+=3
        elif r>=0.55: score+=2
        elif r>=0.40: score+=1
    if ms:
        r = sum(1 for m in ms if m["over15"])/len(ms); sigs["le"]=f"{r:.0%}"
        if r>=0.75: score+=4
        elif r>=0.65: score+=3
        elif r>=0.55: score+=2
        elif r>=0.45: score+=1
    return score, sigs

def run():
    print("="*55)
    print("🏟️ MEGA GRAND AUDIT v3 — 30k-60k TARGET")
    print(f"📅 {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)
    
    events = fetch_upcoming()
    history = fetch_history(3)
    
    print(f"\n🔬 Analyzing {len(events)} events...")
    all_picks = []
    
    for i, ev in enumerate(events):
        detail = api(DETAIL, {"gameId":ev["gameId"],"productId":3,"_t":int(time.time()*1000)})
        if isinstance(detail,dict) and "markets" not in detail:
            for k in ["event","data"]:
                if k in detail and isinstance(detail[k],dict): detail=detail[k]; break
        
        sa, odds, sa_s = section_a(detail)
        sb, sb_s = section_b(ev["home"],ev["away"],ev["league"],history)
        comb = sa*0.6 + sb*0.4
        
        # Skip only zero signal
        if sa==0 and sb==0: continue
        if comb < 2.0: continue
        if odds < 1.10: continue  # absolute floor
        
        # Tier assignment
        if odds >= 1.38 and comb >= 7.0: tier = "🔒LOCK"
        elif odds >= 1.38 and comb >= 4.5: tier = "🎯PICK"
        elif odds < 1.38 and comb >= 8.0: tier = "⚡ELITE"  # Low odds but super high signal
        elif odds < 1.38 and comb >= 5.0: tier = "📌SAFE"   # Safe banker to boost odds
        else: continue
        
        oid = None
        if detail:
            for mk in detail.get("markets",[]):
                if str(mk.get("id",""))=="18" and mk.get("specifier")=="total=1.5":
                    for o in mk.get("outcomes",[]):
                        if "over" in o.get("desc","").lower(): oid=o.get("id"); break
        
        all_picks.append({**ev,"sa":sa,"sb":sb,"comb":comb,"odds":odds,
                          "tier":tier,"oid":oid,"sa_s":sa_s,"sb_s":sb_s})
        tag = tier.split("]")[-1] if "]" in tier else tier
        print(f"  [{i+1}] {FLAGS.get(ev['league'],'')} {ev['home']}v{ev['away']} {tier} SA={sa} SB={sb} C={comb:.1f} @{odds:.2f}")
        time.sleep(0.35)
    
    # Sort by combined score
    all_picks.sort(key=lambda x: (-x["comb"], -x["odds"]))
    
    locks = [p for p in all_picks if "LOCK" in p["tier"]]
    picks = [p for p in all_picks if "PICK" in p["tier"]]
    elites = [p for p in all_picks if "ELITE" in p["tier"]]
    safes = [p for p in all_picks if "SAFE" in p["tier"]]
    
    print(f"\n📊 Breakdown:")
    print(f"  🔒 LOCKs: {len(locks)} (odds≥1.38, score≥7)")
    print(f"  🎯 PICKs: {len(picks)} (odds≥1.38, score≥4.5)")
    print(f"  ⚡ ELITEs: {len(elites)} (odds<1.38, score≥8)")  
    print(f"  📌 SAFEs: {len(safes)} (odds<1.38, score≥5)")
    
    # BUILD MEGA ACCUMULATOR targeting 30k-60k
    # Strategy: Start with all LOCKs + PICKs, add ELITEs + SAFEs until target
    mega = locks + picks
    current_odds = math.prod(p["odds"] for p in mega) if mega else 1
    
    # Add elites (sorted by combined score desc) until we reach target or run out
    for p in sorted(elites + safes, key=lambda x: -x["comb"]):
        mega.append(p)
        current_odds = math.prod(pp["odds"] for pp in mega)
        if current_odds >= 60000:
            break
    
    final_odds = math.prod(p["odds"] for p in mega) if mega else 0
    
    print(f"\n💰 MEGA ACCUMULATOR:")
    print(f"  Selections: {len(mega)}")
    print(f"  Combined odds: {final_odds:,.0f}x")
    print(f"  Status: {'✅ IN RANGE' if 30000<=final_odds<=60000 else '⚠️ '+('BELOW' if final_odds<30000 else 'ABOVE')+' TARGET'}")
    
    # Booking code
    code = None
    valid = [m for m in mega if m.get("oid") and m.get("eventId")]
    if valid:
        sels = [{"sportId":SPORT,"eventId":str(m["eventId"]),"marketId":"18",
                 "specifier":"total=1.5","outcomeId":str(m["oid"]),"odds":str(m["odds"])} for m in valid]
        try:
            r = requests.post(BOOK, json={"selections":sels,"stake":100,"channel":"WEB"},
                            headers={**HDRS,"Content-Type":"application/json"}, timeout=15)
            d = r.json().get("data",{})
            code = d.get("shareCode") or d.get("code") or d.get("bookingCode") or d.get("shareNo")
            print(f"  🎫 MEGA Code: {code or 'N/A'}")
            if not code: print(f"  🎫 API response: {r.text[:200]}")
        except Exception as e:
            print(f"  🎫 Error: {e}")
    
    # Also build LOCK-only code (safer bet)
    lock_code = None
    lock_valid = [m for m in locks if m.get("oid") and m.get("eventId")]
    if lock_valid and len(lock_valid) >= 3:
        sels2 = [{"sportId":SPORT,"eventId":str(m["eventId"]),"marketId":"18",
                  "specifier":"total=1.5","outcomeId":str(m["oid"]),"odds":str(m["odds"])} for m in lock_valid]
        try:
            r2 = requests.post(BOOK, json={"selections":sels2,"stake":100,"channel":"WEB"},
                             headers={**HDRS,"Content-Type":"application/json"}, timeout=15)
            d2 = r2.json().get("data",{})
            lock_code = d2.get("shareCode") or d2.get("code") or d2.get("bookingCode") or d2.get("shareNo")
            lock_odds = math.prod(m["odds"] for m in locks)
            print(f"  🎫 LOCK-only code: {lock_code or 'N/A'} ({lock_odds:,.0f}x)")
        except: pass
    
    # ELITE+LOCK code (medium risk)
    elite_code = None
    el_valid = [m for m in (locks + elites) if m.get("oid") and m.get("eventId")]
    if el_valid and len(el_valid) >= 3:
        sels3 = [{"sportId":SPORT,"eventId":str(m["eventId"]),"marketId":"18",
                  "specifier":"total=1.5","outcomeId":str(m["oid"]),"odds":str(m["odds"])} for m in el_valid]
        try:
            r3 = requests.post(BOOK, json={"selections":sels3,"stake":100,"channel":"WEB"},
                             headers={**HDRS,"Content-Type":"application/json"}, timeout=15)
            d3 = r3.json().get("data",{})
            elite_code = d3.get("shareCode") or d3.get("code") or d3.get("bookingCode") or d3.get("shareNo")
            el_odds = math.prod(m["odds"] for m in (locks + elites))
            print(f"  🎫 LOCK+ELITE code: {elite_code or 'N/A'} ({el_odds:,.0f}x)")
        except: pass
    
    # BUILD TELEGRAM MESSAGE
    lines = [
        "🏟️ *MEGA GRAND AUDIT v3*",
        f"📅 {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"🎯 {len(mega)} selections | {final_odds:,.0f}x combined",
        "",
    ]
    
    for league in LEAGUES.values():
        lp = [m for m in mega if m["league"]==league]
        if not lp: continue
        f = FLAGS.get(league,"🏟️")
        lines.append(f"\n{f} *{league}* ({len(lp)})")
        lines.append("─"*22)
        for m in lp:
            lines.append(f"{m['tier']} {m['home']} vs {m['away']} ⏰{m['kickoff_str']}")
            lines.append(f"   O1.5 @{m['odds']:.2f} | SA:{m['sa']}/14 SB:{m['sb']}/14 C:{m['comb']:.1f}")
            sp = []
            if m['sa_s'].get('ou'): sp.append(f"OU:{m['sa_s']['ou']}")
            if m['sa_s'].get('btts'): sp.append(f"BTTS:{m['sa_s']['btts']}")
            if m['sb_s'].get('h2h'): sp.append(f"H2H:{m['sb_s']['h2h']}")
            if sp: lines.append(f"   📈 {' | '.join(sp)}")
    
    lines.append(f"\n{'='*25}")
    lines.append(f"🔒 LOCKs: {len(locks)} | 🎯 PICKs: {len(picks)}")
    lines.append(f"⚡ ELITEs: {len(elites)} | 📌 SAFEs: {len(safes)}")
    lines.append(f"💰 *MEGA ODDS: {final_odds:,.0f}x*")
    if code: lines.append(f"\n🎫 *MEGA CODE: {code}*")
    if elite_code:
        el_odds = math.prod(m["odds"] for m in (locks + elites))
        lines.append(f"🎫 *LOCK+ELITE CODE: {elite_code}* ({el_odds:,.0f}x)")
    if lock_code:
        lock_odds = math.prod(m["odds"] for m in locks)
        lines.append(f"🎫 *LOCK CODE: {lock_code}* ({lock_odds:,.0f}x)")
    lines.append(f"\n_Deep 6-market + 3-day history_")
    lines.append("_ONIMIX TECH MEGA AUDIT 🤖_")
    
    msg = "\n".join(lines)
    
    # Send Telegram
    sent = False
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                         json={"chat_id":TG_CHAT,"text":msg,"parse_mode":"Markdown"}, timeout=15)
        if r.json().get("ok"):
            print("\n✅ Telegram delivered!")
            sent = True
        else:
            # Try plain text
            r2 = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                              json={"chat_id":TG_CHAT,"text":msg.replace("*","").replace("_","")}, timeout=15)
            if r2.json().get("ok"):
                print("\n✅ Telegram delivered (plain)")
                sent = True
            else:
                print(f"\n⚠️ Telegram failed: {r.json().get('description','unknown')}")
    except Exception as e:
        print(f"\n⚠️ Telegram: {e}")
    
    if not sent:
        print("\n⚠️ Telegram bot token may have expired. Message saved locally.")
    
    # Save message to file for manual delivery if needed
    with open("/tmp/mega_audit_message.txt", "w") as f:
        f.write(msg.replace("*","").replace("_",""))
    
    # Save results
    result = {
        "ts": dt.datetime.now().isoformat(),
        "total": len(mega), "locks": len(locks), "picks": len(picks),
        "elites": len(elites), "safes": len(safes),
        "combined_odds": final_odds, "mega_code": code, "lock_elite_code": elite_code, "lock_code": lock_code,
        "telegram_sent": sent,
        "selections": [{
            "home":m["home"],"away":m["away"],"league":m["league"],
            "odds":m["odds"],"tier":m["tier"],"comb":m["comb"],
            "sa":m["sa"],"sb":m["sb"],"kickoff":m["kickoff"],
            "gameId":m.get("gameId",""),"eventId":m.get("eventId",""),"oid":m.get("oid","")
        } for m in mega]
    }
    with open("/tmp/mega_audit_results.json","w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'='*55}")
    print(f"✅ MEGA AUDIT v3: {len(mega)} picks | {final_odds:,.0f}x | Codes: {code or 'N/A'} / {lock_code or 'N/A'}")
    print(f"   Message: /tmp/mega_audit_message.txt")
    return result

if __name__ == "__main__":
    run()
