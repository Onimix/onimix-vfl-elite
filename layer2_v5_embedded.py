#!/usr/bin/env python3
"""
ONIMIX VFL Layer 2 — 12-Layer Scoring Engine v5
Rebuilt with LIVE VFL API (sr:sport:202120001)
Team profiles from 11,822 fresh matches + ONIMIX scoring logic
"""
import requests, json, hashlib, time, os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

TG_TOKEN = "8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
TG_CHAT  = "1745848158"
BOOK_URL = "https://www.sportybet.com/api/ng/orders/share"
DEDUP_FILE = "/tmp/vfl_dedup_L2.json"
DEDUP_TTL  = 3600
WAT = timezone(timedelta(hours=1))
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

VFL_SPORT = "sr:sport:202120001"
LEAGUES = {
    1: ("sv:category:202120001", "sv:league:1", "🏴 ENG"),
    2: ("sv:category:202120002", "sv:league:2", "🇪🇸 ESP"),
    3: ("sv:category:202120003", "sv:league:3", "🇮🇹 ITA"),
    4: ("sv:category:202120004", "sv:league:4", "🇩🇪 GER"),
    5: ("sv:category:202120005", "sv:league:5", "🇫🇷 FRA"),
}
LEAGUE_NAMES = {1: "England", 2: "Spain", 3: "Italy", 4: "Germany", 5: "France"}

# ─── BUILD TEAM PROFILES FROM FRESH DATA ───
def build_team_profiles():
    """Return pre-computed team profiles"""
    return json.loads('{"England|BHA":{"g":257,"as":1.07,"ac":1.33,"o05r":0.9261,"o15r":0.6887,"o25r":0.4047,"btts":0.4903,"ho15":0.7063,"ao15":0.6718,"ravg":3.1,"stk":3},"England|EVE":{"g":257,"as":1.19,"ac":1.28,"o05r":0.9105,"o15r":0.716,"o25r":0.4436,"btts":0.463,"ho15":0.7222,"ao15":0.7099,"ravg":3.0,"stk":4},"England|BOU":{"g":257,"as":1.27,"ac":1.41,"o05r":0.9261,"o15r":0.7432,"o25r":0.4669,"btts":0.5525,"ho15":0.7717,"ao15":0.7154,"ravg":2.9,"stk":5},"England|TOT":{"g":257,"as":1.46,"ac":1.53,"o05r":0.9611,"o15r":0.8132,"o25r":0.5798,"btts":0.5992,"ho15":0.8346,"ao15":0.7923,"ravg":2.4,"stk":2},"England|BRE":{"g":257,"as":1.37,"ac":1.47,"o05r":0.9494,"o15r":0.7432,"o25r":0.5447,"btts":0.5798,"ho15":0.6992,"ao15":0.7903,"ravg":3.3,"stk":5},"England|ARS":{"g":257,"as":1.63,"ac":1.3,"o05r":0.965,"o15r":0.7743,"o25r":0.5564,"btts":0.5953,"ho15":0.7669,"ao15":0.7823,"ravg":3.0,"stk":5},"England|CRY":{"g":257,"as":1.75,"ac":1.45,"o05r":0.9844,"o15r":0.8171,"o25r":0.5759,"btts":0.6226,"ho15":0.8462,"ao15":0.7874,"ravg":2.3,"stk":3},"England|AST":{"g":257,"as":1.39,"ac":1.74,"o05r":0.93,"o15r":0.7665,"o25r":0.5603,"btts":0.6187,"ho15":0.876,"ao15":0.6562,"ravg":3.9,"stk":5},"England|FOR":{"g":257,"as":1.35,"ac":1.48,"o05r":0.9455,"o15r":0.7393,"o25r":0.5525,"btts":0.572,"ho15":0.7121,"ao15":0.768,"ravg":2.9,"stk":3},"England|SUN":{"g":257,"as":1.21,"ac":1.31,"o05r":0.9222,"o15r":0.7043,"o25r":0.463,"btts":0.4903,"ho15":0.5846,"ao15":0.8268,"ravg":2.8,"stk":3},"England|FUL":{"g":257,"as":1.33,"ac":1.42,"o05r":0.9377,"o15r":0.786,"o25r":0.5331,"btts":0.5837,"ho15":0.808,"ao15":0.7652,"ravg":2.0,"stk":3},"England|BUR":{"g":257,"as":1.24,"ac":1.49,"o05r":0.9144,"o15r":0.6809,"o25r":0.5097,"btts":0.5292,"ho15":0.616,"ao15":0.7424,"ravg":2.1,"stk":0},"England|LEE":{"g":257,"as":1.27,"ac":1.3,"o05r":0.9027,"o15r":0.7393,"o25r":0.4669,"btts":0.5292,"ho15":0.68,"ao15":0.7955,"ravg":2.4,"stk":2},"England|MCI":{"g":257,"as":1.75,"ac":1.11,"o05r":0.9222,"o15r":0.7588,"o25r":0.5097,"btts":0.4903,"ho15":0.7258,"ao15":0.7895,"ravg":2.7,"stk":4},"England|LIV":{"g":257,"as":1.65,"ac":1.37,"o05r":0.9572,"o15r":0.8093,"o25r":0.5914,"btts":0.5953,"ho15":0.8333,"ao15":0.784,"ravg":1.8,"stk":3},"England|MUN":{"g":257,"as":1.49,"ac":1.47,"o05r":0.93,"o15r":0.7938,"o25r":0.5914,"btts":0.6187,"ho15":0.8182,"ao15":0.768,"ravg":2.7,"stk":3},"England|WHU":{"g":257,"as":1.26,"ac":1.48,"o05r":0.9455,"o15r":0.7315,"o25r":0.5097,"btts":0.5331,"ho15":0.7422,"ao15":0.7209,"ravg":2.8,"stk":4},"England|CHE":{"g":257,"as":1.81,"ac":1.47,"o05r":0.9416,"o15r":0.8638,"o25r":0.7004,"btts":0.6226,"ho15":0.8976,"ao15":0.8308,"ravg":3.8,"stk":5},"England|WOL":{"g":257,"as":1.18,"ac":1.42,"o05r":0.9261,"o15r":0.7471,"o25r":0.5019,"btts":0.537,"ho15":0.7538,"ao15":0.7402,"ravg":2.2,"stk":3},"England|NEW":{"g":257,"as":1.74,"ac":1.57,"o05r":0.9805,"o15r":0.8599,"o25r":0.6304,"btts":0.6537,"ho15":0.876,"ao15":0.8438,"ravg":3.1,"stk":5},"Spain|BIL":{"g":256,"as":1.27,"ac":0.99,"o05r":0.9062,"o15r":0.6914,"o25r":0.4219,"btts":0.457,"ho15":0.7424,"ao15":0.6371,"ravg":1.8,"stk":4},"Spain|ALA":{"g":256,"as":1.19,"ac":1.16,"o05r":0.8984,"o15r":0.6797,"o25r":0.4492,"btts":0.4766,"ho15":0.6538,"ao15":0.7063,"ravg":1.9,"stk":2},"Spain|ESP":{"g":256,"as":1.04,"ac":1.25,"o05r":0.8945,"o15r":0.6523,"o25r":0.3984,"btts":0.457,"ho15":0.6615,"ao15":0.6429,"ravg":2.1,"stk":3},"Spain|VIL":{"g":256,"as":1.26,"ac":1.07,"o05r":0.9141,"o15r":0.6445,"o25r":0.4219,"btts":0.457,"ho15":0.622,"ao15":0.6667,"ravg":2.1,"stk":4},"Spain|FCB":{"g":256,"as":1.49,"ac":1.0,"o05r":0.9336,"o15r":0.7188,"o25r":0.4844,"btts":0.4961,"ho15":0.6935,"ao15":0.7424,"ravg":2.3,"stk":4},"Spain|CEL":{"g":256,"as":0.99,"ac":1.25,"o05r":0.9102,"o15r":0.6758,"o25r":0.4102,"btts":0.4414,"ho15":0.6855,"ao15":0.6667,"ravg":1.9,"stk":4},"Spain|GET":{"g":256,"as":1.1,"ac":1.28,"o05r":0.9258,"o15r":0.6797,"o25r":0.4453,"btts":0.4688,"ho15":0.6929,"ao15":0.6667,"ravg":1.7,"stk":2},"Spain|ATM":{"g":256,"as":1.23,"ac":1.15,"o05r":0.9062,"o15r":0.6836,"o25r":0.4453,"btts":0.4609,"ho15":0.7381,"ao15":0.6308,"ravg":1.6,"stk":4},"Spain|LEV":{"g":256,"as":1.25,"ac":1.32,"o05r":0.9141,"o15r":0.7148,"o25r":0.4922,"btts":0.5234,"ho15":0.6905,"ao15":0.7385,"ravg":2.9,"stk":4},"Spain|RMA":{"g":256,"as":1.41,"ac":1.07,"o05r":0.9258,"o15r":0.7188,"o25r":0.4531,"btts":0.4844,"ho15":0.7016,"ao15":0.7348,"ravg":1.9,"stk":3},"Spain|OSA":{"g":256,"as":0.98,"ac":1.12,"o05r":0.8711,"o15r":0.6133,"o25r":0.3555,"btts":0.4219,"ho15":0.5833,"ao15":0.6452,"ravg":2.4,"stk":3},"Spain|RSO":{"g":256,"as":1.06,"ac":1.25,"o05r":0.8945,"o15r":0.6719,"o25r":0.4414,"btts":0.5078,"ho15":0.7364,"ao15":0.6063,"ravg":2.2,"stk":4},"Spain|OVI":{"g":256,"as":1.12,"ac":1.07,"o05r":0.8984,"o15r":0.6367,"o25r":0.3828,"btts":0.4219,"ho15":0.5846,"ao15":0.6905,"ravg":2.2,"stk":3},"Spain|ELC":{"g":256,"as":1.23,"ac":1.21,"o05r":0.8984,"o15r":0.6992,"o25r":0.4492,"btts":0.4766,"ho15":0.6328,"ao15":0.7656,"ravg":2.6,"stk":4},"Spain|RAY":{"g":256,"as":0.98,"ac":1.15,"o05r":0.8711,"o15r":0.6484,"o25r":0.3516,"btts":0.4336,"ho15":0.5969,"ao15":0.7008,"ravg":1.4,"stk":2},"Spain|VCF":{"g":256,"as":0.89,"ac":1.2,"o05r":0.9102,"o15r":0.6484,"o25r":0.3164,"btts":0.3984,"ho15":0.6984,"ao15":0.6,"ravg":2.3,"stk":3},"Spain|RBB":{"g":256,"as":1.2,"ac":1.08,"o05r":0.8906,"o15r":0.6445,"o25r":0.4414,"btts":0.418,"ho15":0.6667,"ao15":0.6231,"ravg":1.6,"stk":2},"Spain|MAL":{"g":256,"as":1.03,"ac":1.17,"o05r":0.8984,"o15r":0.6328,"o25r":0.3789,"btts":0.4258,"ho15":0.68,"ao15":0.5878,"ravg":2.4,"stk":4},"Spain|SEV":{"g":256,"as":1.17,"ac":1.29,"o05r":0.9023,"o15r":0.6719,"o25r":0.4727,"btts":0.4805,"ho15":0.687,"ao15":0.656,"ravg":2.3,"stk":3},"Spain|GIR":{"g":256,"as":1.23,"ac":1.06,"o05r":0.8828,"o15r":0.6562,"o25r":0.457,"btts":0.4414,"ho15":0.6418,"ao15":0.6721,"ravg":3.0,"stk":2},"Italy|FIO":{"g":257,"as":1.22,"ac":1.32,"o05r":0.9183,"o15r":0.7315,"o25r":0.4708,"btts":0.5486,"ho15":0.7615,"ao15":0.7008,"ravg":2.1,"stk":4},"Italy|BFC":{"g":257,"as":1.14,"ac":1.02,"o05r":0.8794,"o15r":0.6187,"o25r":0.3891,"btts":0.4358,"ho15":0.6328,"ao15":0.6047,"ravg":2.3,"stk":3},"Italy|GEN":{"g":257,"as":1.13,"ac":1.18,"o05r":0.9066,"o15r":0.6459,"o25r":0.428,"btts":0.4514,"ho15":0.6457,"ao15":0.6462,"ravg":1.9,"stk":3},"Italy|NAP":{"g":257,"as":0.99,"ac":1.17,"o05r":0.8949,"o15r":0.6265,"o25r":0.3813,"btts":0.4436,"ho15":0.6349,"ao15":0.6183,"ravg":1.6,"stk":2},"Italy|INT":{"g":257,"as":1.53,"ac":1.01,"o05r":0.9416,"o15r":0.7198,"o25r":0.4553,"btts":0.4825,"ho15":0.7339,"ao15":0.7068,"ravg":2.9,"stk":5},"Italy|USC":{"g":257,"as":1.13,"ac":1.24,"o05r":0.8872,"o15r":0.7004,"o25r":0.4163,"btts":0.4942,"ho15":0.648,"ao15":0.75,"ravg":1.8,"stk":3},"Italy|JUV":{"g":257,"as":1.11,"ac":1.09,"o05r":0.9066,"o15r":0.6381,"o25r":0.3502,"btts":0.4241,"ho15":0.6172,"ao15":0.6589,"ravg":2.1,"stk":4},"Italy|ACM":{"g":257,"as":1.34,"ac":1.13,"o05r":0.9377,"o15r":0.7043,"o25r":0.428,"btts":0.4942,"ho15":0.7258,"ao15":0.6842,"ravg":3.2,"stk":4},"Italy|LAZ":{"g":257,"as":1.05,"ac":1.18,"o05r":0.9377,"o15r":0.6498,"o25r":0.3658,"btts":0.4436,"ho15":0.6336,"ao15":0.6667,"ravg":1.8,"stk":2},"Italy|LEC":{"g":257,"as":0.97,"ac":1.24,"o05r":0.8872,"o15r":0.6265,"o25r":0.4047,"btts":0.4591,"ho15":0.5969,"ao15":0.6562,"ravg":2.8,"stk":4},"Italy|PIS":{"g":257,"as":1.25,"ac":1.22,"o05r":0.9377,"o15r":0.7004,"o25r":0.4553,"btts":0.4591,"ho15":0.7462,"ao15":0.6535,"ravg":2.3,"stk":3},"Italy|ATA":{"g":257,"as":1.42,"ac":1.13,"o05r":0.9455,"o15r":0.7471,"o25r":0.428,"btts":0.5253,"ho15":0.7969,"ao15":0.6977,"ravg":1.9,"stk":3},"Italy|ROM":{"g":257,"as":1.31,"ac":1.07,"o05r":0.8949,"o15r":0.6654,"o25r":0.4202,"btts":0.463,"ho15":0.6718,"ao15":0.6587,"ravg":2.7,"stk":4},"Italy|CAG":{"g":257,"as":1.16,"ac":1.37,"o05r":0.8949,"o15r":0.716,"o25r":0.5058,"btts":0.5486,"ho15":0.7634,"ao15":0.6667,"ravg":3.2,"stk":4},"Italy|SAS":{"g":257,"as":1.09,"ac":1.12,"o05r":0.8949,"o15r":0.6187,"o25r":0.3619,"btts":0.463,"ho15":0.5338,"ao15":0.7097,"ravg":1.7,"stk":2},"Italy|TOR":{"g":257,"as":0.96,"ac":1.09,"o05r":0.8872,"o15r":0.6109,"o25r":0.3152,"btts":0.3774,"ho15":0.6183,"ao15":0.6032,"ravg":2.8,"stk":5},"Italy|UDI":{"g":257,"as":0.92,"ac":1.26,"o05r":0.8716,"o15r":0.6148,"o25r":0.3852,"btts":0.4163,"ho15":0.632,"ao15":0.5985,"ravg":2.2,"stk":3},"Italy|COM":{"g":257,"as":1.26,"ac":1.16,"o05r":0.9261,"o15r":0.7004,"o25r":0.4163,"btts":0.4903,"ho15":0.6585,"ao15":0.7388,"ravg":1.6,"stk":1},"Italy|VER":{"g":257,"as":1.21,"ac":1.16,"o05r":0.9261,"o15r":0.6576,"o25r":0.4047,"btts":0.4669,"ho15":0.6489,"ao15":0.6667,"ravg":2.9,"stk":3},"Italy|PAR":{"g":257,"as":1.03,"ac":1.08,"o05r":0.9105,"o15r":0.6148,"o25r":0.3268,"btts":0.428,"ho15":0.6148,"ao15":0.6148,"ravg":2.4,"stk":4},"Germany|BVB":{"g":229,"as":1.43,"ac":1.14,"o05r":0.9039,"o15r":0.7424,"o25r":0.4672,"btts":0.4803,"ho15":0.8136,"ao15":0.6667,"ravg":3.0,"stk":4},"Germany|WOB":{"g":229,"as":1.14,"ac":1.33,"o05r":0.9127,"o15r":0.7031,"o25r":0.4323,"btts":0.5153,"ho15":0.7241,"ao15":0.6814,"ravg":2.2,"stk":4},"Germany|HSV":{"g":229,"as":1.21,"ac":1.42,"o05r":0.9258,"o15r":0.7074,"o25r":0.5022,"btts":0.5066,"ho15":0.5982,"ao15":0.812,"ravg":3.0,"stk":3},"Germany|FCA":{"g":229,"as":1.28,"ac":1.3,"o05r":0.917,"o15r":0.7118,"o25r":0.4803,"btts":0.524,"ho15":0.7207,"ao15":0.7034,"ravg":2.5,"stk":3},"Germany|KOE":{"g":229,"as":1.17,"ac":1.43,"o05r":0.9039,"o15r":0.7249,"o25r":0.4934,"btts":0.5284,"ho15":0.75,"ao15":0.6991,"ravg":2.5,"stk":3},"Germany|HDH":{"g":229,"as":1.17,"ac":1.2,"o05r":0.9039,"o15r":0.6987,"o25r":0.3974,"btts":0.4672,"ho15":0.7257,"ao15":0.6724,"ravg":2.6,"stk":4},"Germany|LEV":{"g":229,"as":1.77,"ac":1.0,"o05r":0.9389,"o15r":0.7686,"o25r":0.5546,"btts":0.5677,"ho15":0.7797,"ao15":0.7568,"ravg":2.9,"stk":3},"Germany|BMU":{"g":229,"as":1.39,"ac":1.34,"o05r":0.9432,"o15r":0.7642,"o25r":0.5109,"btts":0.5895,"ho15":0.7,"ao15":0.8349,"ravg":2.4,"stk":3},"Germany|RBL":{"g":229,"as":1.53,"ac":1.17,"o05r":0.9345,"o15r":0.7904,"o25r":0.5153,"btts":0.5371,"ho15":0.7232,"ao15":0.8547,"ravg":2.5,"stk":2},"Germany|VFB":{"g":229,"as":1.41,"ac":1.2,"o05r":0.9127,"o15r":0.7118,"o25r":0.4716,"btts":0.5328,"ho15":0.7455,"ao15":0.6807,"ravg":2.3,"stk":4},"Germany|SCF":{"g":229,"as":1.26,"ac":1.41,"o05r":0.952,"o15r":0.7686,"o25r":0.4716,"btts":0.5633,"ho15":0.8205,"ao15":0.7143,"ravg":2.2,"stk":4},"Germany|MAI":{"g":229,"as":1.17,"ac":1.11,"o05r":0.8821,"o15r":0.6769,"o25r":0.4017,"btts":0.4367,"ho15":0.7018,"ao15":0.6522,"ravg":1.9,"stk":3},"Germany|SGE":{"g":229,"as":1.22,"ac":1.44,"o05r":0.917,"o15r":0.7424,"o25r":0.5197,"btts":0.5066,"ho15":0.7265,"ao15":0.7589,"ravg":3.5,"stk":4},"Germany|STP":{"g":229,"as":1.18,"ac":1.18,"o05r":0.8952,"o15r":0.6681,"o25r":0.4454,"btts":0.4803,"ho15":0.6087,"ao15":0.7281,"ravg":2.2,"stk":2},"Germany|TSG":{"g":229,"as":1.4,"ac":1.56,"o05r":0.9258,"o15r":0.821,"o25r":0.5284,"btts":0.5721,"ho15":0.7788,"ao15":0.8621,"ravg":2.4,"stk":2},"Germany|BMG":{"g":229,"as":1.18,"ac":1.51,"o05r":0.9301,"o15r":0.7336,"o25r":0.5153,"btts":0.5633,"ho15":0.7054,"ao15":0.7607,"ravg":2.8,"stk":3},"Germany|UNI":{"g":229,"as":1.04,"ac":1.25,"o05r":0.9039,"o15r":0.6812,"o25r":0.4017,"btts":0.4672,"ho15":0.7478,"ao15":0.614,"ravg":2.6,"stk":3},"Germany|SVW":{"g":229,"as":1.16,"ac":1.14,"o05r":0.8865,"o15r":0.6594,"o25r":0.4236,"btts":0.4629,"ho15":0.6964,"ao15":0.6239,"ravg":3.1,"stk":4},"France|AMO":{"g":229,"as":1.46,"ac":1.17,"o05r":0.9039,"o15r":0.738,"o25r":0.4934,"btts":0.5022,"ho15":0.7207,"ao15":0.7542,"ravg":1.9,"stk":2},"France|LIL":{"g":229,"as":1.48,"ac":1.23,"o05r":0.9345,"o15r":0.7467,"o25r":0.4847,"btts":0.4891,"ho15":0.7568,"ao15":0.7373,"ravg":2.4,"stk":4},"France|ANG":{"g":229,"as":1.16,"ac":1.49,"o05r":0.9039,"o15r":0.7336,"o25r":0.4716,"btts":0.5284,"ho15":0.735,"ao15":0.7321,"ravg":2.1,"stk":4},"France|OLM":{"g":229,"as":1.33,"ac":1.33,"o05r":0.9301,"o15r":0.7598,"o25r":0.4629,"btts":0.5546,"ho15":0.7391,"ao15":0.7807,"ravg":2.7,"stk":5},"France|B29":{"g":229,"as":1.36,"ac":1.3,"o05r":0.9083,"o15r":0.69,"o25r":0.4847,"btts":0.5066,"ho15":0.6106,"ao15":0.7672,"ravg":2.8,"stk":4},"France|AUX":{"g":229,"as":1.2,"ac":1.51,"o05r":0.952,"o15r":0.7773,"o25r":0.5066,"btts":0.5415,"ho15":0.8182,"ao15":0.7395,"ravg":2.2,"stk":2},"France|LOR":{"g":229,"as":1.6,"ac":1.34,"o05r":0.9694,"o15r":0.7904,"o25r":0.5066,"btts":0.5633,"ho15":0.7966,"ao15":0.7838,"ravg":2.2,"stk":4},"France|PFC":{"g":229,"as":1.41,"ac":1.27,"o05r":0.9258,"o15r":0.7336,"o25r":0.5066,"btts":0.559,"ho15":0.7521,"ao15":0.7143,"ravg":1.7,"stk":2},"France|LYO":{"g":229,"as":1.32,"ac":1.31,"o05r":0.9258,"o15r":0.738,"o25r":0.4629,"btts":0.5109,"ho15":0.7043,"ao15":0.7719,"ravg":2.6,"stk":3},"France|NCE":{"g":229,"as":1.28,"ac":1.23,"o05r":0.9083,"o15r":0.7118,"o25r":0.4585,"btts":0.4978,"ho15":0.708,"ao15":0.7155,"ravg":1.8,"stk":3},"France|NAN":{"g":229,"as":1.08,"ac":1.41,"o05r":0.9083,"o15r":0.738,"o25r":0.4585,"btts":0.476,"ho15":0.823,"ao15":0.6552,"ravg":3.2,"stk":5},"France|LEH":{"g":229,"as":1.05,"ac":1.4,"o05r":0.9127,"o15r":0.6725,"o25r":0.4585,"btts":0.4541,"ho15":0.5982,"ao15":0.7436,"ravg":2.4,"stk":4},"France|REN":{"g":229,"as":1.39,"ac":1.35,"o05r":0.9083,"o15r":0.7467,"o25r":0.5546,"btts":0.6026,"ho15":0.7179,"ao15":0.7768,"ravg":2.5,"stk":3},"France|LEN":{"g":229,"as":1.21,"ac":1.29,"o05r":0.9214,"o15r":0.7205,"o25r":0.4672,"btts":0.5066,"ho15":0.807,"ao15":0.6348,"ravg":2.3,"stk":3},"France|STR":{"g":229,"as":1.22,"ac":1.35,"o05r":0.9214,"o15r":0.7424,"o25r":0.5066,"btts":0.524,"ho15":0.7881,"ao15":0.6937,"ravg":2.5,"stk":3},"France|PSG":{"g":229,"as":1.46,"ac":1.23,"o05r":0.952,"o15r":0.7642,"o25r":0.4803,"btts":0.524,"ho15":0.7917,"ao15":0.7339,"ravg":2.8,"stk":5},"France|TOU":{"g":229,"as":1.33,"ac":1.17,"o05r":0.9127,"o15r":0.738,"o25r":0.441,"btts":0.5502,"ho15":0.7544,"ao15":0.7217,"ravg":2.7,"stk":4},"France|MET":{"g":229,"as":1.34,"ac":1.27,"o05r":0.9214,"o15r":0.7162,"o25r":0.476,"btts":0.5415,"ho15":0.6283,"ao15":0.8017,"ravg":1.6,"stk":2}}')

def _old_build_team_profiles():
    try:
        with open("/home/user/vfl_fresh_7days.json") as f:
            matches = json.load(f)
    except:
        return {}
    
    teams = defaultdict(lambda: {
        "games": 0, "goals_scored": 0, "goals_conceded": 0,
        "o05": 0, "o15": 0, "o25": 0, "btts": 0,
        "home_games": 0, "home_o15": 0,
        "away_games": 0, "away_o15": 0,
        "recent_totals": [],
        "league": ""
    })
    
    for m in matches:
        score = m["score"].split(":")
        hg, ag = int(score[0]), int(score[1])
        total = hg + ag
        lg = m["league"]
        
        # Home team
        hk = f"{lg}|{m['home']}"
        teams[hk]["games"] += 1
        teams[hk]["goals_scored"] += hg
        teams[hk]["goals_conceded"] += ag
        teams[hk]["o05"] += 1 if total >= 1 else 0
        teams[hk]["o15"] += 1 if total >= 2 else 0
        teams[hk]["o25"] += 1 if total >= 3 else 0
        teams[hk]["btts"] += 1 if (hg >= 1 and ag >= 1) else 0
        teams[hk]["home_games"] += 1
        teams[hk]["home_o15"] += 1 if total >= 2 else 0
        teams[hk]["recent_totals"].append(total)
        teams[hk]["league"] = lg
        
        # Away team
        ak = f"{lg}|{m['away']}"
        teams[ak]["games"] += 1
        teams[ak]["goals_scored"] += ag
        teams[ak]["goals_conceded"] += hg
        teams[ak]["o05"] += 1 if total >= 1 else 0
        teams[ak]["o15"] += 1 if total >= 2 else 0
        teams[ak]["o25"] += 1 if total >= 3 else 0
        teams[ak]["btts"] += 1 if (hg >= 1 and ag >= 1) else 0
        teams[ak]["away_games"] += 1
        teams[ak]["away_o15"] += 1 if total >= 2 else 0
        teams[ak]["recent_totals"].append(total)
        teams[ak]["league"] = lg
    
    # Compute rates
    profiles = {}
    for key, t in teams.items():
        if t["games"] < 3:
            continue
        profiles[key] = {
            "games": t["games"],
            "avg_scored": round(t["goals_scored"] / t["games"], 2),
            "avg_conceded": round(t["goals_conceded"] / t["games"], 2),
            "o05_rate": round(t["o05"] / t["games"], 4),
            "o15_rate": round(t["o15"] / t["games"], 4),
            "o25_rate": round(t["o25"] / t["games"], 4),
            "btts_rate": round(t["btts"] / t["games"], 4),
            "home_o15": round(t["home_o15"] / max(t["home_games"], 1), 4),
            "away_o15": round(t["away_o15"] / max(t["away_games"], 1), 4),
            "recent_avg": round(sum(t["recent_totals"][-10:]) / min(len(t["recent_totals"]), 10), 2),
            "streak_o15": sum(1 for g in t["recent_totals"][-5:] if g >= 2),
            "league": t["league"]
        }
    return profiles

TEAM_PROFILES = build_team_profiles()

# ─── ELITE LOOKUP ───
ELITE_RAW = json.loads('{"BOUvTOT":{"lg":"England","g":7,"r":1.0,"b":0.5714},"CRYvAST":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"FORvSUN":{"lg":"England","g":7,"r":1.0,"b":0.5714},"FULvBUR":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"LIVvMUN":{"lg":"England","g":7,"r":1.0,"b":0.8571},"WOLvNEW":{"lg":"England","g":7,"r":1.0,"b":0.7143},"CRYvCHE":{"lg":"England","g":7,"r":1.0,"b":0.7143},"WOLvTOT":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"BREvNEW":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"WOLvBUR":{"lg":"England","g":7,"r":1.0,"b":0.7143},"ASTvARS":{"lg":"England","g":7,"r":1.0,"b":0.8571},"BREvTOT":{"lg":"England","g":7,"r":1.0,"b":0.5714},"CRYvMCI":{"lg":"England","g":7,"r":1.0,"b":0.7143},"MUNvCHE":{"lg":"England","g":7,"r":1.0,"b":0.7143},"SUNvNEW":{"lg":"England","g":7,"r":1.0,"b":0.4286},"WOLvLEE":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"ASTvCHE":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"LIVvMCI":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"MUNvEVE":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"NEWvARS":{"lg":"England","g":8,"r":1.0,"b":0.75},"ASTvEVE":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"CHEvARS":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"CRYvBOU":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"LIVvFUL":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"NEWvTOT":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"CHEvEVE":{"lg":"England","g":7,"r":1.0,"b":0.5714},"CRYvWOL":{"lg":"England","g":7,"r":1.0,"b":0.5714},"FORvWHU":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"LIVvBOU":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"MUNvFUL":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"NEWvBUR":{"lg":"England","g":7,"r":1.0,"b":0.8571},"TOTvARS":{"lg":"England","g":7,"r":1.0,"b":0.7143},"ASTvFUL":{"lg":"England","g":7,"r":1.0,"b":0.5714},"CHEvMCI":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"EVEvARS":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"FORvCRY":{"lg":"England","g":8,"r":0.875,"b":0.75},"LIVvWOL":{"lg":"England","g":7,"r":1.0,"b":0.4286},"MUNvBOU":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"NEWvLEE":{"lg":"England","g":7,"r":1.0,"b":0.7143},"ASTvBOU":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"BREvCRY":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"CHEvFUL":{"lg":"England","g":7,"r":1.0,"b":0.5714},"EVEvMCI":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"LIVvFOR":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"MUNvWOL":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"TOTvLEE":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"ARSvMCI":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"BOUvCHE":{"lg":"England","g":7,"r":1.0,"b":0.5714},"CRYvSUN":{"lg":"England","g":7,"r":1.0,"b":1.0},"FORvMUN":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"FULvEVE":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"LIVvBRE":{"lg":"England","g":7,"r":1.0,"b":0.7143},"ARSvLEE":{"lg":"England","g":7,"r":1.0,"b":0.7143},"BHAvBUR":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"CRYvNEW":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"FULvMCI":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"ARSvFUL":{"lg":"England","g":7,"r":1.0,"b":0.8571},"BHAvLEE":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"BOUvMCI":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"CRYvTOT":{"lg":"England","g":7,"r":1.0,"b":0.4286},"LIVvNEW":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"MUNvSUN":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"WOLvEVE":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"BREvCHE":{"lg":"England","g":8,"r":0.875,"b":0.75},"MUNvNEW":{"lg":"England","g":7,"r":1.0,"b":0.7143},"WHUvLEE":{"lg":"England","g":7,"r":1.0,"b":0.8571},"WOLvMCI":{"lg":"England","g":7,"r":1.0,"b":0.5714},"CRYvLEE":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"LIVvBUR":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"MUNvTOT":{"lg":"England","g":7,"r":1.0,"b":0.7143},"WHUvBHA":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"BREvMCI":{"lg":"England","g":7,"r":1.0,"b":0.8571},"CRYvBHA":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"LIVvLEE":{"lg":"England","g":7,"r":1.0,"b":0.5714},"MUNvBUR":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"NEWvCHE":{"lg":"England","g":7,"r":1.0,"b":0.8571},"CHEvTOT":{"lg":"England","g":7,"r":1.0,"b":1.0},"FORvBOU":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"MUNvLEE":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"NEWvEVE":{"lg":"England","g":7,"r":1.0,"b":0.2857},"ARSvCRY":{"lg":"England","g":7,"r":1.0,"b":0.7143},"ASTvLEE":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"CHEvBUR":{"lg":"England","g":7,"r":1.0,"b":0.8571},"LIVvWHU":{"lg":"England","g":7,"r":1.0,"b":0.7143},"NEWvMCI":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"SUNvFUL":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"ASTvBHA":{"lg":"England","g":7,"r":1.0,"b":0.8571},"CHEvLEE":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"LIVvCRY":{"lg":"England","g":7,"r":1.0,"b":0.8571},"MUNvWHU":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"NEWvFUL":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"TOTvMCI":{"lg":"England","g":7,"r":1.0,"b":0.5714},"ARSvLIV":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"ASTvWHU":{"lg":"England","g":7,"r":1.0,"b":0.7143},"BURvMCI":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"CHEvBHA":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"SUNvWOL":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"ASTvCRY":{"lg":"England","g":7,"r":1.0,"b":0.8571},"BURvFUL":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"CHEvWHU":{"lg":"England","g":7,"r":1.0,"b":0.5714},"MUNvLIV":{"lg":"England","g":8,"r":0.875,"b":0.75},"TOTvBOU":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"ARSvMUN":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"ASTvLIV":{"lg":"England","g":7,"r":1.0,"b":0.8571},"LEEvFUL":{"lg":"England","g":8,"r":0.875,"b":0.625},"NEWvFOR":{"lg":"England","g":7,"r":1.0,"b":1.0},"TOTvWOL":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"ARSvSUN":{"lg":"England","g":7,"r":1.0,"b":0.7143},"ASTvMUN":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"EVEvCRY":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"FULvBHA":{"lg":"England","g":7,"r":0.8571,"b":0.2857},"LEEvBOU":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"MCIvWHU":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"TOTvFOR":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"BURvFOR":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"CHEvMUN":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"MCIvCRY":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"TOTvBRE":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"CHEvAST":{"lg":"England","g":7,"r":1.0,"b":0.7143},"LEEvFOR":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"ARSvCHE":{"lg":"England","g":7,"r":1.0,"b":0.5714},"BHAvFOR":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"BOUvCRY":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"BURvSUN":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"FULvLIV":{"lg":"England","g":7,"r":1.0,"b":0.5714},"TOTvNEW":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"ARSvTOT":{"lg":"England","g":7,"r":1.0,"b":0.8571},"EVEvCHE":{"lg":"England","g":7,"r":1.0,"b":0.5714},"FULvMUN":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"WHUvFOR":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"WOLvCRY":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"BHAvSUN":{"lg":"England","g":7,"r":0.8571,"b":0.2857},"BURvTOT":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"FULvAST":{"lg":"England","g":7,"r":1.0,"b":1.0},"LEEvNEW":{"lg":"England","g":7,"r":1.0,"b":0.7143},"MCIvCHE":{"lg":"England","g":7,"r":0.8571,"b":0.4286},"WOLvLIV":{"lg":"England","g":7,"r":0.8571,"b":0.7143},"BHAvNEW":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"FORvLIV":{"lg":"England","g":7,"r":0.8571,"b":0.8571},"FULvCHE":{"lg":"England","g":7,"r":1.0,"b":0.7143},"MCIvEVE":{"lg":"England","g":7,"r":1.0,"b":0.7143},"WHUvSUN":{"lg":"England","g":7,"r":0.8571,"b":0.5714},"GETvATM":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"LEVvRMA":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"OVIvELC":{"lg":"Spain","g":7,"r":1.0,"b":0.8571},"BILvELC":{"lg":"Spain","g":7,"r":1.0,"b":0.8571},"GETvRMA":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"RBBvCEL":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"BILvVCF":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"RBBvLEV":{"lg":"Spain","g":7,"r":0.8571,"b":0.8571},"RAYvLEV":{"lg":"Spain","g":7,"r":1.0,"b":0.8571},"RSOvVIL":{"lg":"Spain","g":7,"r":0.8571,"b":0.8571},"SEVvATM":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"ELCvVCF":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"ESPvRBB":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"SEVvRMA":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"BILvLEV":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"ESPvRAY":{"lg":"Spain","g":7,"r":0.8571,"b":0.8571},"RSOvRMA":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"VILvATM":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"ATMvRMA":{"lg":"Spain","g":7,"r":1.0,"b":0.4286},"MALvGIR":{"lg":"Spain","g":7,"r":1.0,"b":0.8571},"RSOvRBB":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"SEVvRAY":{"lg":"Spain","g":7,"r":1.0,"b":0.8571},"VILvFCB":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"GETvELC":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"LEVvMAL":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"OSAvALA":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"GIRvFCB":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"LEVvCEL":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"RBBvRMA":{"lg":"Spain","g":7,"r":1.0,"b":1.0},"GETvCEL":{"lg":"Spain","g":7,"r":0.8571,"b":0.8571},"RAYvRMA":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"RBBvFCB":{"lg":"Spain","g":7,"r":1.0,"b":0.5714},"ALAvVIL":{"lg":"Spain","g":7,"r":1.0,"b":0.8571},"RSOvELC":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"ESPvLEV":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"OSAvCEL":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"OVIvFCB":{"lg":"Spain","g":7,"r":1.0,"b":0.4286},"RAYvRBB":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"SEVvMAL":{"lg":"Spain","g":7,"r":0.8571,"b":0.2857},"BILvRBB":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"OSAvGET":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"OVIvRAY":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"RSOvCEL":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"SEVvLEV":{"lg":"Spain","g":7,"r":1.0,"b":0.5714},"ATMvMAL":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"BILvRAY":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"GIRvOVI":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"OSAvESP":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"VCFvRMA":{"lg":"Spain","g":7,"r":0.8571,"b":0.8571},"VILvCEL":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"ATMvCEL":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"BILvOVI":{"lg":"Spain","g":7,"r":1.0,"b":0.7143},"GIRvOSA":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"ATMvLEV":{"lg":"Spain","g":7,"r":1.0,"b":0.8571},"MALvFCB":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"ATMvGET":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"CELvFCB":{"lg":"Spain","g":7,"r":1.0,"b":0.5714},"GIRvSEV":{"lg":"Spain","g":8,"r":0.875,"b":0.5},"MALvRAY":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"VCFvOVI":{"lg":"Spain","g":7,"r":1.0,"b":0.5714},"ELCvALA":{"lg":"Spain","g":7,"r":0.8571,"b":0.2857},"FCBvGET":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"CELvOVI":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"RMAvOSA":{"lg":"Spain","g":7,"r":0.8571,"b":0.7143},"VCFvALA":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"FCBvOSA":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"VCFvELC":{"lg":"Spain","g":7,"r":1.0,"b":0.5714},"CELvALA":{"lg":"Spain","g":7,"r":0.8571,"b":0.2857},"LEVvBIL":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"CELvELC":{"lg":"Spain","g":7,"r":0.8571,"b":0.5714},"GETvBIL":{"lg":"Spain","g":7,"r":0.8571,"b":0.8571},"ESPvGIR":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"VCFvLEV":{"lg":"Spain","g":6,"r":0.8333,"b":0.3333},"FIOvBFC":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"INTvUSC":{"lg":"Italy","g":7,"r":1.0,"b":0.8571},"VERvPAR":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"GENvCOM":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"LAZvNAP":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"PISvBFC":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"UDIvINT":{"lg":"Italy","g":7,"r":1.0,"b":0.4286},"FIOvUSC":{"lg":"Italy","g":7,"r":0.8571,"b":0.8571},"PISvACM":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"ROMvNAP":{"lg":"Italy","g":7,"r":1.0,"b":0.8571},"FIOvUDI":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"PISvUSC":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"ROMvCOM":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"ATAvBFC":{"lg":"Italy","g":7,"r":1.0,"b":0.7143},"FIOvGEN":{"lg":"Italy","g":7,"r":1.0,"b":0.8571},"VERvCOM":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"CAGvCOM":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"PISvGEN":{"lg":"Italy","g":7,"r":1.0,"b":0.8571},"TORvUSC":{"lg":"Italy","g":7,"r":0.8571,"b":0.2857},"ATAvUSC":{"lg":"Italy","g":7,"r":1.0,"b":0.7143},"CAGvINT":{"lg":"Italy","g":7,"r":1.0,"b":1.0},"LECvCOM":{"lg":"Italy","g":7,"r":0.8571,"b":0.8571},"PISvLAZ":{"lg":"Italy","g":7,"r":1.0,"b":0.5714},"ROMvFIO":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"ATAvUDI":{"lg":"Italy","g":7,"r":1.0,"b":0.7143},"VERvFIO":{"lg":"Italy","g":7,"r":1.0,"b":0.5714},"JUVvLEC":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"PISvVER":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"FIOvLEC":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"PARvUSC":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"PISvCAG":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"ROMvTOR":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"UDIvACM":{"lg":"Italy","g":7,"r":0.8571,"b":0.8571},"UDIvUSC":{"lg":"Italy","g":7,"r":1.0,"b":0.7143},"FIOvCOM":{"lg":"Italy","g":7,"r":1.0,"b":1.0},"CAGvATA":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"PISvINT":{"lg":"Italy","g":7,"r":0.8571,"b":0.2857},"ROMvUSC":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"ATAvNAP":{"lg":"Italy","g":7,"r":1.0,"b":0.7143},"CAGvACM":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"ATAvCOM":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"CAGvUSC":{"lg":"Italy","g":7,"r":1.0,"b":1.0},"PISvFIO":{"lg":"Italy","g":7,"r":1.0,"b":0.8571},"TORvINT":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"VERvUDI":{"lg":"Italy","g":7,"r":0.8571,"b":0.8571},"ACMvCOM":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"BFCvINT":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"ACMvINT":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"ATAvFIO":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"BFCvJUV":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"CAGvLAZ":{"lg":"Italy","g":7,"r":1.0,"b":0.7143},"PARvSAS":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"ACMvJUV":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"ATAvPIS":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"ATAvSAS":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"NAPvLAZ":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"PARvTOR":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"BFCvSAS":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"USCvFIO":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"ACMvSAS":{"lg":"Italy","g":7,"r":1.0,"b":0.7143},"JUVvGEN":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"LECvCAG":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"PARvATA":{"lg":"Italy","g":7,"r":1.0,"b":0.8571},"COMvVER":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"NAPvCAG":{"lg":"Italy","g":7,"r":1.0,"b":0.5714},"FIOvLAZ":{"lg":"Italy","g":7,"r":1.0,"b":0.7143},"INTvVER":{"lg":"Italy","g":7,"r":0.8571,"b":0.8571},"COMvLEC":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"GENvSAS":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"INTvCAG":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"USCvATA":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"FIOvVER":{"lg":"Italy","g":7,"r":0.8571,"b":0.7143},"LAZvSAS":{"lg":"Italy","g":7,"r":0.8571,"b":0.5714},"USCvBFC":{"lg":"Italy","g":7,"r":0.8571,"b":0.4286},"CAGvSAS":{"lg":"Italy","g":6,"r":0.8333,"b":0.8333},"LECvATA":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"LEVvBMU":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"TSGvBMG":{"lg":"Germany","g":7,"r":0.8571,"b":0.8571},"KOEvBMG":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"SCFvSVW":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"UNIvVFB":{"lg":"Germany","g":7,"r":0.8571,"b":0.2857},"KOEvFCA":{"lg":"Germany","g":7,"r":0.8571,"b":0.8571},"LEVvHDH":{"lg":"Germany","g":7,"r":1.0,"b":0.4286},"SGEvBMG":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"TSGvRBL":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"UNIvHSV":{"lg":"Germany","g":7,"r":1.0,"b":0.8571},"WOBvMAI":{"lg":"Germany","g":7,"r":0.8571,"b":0.2857},"KOEvRBL":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"MAIvBMU":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"UNIvTSG":{"lg":"Germany","g":7,"r":0.8571,"b":0.8571},"BVBvHSV":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"HDHvBMU":{"lg":"Germany","g":7,"r":1.0,"b":0.8571},"MAIvSVW":{"lg":"Germany","g":7,"r":1.0,"b":0.5714},"SCFvTSG":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"SGEvRBL":{"lg":"Germany","g":7,"r":0.8571,"b":0.4286},"BVBvTSG":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"LEVvRBL":{"lg":"Germany","g":8,"r":0.875,"b":0.75},"SCFvKOE":{"lg":"Germany","g":7,"r":1.0,"b":0.8571},"SVWvBMU":{"lg":"Germany","g":7,"r":1.0,"b":0.5714},"BMGvBMU":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"BVBvKOE":{"lg":"Germany","g":7,"r":0.8571,"b":0.2857},"HDHvFCA":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"MAIvHSV":{"lg":"Germany","g":7,"r":1.0,"b":0.2857},"SGEvSCF":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"STPvRBL":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"SVWvVFB":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"WOBvTSG":{"lg":"Germany","g":7,"r":1.0,"b":0.5714},"BMUvVFB":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"SGEvBVB":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"UNIvSTP":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"BVBvLEV":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"SCFvSTP":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"SGEvWOB":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"UNIvHDH":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"SCFvHDH":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"BMUvRBL":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"KOEvVFB":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"TSGvHSV":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"WOBvSTP":{"lg":"Germany","g":7,"r":0.8571,"b":0.8571},"BMUvTSG":{"lg":"Germany","g":8,"r":0.875,"b":0.625},"BVBvBMG":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"KOEvHSV":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"SCFvFCA":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"UNIvRBL":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"BVBvFCA":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"KOEvTSG":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"LEVvVFB":{"lg":"Germany","g":7,"r":1.0,"b":0.8571},"SCFvRBL":{"lg":"Germany","g":7,"r":1.0,"b":0.5714},"WOBvBMG":{"lg":"Germany","g":7,"r":1.0,"b":1.0},"BVBvRBL":{"lg":"Germany","g":7,"r":1.0,"b":0.4286},"MAIvBMG":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"BVBvUNI":{"lg":"Germany","g":7,"r":0.8571,"b":0.4286},"LEVvTSG":{"lg":"Germany","g":7,"r":1.0,"b":0.8571},"SGEvKOE":{"lg":"Germany","g":7,"r":0.8571,"b":0.8571},"STPvHSV":{"lg":"Germany","g":7,"r":0.8571,"b":0.4286},"SVWvBMG":{"lg":"Germany","g":7,"r":0.8571,"b":0.4286},"BMGvVFB":{"lg":"Germany","g":7,"r":0.8571,"b":0.4286},"BMUvSGE":{"lg":"Germany","g":7,"r":0.8571,"b":0.2857},"BVBvSCF":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"HDHvHSV":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"LEVvSGE":{"lg":"Germany","g":7,"r":0.8571,"b":0.1429},"BMGvTSG":{"lg":"Germany","g":7,"r":1.0,"b":0.5714},"FCAvHSV":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"VFBvRBL":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"WOBvBVB":{"lg":"Germany","g":7,"r":0.8571,"b":0.4286},"BMGvKOE":{"lg":"Germany","g":7,"r":0.8571,"b":0.4286},"STPvLEV":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"HDHvLEV":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"HSVvUNI":{"lg":"Germany","g":7,"r":0.8571,"b":0.2857},"RBLvTSG":{"lg":"Germany","g":7,"r":0.8571,"b":0.2857},"VFBvSCF":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"BMUvMAI":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"RBLvKOE":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"SVWvWOB":{"lg":"Germany","g":7,"r":0.8571,"b":0.8571},"TSGvUNI":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"VFBvBVB":{"lg":"Germany","g":7,"r":0.8571,"b":0.8571},"FCAvLEV":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"VFBvWOB":{"lg":"Germany","g":7,"r":0.8571,"b":0.4286},"BMGvHDH":{"lg":"Germany","g":8,"r":0.875,"b":0.625},"KOEvSCF":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"RBLvLEV":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"UNIvSGE":{"lg":"Germany","g":7,"r":1.0,"b":0.7143},"RBLvSTP":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"TSGvWOB":{"lg":"Germany","g":7,"r":0.8571,"b":0.7143},"UNIvLEV":{"lg":"Germany","g":7,"r":0.8571,"b":0.5714},"AMOvLIL":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"ANGvOLM":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"STRvPSG":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"TOUvMET":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"NANvLIL":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"RENvMET":{"lg":"France","g":7,"r":1.0,"b":1.0},"STRvOLM":{"lg":"France","g":7,"r":1.0,"b":0.8571},"LORvMET":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"LYOvLIL":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"NANvB29":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"RENvAUX":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"STRvNCE":{"lg":"France","g":7,"r":0.8571,"b":0.8571},"ANGvLIL":{"lg":"France","g":7,"r":1.0,"b":0.5714},"LENvPSG":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"LORvAUX":{"lg":"France","g":8,"r":0.875,"b":0.625},"LYOvB29":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"OLMvNCE":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"STRvLEH":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"LORvAMO":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"NCEvPSG":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"LENvAUX":{"lg":"France","g":7,"r":1.0,"b":0.8571},"LORvNAN":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"NCEvLEH":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"OLMvLIL":{"lg":"France","g":7,"r":1.0,"b":0.5714},"PFCvAMO":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"STRvB29":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"LORvLYO":{"lg":"France","g":7,"r":1.0,"b":0.8571},"METvAUX":{"lg":"France","g":7,"r":0.8571,"b":0.8571},"STRvTOU":{"lg":"France","g":7,"r":0.8571,"b":0.8571},"ANGvLOR":{"lg":"France","g":7,"r":1.0,"b":0.7143},"LILvLEH":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"NANvMET":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"TOUvNCE":{"lg":"France","g":7,"r":1.0,"b":0.4286},"LYOvMET":{"lg":"France","g":7,"r":1.0,"b":0.7143},"NANvAUX":{"lg":"France","g":7,"r":1.0,"b":0.5714},"PSGvAMO":{"lg":"France","g":7,"r":1.0,"b":0.8571},"ANGvMET":{"lg":"France","g":7,"r":0.8571,"b":0.2857},"LYOvAUX":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"NANvAMO":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"PFCvOLM":{"lg":"France","g":7,"r":0.8571,"b":0.2857},"PSGvB29":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"RENvLEH":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"TOUvLIL":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"ANGvAUX":{"lg":"France","g":7,"r":1.0,"b":0.8571},"LYOvAMO":{"lg":"France","g":7,"r":1.0,"b":0.4286},"PFCvNCE":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"LENvNCE":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"OLMvMET":{"lg":"France","g":7,"r":1.0,"b":0.7143},"PFCvLEH":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"LENvLEH":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"LORvB29":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"PSGvLYO":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"ANGvLYO":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"LORvTOU":{"lg":"France","g":7,"r":0.8571,"b":0.1429},"METvLEH":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"PSGvREN":{"lg":"France","g":7,"r":1.0,"b":0.7143},"STRvNAN":{"lg":"France","g":7,"r":0.8571,"b":0.8571},"LEHvAUX":{"lg":"France","g":7,"r":1.0,"b":0.5714},"LENvB29":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"LORvREN":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"NCEvAMO":{"lg":"France","g":7,"r":0.8571,"b":0.8571},"PFCvTOU":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"PSGvANG":{"lg":"France","g":7,"r":1.0,"b":0.4286},"STRvLYO":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"LENvTOU":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"NCEvNAN":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"PFCvREN":{"lg":"France","g":7,"r":0.8571,"b":0.8571},"PSGvLOR":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"STRvANG":{"lg":"France","g":8,"r":0.875,"b":0.5},"AUXvB29":{"lg":"France","g":7,"r":1.0,"b":0.4286},"LENvREN":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"LILvAMO":{"lg":"France","g":7,"r":1.0,"b":0.7143},"OLMvANG":{"lg":"France","g":7,"r":1.0,"b":1.0},"PFCvLOR":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"AMOvB29":{"lg":"France","g":7,"r":1.0,"b":0.5714},"AUXvTOU":{"lg":"France","g":7,"r":1.0,"b":0.8571},"LEHvLYO":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"NCEvANG":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"OLMvSTR":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"PSGvPFC":{"lg":"France","g":7,"r":0.8571,"b":0.8571},"AMOvTOU":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"AUXvREN":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"LENvPFC":{"lg":"France","g":7,"r":1.0,"b":0.8571},"LILvLYO":{"lg":"France","g":7,"r":1.0,"b":0.7143},"AUXvLOR":{"lg":"France","g":7,"r":1.0,"b":0.4286},"NCEvOLM":{"lg":"France","g":7,"r":1.0,"b":0.7143},"AUXvPFC":{"lg":"France","g":7,"r":0.8571,"b":0.4286},"B29vANG":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"NANvREN":{"lg":"France","g":7,"r":0.8571,"b":0.2857},"PSGvNCE":{"lg":"France","g":7,"r":1.0,"b":0.5714},"LYOvREN":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"NANvLOR":{"lg":"France","g":7,"r":1.0,"b":0.7143},"TOUvANG":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"AMOvLEN":{"lg":"France","g":7,"r":1.0,"b":0.8571},"AUXvMET":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"B29vOLM":{"lg":"France","g":7,"r":0.8571,"b":0.5714},"LYOvLOR":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"NANvPFC":{"lg":"France","g":7,"r":1.0,"b":1.0},"PSGvLEH":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"TOUvSTR":{"lg":"France","g":7,"r":1.0,"b":0.8571},"NCEvREN":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"CHEvNEW":{"lg":"England","g":6,"r":1.0,"b":0.5},"WOLvSUN":{"lg":"England","g":6,"r":0.8333,"b":0.5},"BHAvMUN":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"BOUvNEW":{"lg":"England","g":6,"r":1.0,"b":0.5},"CRYvARS":{"lg":"England","g":6,"r":1.0,"b":0.8333},"EVEvSUN":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"ASTvWOL":{"lg":"England","g":6,"r":0.8333,"b":0.8333},"CHEvSUN":{"lg":"England","g":6,"r":1.0,"b":0.8333},"CRYvLIV":{"lg":"England","g":6,"r":1.0,"b":0.8333},"BOUvARS":{"lg":"England","g":6,"r":1.0,"b":0.8333},"BOUvWOL":{"lg":"England","g":6,"r":0.8333,"b":0.8333},"WHUvAST":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"TOTvLIV":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"MUNvFOR":{"lg":"England","g":6,"r":0.8333,"b":0.5},"FULvBRE":{"lg":"England","g":6,"r":0.8333,"b":0.5},"MCIvNEW":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"FULvBOU":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"LEEvCRY":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"TOTvCHE":{"lg":"England","g":6,"r":1.0,"b":0.6667},"BURvMUN":{"lg":"England","g":6,"r":1.0,"b":0.6667},"MCIvBRE":{"lg":"England","g":6,"r":0.8333,"b":0.5},"ASTvBRE":{"lg":"England","g":6,"r":1.0,"b":0.8333},"EVEvNEW":{"lg":"England","g":6,"r":1.0,"b":0.8333},"LEEvMUN":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"BURvLIV":{"lg":"England","g":6,"r":0.8333,"b":0.5},"FULvWOL":{"lg":"England","g":6,"r":0.8333,"b":0.5},"FULvFOR":{"lg":"England","g":6,"r":1.0,"b":0.6667},"TOTvAST":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"BOUvBRE":{"lg":"England","g":6,"r":0.8333,"b":0.8333},"NEWvWHU":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"TOTvCRY":{"lg":"England","g":6,"r":1.0,"b":0.6667},"MCIvWOL":{"lg":"England","g":6,"r":1.0,"b":0.8333},"MUNvBRE":{"lg":"England","g":6,"r":1.0,"b":0.6667},"TOTvBHA":{"lg":"England","g":6,"r":0.8333,"b":0.8333},"MCIvFOR":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"ASTvFOR":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"NEWvMUN":{"lg":"England","g":6,"r":1.0,"b":1.0},"LEEvWHU":{"lg":"England","g":6,"r":0.8333,"b":0.5},"TOTvMUN":{"lg":"England","g":6,"r":0.8333,"b":0.3333},"WOLvBRE":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"FORvBRE":{"lg":"England","g":6,"r":0.8333,"b":0.8333},"MCIvBUR":{"lg":"England","g":6,"r":0.8333,"b":0.5},"CHEvBRE":{"lg":"England","g":6,"r":1.0,"b":0.6667},"EVEvBOU":{"lg":"England","g":6,"r":0.8333,"b":0.3333},"LIVvARS":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"ASTvSUN":{"lg":"England","g":6,"r":0.8333,"b":0.5},"NEWvLIV":{"lg":"England","g":6,"r":1.0,"b":1.0},"WOLvARS":{"lg":"England","g":6,"r":0.8333,"b":0.5},"EVEvTOT":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"FORvARS":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"WHUvMUN":{"lg":"England","g":6,"r":1.0,"b":1.0},"NEWvAST":{"lg":"England","g":6,"r":1.0,"b":0.6667},"BOUvSUN":{"lg":"England","g":6,"r":1.0,"b":0.6667},"EVEvWOL":{"lg":"England","g":6,"r":1.0,"b":0.8333},"WHUvARS":{"lg":"England","g":6,"r":0.8333,"b":0.8333},"FULvARS":{"lg":"England","g":6,"r":0.8333,"b":0.5},"NEWvCRY":{"lg":"England","g":6,"r":0.8333,"b":0.6667},"WHUvLIV":{"lg":"England","g":6,"r":1.0,"b":1.0},"CHEvFOR":{"lg":"England","g":6,"r":1.0,"b":1.0},"VCFvRSO":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"RBBvELC":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"FCBvELC":{"lg":"Spain","g":6,"r":1.0,"b":0.8333},"FCBvMAL":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"RBBvOVI":{"lg":"Spain","g":6,"r":1.0,"b":0.5},"RSOvALA":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"FCBvALA":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"CELvGET":{"lg":"Spain","g":7,"r":0.8571,"b":0.4286},"FCBvBIL":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"RSOvOVI":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"RSOvRAY":{"lg":"Spain","g":6,"r":1.0,"b":0.6667},"CELvOSA":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"RMAvRBB":{"lg":"Spain","g":6,"r":0.8333,"b":0.3333},"RMAvVCF":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"ELCvESP":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"MALvESP":{"lg":"Spain","g":6,"r":1.0,"b":0.5},"ALAvESP":{"lg":"Spain","g":6,"r":0.8333,"b":0.8333},"ATMvRBB":{"lg":"Spain","g":7,"r":1.0,"b":0.8571},"RBBvVCF":{"lg":"Spain","g":6,"r":0.8333,"b":0.3333},"VILvBIL":{"lg":"Spain","g":6,"r":1.0,"b":0.5},"LEVvRSO":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"ALAvOSA":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"CELvGIR":{"lg":"Spain","g":6,"r":1.0,"b":0.6667},"ATMvOVI":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"ELCvRSO":{"lg":"Spain","g":6,"r":0.8333,"b":0.8333},"ATMvRAY":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"MALvRSO":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"GETvSEV":{"lg":"Spain","g":6,"r":0.8333,"b":0.8333},"LEVvVIL":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"RBBvGIR":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"GETvVIL":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"LEVvATM":{"lg":"Spain","g":6,"r":1.0,"b":0.5},"OVIvBIL":{"lg":"Spain","g":6,"r":0.8333,"b":0.3333},"RAYvALA":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"RMAvFCB":{"lg":"Spain","g":6,"r":1.0,"b":0.3333},"RMAvELC":{"lg":"Spain","g":6,"r":1.0,"b":0.6667},"RAYvOVI":{"lg":"Spain","g":6,"r":0.8333,"b":0.6667},"VCFvGET":{"lg":"Spain","g":6,"r":0.8333,"b":0.5},"ELCvSEV":{"lg":"Spain","g":6,"r":1.0,"b":0.8333},"RMAvALA":{"lg":"Spain","g":6,"r":0.8333,"b":0.3333},"ELCvGET":{"lg":"Spain","g":6,"r":0.8333,"b":0.3333},"ATAvROM":{"lg":"Italy","g":6,"r":1.0,"b":0.8333},"ATAvGEN":{"lg":"Italy","g":6,"r":0.8333,"b":0.6667},"JUVvPIS":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"CAGvPIS":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"GENvROM":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"INTvPIS":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"CAGvTOR":{"lg":"Italy","g":6,"r":0.8333,"b":0.6667},"LECvFIO":{"lg":"Italy","g":6,"r":0.8333,"b":0.8333},"SASvPAR":{"lg":"Italy","g":6,"r":0.8333,"b":0.6667},"INTvTOR":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"ATAvCAG":{"lg":"Italy","g":6,"r":0.8333,"b":0.5},"USCvROM":{"lg":"Italy","g":6,"r":0.8333,"b":0.6667},"NAPvJUV":{"lg":"Italy","g":6,"r":1.0,"b":0.6667},"ACMvROM":{"lg":"Italy","g":6,"r":1.0,"b":0.5},"COMvATA":{"lg":"Italy","g":6,"r":0.8333,"b":0.6667},"NAPvINT":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"UDIvGEN":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"TORvROM":{"lg":"Italy","g":6,"r":0.8333,"b":0.5},"BFCvROM":{"lg":"Italy","g":6,"r":0.8333,"b":0.8333},"COMvACM":{"lg":"Italy","g":6,"r":0.8333,"b":0.6667},"LAZvPAR":{"lg":"Italy","g":6,"r":1.0,"b":0.5},"COMvINT":{"lg":"Italy","g":6,"r":0.8333,"b":0.5},"ACMvLEC":{"lg":"Italy","g":6,"r":1.0,"b":1.0},"USCvGEN":{"lg":"Italy","g":7,"r":1.0,"b":0.8571},"BFCvCAG":{"lg":"Italy","g":6,"r":0.8333,"b":0.5},"FIOvATA":{"lg":"Italy","g":6,"r":0.8333,"b":0.6667},"USCvNAP":{"lg":"Italy","g":6,"r":1.0,"b":0.8333},"LECvSAS":{"lg":"Italy","g":6,"r":1.0,"b":0.8333},"ACMvUSC":{"lg":"Italy","g":6,"r":0.8333,"b":0.8333},"ATAvVER":{"lg":"Italy","g":6,"r":0.8333,"b":0.6667},"CAGvFIO":{"lg":"Italy","g":6,"r":1.0,"b":0.8333},"INTvACM":{"lg":"Italy","g":6,"r":1.0,"b":0.6667},"INTvFIO":{"lg":"Italy","g":6,"r":0.8333,"b":0.3333},"FCAvBMU":{"lg":"Germany","g":6,"r":0.8333,"b":0.6667},"HSVvTSG":{"lg":"Germany","g":6,"r":0.8333,"b":0.6667},"KOEvSGE":{"lg":"Germany","g":6,"r":0.8333,"b":0.8333},"BVBvBMU":{"lg":"Germany","g":6,"r":1.0,"b":0.5},"FCAvRBL":{"lg":"Germany","g":6,"r":1.0,"b":1.0},"MAIvTSG":{"lg":"Germany","g":6,"r":1.0,"b":1.0},"VFBvSGE":{"lg":"Germany","g":6,"r":1.0,"b":1.0},"MAIvLEV":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"VFBvBMU":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"HDHvRBL":{"lg":"Germany","g":6,"r":1.0,"b":0.6667},"VFBvHSV":{"lg":"Germany","g":6,"r":0.8333,"b":0.6667},"WOBvLEV":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"TSGvLEV":{"lg":"Germany","g":6,"r":0.8333,"b":0.6667},"HDHvMAI":{"lg":"Germany","g":6,"r":1.0,"b":0.6667},"SCFvBVB":{"lg":"Germany","g":6,"r":1.0,"b":0.5},"LEVvBVB":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"TSGvSTP":{"lg":"Germany","g":6,"r":0.8333,"b":0.3333},"MAIvSGE":{"lg":"Germany","g":6,"r":0.8333,"b":0.6667},"TSGvHDH":{"lg":"Germany","g":6,"r":0.8333,"b":0.3333},"BMGvSCF":{"lg":"Germany","g":6,"r":1.0,"b":0.6667},"BVBvSGE":{"lg":"Germany","g":6,"r":1.0,"b":0.3333},"SVWvHDH":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"BMGvFCA":{"lg":"Germany","g":6,"r":0.8333,"b":0.8333},"RBLvBVB":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"TSGvKOE":{"lg":"Germany","g":6,"r":0.8333,"b":0.3333},"LEVvSCF":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"RBLvBMU":{"lg":"Germany","g":6,"r":1.0,"b":0.6667},"BMGvRBL":{"lg":"Germany","g":6,"r":0.8333,"b":0.8333},"SGEvLEV":{"lg":"Germany","g":6,"r":1.0,"b":0.6667},"SVWvTSG":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"STPvSCF":{"lg":"Germany","g":6,"r":0.8333,"b":0.6667},"UNIvBMU":{"lg":"Germany","g":6,"r":0.8333,"b":0.6667},"FCAvSVW":{"lg":"Germany","g":6,"r":0.8333,"b":0.5},"KOEvBMU":{"lg":"Germany","g":6,"r":1.0,"b":0.8333},"HDHvWOB":{"lg":"Germany","g":6,"r":0.8333,"b":0.3333},"SCFvBMU":{"lg":"Germany","g":6,"r":0.8333,"b":0.8333},"B29vPSG":{"lg":"France","g":6,"r":0.8333,"b":0.1667},"METvOLM":{"lg":"France","g":7,"r":0.8571,"b":0.7143},"TOUvREN":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"LENvOLM":{"lg":"France","g":6,"r":1.0,"b":0.8333},"NANvANG":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"METvSTR":{"lg":"France","g":6,"r":0.8333,"b":0.8333},"NCEvPFC":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"AUXvOLM":{"lg":"France","g":6,"r":1.0,"b":0.6667},"LILvREN":{"lg":"France","g":6,"r":1.0,"b":0.8333},"NCEvLOR":{"lg":"France","g":6,"r":0.8333,"b":0.5},"LENvNAN":{"lg":"France","g":6,"r":0.8333,"b":0.1667},"OLMvREN":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"TOUvLOR":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"AUXvSTR":{"lg":"France","g":6,"r":1.0,"b":0.6667},"TOUvLEN":{"lg":"France","g":6,"r":0.8333,"b":0.5},"AUXvNAN":{"lg":"France","g":6,"r":0.8333,"b":0.5},"LILvMET":{"lg":"France","g":6,"r":1.0,"b":0.5},"AUXvNCE":{"lg":"France","g":6,"r":0.8333,"b":0.3333},"LILvLEN":{"lg":"France","g":6,"r":1.0,"b":0.6667},"LILvB29":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"LYOvPSG":{"lg":"France","g":6,"r":0.8333,"b":0.3333},"STRvREN":{"lg":"France","g":6,"r":1.0,"b":1.0},"LILvAUX":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"AMOvLYO":{"lg":"France","g":6,"r":1.0,"b":0.6667},"LORvPSG":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"NANvNCE":{"lg":"France","g":6,"r":0.8333,"b":0.8333},"B29vLEN":{"lg":"France","g":6,"r":1.0,"b":1.0},"OLMvLOR":{"lg":"France","g":6,"r":1.0,"b":0.8333},"PFCvSTR":{"lg":"France","g":6,"r":1.0,"b":0.5},"AUXvPSG":{"lg":"France","g":6,"r":0.8333,"b":0.5},"LEHvB29":{"lg":"France","g":6,"r":1.0,"b":0.6667},"METvNCE":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"NANvPSG":{"lg":"France","g":6,"r":1.0,"b":0.5},"NCEvB29":{"lg":"France","g":6,"r":0.8333,"b":0.6667},"LENvLYO":{"lg":"France","g":6,"r":0.8333,"b":0.8333},"LORvANG":{"lg":"France","g":6,"r":1.0,"b":0.8333},"RENvPFC":{"lg":"France","g":6,"r":0.8333,"b":0.8333},"TOUvPSG":{"lg":"France","g":6,"r":0.8333,"b":0.8333},"RENvLOR":{"lg":"France","g":6,"r":1.0,"b":1.0},"NANvSTR":{"lg":"France","g":6,"r":1.0,"b":0.6667}}')
def build_elite_index():
    idx = {}
    for key, val in ELITE_RAW.items():
        parts = key.split("v", 1)
        if len(parts) == 2:
            idx[f"{val['lg']}|{parts[0]}|{parts[1]}"] = val
    return idx
ELITE = build_elite_index()

# ─── DEDUP ───
def load_dedup():
    try:
        with open(DEDUP_FILE) as f:
            data = json.load(f)
        now = time.time()
        return {k: v for k, v in data.items() if now - v < DEDUP_TTL}
    except:
        return {}

def save_dedup(seen):
    with open(DEDUP_FILE, "w") as f:
        json.dump(seen, f)

# ─── FETCH MATCHES ───
def fetch_matches():
    matches = []
    now_ms = int(time.time() * 1000)
    seen_ids = set()
    
    for lid, (cat_id, tourn_id, flag) in LEAGUES.items():
        try:
            url = "https://www.sportybet.com/api/ng/factsCenter/wapConfigurableUpcomingEvents"
            params = {"sportId": VFL_SPORT, "categoryId": cat_id, "tournamentId": tourn_id, "_t": now_ms}
            r = requests.get(url, params=params, headers=HEADERS, timeout=15)
            data = r.json()
            events = data.get("data", [])
            if isinstance(events, dict):
                events = events.get("tournaments", [{}])[0].get("events", []) if "tournaments" in events else []
            for e in events:
                eid = e.get("eventId", "")
                if eid in seen_ids:
                    continue
                seen_ids.add(eid)
                kick_off = e.get("estimateStartTime", 0)
                if kick_off > now_ms - 300000:
                    o15_odds = None
                    for mkt in e.get("markets", []):
                        if mkt.get("id") == "18" and mkt.get("specifier") == "total=1.5":
                            for out in mkt.get("outcomes", []):
                                if out.get("id") == "12" or out.get("desc") == "Over":
                                    o15_odds = out.get("odds")
                    matches.append({
                        "eventId": eid, "home": e.get("homeTeamName", ""),
                        "away": e.get("awayTeamName", ""), "kickoff": kick_off,
                        "league": flag, "league_id": lid,
                        "status": e.get("matchStatus", ""), "gameId": e.get("gameId", ""),
                        "o15_odds": o15_odds
                    })
            time.sleep(0.3)
        except Exception as ex:
            print(f"  Upcoming {flag}: {ex}")
    
    # Also grab live (early minutes)
    try:
        url = "https://www.sportybet.com/api/ng/factsCenter/wapConfigurableIndexLiveEvents"
        params = {"sportId": VFL_SPORT, "_t": now_ms}
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        data = r.json()
        events = data.get("data", [])
        if isinstance(events, dict):
            events = []
        for e in events:
            eid = e.get("eventId", "")
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            played = e.get("playedSeconds", "0:00")
            try:
                mins = int(played.split(":")[0])
                if mins > 5:
                    continue
            except:
                pass
            cat = e.get("sport", {}).get("category", {}).get("id", "")
            lid = None
            for l, (c, _, _) in LEAGUES.items():
                if c == cat:
                    lid = l
                    break
            if not lid:
                continue
            flag = LEAGUES[lid][2]
            o15_odds = None
            for mkt in e.get("markets", []):
                if mkt.get("id") == "18" and mkt.get("specifier") == "total=1.5":
                    for out in mkt.get("outcomes", []):
                        if out.get("id") == "12" or out.get("desc") == "Over":
                            o15_odds = out.get("odds")
            matches.append({
                "eventId": eid, "home": e.get("homeTeamName", ""),
                "away": e.get("awayTeamName", ""), "kickoff": e.get("estimateStartTime", 0),
                "league": flag, "league_id": lid,
                "status": e.get("matchStatus", ""), "gameId": e.get("gameId", ""),
                "o15_odds": o15_odds
            })
    except:
        pass
    return matches

# ─── 12-LAYER ONIMIX SCORING ───
def score_12layer(m):
    lg = LEAGUE_NAMES.get(m["league_id"], "")
    home_key = f"{lg}|{m['home']}"
    away_key = f"{lg}|{m['away']}"
    
    hp = TEAM_PROFILES.get(home_key)
    ap = TEAM_PROFILES.get(away_key)
    
    if not hp or not ap:
        return None, {}
    
    score = 0
    layers = {}
    
    # Layer 1: O0.5 Safety Net
    avg_o05 = (hp["o05_rate"] + ap["o05_rate"]) / 2
    l1 = round(avg_o05 * 15, 1)
    score += l1
    layers["O0.5"] = l1
    
    # Layer 2: O1.5 Core
    avg_o15 = (hp["o15_rate"] + ap["o15_rate"]) / 2
    l2 = round(avg_o15 * 25, 1)
    score += l2
    layers["O1.5"] = l2
    
    # Layer 3: O2.5 Bonus
    avg_o25 = (hp["o25_rate"] + ap["o25_rate"]) / 2
    l3 = round(avg_o25 * 10, 1)
    score += l3
    layers["O2.5"] = l3
    
    # Layer 4: BTTS Power
    avg_btts = (hp["btts_rate"] + ap["btts_rate"]) / 2
    l4 = round(avg_btts * 12, 1)
    score += l4
    layers["BTTS"] = l4
    
    # Layer 5: Attack Strength
    combined_attack = hp["avg_scored"] + ap["avg_scored"]
    l5 = round(min(combined_attack / 4.0, 1.0) * 10, 1)
    score += l5
    layers["ATK"] = l5
    
    # Layer 6: Defense Weakness (higher = weaker defense = more goals)
    combined_concede = hp["avg_conceded"] + ap["avg_conceded"]
    l6 = round(min(combined_concede / 4.0, 1.0) * 8, 1)
    score += l6
    layers["DEF"] = l6
    
    # Layer 7: Home/Away Venue Factor
    venue_o15 = (hp["home_o15"] + ap["away_o15"]) / 2
    l7 = round(venue_o15 * 5, 1)
    score += l7
    layers["VEN"] = l7
    
    # Layer 8: Recent Trend (last 10 games avg goals)
    trend = (hp["recent_avg"] + ap["recent_avg"]) / 2
    l8 = round(min(trend / 3.5, 1.0) * 5, 1)
    score += l8
    layers["TRD"] = l8
    
    # Layer 9: Momentum (streak of O1.5 in last 5)
    streak = (hp["streak_o15"] + ap["streak_o15"]) / 2
    l9 = round((streak / 5.0) * 5, 1)
    score += l9
    layers["MOM"] = l9
    
    # Layer 10: ELITE Matchup Bonus
    mk = f"{lg}|{m['home']}|{m['away']}"
    if mk in ELITE:
        l10 = 5.0
    else:
        l10 = 0
    score += l10
    layers["ELT"] = l10
    
    # Layer 11: League Bonus (England & Germany higher scoring)
    if lg in ["England", "Germany", "France"]:
        l11 = 2.0
    else:
        l11 = 0
    score += l11
    layers["LGB"] = l11
    
    # Layer 12: Odds Confidence
    if m.get("o15_odds"):
        try:
            odds_val = float(m["o15_odds"])
            if odds_val < 1.3:
                l12 = 3.0
            elif odds_val < 1.5:
                l12 = 2.0
            elif odds_val < 1.8:
                l12 = 1.0
            else:
                l12 = 0
        except:
            l12 = 0
    else:
        l12 = 0
    score += l12
    layers["ODS"] = l12
    
    return round(score, 1), layers

# ─── BOOKING CODE ───
def get_booking_code(picks):
    if not picks:
        return None
    selections = [{"eventId": p["eventId"], "marketId": "18", "outcomeId": "12", "specifier": "total=1.5"} for p in picks[:10]]
    try:
        r = requests.post(BOOK_URL, json={"selections": selections}, headers={**HEADERS, "Content-Type": "application/json"}, timeout=15)
        data = r.json()
        return data.get("data", {}).get("code") or data.get("data", {}).get("shareCode")
    except:
        return None

def send_telegram(text):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                         json={"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"}, timeout=15)
        return r.json().get("ok", False)
    except:
        return False

# ─── MAIN ───
def main():
    now = datetime.now(WAT)
    print(f"[L2 ONIMIX 12-Layer v5] {now.strftime('%H:%M:%S WAT')}")
    print(f"Team profiles: {len(TEAM_PROFILES)}")
    
    matches = fetch_matches()
    print(f"Matches: {len(matches)}")
    
    if not matches:
        print("No matches. Silent exit.")
        return
    
    # Score all matches
    scored = []
    for m in matches:
        score, layers = score_12layer(m)
        if score is not None:
            scored.append({**m, "score": score, "layers": layers})
    
    scored.sort(key=lambda x: -x["score"])
    
    # Tier classification (max possible ~105)
    ultra = [s for s in scored if s["score"] >= 75]
    premium = [s for s in scored if 60 <= s["score"] < 75]
    standard = [s for s in scored if 50 <= s["score"] < 60]
    
    picks = ultra + premium  # Only send ULTRA + PREMIUM
    print(f"Scored: {len(scored)} | ULTRA: {len(ultra)} | PREMIUM: {len(premium)} | STANDARD: {len(standard)}")
    
    if not picks:
        print("No qualifying picks. Silent exit.")
        return
    
    # Dedup
    seen = load_dedup()
    new_picks = []
    for p in picks:
        h = hashlib.md5(f"{p['eventId']}|{p['home']}|{p['away']}|L2".encode()).hexdigest()
        if h not in seen:
            new_picks.append(p)
            seen[h] = time.time()
    save_dedup(seen)
    
    if not new_picks:
        print("All picks already sent. Silent exit.")
        return
    
    booking = get_booking_code(new_picks)
    
    lines = [f"🧠 <b>ONIMIX 12-Layer Engine v5</b>", f"📅 {now.strftime('%d %b %Y • %H:%M WAT')}", ""]
    
    u_picks = [p for p in new_picks if p["score"] >= 75]
    p_picks = [p for p in new_picks if 60 <= p["score"] < 75]
    
    if u_picks:
        lines.append("🔴 <b>ULTRA (Score ≥75)</b>")
        for p in u_picks[:8]:
            kt = datetime.fromtimestamp(p["kickoff"]/1000, WAT).strftime("%H:%M")
            odds_str = f" @{p['o15_odds']}" if p.get("o15_odds") else ""
            lines.append(f"  🔥 {p['league']} {p['home']} vs {p['away']}")
            lines.append(f"     ⏰ {kt} | Score={p['score']:.0f}/105{odds_str}")
        lines.append("")
    
    if p_picks:
        lines.append("🟡 <b>PREMIUM (Score 60-74)</b>")
        for p in p_picks[:8]:
            kt = datetime.fromtimestamp(p["kickoff"]/1000, WAT).strftime("%H:%M")
            odds_str = f" @{p['o15_odds']}" if p.get("o15_odds") else ""
            lines.append(f"  ⚡ {p['league']} {p['home']} vs {p['away']}")
            lines.append(f"     ⏰ {kt} | Score={p['score']:.0f}/105{odds_str}")
        lines.append("")
    
    lines.append(f"📊 {len(u_picks)} ULTRA + {len(p_picks)} PREMIUM = {len(new_picks)} picks")
    if booking:
        lines.append(f"\n🎫 <b>BOOKING CODE:</b> <code>{booking}</code>")
        lines.append("👉 Paste on SportyBet to bet all at once!")
    lines.append(f"\n🤖 Layer 2 | {len(TEAM_PROFILES)} team profiles")
    
    msg = "\n".join(lines)
    print(f"\n{msg}\n")
    ok = send_telegram(msg)
    print(f"Telegram: {ok}")

if __name__ == "__main__":
    main()
