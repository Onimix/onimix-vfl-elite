"""
VFL Engine v3.7 — ONIMIX TECH
Section A: Pre-match JSON Probability Decoder (6 markets)
Section B: Yesterday Same-Slot Energy Cards (restored via results accumulation)
Failure Monitoring + Learning System
v3.7: GitHub-based persistent storage for cross-run tracking
"""

import requests, json, time, hashlib, os
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
    'spain': {'name': 'Spain VFL', 'catName': 'Spain'},
    'germany': {'name': 'Germany VFL', 'catName': 'Germany'},
}

# ── SINGLE-FILE STATE PERSISTENCE ──
# State is loaded from /tmp/vfl_state.json (pre-loaded by bootstrap from GitHub)
# State is saved back to /tmp/vfl_state.json (bootstrap pushes to GitHub after run)
STATE_FILE = '/tmp/vfl_state.json'

_state_cache = None

def _load_state():
    global _state_cache
    if _state_cache is not None:
        return _state_cache
    try:
        with open(STATE_FILE) as f:
            _state_cache = json.load(f)
    except:
        _state_cache = {'predictions': {}, 'blacklist': {}, 'results': [], 'sent': {}, 'updated': 0}
    return _state_cache

def _save_state():
    global _state_cache
    if _state_cache is None:
        return
    _state_cache['updated'] = time.time()
    with open(STATE_FILE, 'w') as f:
        json.dump(_state_cache, f, separators=(',', ':'))

def load_predictions():
    s = _load_state()
    return s.get('predictions', {}), ''

def save_predictions(preds, sha=''):
    s = _load_state()
    s['predictions'] = preds
    _save_state()

def load_blacklist():
    s = _load_state()
    return s.get('blacklist', {}), ''

def save_blacklist(bl, sha=''):
    s = _load_state()
    s['blacklist'] = bl
    _save_state()

def load_results_history():
    s = _load_state()
    r = s.get('results', [])
    if isinstance(r, dict) and 'results' in r:
        r = r['results']
    return r, ''

def save_results_history(results, sha=''):
    s = _load_state()
    s['results'] = results
    _save_state()

def matchup_key(home, away):
    h = (home or '').strip().lower()
    a = (away or '').strip().lower()
    return '|'.join(sorted([h, a]))

# ── DEDUP ──
def load_sent():
    s = _load_state()
    return s.get('sent', {}), ''

def save_sent(d, sha=''):
    s = _load_state()
    s['sent'] = d
    _save_state()

def dedup_key(picks):
    ids = sorted(str(p.get('gid','')) for p in picks if p.get('gid'))
    return hashlib.md5('|'.join(ids).encode()).hexdigest()

def already_sent(key):
    d, sha = load_sent()
    now = time.time()
    d = {k:v for k,v in d.items() if now-v < 21600}
    save_sent(d, sha)
    return key in d

def mark_sent(key):
    d, sha = load_sent()
    d[key] = time.time()
    save_sent(d, sha)

# ── DISCOVERY ──
def discover_all():
    """Get ALL upcoming VFL events from commonThumbnailEvents."""
    r = requests.get('https://www.sportybet.com/api/ng/factsCenter/commonThumbnailEvents', params={
        'sportId': SPORT, 'productId': 3,
    }, headers=HEADERS, timeout=15)
    d = r.json()
    if d.get('bizCode') != 10000:
        print("  warning: Discovery failed: %s" % d.get('message',''))
        return {}
    by_league = defaultdict(list)
    for tour in d.get('data', []):
        cn = tour.get('categoryName', '')
        by_league[cn].extend(tour.get('events', []))
    return by_league

def event_detail(game_id):
    """Fetch full event detail using numeric gameId — pre-match only."""
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
        ms = ev.get('matchStatus')
        if ms and ms not in ('Not start', 'not_started', 0, '0', None):
            return None
        if ev.get('status') not in (0, '0'):
            return None
        return ev
    except:
        return None

def event_result(game_id):
    """Fetch event to check if ended and get score (no matchStatus filter)."""
    try:
        r = requests.get('https://www.sportybet.com/api/ng/factsCenter/event', params={
            'gameId': str(game_id), 'productId': 3
        }, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None
        d = r.json()
        if d.get('bizCode') != 10000:
            return None
        return d.get('data')
    except:
        return None

# ── FAILURE MONITOR + RESULTS ACCUMULATION ──
def check_past_predictions():
    """Check results of predicted matches. Accumulate completed results for Section B."""
    preds, preds_sha = load_predictions()
    blacklist, bl_sha = load_blacklist()
    results_history, rh_sha = load_results_history()
    existing_gids = set(str(r.get('gid','')) for r in results_history)

    if not preds:
        return {'checked': 0, 'won': 0, 'lost': 0, 'pending': 0, 'new_blacklist': [],
                'new_results': 0, 'total_history': len(results_history),
                'preds_sha': preds_sha, 'bl_sha': bl_sha, 'rh_sha': rh_sha}

    checked, won, lost, pending = 0, 0, 0, 0
    new_blacklist_entries = []
    new_results_count = 0

    cutoff = time.time() - 86400
    gids_to_check = [gid for gid, info in preds.items()
                     if info.get('timestamp', 0) > cutoff and info.get('status') != 'settled']

    print("  Checking %d pending predictions..." % len(gids_to_check))

    def fetch_result(gid):
        return (gid, event_result(gid))

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        fetched = list(ex.map(lambda g: fetch_result(g), gids_to_check))

    for gid, ev in fetched:
        if ev is None:
            pending += 1
            continue

        ms = ev.get('matchStatus')
        status = ev.get('status')

        if ms != 'Ended' and status not in (3, '3'):
            pending += 1
            continue

        checked += 1
        score = ev.get('setScore', '')
        try:
            parts = str(score).split(':')
            home_goals = int(parts[0])
            away_goals = int(parts[1])
            total_goals = home_goals + away_goals
        except:
            total_goals = -1
            pending += 1
            continue

        pred_info = preds[gid]
        pred_info['actual_score'] = score
        pred_info['total_goals'] = total_goals
        pred_info['status'] = 'settled'

        if total_goals >= 2:
            won += 1
            pred_info['result'] = 'WON'
        else:
            lost += 1
            pred_info['result'] = 'LOST'
            home = pred_info.get('home', '')
            away = pred_info.get('away', '')
            mk = matchup_key(home, away)
            if mk not in blacklist:
                blacklist[mk] = {'fails': 0, 'history': []}
            blacklist[mk]['fails'] += 1
            blacklist[mk]['last_fail'] = time.time()
            blacklist[mk]['history'].append({
                'score': score,
                'verdict': pred_info.get('verdict', ''),
                'pct': pred_info.get('pct', 0),
                'odds': pred_info.get('odds', 0),
                'time': time.time(),
                'reason': analyze_failure(pred_info, total_goals)
            })
            new_blacklist_entries.append({
                'match': '%s v %s' % (home, away),
                'score': score,
                'verdict': pred_info.get('verdict'),
                'reason': analyze_failure(pred_info, total_goals),
            })

        # ── ACCUMULATE for Section B history ──
        if str(gid) not in existing_gids:
            results_history.append({
                'gid': str(gid),
                'home': pred_info.get('home', ''),
                'away': pred_info.get('away', ''),
                'score': score,
                'home_goals': home_goals,
                'away_goals': away_goals,
                'total_goals': total_goals,
                'start': pred_info.get('start', 0),
                'timestamp': pred_info.get('timestamp', 0),
                'league': pred_info.get('league', ''),
                'settled_at': time.time(),
            })
            existing_gids.add(str(gid))
            new_results_count += 1

    # Prune old predictions (>48h)
    old_cutoff = time.time() - 172800
    for gid in [g for g, info in preds.items() if info.get('timestamp', 0) < old_cutoff]:
        del preds[gid]

    # Prune results history older than 3 days
    hist_cutoff = time.time() - 259200
    results_history = [r for r in results_history if r.get('settled_at', r.get('timestamp', 0)) > hist_cutoff]

    save_predictions(preds, preds_sha)
    save_blacklist(blacklist, bl_sha)
    save_results_history(results_history, rh_sha)

    return {
        'checked': checked,
        'won': won,
        'lost': lost,
        'pending': pending,
        'new_blacklist': new_blacklist_entries,
        'win_rate': round(won / checked * 100, 1) if checked > 0 else 0,
        'new_results': new_results_count,
        'total_history': len(results_history),
    }

def analyze_failure(pred_info, total_goals):
    reasons = []
    pct = pred_info.get('pct', 0)
    sig = pred_info.get('signals', {})

    if total_goals == 0:
        reasons.append("0-0 dead match")
    elif total_goals == 1:
        reasons.append("Only 1 goal scored")

    if pct < 60:
        reasons.append("Low confidence (%d%%)" % pct)

    cs_o15 = sig.get('cs_o15', 0)
    if cs_o15 < 0.50:
        reasons.append("Weak CS signal (%.0f%%)" % (cs_o15 * 100))

    fp11 = sig.get('fp11', 0)
    if fp11 > 0.10:
        reasons.append("1:1 fingerprint detected (%.1f%%)" % (fp11 * 100))

    ou15_prob = sig.get('ou15_prob', 0)
    if ou15_prob < 0.60:
        reasons.append("Low O1.5 prob (%.0f%%)" % (ou15_prob * 100))

    gg_prob = sig.get('gg_prob', 0)
    if gg_prob < 0.35:
        reasons.append("Low GG prob (%.0f%%)" % (gg_prob * 100))

    return '; '.join(reasons) if reasons else 'Unknown'

def is_blacklisted(home, away, blacklist):
    mk = matchup_key(home, away)
    entry = blacklist.get(mk)
    if not entry:
        return False, ''
    fails = entry.get('fails', 0)
    last_fail = entry.get('last_fail', 0)
    if time.time() - last_fail > 604800:
        return False, ''
    if fails >= 2:
        return True, 'Failed %d times (last: %s)' % (fails, entry.get('history', [{}])[-1].get('reason', '?'))
    return False, ''

# ── ALSO HARVEST COMPLETED EVENTS FROM DISCOVERY ──
def harvest_completed_events():
    """Scan recently completed events from discovery to build Section B history faster."""
    results_history, rh_sha = load_results_history()
    existing_gids = set(str(r.get('gid','')) for r in results_history)
    
    try:
        r = requests.get('https://www.sportybet.com/api/ng/factsCenter/commonThumbnailEvents', params={
            'sportId': SPORT, 'productId': 3,
        }, headers=HEADERS, timeout=15)
        d = r.json()
        if d.get('bizCode') != 10000:
            return 0
        
        all_game_ids = []
        for tour in d.get('data', []):
            for ev in tour.get('events', []):
                gid = ev.get('gameId')
                if gid:
                    all_game_ids.append(int(gid))
        
        if not all_game_ids:
            return 0
        
        min_gid = min(all_game_ids)
        scan_gids = list(range(max(1, min_gid - 100), min_gid))
        scan_gids = [g for g in scan_gids if str(g) not in existing_gids]
        
        if not scan_gids:
            return 0
        
        scan_gids = scan_gids[-40:]
        
        print("  Harvesting %d recent completed events for Section B..." % len(scan_gids))
        
        def fetch_ev(gid):
            return (gid, event_result(gid))
        
        new_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            fetched = list(ex.map(lambda g: fetch_ev(g), scan_gids))
        
        for gid, ev in fetched:
            if ev is None:
                continue
            ms = ev.get('matchStatus')
            status = ev.get('status')
            if ms != 'Ended' and status not in (3, '3'):
                continue
            
            score = ev.get('setScore', '')
            try:
                parts = str(score).split(':')
                hg = int(parts[0])
                ag = int(parts[1])
            except:
                continue
            
            home = ev.get('homeTeamName', '')
            away = ev.get('awayTeamName', '')
            start = ev.get('estimateStartTime', 0)
            
            if not home or not away:
                continue
            
            sgid = str(gid)
            if sgid not in existing_gids:
                results_history.append({
                    'gid': sgid,
                    'home': home,
                    'away': away,
                    'score': score,
                    'home_goals': hg,
                    'away_goals': ag,
                    'total_goals': hg + ag,
                    'start': start,
                    'timestamp': (start / 1000) if start > 1000000000000 else start,
                    'settled_at': time.time(),
                })
                existing_gids.add(sgid)
                new_count += 1
        
        if new_count > 0:
            hist_cutoff = time.time() - 259200
            results_history = [r for r in results_history if r.get('settled_at', r.get('timestamp', 0)) > hist_cutoff]
            save_results_history(results_history, rh_sha)
        
        return new_count
    except Exception as e:
        print("  Harvest error: %s" % e)
        return 0


def sum_score(desc):
    try:
        parts = desc.replace(' ','').split(':')
        return int(parts[0]) + int(parts[1])
    except:
        return 0

# ── SECTION A: Pre-match JSON Probability Decoder ──
def sec_a(event):
    """Decode 6 markets in order: CS(45) > HG(23) > AG(24) > OU(18) > FH(68) > GG(29)."""
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

    # Market 18: Over/Under
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
    fp11_flag = sig.get('fp11', 0) > 0.10

    top_cs_prob = max((v['prob'] for d, v in (cs or {}).items()), default=0)
    if top_cs_prob > 0.12:
        conf = 'HIGH'
    elif top_cs_prob > 0.08:
        conf = 'MEDIUM'
    else:
        conf = 'LOW'

    return {
        'sc': sc, 'mx': mx, 'pct': pct,
        'ou15_odds': ou15_odds, 'ou15_prob': ou15_prob, 'ou15_oid': ou15_oid,
        'sweet': sweet, 'fp11': fp11_flag, 'sig': sig, 'conf': conf,
    }

# ── SECTION B: Yesterday Same-Slot Energy Cards ──
def find_slot(history, target_est):
    """Find yesterday's matches in the same time slot (+/- 10 min)."""
    target_dt = datetime.fromtimestamp(target_est / 1000, tz=timezone.utc)
    target_min = target_dt.hour * 60 + target_dt.minute
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yest_start = today_start - timedelta(days=1)
    yest_start_ts = yest_start.timestamp()
    today_start_ts = today_start.timestamp()
    
    yesterday_results = []
    for r in history:
        ts = r.get('timestamp', 0)
        if ts > 1000000000000:
            ts = ts / 1000
        if yest_start_ts <= ts < today_start_ts:
            yesterday_results.append(r)
    
    if not yesterday_results:
        return []
    
    slots = defaultdict(list)
    for r in yesterday_results:
        st = r.get('start', 0)
        if st > 0:
            slots[st].append(r)
    
    best, best_diff = None, 999
    for t in slots:
        dt = datetime.fromtimestamp(t / 1000 if t > 1000000000000 else t, tz=timezone.utc)
        slot_min = dt.hour * 60 + dt.minute
        diff = abs(slot_min - target_min)
        if diff < best_diff:
            best_diff = diff
            best = t
    
    if best is not None and best_diff <= 10:
        return slots[best]
    return []

def energy(slot, home, away):
    """Build energy card from yesterday's same-slot results."""
    sf = None
    hd = {'s': 0, 'c': 0, 't': 0}
    ad = {'s': 0, 'c': 0, 't': 0}
    
    for m in slot:
        h = m.get('home', '')
        a = m.get('away', '')
        hs = m.get('home_goals')
        aws = m.get('away_goals')
        
        if hs is None or aws is None:
            continue
        
        if h == home and a == away:
            sf = {'hs': hs, 'as': aws, 't': hs + aws}
        
        if h == home:
            hd = {'s': hs, 'c': aws, 't': hs + aws}
        elif a == home:
            hd = {'s': aws, 'c': hs, 't': hs + aws}
        
        if h == away:
            ad = {'s': hs, 'c': aws, 't': hs + aws}
        elif a == away:
            ad = {'s': aws, 'c': hs, 't': hs + aws}
    
    return {'sf': sf, 'h': hd, 'a': ad, 'n': len(slot)}

def sec_b(en):
    """Section B: Skip rules (C,D,E) + Scoring rules (R1-R7, max 14 points)."""
    h, a, sf = en['h'], en['a'], en['sf']
    
    if h['t'] >= 4 and a['t'] >= 4:
        return {'skip': True, 'reason': 'Skip-C: Compression', 'sc': 0, 'conf': 'SKIP', 'reasons': ['Skip-C']}
    if h['t'] + a['t'] < 2:
        return {'skip': True, 'reason': 'Skip-D: Low energy', 'sc': 0, 'conf': 'SKIP', 'reasons': ['Skip-D']}
    if sf and sf['t'] == 0:
        return {'skip': True, 'reason': 'Skip-E: Same fix 0-0', 'sc': 0, 'conf': 'SKIP', 'reasons': ['Skip-E']}
    
    pts, reasons = 0, []
    if h['s'] >= 1:
        pts += 2; reasons.append("R1:H scored %d(+2)" % h['s'])
    if a['s'] >= 1:
        pts += 2; reasons.append("R2:A scored %d(+2)" % a['s'])
    if sf and sf['t'] >= 2:
        pts += 2; reasons.append("R3:Fix %d-%d(+2)" % (sf['hs'], sf['as']))
    if h['t'] >= 2:
        pts += 2; reasons.append("R4:H total %d>=2(+2)" % h['t'])
    if a['t'] >= 2:
        pts += 2; reasons.append("R5:A total %d>=2(+2)" % a['t'])
    if h['t'] + a['t'] >= 4:
        pts += 1; reasons.append("R6:Comb %d>=4(+1)" % (h['t'] + a['t']))
    if h['s'] > 0 and h['c'] > 0 and a['s'] > 0 and a['c'] > 0:
        pts += 1; reasons.append("R7:Both S&C(+1)")
    
    if pts >= 10: conf = 'LOCK'
    elif pts >= 6: conf = 'PICK'
    elif pts >= 3: conf = 'CONSIDER'
    else: conf = 'SKIP'
    
    return {
        'skip': conf == 'SKIP',
        'reason': '' if conf != 'SKIP' else 'B:%d<3' % pts,
        'sc': pts, 'conf': conf, 'reasons': reasons,
    }


# ── COMBINED ANALYSIS ──
def analyze(event, blacklist, results_history):
    """Combine Section A + Section B + blacklist check."""
    hn = event.get('homeTeamName') or '?'
    an = event.get('awayTeamName') or '?'
    est = int(event.get('estimateStartTime', 0))
    
    a = sec_a(event)
    
    slot = find_slot(results_history, est)
    en = energy(slot, hn, an)
    has_section_b = len(slot) > 0
    
    if has_section_b:
        b = sec_b(en)
        combined = a['sc'] + b['sc']
        cmax = a['mx'] + 14
        cpct = round(combined / cmax * 100) if cmax > 0 else 0
        
        if b['skip']:
            verdict = 'SKIP'
        elif cpct >= 70:
            verdict = 'LOCK'
        elif cpct >= 50:
            verdict = 'PICK'
        elif cpct >= 35:
            verdict = 'CONSIDER'
        else:
            verdict = 'SKIP'
    else:
        b = {'skip': False, 'reason': 'NO_DATA', 'sc': 0, 'conf': 'N/A', 'reasons': ['No yesterday data']}
        combined = a['sc']
        cmax = a['mx']
        cpct = a['pct']
        
        if cpct >= 75:
            verdict = 'LOCK'
        elif cpct >= 55:
            verdict = 'PICK'
        elif cpct >= 40:
            verdict = 'CONSIDER'
        else:
            verdict = 'SKIP'
    
    if a['ou15_odds'] > 0 and a['ou15_odds'] < SWEET[0]:
        verdict = 'SKIP'
    
    if a['ou15_odds'] <= 0:
        verdict = 'SKIP'
    
    if a['fp11'] and verdict in ('LOCK', 'PICK'):
        verdict = 'PICK' if verdict == 'LOCK' else 'CONSIDER'
    
    bl_hit, bl_reason = is_blacklisted(hn, an, blacklist)
    if bl_hit and verdict in ('LOCK', 'PICK', 'CONSIDER'):
        verdict = 'SKIP'
    
    return {
        'match': '%s v %s' % (hn, an),
        'home': hn,
        'away': an,
        'eid': event.get('eventId', ''),
        'gid': str(event.get('gameId', '')),
        'start': est,
        'a': a,
        'b': b,
        'en': en,
        'has_b': has_section_b,
        'combined': combined,
        'cmax': cmax,
        'cpct': cpct,
        'verdict': verdict,
        'ou15_odds': a['ou15_odds'],
        'ou15_oid': a['ou15_oid'],
        'sweet': a['sweet'],
        'fp11': a['fp11'],
        'conf': a['conf'],
        'bl_hit': bl_hit,
        'bl_reason': bl_reason,
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
    print("    Booking: %d selections" % len(outcomes))
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
        print("    Booking response: %s" % json.dumps(d)[:200])
    except Exception as e:
        print("    Booking failed: %s" % e)
    return None

# ── TELEGRAM ──
def tg_send(text, chat_id=None):
    cid = chat_id or TG_CHAT
    try:
        r = requests.post('%s/sendMessage' % TG_API, json={
            'chat_id': cid, 'text': text,
            'parse_mode': 'HTML', 'disable_web_page_preview': True,
        }, timeout=15)
        d = r.json()
        if d.get('ok'):
            return True
        print("  TG error: %s" % d.get('description', ''))
    except Exception as e:
        print("  TG send failed: %s" % e)
    return False

def format_section(picks, icon, label, code, total_odds):
    if not picks:
        return []
    lines = ["%s <b>%s (%d sel | %.0fx odds)</b>" % (icon, label, len(picks), total_odds), ""]
    by_time = defaultdict(list)
    for p in picks:
        by_time[p.get('start', 0)].append(p)
    for t in sorted(by_time.keys()):
        dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
        lines.append("<b>%s UTC</b>" % dt.strftime('%H:%M'))
        for p in by_time[t]:
            sw = ' [S]' if p['sweet'] else ''
            fp = ' [1:1]' if p['fp11'] else ''
            bconf = p['b']['conf'] if p.get('has_b') else 'N/A'
            bsc = p['b']['sc'] if p.get('has_b') else '-'
            lines.append("  %s %s — O1.5 @%.2f %s%s" % (icon, p['match'], p['ou15_odds'], sw, fp))
            lines.append("      A:%d%% B:%s(%s/14) C:%d%%" % (p['a']['pct'], bconf, bsc, p['cpct']))
        lines.append("")
    lines.append("<b>ODDS: %.0fx</b>" % total_odds)
    if code:
        lines.append("<b>CODE: %s</b>" % code)
        lines.append("sportybet.com/ng/share/%s" % code)
    else:
        lines.append("Code: manual entry required")
    return lines

# ── MAIN SCANNER ──
def run():
    scan_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print("=" * 60)
    print("VFL ENGINE v3.7 — ONIMIX TECH")
    print("Section A + Section B + Failure Monitor + GitHub Persist")
    print(scan_time)
    print("=" * 60)

    print("\n[PERSIST] State management via /tmp/vfl_state.json")

    # ── PHASE 0: Check past predictions + accumulate results ──
    print("\n[PHASE 0] Checking past predictions & accumulating results...")
    monitor = check_past_predictions()
    if monitor['checked'] > 0:
        print("  Results: %d checked | %d won | %d lost | %.1f%% win rate" % (
            monitor['checked'], monitor['won'], monitor['lost'], monitor['win_rate']))
        if monitor['new_blacklist']:
            print("  NEW BLACKLIST entries:")
            for bl in monitor['new_blacklist']:
                print("    X %s | %s | %s" % (bl['match'], bl['score'], bl['reason']))
    else:
        print("  No settled predictions to check yet")
    print("  Pending: %d | New results: %d | Total history: %d" % (
        monitor.get('pending', 0), monitor.get('new_results', 0), monitor.get('total_history', 0)))

    # ── PHASE 0.5: Harvest completed events for Section B ──
    print("\n[PHASE 0.5] Harvesting completed events for Section B...")
    harvested = harvest_completed_events()
    print("  Harvested %d new completed events" % harvested)
    
    blacklist, _ = load_blacklist()
    results_history, _ = load_results_history()
    bl_count = sum(1 for v in blacklist.values() if v.get('fails', 0) >= 2)
    print("  Active blacklist: %d matchups" % bl_count)
    print("  Results history: %d matches available for Section B" % len(results_history))

    # ── PHASE 1: Discover events ──
    print("\n[PHASE 1] Discovering all upcoming VFL events...")
    all_upcoming = discover_all()

    all_results = []

    for lk, cfg in LEAGUES.items():
        cat_name = cfg['catName']
        events = all_upcoming.get(cat_name, [])
        print("\n  %s: %d upcoming matches" % (cfg['name'], len(events)))

        if not events:
            continue

        rounds = sorted(set(e['estimateStartTime'] for e in events))
        for t in rounds[:5]:
            dt = datetime.fromtimestamp(t/1000, tz=timezone.utc)
            n = sum(1 for e in events if e['estimateStartTime'] == t)
            print("    %s UTC (%d matches)" % (dt.strftime('%H:%M'), n))
        if len(rounds) > 5:
            print("    ... +%d more rounds" % (len(rounds) - 5))

        game_ids = [e.get('gameId') for e in events if e.get('gameId')]
        print("  Fetching %d event details..." % len(game_ids))

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
            details = list(ex.map(event_detail, game_ids))

        valid = [d for d in details if d is not None]
        print("  Got %d valid events" % len(valid))

        for ev in valid:
            r = analyze(ev, blacklist, results_history)
            emoji = {'LOCK': 'L', 'PICK': 'P', 'CONSIDER': '?', 'SKIP': 'X'}[r['verdict']]
            bl = ' [BL]' if r['bl_hit'] else ''
            binfo = 'B:%s(%d)' % (r['b']['conf'], r['b']['sc']) if r['has_b'] else 'B:N/A'
            print("  [%s] %s: A:%d%% %s C:%d%% O1.5@%.2f %s%s" % (
                emoji, r['match'], r['a']['pct'], binfo, r['cpct'],
                r['ou15_odds'], r['conf'], bl
            ))
            all_results.append(r)

    # ── PHASE 2: Sort and filter ──
    locks = [r for r in all_results if r['verdict'] == 'LOCK']
    picks = [r for r in all_results if r['verdict'] == 'PICK']
    cons = [r for r in all_results if r['verdict'] == 'CONSIDER']
    skips = [r for r in all_results if r['verdict'] == 'SKIP']
    bl_skips = [r for r in all_results if r['bl_hit']]
    b_active = sum(1 for r in all_results if r['has_b'])

    print("\n" + "=" * 60)
    print("L:%d P:%d ?:%d X:%d | BL:%d | B-active:%d/%d" % (
        len(locks), len(picks), len(cons), len(skips), len(bl_skips),
        b_active, len(all_results)))

    bookable = locks + picks
    if not bookable:
        print("No bookable picks found")
        msg = "VFL Scan %s\nNo bookable picks across %d matches.\nSection B: %d/%d active" % (
            scan_time, len(all_results), b_active, len(all_results))
        if monitor['checked'] > 0:
            msg += "\n\nMonitor: %d/%d won (%.1f%%)" % (monitor['won'], monitor['checked'], monitor['win_rate'])
        tg_send(msg, TG_CHAT)
        return

    dk = dedup_key(bookable)
    if already_sent(dk):
        print("Already sent this exact combo — skipping")
        return

    locks.sort(key=lambda x: (x['sweet'], x['cpct']), reverse=True)
    picks.sort(key=lambda x: (x['sweet'], x['cpct']), reverse=True)

    lock_odds = 1.0
    for p in locks:
        lock_odds *= p['ou15_odds']
    pick_odds = 1.0
    for p in picks:
        pick_odds *= p['ou15_odds']

    print("\nLOCK ACCA: %d @ %.1fx" % (len(locks), lock_odds))
    print("PICK ACCA: %d @ %.1fx" % (len(picks), pick_odds))

    # ── PHASE 3: Generate booking codes ──
    lock_code = None
    pick_code = None

    if locks:
        print("\nGenerating LOCK booking code...")
        lock_code = gen_booking(locks)
        if lock_code:
            print("  LOCK Code: %s" % lock_code)

    if picks:
        print("Generating PICK booking code...")
        pick_code = gen_booking(picks)
        if pick_code:
            print("  PICK Code: %s" % pick_code)

    # ── PHASE 4: Track predictions for monitoring ──
    preds, preds_sha = load_predictions()
    for p in bookable:
        gid = p['gid']
        preds[gid] = {
            'match': p['match'],
            'home': p['home'],
            'away': p['away'],
            'verdict': p['verdict'],
            'pct': p['cpct'],
            'odds': p['ou15_odds'],
            'signals': p['a']['sig'],
            'conf': p['conf'],
            'start': p['start'],
            'b_score': p['b']['sc'],
            'b_conf': p['b']['conf'],
            'has_b': p['has_b'],
            'timestamp': time.time(),
            'status': 'pending',
        }
    save_predictions(preds, preds_sha)
    print("\nTracking %d predictions for monitoring" % len(bookable))

    # ── PHASE 5: Telegram delivery ──
    total_sel = len(locks) + len(picks)
    lines = [
        "<b>VFL MEGA — ONIMIX ELITE v3.7</b>",
        scan_time,
        "%d selections from %d analyzed" % (total_sel, len(all_results)),
        "L:%d | P:%d | Section B: %d/%d active" % (len(locks), len(picks), b_active, len(all_results)),
    ]

    if monitor['checked'] > 0:
        lines.append("")
        lines.append("<b>MONITOR:</b> %d/%d won (%.1f%%)" % (
            monitor['won'], monitor['checked'], monitor['win_rate']))
        if monitor['new_blacklist']:
            for bl in monitor['new_blacklist'][:3]:
                lines.append("  X %s %s" % (bl['match'], bl['score']))

    lines.append("")

    if locks:
        lines.extend(format_section(locks, 'L', 'LOCK ACCUMULATOR', lock_code, lock_odds))
        lines.append("")

    if picks:
        lines.extend(format_section(picks, 'P', 'PICK ACCUMULATOR', pick_code, pick_odds))
        lines.append("")

    if bl_skips:
        lines.append("<i>Blacklisted: %d matches skipped</i>" % len(bl_skips))

    lines.extend([
        "",
        "<i>Engine v3.7 | A+B Active | Monitor On | GitHub Persist | ONIMIX TECH</i>",
    ])

    msg = '\n'.join(lines)

    if len(msg) > 4000:
        if locks:
            lock_msg = '\n'.join([
                "<b>VFL MEGA — ONIMIX ELITE v3.7 (1/2)</b>",
                scan_time, "",
            ] + format_section(locks, 'L', 'LOCK ACCUMULATOR', lock_code, lock_odds))
            tg_send(lock_msg, TG_CHAT)
        if picks:
            pick_msg = '\n'.join([
                "<b>VFL MEGA — ONIMIX ELITE v3.7 (2/2)</b>",
                scan_time, "",
            ] + format_section(picks, 'P', 'PICK ACCUMULATOR', pick_code, pick_odds) + [
                "", "<i>Engine v3.7 | A+B Active | ONIMIX TECH</i>",
            ])
            tg_send(pick_msg, TG_CHAT)
    else:
        tg_send(msg, TG_CHAT)

    mark_sent(dk)
    print("\nScan complete!")

if __name__ == '__main__':
    run()
