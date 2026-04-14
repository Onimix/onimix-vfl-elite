"""
MEGA GRAND AUDIT v4 — ALL 5 VFL LEAGUES  
Target: 30k-60k combined odds
STRICT RULE: Only O1.5 odds between 1.38 and 1.60 (anything below = TRAP)
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

# STRICT ODDS BOUNDARIES — user's rule: 1.38 to 1.60 ONLY
MIN_ODDS = 1.38
MAX_ODDS = 1.60

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
    """6-market prematch JSON decoder. Returns score (0-14), odds, signals dict."""
    if not detail: return 0, 0.0, {}
    mkts = {}
    for m in detail.get("markets",[]):
        if isinstance(m,dict): mkts[(str(m.get("id","")),m.get("specifier",""))] = m
    score = 0; odds = 0.0; sigs = {}
    
    # Market 18: Over/Under 1.5 — THE main market
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
    
    # Market 19: Home Over 0.5 Goals
    m = mkts.get(("19","total=0.5"))
    if m:
        for o in m.get("outcomes",[]):
            if "over" in o.get("desc","").lower():
                p = float(o.get("probability","0") or "0"); sigs["hg"]=f"{p:.0%}"
                if p>=0.70: score+=2
                elif p>=0.55: score+=1
    
    # Market 20: Away Over 0.5 Goals
    m = mkts.get(("20","total=0.5"))
    if m:
        for o in m.get("outcomes",[]):
            if "over" in o.get("desc","").lower():
                p = float(o.get("probability","0") or "0"); sigs["ag"]=f"{p:.0%}"
                if p>=0.70: score+=2
                elif p>=0.55: score+=1
    
    # Market 29: BTTS
    for spec in ["","total=0.5"]:
        m = mkts.get(("29",spec))
        if m:
            for o in m.get("outcomes",[]):
                if "yes" in o.get("desc","").lower():
                    p = float(o.get("probability","0") or "0"); sigs["btts"]=f"{p:.0%}"
                    if p>=0.55: score+=2
                    elif p>=0.40: score+=1
            break
    
    # Market 45: Correct Score (sum probability of scores ≥2 goals)
    m = mkts.get(("45",""))
    if m:
        hi = sum(float(o.get("probability","0") or "0") for o in m.get("outcomes",[])
                 if ":" in o.get("desc","") and sum(int(x) for x in o["desc"].split(":") if x.isdigit())>=2)
        sigs["cs2+"]=f"{hi:.0%}"
        if hi>=0.70: score+=2
        elif hi>=0.55: score+=1
    
    # Market 68: First Half Over 0.5
    m = mkts.get(("68","total=0.5"))
    if m:
        for o in m.get("outcomes",[]):
            if "over" in o.get("desc","").lower():
                p = float(o.get("probability","0") or "0"); sigs["fh"]=f"{p:.0%}"
                if p>=0.65: score+=2
                elif p>=0.50: score+=1
    return score, odds, sigs

def section_b(home, away, league, history):
    """Historical data analysis. Returns score (0-14), signals dict."""
    ms = history.get(league,[])
    if not ms: return 0, {}
    score = 0; sigs = {}
    
    # H2H in last 3 days
    h2h = [m for m in ms if (m["home"]==home and m["away"]==away) or (m["home"]==away and m["away"]==home)]
    if h2h:
        r = sum(1 for m in h2h if m["over15"])/len(h2h)
        sigs["h2h"]=f"{sum(1 for m in h2h if m['over15'])}/{len(h2h)}"
        if r>=0.80: score+=4
        elif r>=0.60: score+=3
        elif r>=0.40: score+=2
    
    # Home team form
    hm = [m for m in ms if m["home"]==home]
    if hm:
        r = sum(1 for m in hm if m["over15"])/len(hm); sigs["hf"]=f"{r:.0%}"
        if r>=0.75: score+=3
        elif r>=0.55: score+=2
        elif r>=0.40: score+=1
    
    # Away team form
    am = [m for m in ms if m["away"]==away]
    if am:
        r = sum(1 for m in am if m["over15"])/len(am); sigs["af"]=f"{r:.0%}"
        if r>=0.75: score+=3
        elif r>=0.55: score+=2
        elif r>=0.40: score+=1
    
    # League overall O1.5 rate
    if ms:
        r = sum(1 for m in ms if m["over15"])/len(ms); sigs["le"]=f"{r:.0%}"
        if r>=0.75: score+=4
        elif r>=0.65: score+=3
        elif r>=0.55: score+=2
        elif r>=0.45: score+=1
    return score, sigs

def run():
    print("="*55)
    print("🏟️ MEGA GRAND AUDIT v4 — STRICT 1.38-1.60")
    print(f"📅 {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"⚠️  ODDS FILTER: {MIN_ODDS} – {MAX_ODDS} ONLY")
    print("="*55)
    
    events = fetch_upcoming()
    history = fetch_history(3)
    
    print(f"\n🔬 Analyzing {len(events)} events (strict {MIN_ODDS}-{MAX_ODDS} filter)...")
    all_picks = []
    skipped_low = 0
    skipped_high = 0
    
    for i, ev in enumerate(events):
        detail = api(DETAIL, {"gameId":ev["gameId"],"productId":3,"_t":int(time.time()*1000)})
        if isinstance(detail,dict) and "markets" not in detail:
            for k in ["event","data"]:
                if k in detail and isinstance(detail[k],dict): detail=detail[k]; break
        
        sa, odds, sa_s = section_a(detail)
        sb, sb_s = section_b(ev["home"],ev["away"],ev["league"],history)
        comb = sa*0.6 + sb*0.4
        
        # Skip zero signal
        if sa==0 and sb==0: continue
        if comb < 2.0: continue
        
        # STRICT ODDS FILTER — user rule: 1.38 to 1.60 ONLY
        if odds < MIN_ODDS:
            skipped_low += 1
            continue  # TRAP zone — skip
        if odds > MAX_ODDS:
            skipped_high += 1
            continue  # Too risky — skip
        
        # Tier assignment (only within 1.38-1.60 range)
        if comb >= 7.0: tier = "🔒LOCK"
        elif comb >= 5.0: tier = "🎯PICK"
        elif comb >= 3.5: tier = "📌SOLID"
        else: continue
        
        oid = None
        if detail:
            for mk in detail.get("markets",[]):
                if str(mk.get("id",""))=="18" and mk.get("specifier")=="total=1.5":
                    for o in mk.get("outcomes",[]):
                        if "over" in o.get("desc","").lower(): oid=o.get("id"); break
        
        all_picks.append({**ev,"sa":sa,"sb":sb,"comb":comb,"odds":odds,
                          "tier":tier,"oid":oid,"sa_s":sa_s,"sb_s":sb_s})
        print(f"  [{len(all_picks)}] {FLAGS.get(ev['league'],'')} {ev['home']} v {ev['away']} {tier} SA={sa} SB={sb} C={comb:.1f} @{odds:.2f}")
        time.sleep(0.35)
    
    # Sort by combined score descending, then by odds ascending (prefer stronger signal + lower risk)
    all_picks.sort(key=lambda x: (-x["comb"], x["odds"]))
    
    locks = [p for p in all_picks if "LOCK" in p["tier"]]
    picks = [p for p in all_picks if "PICK" in p["tier"]]
    solids = [p for p in all_picks if "SOLID" in p["tier"]]
    
    print(f"\n📊 Results (strict {MIN_ODDS}-{MAX_ODDS}):")
    print(f"  🔒 LOCKs: {len(locks)} (score≥7.0)")
    print(f"  🎯 PICKs: {len(picks)} (score≥5.0)")
    print(f"  📌 SOLIDs: {len(solids)} (score≥3.5)")
    print(f"  ⛔ Skipped <{MIN_ODDS}: {skipped_low}")
    print(f"  ⛔ Skipped >{MAX_ODDS}: {skipped_high}")
    
    # BUILD MEGA ACCUMULATOR targeting 30k-60k
    # With avg odds ~1.48 in 1.38-1.60 range, need ~27-28 picks for 30k-60k
    # Take all LOCKs first, then PICKs, then SOLIDs until target reached
    mega = []
    for p in locks + picks + solids:
        mega.append(p)
        current_odds = math.prod(pp["odds"] for pp in mega)
        if current_odds >= 60000:
            break
    
    final_odds = math.prod(p["odds"] for p in mega) if mega else 0
    
    # If under target but we have all picks, that's our max
    if mega:
        print(f"\n💰 MEGA ACCUMULATOR:")
        print(f"  Selections: {len(mega)}")
        print(f"  Combined odds: {final_odds:,.0f}x")
        avg_odds = sum(p["odds"] for p in mega)/len(mega) if mega else 0
        print(f"  Average odds: {avg_odds:.2f}")
        needed_for_30k = math.ceil(math.log(30000)/math.log(avg_odds)) if avg_odds > 1 else 999
        print(f"  Picks needed for 30k at avg {avg_odds:.2f}: ~{needed_for_30k}")
        if final_odds >= 30000:
            print(f"  Status: ✅ IN RANGE ({final_odds:,.0f}x)")
        else:
            print(f"  Status: ⚠️ BELOW TARGET — only {len(mega)} qualifying picks available")
            print(f"  💡 Need ~{needed_for_30k} picks at avg {avg_odds:.2f} odds for 30k+")
    
    # Generate booking codes
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
            if not code: print(f"  🎫 API resp: {r.text[:300]}")
        except Exception as e:
            print(f"  🎫 Error: {e}")
    
    # LOCK-only code (safest tier)
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
    
    # BUILD TELEGRAM MESSAGE
    lines = [
        "🏟️ *MEGA GRAND AUDIT v4*",
        f"📅 {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"⚠️ STRICT ODDS: {MIN_ODDS} – {MAX_ODDS} ONLY",
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
            if m['sa_s'].get('hg'): sp.append(f"HG:{m['sa_s']['hg']}")
            if m['sa_s'].get('ag'): sp.append(f"AG:{m['sa_s']['ag']}")
            if m['sb_s'].get('h2h'): sp.append(f"H2H:{m['sb_s']['h2h']}")
            if m['sb_s'].get('hf'): sp.append(f"HF:{m['sb_s']['hf']}")
            if m['sb_s'].get('af'): sp.append(f"AF:{m['sb_s']['af']}")
            if sp: lines.append(f"   📈 {' | '.join(sp)}")
    
    lines.append(f"\n{'='*25}")
    lines.append(f"🔒 LOCKs: {len(locks)} | 🎯 PICKs: {len(picks)} | 📌 SOLIDs: {len(solids)}")
    lines.append(f"💰 *MEGA ODDS: {final_odds:,.0f}x*")
    if code: lines.append(f"\n🎫 *MEGA CODE: {code}*")
    if lock_code:
        lock_odds = math.prod(m["odds"] for m in locks)
        lines.append(f"🎫 *LOCK CODE: {lock_code}* ({lock_odds:,.0f}x)")
    lines.append(f"\n⛔ Rejected: {skipped_low} below 1.38 (TRAP) | {skipped_high} above 1.60")
    lines.append(f"_Deep 6-market + 3-day history_")
    lines.append("_ONIMIX TECH MEGA AUDIT v4 🤖_")
    
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
            # Try plain text fallback
            r2 = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                              json={"chat_id":TG_CHAT,"text":msg.replace("*","").replace("_","")}, timeout=15)
            if r2.json().get("ok"):
                print("\n✅ Telegram delivered (plain)")
                sent = True
            else:
                print(f"\n⚠️ Telegram failed: {r.json().get('description','unknown')}")
    except Exception as e:
        print(f"\n⚠️ Telegram: {e}")
    
    # Save message locally
    with open("/tmp/mega_audit_message.txt", "w") as f:
        f.write(msg.replace("*","").replace("_",""))
    
    # Save results JSON
    result = {
        "ts": dt.datetime.now().isoformat(),
        "version": "v4_strict_odds",
        "odds_range": f"{MIN_ODDS}-{MAX_ODDS}",
        "total": len(mega), "locks": len(locks), "picks": len(picks), "solids": len(solids),
        "skipped_below_138": skipped_low, "skipped_above_160": skipped_high,
        "combined_odds": final_odds, "mega_code": code, "lock_code": lock_code,
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
    print(f"✅ MEGA AUDIT v4: {len(mega)} picks | {final_odds:,.0f}x | Code: {code or 'N/A'}")
    return result

if __name__ == "__main__":
    run()
