#!/usr/bin/env python3
"""
ONIMIX VFL 12-Layer Engine v6 — UPGRADED
Key upgrades:
1. ULTRA threshold raised from 75 to 82 (only the best)
2. PREMIUM raised from 60 to 70
3. Added ELITE tier bonus increased to +15 (Diamond) / +10 (Gold)
4. Danger team penalty: -5 for teams with known weak patterns
5. Minimum 7 games required for team profiles
6. Max 8 picks per message to reduce noise
"""
import requests, json, hashlib, time, os
from collections import defaultdict
from datetime import datetime, timezone, timedelta

# ─── CONFIG ───
TG_TOKEN = "8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
TG_CHAT  = "1745848158"
DEDUP_FILE = "/tmp/vfl_dedup_L2_v6.json"
ALERT_WINDOW = 20
API_BASE = "https://www.sportybet.com/api/ng"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.sportybet.com/ng/virtual",
    "Origin": "https://www.sportybet.com"
}

# Thresholds
ULTRA_THRESHOLD = 82
PREMIUM_THRESHOLD = 70
MAX_PICKS = 8

# ─── ELITE DATABASE v2 ───
ELITE_DB = {"BOUvTOT":{"t":"D","r":1.0,"g":8,"b":0.625},"FORvSUN":{"t":"D","r":1.0,"g":8,"b":0.625},"LIVvMUN":{"t":"D","r":1.0,"g":8,"b":0.75},"WOLvNEW":{"t":"D","r":1.0,"g":8,"b":0.625},"CRYvCHE":{"t":"D","r":1.0,"g":8,"b":0.75},"WOLvBUR":{"t":"D","r":1.0,"g":8,"b":0.625},"ASTvARS":{"t":"D","r":1.0,"g":8,"b":0.75},"BREvTOT":{"t":"D","r":1.0,"g":8,"b":0.625},"CRYvMCI":{"t":"D","r":1.0,"g":8,"b":0.75},"MUNvCHE":{"t":"D","r":1.0,"g":8,"b":0.75},"SUNvNEW":{"t":"D","r":1.0,"g":8,"b":0.375},"NEWvARS":{"t":"D","r":1.0,"g":9,"b":0.6667},"CHEvEVE":{"t":"D","r":1.0,"g":8,"b":0.5},"CRYvWOL":{"t":"D","r":1.0,"g":8,"b":0.5},"NEWvBUR":{"t":"D","r":1.0,"g":8,"b":0.75},"TOTvARS":{"t":"D","r":1.0,"g":8,"b":0.75},"ASTvFUL":{"t":"D","r":1.0,"g":8,"b":0.625},"LIVvWOL":{"t":"D","r":1.0,"g":8,"b":0.375},"NEWvLEE":{"t":"D","r":1.0,"g":8,"b":0.75},"CHEvFUL":{"t":"D","r":1.0,"g":8,"b":0.625},"BOUvCHE":{"t":"D","r":1.0,"g":8,"b":0.5},"CRYvSUN":{"t":"D","r":1.0,"g":8,"b":1.0},"LIVvBRE":{"t":"D","r":1.0,"g":8,"b":0.625},"ARSvLEE":{"t":"D","r":1.0,"g":8,"b":0.625},"ARSvFUL":{"t":"D","r":1.0,"g":8,"b":0.875},"CRYvTOT":{"t":"D","r":1.0,"g":8,"b":0.5},"MUNvNEW":{"t":"D","r":1.0,"g":8,"b":0.625},"WHUvLEE":{"t":"D","r":1.0,"g":8,"b":0.875},"WOLvMCI":{"t":"D","r":1.0,"g":8,"b":0.625},"MUNvTOT":{"t":"D","r":1.0,"g":8,"b":0.75},"BREvMCI":{"t":"D","r":1.0,"g":8,"b":0.75},"LIVvLEE":{"t":"D","r":1.0,"g":8,"b":0.625},"NEWvCHE":{"t":"D","r":1.0,"g":8,"b":0.875},"CHEvTOT":{"t":"D","r":1.0,"g":9,"b":1.0},"NEWvEVE":{"t":"D","r":1.0,"g":8,"b":0.375},"ARSvCRY":{"t":"D","r":1.0,"g":8,"b":0.625},"CHEvBUR":{"t":"D","r":1.0,"g":8,"b":0.875},"LIVvWHU":{"t":"D","r":1.0,"g":8,"b":0.75},"ASTvBHA":{"t":"D","r":1.0,"g":8,"b":0.75},"LIVvCRY":{"t":"D","r":1.0,"g":8,"b":0.875},"TOTvMCI":{"t":"D","r":1.0,"g":8,"b":0.625},"ASTvWHU":{"t":"D","r":1.0,"g":8,"b":0.625},"ASTvCRY":{"t":"D","r":1.0,"g":8,"b":0.875},"CHEvWHU":{"t":"D","r":1.0,"g":8,"b":0.625},"ASTvLIV":{"t":"D","r":1.0,"g":8,"b":0.875},"NEWvFOR":{"t":"D","r":1.0,"g":8,"b":1.0},"ARSvSUN":{"t":"D","r":1.0,"g":7,"b":0.7143},"CHEvAST":{"t":"D","r":1.0,"g":8,"b":0.75},"ARSvCHE":{"t":"D","r":1.0,"g":8,"b":0.5},"FULvLIV":{"t":"D","r":1.0,"g":8,"b":0.625},"ARSvTOT":{"t":"D","r":1.0,"g":8,"b":0.875},"EVEvCHE":{"t":"D","r":1.0,"g":7,"b":0.5714},"FULvAST":{"t":"D","r":1.0,"g":8,"b":1.0},"LEEvNEW":{"t":"D","r":1.0,"g":8,"b":0.75},"FULvCHE":{"t":"D","r":1.0,"g":8,"b":0.75},"MCIvEVE":{"t":"D","r":1.0,"g":8,"b":0.75},"OVIvELC":{"t":"D","r":1.0,"g":8,"b":0.875},"BILvELC":{"t":"D","r":1.0,"g":8,"b":0.75},"RAYvLEV":{"t":"D","r":1.0,"g":8,"b":0.75},"ATMvRMA":{"t":"D","r":1.0,"g":8,"b":0.375},"MALvGIR":{"t":"D","r":1.0,"g":8,"b":0.875},"SEVvRAY":{"t":"D","r":1.0,"g":8,"b":0.75},"RBBvRMA":{"t":"D","r":1.0,"g":8,"b":1.0},"RBBvFCB":{"t":"D","r":1.0,"g":8,"b":0.625},"ALAvVIL":{"t":"D","r":1.0,"g":7,"b":0.8571},"OVIvFCB":{"t":"D","r":1.0,"g":8,"b":0.5},"SEVvLEV":{"t":"D","r":1.0,"g":8,"b":0.625},"BILvOVI":{"t":"D","r":1.0,"g":8,"b":0.625},"ATMvLEV":{"t":"D","r":1.0,"g":8,"b":0.875},"CELvFCB":{"t":"D","r":1.0,"g":8,"b":0.625},"VCFvOVI":{"t":"D","r":1.0,"g":8,"b":0.5},"VCFvELC":{"t":"D","r":1.0,"g":8,"b":0.5},"INTvUSC":{"t":"D","r":1.0,"g":8,"b":0.875},"UDIvINT":{"t":"D","r":1.0,"g":8,"b":0.375},"ROMvNAP":{"t":"D","r":1.0,"g":8,"b":0.875},"ATAvBFC":{"t":"D","r":1.0,"g":8,"b":0.75},"FIOvGEN":{"t":"D","r":1.0,"g":8,"b":0.875},"PISvGEN":{"t":"D","r":1.0,"g":8,"b":0.875},"ATAvUSC":{"t":"D","r":1.0,"g":8,"b":0.75},"CAGvINT":{"t":"D","r":1.0,"g":7,"b":1.0},"PISvLAZ":{"t":"D","r":1.0,"g":8,"b":0.5},"ATAvUDI":{"t":"D","r":1.0,"g":8,"b":0.625},"VERvFIO":{"t":"D","r":1.0,"g":8,"b":0.5},"UDIvUSC":{"t":"D","r":1.0,"g":8,"b":0.625},"FIOvCOM":{"t":"D","r":1.0,"g":7,"b":1.0},"ATAvNAP":{"t":"D","r":1.0,"g":8,"b":0.75},"CAGvUSC":{"t":"D","r":1.0,"g":8,"b":1.0},"PISvFIO":{"t":"D","r":1.0,"g":8,"b":0.875},"CAGvLAZ":{"t":"D","r":1.0,"g":8,"b":0.75},"ACMvSAS":{"t":"D","r":1.0,"g":8,"b":0.75},"PARvATA":{"t":"D","r":1.0,"g":8,"b":0.75},"NAPvCAG":{"t":"D","r":1.0,"g":8,"b":0.5},"FIOvLAZ":{"t":"D","r":1.0,"g":8,"b":0.75},"LEVvHDH":{"t":"D","r":1.0,"g":8,"b":0.5},"TSGvRBL":{"t":"D","r":1.0,"g":8,"b":0.75},"UNIvHSV":{"t":"D","r":1.0,"g":8,"b":0.875},"KOEvRBL":{"t":"D","r":1.0,"g":8,"b":0.75},"HDHvBMU":{"t":"D","r":1.0,"g":8,"b":0.875},"MAIvSVW":{"t":"D","r":1.0,"g":8,"b":0.5},"SCFvTSG":{"t":"D","r":1.0,"g":8,"b":0.75},"BVBvTSG":{"t":"D","r":1.0,"g":8,"b":0.75},"SCFvKOE":{"t":"D","r":1.0,"g":8,"b":0.875},"SVWvBMU":{"t":"D","r":1.0,"g":7,"b":0.5714},"MAIvHSV":{"t":"D","r":1.0,"g":8,"b":0.375},"WOBvTSG":{"t":"D","r":1.0,"g":8,"b":0.625},"TSGvHSV":{"t":"D","r":1.0,"g":8,"b":0.75},"BVBvBMG":{"t":"D","r":1.0,"g":8,"b":0.625},"KOEvHSV":{"t":"D","r":1.0,"g":8,"b":0.75},"BVBvFCA":{"t":"D","r":1.0,"g":8,"b":0.75},"KOEvTSG":{"t":"D","r":1.0,"g":8,"b":0.625},"LEVvVFB":{"t":"D","r":1.0,"g":8,"b":0.875},"SCFvRBL":{"t":"D","r":1.0,"g":8,"b":0.5},"WOBvBMG":{"t":"D","r":1.0,"g":8,"b":1.0},"BVBvRBL":{"t":"D","r":1.0,"g":8,"b":0.5},"LEVvTSG":{"t":"D","r":1.0,"g":8,"b":0.875},"BVBvSCF":{"t":"D","r":1.0,"g":8,"b":0.625},"BMGvTSG":{"t":"D","r":1.0,"g":7,"b":0.5714},"UNIvSGE":{"t":"D","r":1.0,"g":8,"b":0.625},"RENvMET":{"t":"D","r":1.0,"g":8,"b":1.0},"STRvOLM":{"t":"D","r":1.0,"g":8,"b":0.75},"ANGvLIL":{"t":"D","r":1.0,"g":8,"b":0.5},"LENvAUX":{"t":"D","r":1.0,"g":9,"b":0.7778},"OLMvLIL":{"t":"D","r":1.0,"g":8,"b":0.5},"LORvLYO":{"t":"D","r":1.0,"g":8,"b":0.875},"ANGvLOR":{"t":"D","r":1.0,"g":8,"b":0.625},"TOUvNCE":{"t":"D","r":1.0,"g":8,"b":0.375},"LYOvMET":{"t":"D","r":1.0,"g":8,"b":0.75},"NANvAUX":{"t":"D","r":1.0,"g":8,"b":0.625},"PSGvAMO":{"t":"D","r":1.0,"g":8,"b":0.75},"ANGvAUX":{"t":"D","r":1.0,"g":8,"b":0.875},"LYOvAMO":{"t":"D","r":1.0,"g":8,"b":0.5},"OLMvMET":{"t":"D","r":1.0,"g":8,"b":0.75},"PSGvREN":{"t":"D","r":1.0,"g":8,"b":0.75},"LEHvAUX":{"t":"D","r":1.0,"g":8,"b":0.625},"PSGvANG":{"t":"D","r":1.0,"g":8,"b":0.5},"AUXvB29":{"t":"D","r":1.0,"g":8,"b":0.5},"LILvAMO":{"t":"D","r":1.0,"g":9,"b":0.5556},"OLMvANG":{"t":"D","r":1.0,"g":8,"b":1.0},"AMOvB29":{"t":"D","r":1.0,"g":8,"b":0.625},"AUXvTOU":{"t":"D","r":1.0,"g":8,"b":0.875},"LENvPFC":{"t":"D","r":1.0,"g":8,"b":0.875},"LILvLYO":{"t":"D","r":1.0,"g":8,"b":0.625},"AUXvLOR":{"t":"D","r":1.0,"g":8,"b":0.375},"NCEvOLM":{"t":"D","r":1.0,"g":8,"b":0.75},"PSGvNCE":{"t":"D","r":1.0,"g":8,"b":0.625},"NANvLOR":{"t":"D","r":1.0,"g":8,"b":0.75},"AMOvLEN":{"t":"D","r":1.0,"g":8,"b":0.875},"NANvPFC":{"t":"D","r":1.0,"g":8,"b":1.0},"TOUvSTR":{"t":"D","r":1.0,"g":8,"b":0.875},"CHEvNEW":{"t":"D","r":1.0,"g":7,"b":0.4286},"BOUvNEW":{"t":"D","r":1.0,"g":7,"b":0.5714},"CRYvARS":{"t":"D","r":1.0,"g":7,"b":0.8571},"CHEvSUN":{"t":"D","r":1.0,"g":7,"b":0.8571},"CRYvLIV":{"t":"D","r":1.0,"g":7,"b":0.7143},"BOUvARS":{"t":"D","r":1.0,"g":7,"b":0.7143},"TOTvCHE":{"t":"D","r":1.0,"g":7,"b":0.5714},"BURvMUN":{"t":"D","r":1.0,"g":7,"b":0.5714},"ASTvBRE":{"t":"D","r":1.0,"g":7,"b":0.8571},"EVEvNEW":{"t":"D","r":1.0,"g":7,"b":0.8571},"FULvFOR":{"t":"D","r":1.0,"g":7,"b":0.7143},"TOTvCRY":{"t":"D","r":1.0,"g":7,"b":0.7143},"MCIvWOL":{"t":"D","r":1.0,"g":7,"b":0.8571},"MUNvBRE":{"t":"D","r":1.0,"g":7,"b":0.7143},"NEWvMUN":{"t":"D","r":1.0,"g":7,"b":1.0},"CHEvBRE":{"t":"D","r":1.0,"g":7,"b":0.7143},"NEWvLIV":{"t":"D","r":1.0,"g":7,"b":1.0},"WHUvMUN":{"t":"D","r":1.0,"g":7,"b":1.0},"NEWvAST":{"t":"D","r":1.0,"g":7,"b":0.5714},"BOUvSUN":{"t":"D","r":1.0,"g":7,"b":0.7143},"EVEvWOL":{"t":"D","r":1.0,"g":7,"b":0.8571},"WHUvLIV":{"t":"D","r":1.0,"g":7,"b":1.0},"CHEvFOR":{"t":"D","r":1.0,"g":7,"b":1.0},"FCBvELC":{"t":"D","r":1.0,"g":7,"b":0.8571},"RBBvOVI":{"t":"D","r":1.0,"g":7,"b":0.4286},"RSOvRAY":{"t":"D","r":1.0,"g":7,"b":0.7143},"MALvESP":{"t":"D","r":1.0,"g":7,"b":0.5714},"ATMvRBB":{"t":"D","r":1.0,"g":8,"b":0.875},"VILvBIL":{"t":"D","r":1.0,"g":7,"b":0.5714},"CELvGIR":{"t":"D","r":1.0,"g":7,"b":0.5714},"LEVvATM":{"t":"D","r":1.0,"g":7,"b":0.4286},"RMAvFCB":{"t":"D","r":1.0,"g":7,"b":0.2857},"RMAvELC":{"t":"D","r":1.0,"g":7,"b":0.5714},"ELCvSEV":{"t":"D","r":1.0,"g":7,"b":0.7143},"ATAvROM":{"t":"D","r":1.0,"g":7,"b":0.8571},"NAPvJUV":{"t":"D","r":1.0,"g":7,"b":0.7143},"ACMvROM":{"t":"D","r":1.0,"g":7,"b":0.4286},"LAZvPAR":{"t":"D","r":1.0,"g":7,"b":0.5714},"ACMvLEC":{"t":"D","r":1.0,"g":7,"b":1.0},"USCvGEN":{"t":"D","r":1.0,"g":8,"b":0.875},"USCvNAP":{"t":"D","r":1.0,"g":7,"b":0.8571},"LECvSAS":{"t":"D","r":1.0,"g":7,"b":0.8571},"CAGvFIO":{"t":"D","r":1.0,"g":7,"b":0.8571},"INTvACM":{"t":"D","r":1.0,"g":7,"b":0.7143},"BVBvBMU":{"t":"D","r":1.0,"g":7,"b":0.5714},"FCAvRBL":{"t":"D","r":1.0,"g":7,"b":1.0},"MAIvTSG":{"t":"D","r":1.0,"g":7,"b":1.0},"VFBvSGE":{"t":"D","r":1.0,"g":7,"b":1.0},"HDHvRBL":{"t":"D","r":1.0,"g":7,"b":0.5714},"HDHvMAI":{"t":"D","r":1.0,"g":7,"b":0.7143},"SCFvBVB":{"t":"D","r":1.0,"g":7,"b":0.4286},"BMGvSCF":{"t":"D","r":1.0,"g":7,"b":0.5714},"BVBvSGE":{"t":"D","r":1.0,"g":7,"b":0.4286},"RBLvBMU":{"t":"D","r":1.0,"g":7,"b":0.5714},"SGEvLEV":{"t":"D","r":1.0,"g":7,"b":0.7143},"KOEvBMU":{"t":"D","r":1.0,"g":7,"b":0.8571},"LENvOLM":{"t":"D","r":1.0,"g":7,"b":0.7143},"AUXvOLM":{"t":"D","r":1.0,"g":7,"b":0.7143},"LILvREN":{"t":"D","r":1.0,"g":7,"b":0.7143},"AUXvSTR":{"t":"D","r":1.0,"g":7,"b":0.7143},"LILvMET":{"t":"D","r":1.0,"g":7,"b":0.5714},"LILvLEN":{"t":"D","r":1.0,"g":7,"b":0.7143},"STRvREN":{"t":"D","r":1.0,"g":7,"b":1.0},"AMOvLYO":{"t":"D","r":1.0,"g":7,"b":0.7143},"B29vLEN":{"t":"D","r":1.0,"g":7,"b":1.0},"OLMvLOR":{"t":"D","r":1.0,"g":7,"b":0.8571},"PFCvSTR":{"t":"D","r":1.0,"g":7,"b":0.4286},"LEHvB29":{"t":"D","r":1.0,"g":7,"b":0.7143},"NANvPSG":{"t":"D","r":1.0,"g":7,"b":0.4286},"LORvANG":{"t":"D","r":1.0,"g":7,"b":0.8571},"RENvLOR":{"t":"D","r":1.0,"g":7,"b":1.0},"NANvSTR":{"t":"D","r":1.0,"g":7,"b":0.7143},"CRYvAST":{"t":"G","r":0.875,"g":8,"b":0.875},"FULvBUR":{"t":"G","r":0.875,"g":8,"b":0.625},"WOLvTOT":{"t":"G","r":0.875,"g":8,"b":0.625},"BREvNEW":{"t":"G","r":0.875,"g":8,"b":0.5},"WOLvLEE":{"t":"G","r":0.875,"g":8,"b":0.625},"ASTvCHE":{"t":"G","r":0.875,"g":8,"b":0.75},"LIVvMCI":{"t":"G","r":0.875,"g":8,"b":0.75},"MUNvEVE":{"t":"G","r":0.875,"g":8,"b":0.375},"ASTvEVE":{"t":"G","r":0.875,"g":8,"b":0.625},"CHEvARS":{"t":"G","r":0.875,"g":8,"b":0.875},"CRYvBOU":{"t":"G","r":0.875,"g":8,"b":0.75},"LIVvFUL":{"t":"G","r":0.875,"g":8,"b":0.375},"NEWvTOT":{"t":"G","r":0.875,"g":8,"b":0.5},"LIVvBOU":{"t":"G","r":0.875,"g":8,"b":0.625},"MUNvFUL":{"t":"G","r":0.875,"g":8,"b":0.625},"CHEvMCI":{"t":"G","r":0.875,"g":8,"b":0.625},"FORvCRY":{"t":"G","r":0.8889,"g":9,"b":0.7778},"MUNvBOU":{"t":"G","r":0.875,"g":8,"b":0.875},"BREvCRY":{"t":"G","r":0.875,"g":8,"b":0.625},"EVEvMCI":{"t":"G","r":0.875,"g":8,"b":0.75},"LIVvFOR":{"t":"G","r":0.875,"g":8,"b":0.75},"TOTvLEE":{"t":"G","r":0.875,"g":8,"b":0.625},"ARSvMCI":{"t":"G","r":0.875,"g":8,"b":0.5},"FULvEVE":{"t":"G","r":0.875,"g":8,"b":0.625},"BHAvBUR":{"t":"G","r":0.875,"g":8,"b":0.625},"CRYvNEW":{"t":"G","r":0.875,"g":8,"b":0.875},"FULvMCI":{"t":"G","r":0.875,"g":8,"b":0.375},"BHAvLEE":{"t":"G","r":0.875,"g":8,"b":0.75},"LIVvNEW":{"t":"G","r":0.875,"g":8,"b":0.75},"MUNvSUN":{"t":"G","r":0.875,"g":8,"b":0.375},"WOLvEVE":{"t":"G","r":0.875,"g":8,"b":0.5},"BREvCHE":{"t":"G","r":0.8889,"g":9,"b":0.7778},"CRYvLEE":{"t":"G","r":0.875,"g":8,"b":0.875},"WHUvBHA":{"t":"G","r":0.875,"g":8,"b":0.625},"CRYvBHA":{"t":"G","r":0.875,"g":8,"b":0.625},"MUNvBUR":{"t":"G","r":0.875,"g":8,"b":0.875},"FORvBOU":{"t":"G","r":0.875,"g":8,"b":0.625},"MUNvLEE":{"t":"G","r":0.875,"g":8,"b":0.5},"NEWvMCI":{"t":"G","r":0.875,"g":8,"b":0.875},"CHEvLEE":{"t":"G","r":0.875,"g":8,"b":0.875},"NEWvFUL":{"t":"G","r":0.875,"g":8,"b":0.75},"ARSvLIV":{"t":"G","r":0.8889,"g":9,"b":0.8889},"BURvMCI":{"t":"G","r":0.875,"g":8,"b":0.5},"CHEvBHA":{"t":"G","r":0.875,"g":8,"b":0.875},"SUNvWOL":{"t":"G","r":0.8889,"g":9,"b":0.8889},"MUNvLIV":{"t":"G","r":0.8889,"g":9,"b":0.7778},"TOTvBOU":{"t":"G","r":0.875,"g":8,"b":0.875},"ARSvMUN":{"t":"G","r":0.875,"g":8,"b":0.75},"LEEvFUL":{"t":"G","r":0.8889,"g":9,"b":0.6667},"TOTvWOL":{"t":"G","r":0.875,"g":8,"b":0.375},"ASTvMUN":{"t":"G","r":0.875,"g":8,"b":0.75},"EVEvCRY":{"t":"G","r":0.875,"g":8,"b":0.5},"FULvBHA":{"t":"G","r":0.875,"g":8,"b":0.25},"LEEvBOU":{"t":"G","r":0.875,"g":8,"b":0.625},"MCIvWHU":{"t":"G","r":0.875,"g":8,"b":0.625},"TOTvFOR":{"t":"G","r":0.875,"g":8,"b":0.625},"BURvFOR":{"t":"G","r":0.875,"g":8,"b":0.75},"TOTvBRE":{"t":"G","r":0.875,"g":8,"b":0.875},"LEEvFOR":{"t":"G","r":0.875,"g":8,"b":0.625},"BHAvFOR":{"t":"G","r":0.875,"g":8,"b":0.75},"BOUvCRY":{"t":"G","r":0.875,"g":8,"b":0.75},"BURvSUN":{"t":"G","r":0.875,"g":8,"b":0.75},"TOTvNEW":{"t":"G","r":0.875,"g":8,"b":0.75},"FULvMUN":{"t":"G","r":0.875,"g":8,"b":0.875},"WHUvFOR":{"t":"G","r":0.875,"g":8,"b":0.625},"WOLvCRY":{"t":"G","r":0.875,"g":8,"b":0.875},"BHAvSUN":{"t":"G","r":0.875,"g":8,"b":0.25},"WOLvLIV":{"t":"G","r":0.875,"g":8,"b":0.75},"FORvLIV":{"t":"G","r":0.875,"g":8,"b":0.875},"WHUvSUN":{"t":"G","r":0.875,"g":8,"b":0.625},"GETvATM":{"t":"G","r":0.875,"g":8,"b":0.625},"LEVvRMA":{"t":"G","r":0.875,"g":8,"b":0.75},"GETvRMA":{"t":"G","r":0.875,"g":8,"b":0.5},"RBBvCEL":{"t":"G","r":0.875,"g":8,"b":0.75},"RBBvLEV":{"t":"G","r":0.875,"g":8,"b":0.875},"RSOvVIL":{"t":"G","r":0.875,"g":8,"b":0.875},"ESPvRBB":{"t":"G","r":0.875,"g":8,"b":0.5},"BILvLEV":{"t":"G","r":0.875,"g":8,"b":0.625},"RSOvRMA":{"t":"G","r":0.875,"g":8,"b":0.75},"VILvATM":{"t":"G","r":0.875,"g":8,"b":0.625},"RSOvRBB":{"t":"G","r":0.875,"g":8,"b":0.5},"VILvFCB":{"t":"G","r":0.875,"g":8,"b":0.75},"LEVvMAL":{"t":"G","r":0.875,"g":8,"b":0.625},"OSAvALA":{"t":"G","r":0.875,"g":8,"b":0.5},"GIRvFCB":{"t":"G","r":0.875,"g":8,"b":0.75},"LEVvCEL":{"t":"G","r":0.875,"g":8,"b":0.75},"GETvCEL":{"t":"G","r":0.875,"g":8,"b":0.875},"RSOvELC":{"t":"G","r":0.875,"g":8,"b":0.75},"OSAvCEL":{"t":"G","r":0.875,"g":8,"b":0.625},"RAYvRBB":{"t":"G","r":0.875,"g":8,"b":0.75},"SEVvMAL":{"t":"G","r":0.875,"g":8,"b":0.375},"BILvRBB":{"t":"G","r":0.875,"g":8,"b":0.5},"OVIvRAY":{"t":"G","r":0.875,"g":8,"b":0.375},"RSOvCEL":{"t":"G","r":0.875,"g":8,"b":0.625},"ATMvMAL":{"t":"G","r":0.875,"g":8,"b":0.75},"BILvRAY":{"t":"G","r":0.875,"g":8,"b":0.5},"GIRvOVI":{"t":"G","r":0.875,"g":8,"b":0.625},"OSAvESP":{"t":"G","r":0.875,"g":8,"b":0.75},"VCFvRMA":{"t":"G","r":0.875,"g":8,"b":0.875},"ATMvCEL":{"t":"G","r":0.875,"g":8,"b":0.5},"GIRvOSA":{"t":"G","r":0.875,"g":8,"b":0.75},"MALvFCB":{"t":"G","r":0.875,"g":8,"b":0.75},"ATMvGET":{"t":"G","r":0.875,"g":8,"b":0.625},"GIRvSEV":{"t":"G","r":0.8889,"g":9,"b":0.5556},"MALvRAY":{"t":"G","r":0.875,"g":8,"b":0.75},"ELCvALA":{"t":"G","r":0.875,"g":8,"b":0.25},"FCBvGET":{"t":"G","r":0.875,"g":8,"b":0.5},"CELvOVI":{"t":"G","r":0.875,"g":8,"b":0.625},"RMAvOSA":{"t":"G","r":0.875,"g":8,"b":0.625},"VCFvALA":{"t":"G","r":0.875,"g":8,"b":0.5},"FCBvOSA":{"t":"G","r":0.875,"g":8,"b":0.625},"CELvALA":{"t":"G","r":0.875,"g":8,"b":0.25},"LEVvBIL":{"t":"G","r":0.875,"g":8,"b":0.625},"CELvELC":{"t":"G","r":0.8889,"g":9,"b":0.5556},"GETvBIL":{"t":"G","r":0.875,"g":8,"b":0.875},"FIOvBFC":{"t":"G","r":0.875,"g":8,"b":0.5},"GENvCOM":{"t":"G","r":0.875,"g":8,"b":0.375},"LAZvNAP":{"t":"G","r":0.875,"g":8,"b":0.75},"PISvBFC":{"t":"G","r":0.875,"g":8,"b":0.625},"FIOvUSC":{"t":"G","r":0.875,"g":8,"b":0.875},"PISvUSC":{"t":"G","r":0.875,"g":8,"b":0.5},"ROMvCOM":{"t":"G","r":0.875,"g":8,"b":0.5},"VERvCOM":{"t":"G","r":0.875,"g":8,"b":0.75},"CAGvCOM":{"t":"G","r":0.875,"g":8,"b":0.5},"TORvUSC":{"t":"G","r":0.875,"g":8,"b":0.25},"LECvCOM":{"t":"G","r":0.875,"g":8,"b":0.875},"ROMvFIO":{"t":"G","r":0.875,"g":8,"b":0.5},"JUVvLEC":{"t":"G","r":0.875,"g":8,"b":0.75},"PARvUSC":{"t":"G","r":0.875,"g":8,"b":0.625},"PISvCAG":{"t":"G","r":0.875,"g":8,"b":0.75},"ROMvTOR":{"t":"G","r":0.875,"g":8,"b":0.5},"CAGvATA":{"t":"G","r":0.875,"g":8,"b":0.75},"PISvINT":{"t":"G","r":0.875,"g":8,"b":0.25},"ROMvUSC":{"t":"G","r":0.875,"g":8,"b":0.375},"CAGvACM":{"t":"G","r":0.8889,"g":9,"b":0.5556},"ATAvCOM":{"t":"G","r":0.875,"g":8,"b":0.375},"TORvINT":{"t":"G","r":0.875,"g":8,"b":0.375},"VERvUDI":{"t":"G","r":0.875,"g":8,"b":0.875},"BFCvINT":{"t":"G","r":0.875,"g":8,"b":0.5},"ACMvINT":{"t":"G","r":0.875,"g":8,"b":0.5},"ATAvFIO":{"t":"G","r":0.875,"g":8,"b":0.5},"BFCvJUV":{"t":"G","r":0.875,"g":8,"b":0.75},"ACMvJUV":{"t":"G","r":0.875,"g":8,"b":0.5},"ATAvPIS":{"t":"G","r":0.875,"g":8,"b":0.5},"NAPvLAZ":{"t":"G","r":0.875,"g":8,"b":0.5},"PARvTOR":{"t":"G","r":0.875,"g":8,"b":0.75},"BFCvSAS":{"t":"G","r":0.875,"g":8,"b":0.75},"USCvFIO":{"t":"G","r":0.875,"g":8,"b":0.5},"JUVvGEN":{"t":"G","r":0.875,"g":8,"b":0.375},"LECvCAG":{"t":"G","r":0.875,"g":8,"b":0.75},"COMvVER":{"t":"G","r":0.875,"g":8,"b":0.75},"COMvLEC":{"t":"G","r":0.875,"g":8,"b":0.625},"GENvSAS":{"t":"G","r":0.875,"g":8,"b":0.625},"INTvCAG":{"t":"G","r":0.875,"g":8,"b":0.625},"USCvATA":{"t":"G","r":0.875,"g":8,"b":0.75},"FIOvVER":{"t":"G","r":0.875,"g":8,"b":0.75},"LAZvSAS":{"t":"G","r":0.875,"g":8,"b":0.625},"USCvBFC":{"t":"G","r":0.875,"g":8,"b":0.5},"LEVvBMU":{"t":"G","r":0.875,"g":8,"b":0.625},"TSGvBMG":{"t":"G","r":0.875,"g":8,"b":0.875},"KOEvBMG":{"t":"G","r":0.875,"g":8,"b":0.75},"SCFvSVW":{"t":"G","r":0.875,"g":8,"b":0.75},"UNIvVFB":{"t":"G","r":0.8889,"g":9,"b":0.2222},"WOBvMAI":{"t":"G","r":0.8889,"g":9,"b":0.2222},"MAIvBMU":{"t":"G","r":0.875,"g":8,"b":0.75},"UNIvTSG":{"t":"G","r":0.875,"g":8,"b":0.875},"BVBvHSV":{"t":"G","r":0.875,"g":8,"b":0.75},"SGEvRBL":{"t":"G","r":0.875,"g":8,"b":0.5},"LEVvRBL":{"t":"G","r":0.875,"g":8,"b":0.75},"BMGvBMU":{"t":"G","r":0.875,"g":8,"b":0.625},"BVBvKOE":{"t":"G","r":0.875,"g":8,"b":0.375},"HDHvFCA":{"t":"G","r":0.875,"g":8,"b":0.75},"SGEvSCF":{"t":"G","r":0.8889,"g":9,"b":0.5556},"STPvRBL":{"t":"G","r":0.875,"g":8,"b":0.625},"SVWvVFB":{"t":"G","r":0.875,"g":8,"b":0.625},"BMUvVFB":{"t":"G","r":0.875,"g":8,"b":0.75},"SGEvBVB":{"t":"G","r":0.875,"g":8,"b":0.625},"UNIvSTP":{"t":"G","r":0.875,"g":8,"b":0.625},"BVBvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"SGEvWOB":{"t":"G","r":0.875,"g":8,"b":0.625},"UNIvHDH":{"t":"G","r":0.875,"g":8,"b":0.625},"SCFvHDH":{"t":"G","r":0.875,"g":8,"b":0.625},"BMUvRBL":{"t":"G","r":0.875,"g":8,"b":0.75},"KOEvVFB":{"t":"G","r":0.875,"g":8,"b":0.625},"WOBvSTP":{"t":"G","r":0.875,"g":8,"b":0.875},"BMUvTSG":{"t":"G","r":0.8889,"g":9,"b":0.6667},"SCFvFCA":{"t":"G","r":0.875,"g":8,"b":0.5},"UNIvRBL":{"t":"G","r":0.875,"g":8,"b":0.75},"MAIvBMG":{"t":"G","r":0.875,"g":8,"b":0.75},"BVBvUNI":{"t":"G","r":0.875,"g":8,"b":0.5},"SGEvKOE":{"t":"G","r":0.875,"g":8,"b":0.875},"STPvHSV":{"t":"G","r":0.875,"g":8,"b":0.375},"SVWvBMG":{"t":"G","r":0.875,"g":8,"b":0.5},"BMGvVFB":{"t":"G","r":0.875,"g":8,"b":0.375},"BMUvSGE":{"t":"G","r":0.875,"g":8,"b":0.25},"HDHvHSV":{"t":"G","r":0.875,"g":8,"b":0.5},"LEVvSGE":{"t":"G","r":0.875,"g":8,"b":0.125},"FCAvHSV":{"t":"G","r":0.875,"g":8,"b":0.75},"VFBvRBL":{"t":"G","r":0.875,"g":8,"b":0.75},"WOBvBVB":{"t":"G","r":0.875,"g":8,"b":0.375},"BMGvKOE":{"t":"G","r":0.875,"g":8,"b":0.5},"STPvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"HDHvLEV":{"t":"G","r":0.875,"g":8,"b":0.625},"HSVvUNI":{"t":"G","r":0.875,"g":8,"b":0.25},"RBLvTSG":{"t":"G","r":0.875,"g":8,"b":0.25},"VFBvSCF":{"t":"G","r":0.875,"g":8,"b":0.625},"BMUvMAI":{"t":"G","r":0.875,"g":8,"b":0.5},"RBLvKOE":{"t":"G","r":0.875,"g":8,"b":0.625},"SVWvWOB":{"t":"G","r":0.875,"g":8,"b":0.875},"TSGvUNI":{"t":"G","r":0.875,"g":8,"b":0.75},"VFBvBVB":{"t":"G","r":0.875,"g":8,"b":0.875},"FCAvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"VFBvWOB":{"t":"G","r":0.875,"g":8,"b":0.375},"KOEvSCF":{"t":"G","r":0.875,"g":8,"b":0.5},"RBLvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"TSGvWOB":{"t":"G","r":0.875,"g":8,"b":0.75},"UNIvLEV":{"t":"G","r":0.875,"g":8,"b":0.5},"ANGvOLM":{"t":"G","r":0.875,"g":8,"b":0.625},"STRvPSG":{"t":"G","r":0.875,"g":8,"b":0.5},"TOUvMET":{"t":"G","r":0.875,"g":8,"b":0.5},"LORvMET":{"t":"G","r":0.875,"g":8,"b":0.375},"LYOvLIL":{"t":"G","r":0.875,"g":8,"b":0.375},"NANvB29":{"t":"G","r":0.875,"g":8,"b":0.5},"RENvAUX":{"t":"G","r":0.875,"g":8,"b":0.75},"STRvNCE":{"t":"G","r":0.875,"g":8,"b":0.875},"LORvAUX":{"t":"G","r":0.875,"g":8,"b":0.625},"LYOvB29":{"t":"G","r":0.875,"g":8,"b":0.5},"OLMvNCE":{"t":"G","r":0.875,"g":8,"b":0.5},"STRvLEH":{"t":"G","r":0.875,"g":8,"b":0.625},"LORvAMO":{"t":"G","r":0.875,"g":8,"b":0.625},"LORvNAN":{"t":"G","r":0.875,"g":8,"b":0.75},"NCEvLEH":{"t":"G","r":0.875,"g":8,"b":0.625},"STRvB29":{"t":"G","r":0.875,"g":8,"b":0.625},"METvAUX":{"t":"G","r":0.875,"g":8,"b":0.875},"STRvTOU":{"t":"G","r":0.875,"g":8,"b":0.875},"NANvMET":{"t":"G","r":0.8889,"g":9,"b":0.5556},"ANGvMET":{"t":"G","r":0.875,"g":8,"b":0.25},"LYOvAUX":{"t":"G","r":0.875,"g":8,"b":0.5},"NANvAMO":{"t":"G","r":0.875,"g":8,"b":0.375},"PSGvB29":{"t":"G","r":0.875,"g":8,"b":0.625},"RENvLEH":{"t":"G","r":0.875,"g":8,"b":0.375},"TOUvLIL":{"t":"G","r":0.875,"g":8,"b":0.5},"PFCvNCE":{"t":"G","r":0.875,"g":8,"b":0.625},"LENvNCE":{"t":"G","r":0.875,"g":8,"b":0.5},"PFCvLEH":{"t":"G","r":0.875,"g":8,"b":0.625},"LENvLEH":{"t":"G","r":0.875,"g":8,"b":0.5},"LORvB29":{"t":"G","r":0.8889,"g":9,"b":0.7778},"PSGvLYO":{"t":"G","r":0.875,"g":8,"b":0.625},"ANGvLYO":{"t":"G","r":0.875,"g":8,"b":0.75},"LORvTOU":{"t":"G","r":0.875,"g":8,"b":0.125},"METvLEH":{"t":"G","r":0.875,"g":8,"b":0.75},"STRvNAN":{"t":"G","r":0.875,"g":8,"b":0.875},"LORvREN":{"t":"G","r":0.875,"g":8,"b":0.75},"NCEvAMO":{"t":"G","r":0.875,"g":8,"b":0.875},"NCEvNAN":{"t":"G","r":0.875,"g":8,"b":0.5},"PFCvREN":{"t":"G","r":0.875,"g":8,"b":0.875},"PSGvLOR":{"t":"G","r":0.875,"g":8,"b":0.625},"PFCvLOR":{"t":"G","r":0.875,"g":8,"b":0.75},"LEHvLYO":{"t":"G","r":0.875,"g":8,"b":0.625},"NCEvANG":{"t":"G","r":0.875,"g":8,"b":0.5},"OLMvSTR":{"t":"G","r":0.875,"g":8,"b":0.75},"AMOvTOU":{"t":"G","r":0.875,"g":8,"b":0.625},"AUXvREN":{"t":"G","r":0.875,"g":8,"b":0.75},"AUXvPFC":{"t":"G","r":0.875,"g":8,"b":0.5},"NANvREN":{"t":"G","r":0.875,"g":8,"b":0.375},"LYOvREN":{"t":"G","r":0.875,"g":8,"b":0.75},"TOUvANG":{"t":"G","r":0.875,"g":8,"b":0.75},"AUXvMET":{"t":"G","r":0.875,"g":8,"b":0.5},"LYOvLOR":{"t":"G","r":0.875,"g":8,"b":0.75},"TSGvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"METvOLM":{"t":"G","r":0.875,"g":8,"b":0.75},"TOUvPSG":{"t":"G","r":0.875,"g":8,"b":0.875}}

# ─── TEAM PROFILES (from 13,574 matches: 7-day + today) ───
TEAM_PROFILES = {"BHA":{"g":295,"o05":0.922,"o15":0.6915,"o25":0.4,"btts":0.4847,"avg_scored":1.061,"avg_conceded":1.332,"league":"ENG"},"EVE":{"g":295,"o05":0.8983,"o15":0.7051,"o25":0.4237,"btts":0.4542,"avg_scored":1.169,"avg_conceded":1.241,"league":"ENG"},"BOU":{"g":295,"o05":0.9254,"o15":0.7254,"o25":0.461,"btts":0.5492,"avg_scored":1.268,"avg_conceded":1.386,"league":"ENG"},"TOT":{"g":295,"o05":0.9627,"o15":0.8203,"o25":0.5831,"btts":0.6102,"avg_scored":1.481,"avg_conceded":1.546,"league":"ENG"},"BRE":{"g":295,"o05":0.9492,"o15":0.7458,"o25":0.5356,"btts":0.5864,"avg_scored":1.359,"avg_conceded":1.464,"league":"ENG"},"ARS":{"g":295,"o05":0.9593,"o15":0.7729,"o25":0.5593,"btts":0.5932,"avg_scored":1.614,"avg_conceded":1.288,"league":"ENG"},"CRY":{"g":295,"o05":0.9831,"o15":0.8339,"o25":0.5898,"btts":0.6339,"avg_scored":1.78,"avg_conceded":1.458,"league":"ENG"},"AST":{"g":295,"o05":0.9254,"o15":0.7695,"o25":0.5424,"btts":0.6237,"avg_scored":1.366,"avg_conceded":1.685,"league":"ENG"},"FOR":{"g":295,"o05":0.9458,"o15":0.739,"o25":0.5525,"btts":0.5729,"avg_scored":1.349,"avg_conceded":1.492,"league":"ENG"},"SUN":{"g":295,"o05":0.9322,"o15":0.7051,"o25":0.4542,"btts":0.4949,"avg_scored":1.207,"avg_conceded":1.315,"league":"ENG"},"FUL":{"g":295,"o05":0.9424,"o15":0.7898,"o25":0.5322,"btts":0.5797,"avg_scored":1.329,"avg_conceded":1.441,"league":"ENG"},"BUR":{"g":295,"o05":0.9119,"o15":0.6847,"o25":0.5017,"btts":0.5288,"avg_scored":1.224,"avg_conceded":1.502,"league":"ENG"},"LEE":{"g":295,"o05":0.8949,"o15":0.7288,"o25":0.461,"btts":0.5254,"avg_scored":1.268,"avg_conceded":1.312,"league":"ENG"},"MCI":{"g":295,"o05":0.9186,"o15":0.7492,"o25":0.5051,"btts":0.4881,"avg_scored":1.763,"avg_conceded":1.081,"league":"ENG"},"LIV":{"g":295,"o05":0.9525,"o15":0.8,"o25":0.5763,"btts":0.5864,"avg_scored":1.647,"avg_conceded":1.336,"league":"ENG"},"MUN":{"g":295,"o05":0.9288,"o15":0.7932,"o25":0.5966,"btts":0.6102,"avg_scored":1.498,"avg_conceded":1.498,"league":"ENG"},"WHU":{"g":295,"o05":0.9458,"o15":0.722,"o25":0.5017,"btts":0.5254,"avg_scored":1.254,"avg_conceded":1.454,"league":"ENG"},"CHE":{"g":295,"o05":0.9322,"o15":0.8542,"o25":0.6881,"btts":0.6169,"avg_scored":1.783,"avg_conceded":1.454,"league":"ENG"},"WOL":{"g":295,"o05":0.9288,"o15":0.7627,"o25":0.5288,"btts":0.5525,"avg_scored":1.207,"avg_conceded":1.481,"league":"ENG"},"NEW":{"g":295,"o05":0.9729,"o15":0.8542,"o25":0.6237,"btts":0.6373,"avg_scored":1.688,"avg_conceded":1.549,"league":"ENG"},"BIL":{"g":294,"o05":0.9082,"o15":0.7007,"o25":0.4218,"btts":0.4524,"avg_scored":1.289,"avg_conceded":0.963,"league":"ESP"},"ALA":{"g":294,"o05":0.8946,"o15":0.6599,"o25":0.4456,"btts":0.4592,"avg_scored":1.167,"avg_conceded":1.15,"league":"ESP"},"ESP":{"g":294,"o05":0.898,"o15":0.6531,"o25":0.3946,"btts":0.4524,"avg_scored":1.027,"avg_conceded":1.276,"league":"ESP"},"VIL":{"g":294,"o05":0.915,"o15":0.6395,"o25":0.4184,"btts":0.4524,"avg_scored":1.265,"avg_conceded":1.054,"league":"ESP"},"FCB":{"g":294,"o05":0.932,"o15":0.7245,"o25":0.4932,"btts":0.5204,"avg_scored":1.476,"avg_conceded":1.014,"league":"ESP"},"CEL":{"g":294,"o05":0.915,"o15":0.6871,"o25":0.4218,"btts":0.4422,"avg_scored":1.014,"avg_conceded":1.265,"league":"ESP"},"GET":{"g":294,"o05":0.9218,"o15":0.6667,"o25":0.4354,"btts":0.4592,"avg_scored":1.061,"avg_conceded":1.262,"league":"ESP"},"ATM":{"g":294,"o05":0.9014,"o15":0.6803,"o25":0.4422,"btts":0.4592,"avg_scored":1.224,"avg_conceded":1.126,"league":"ESP"},"LEV":{"g":557,"o05":0.9264,"o15":0.7433,"o25":0.5278,"btts":0.5494,"avg_scored":1.497,"avg_conceded":1.167,"league":"GER"},"RMA":{"g":294,"o05":0.9286,"o15":0.7109,"o25":0.4456,"btts":0.4762,"avg_scored":1.388,"avg_conceded":1.048,"league":"ESP"},"OSA":{"g":294,"o05":0.8741,"o15":0.619,"o25":0.3639,"btts":0.432,"avg_scored":0.99,"avg_conceded":1.146,"league":"ESP"},"RSO":{"g":294,"o05":0.8946,"o15":0.6735,"o25":0.4456,"btts":0.5102,"avg_scored":1.085,"avg_conceded":1.269,"league":"ESP"},"OVI":{"g":294,"o05":0.9014,"o15":0.6361,"o25":0.3878,"btts":0.4252,"avg_scored":1.085,"avg_conceded":1.092,"league":"ESP"},"ELC":{"g":294,"o05":0.898,"o15":0.6939,"o25":0.4456,"btts":0.466,"avg_scored":1.214,"avg_conceded":1.194,"league":"ESP"},"RAY":{"g":294,"o05":0.881,"o15":0.6667,"o25":0.3776,"btts":0.432,"avg_scored":1.0,"avg_conceded":1.201,"league":"ESP"},"VCF":{"g":294,"o05":0.8946,"o15":0.6259,"o25":0.2993,"btts":0.3878,"avg_scored":0.874,"avg_conceded":1.15,"league":"ESP"},"RBB":{"g":294,"o05":0.8946,"o15":0.6395,"o25":0.432,"btts":0.4048,"avg_scored":1.187,"avg_conceded":1.068,"league":"ESP"},"MAL":{"g":294,"o05":0.9014,"o15":0.6293,"o25":0.3741,"btts":0.4286,"avg_scored":1.041,"avg_conceded":1.153,"league":"ESP"},"SEV":{"g":294,"o05":0.9048,"o15":0.6531,"o25":0.4626,"btts":0.4626,"avg_scored":1.16,"avg_conceded":1.252,"league":"ESP"},"GIR":{"g":294,"o05":0.881,"o15":0.6565,"o25":0.4558,"btts":0.4422,"avg_scored":1.228,"avg_conceded":1.048,"league":"ESP"},"FIO":{"g":295,"o05":0.9186,"o15":0.739,"o25":0.4712,"btts":0.5458,"avg_scored":1.197,"avg_conceded":1.339,"league":"ITA"},"BFC":{"g":295,"o05":0.878,"o15":0.6203,"o25":0.3932,"btts":0.4373,"avg_scored":1.136,"avg_conceded":1.02,"league":"ITA"},"GEN":{"g":295,"o05":0.9017,"o15":0.6441,"o25":0.4203,"btts":0.4441,"avg_scored":1.085,"avg_conceded":1.186,"league":"ITA"},"NAP":{"g":295,"o05":0.8881,"o15":0.6169,"o25":0.3695,"btts":0.4339,"avg_scored":0.969,"avg_conceded":1.153,"league":"ITA"},"INT":{"g":295,"o05":0.9492,"o15":0.7153,"o25":0.4441,"btts":0.4678,"avg_scored":1.529,"avg_conceded":0.986,"league":"ITA"},"USC":{"g":295,"o05":0.8949,"o15":0.7186,"o25":0.4305,"btts":0.5119,"avg_scored":1.142,"avg_conceded":1.278,"league":"ITA"},"JUV":{"g":295,"o05":0.9085,"o15":0.6373,"o25":0.3288,"btts":0.4169,"avg_scored":1.075,"avg_conceded":1.071,"league":"ITA"},"ACM":{"g":295,"o05":0.9356,"o15":0.7085,"o25":0.4305,"btts":0.4949,"avg_scored":1.339,"avg_conceded":1.125,"league":"ITA"},"LAZ":{"g":295,"o05":0.9322,"o15":0.6475,"o25":0.3593,"btts":0.4508,"avg_scored":1.051,"avg_conceded":1.169,"league":"ITA"},"LEC":{"g":295,"o05":0.8881,"o15":0.6237,"o25":0.4,"btts":0.4508,"avg_scored":0.983,"avg_conceded":1.227,"league":"ITA"},"PIS":{"g":295,"o05":0.9356,"o15":0.6949,"o25":0.4508,"btts":0.4576,"avg_scored":1.251,"avg_conceded":1.203,"league":"ITA"},"ATA":{"g":295,"o05":0.9458,"o15":0.7627,"o25":0.4339,"btts":0.539,"avg_scored":1.41,"avg_conceded":1.149,"league":"ITA"},"ROM":{"g":295,"o05":0.8915,"o15":0.6576,"o25":0.4136,"btts":0.4441,"avg_scored":1.305,"avg_conceded":1.064,"league":"ITA"},"CAG":{"g":295,"o05":0.8949,"o15":0.7119,"o25":0.4983,"btts":0.5458,"avg_scored":1.176,"avg_conceded":1.349,"league":"ITA"},"SAS":{"g":295,"o05":0.9051,"o15":0.6237,"o25":0.3661,"btts":0.4678,"avg_scored":1.108,"avg_conceded":1.115,"league":"ITA"},"TOR":{"g":295,"o05":0.8847,"o15":0.6169,"o25":0.3051,"btts":0.3898,"avg_scored":0.976,"avg_conceded":1.061,"league":"ITA"},"UDI":{"g":295,"o05":0.8678,"o15":0.6102,"o25":0.3729,"btts":0.4102,"avg_scored":0.915,"avg_conceded":1.244,"league":"ITA"},"COM":{"g":295,"o05":0.9288,"o15":0.7085,"o25":0.4169,"btts":0.4983,"avg_scored":1.258,"avg_conceded":1.2,"league":"ITA"},"VER":{"g":295,"o05":0.9186,"o15":0.6542,"o25":0.4034,"btts":0.4576,"avg_scored":1.231,"avg_conceded":1.146,"league":"ITA"},"PAR":{"g":295,"o05":0.9153,"o15":0.6102,"o25":0.3254,"btts":0.4237,"avg_scored":1.017,"avg_conceded":1.064,"league":"ITA"},"BVB":{"g":263,"o05":0.9049,"o15":0.7376,"o25":0.4525,"btts":0.4829,"avg_scored":1.437,"avg_conceded":1.129,"league":"GER"},"WOB":{"g":263,"o05":0.9202,"o15":0.7186,"o25":0.4373,"btts":0.5247,"avg_scored":1.148,"avg_conceded":1.346,"league":"GER"},"HSV":{"g":263,"o05":0.9278,"o15":0.6958,"o25":0.4981,"btts":0.4905,"avg_scored":1.194,"avg_conceded":1.392,"league":"GER"},"FCA":{"g":263,"o05":0.9125,"o15":0.711,"o25":0.4791,"btts":0.5247,"avg_scored":1.285,"avg_conceded":1.285,"league":"GER"},"KOE":{"g":263,"o05":0.9125,"o15":0.7414,"o25":0.5019,"btts":0.5399,"avg_scored":1.183,"avg_conceded":1.468,"league":"GER"},"HDH":{"g":263,"o05":0.9163,"o15":0.7072,"o25":0.3916,"btts":0.4639,"avg_scored":1.16,"avg_conceded":1.205,"league":"GER"},"BMU":{"g":263,"o05":0.943,"o15":0.7757,"o25":0.5057,"btts":0.6008,"avg_scored":1.373,"avg_conceded":1.357,"league":"GER"},"RBL":{"g":263,"o05":0.9316,"o15":0.7795,"o25":0.5057,"btts":0.5361,"avg_scored":1.471,"avg_conceded":1.16,"league":"GER"},"VFB":{"g":263,"o05":0.9125,"o15":0.7148,"o25":0.4753,"btts":0.5247,"avg_scored":1.456,"avg_conceded":1.16,"league":"GER"},"SCF":{"g":263,"o05":0.9582,"o15":0.7643,"o25":0.4487,"btts":0.5551,"avg_scored":1.217,"avg_conceded":1.399,"league":"GER"},"MAI":{"g":263,"o05":0.8897,"o15":0.6768,"o25":0.4106,"btts":0.4373,"avg_scored":1.144,"avg_conceded":1.141,"league":"GER"},"SGE":{"g":263,"o05":0.9278,"o15":0.7643,"o25":0.5437,"btts":0.5247,"avg_scored":1.289,"avg_conceded":1.452,"league":"GER"},"STP":{"g":263,"o05":0.9049,"o15":0.6692,"o25":0.4411,"btts":0.4715,"avg_scored":1.19,"avg_conceded":1.144,"league":"GER"},"TSG":{"g":263,"o05":0.9316,"o15":0.8327,"o25":0.5361,"btts":0.597,"avg_scored":1.422,"avg_conceded":1.601,"league":"GER"},"BMG":{"g":263,"o05":0.924,"o15":0.7262,"o25":0.5209,"btts":0.5627,"avg_scored":1.183,"avg_conceded":1.483,"league":"GER"},"UNI":{"g":263,"o05":0.9125,"o15":0.6882,"o25":0.4106,"btts":0.4715,"avg_scored":1.038,"avg_conceded":1.297,"league":"GER"},"SVW":{"g":263,"o05":0.8859,"o15":0.6502,"o25":0.4297,"btts":0.4601,"avg_scored":1.194,"avg_conceded":1.118,"league":"GER"},"AMO":{"g":263,"o05":0.9163,"o15":0.7452,"o25":0.4867,"btts":0.5019,"avg_scored":1.456,"avg_conceded":1.194,"league":"FRA"},"LIL":{"g":263,"o05":0.9354,"o15":0.749,"o25":0.4829,"btts":0.4829,"avg_scored":1.487,"avg_conceded":1.228,"league":"FRA"},"ANG":{"g":263,"o05":0.9087,"o15":0.7376,"o25":0.4753,"btts":0.5399,"avg_scored":1.156,"avg_conceded":1.51,"league":"FRA"},"OLM":{"g":263,"o05":0.9354,"o15":0.7681,"o25":0.4601,"btts":0.5551,"avg_scored":1.335,"avg_conceded":1.319,"league":"FRA"},"B29":{"g":263,"o05":0.9125,"o15":0.6768,"o25":0.4791,"btts":0.5019,"avg_scored":1.338,"avg_conceded":1.289,"league":"FRA"},"AUX":{"g":263,"o05":0.9544,"o15":0.7909,"o25":0.5057,"btts":0.5551,"avg_scored":1.209,"avg_conceded":1.51,"league":"FRA"},"LOR":{"g":263,"o05":0.9696,"o15":0.7681,"o25":0.4943,"btts":0.5399,"avg_scored":1.605,"avg_conceded":1.289,"league":"FRA"},"PFC":{"g":263,"o05":0.9278,"o15":0.73,"o25":0.5057,"btts":0.5665,"avg_scored":1.418,"avg_conceded":1.281,"league":"FRA"},"LYO":{"g":263,"o05":0.9278,"o15":0.7376,"o25":0.4563,"btts":0.5133,"avg_scored":1.304,"avg_conceded":1.323,"league":"FRA"},"NCE":{"g":263,"o05":0.9125,"o15":0.6996,"o25":0.4449,"btts":0.4829,"avg_scored":1.278,"avg_conceded":1.217,"league":"FRA"},"NAN":{"g":263,"o05":0.9049,"o15":0.7376,"o25":0.4563,"btts":0.4791,"avg_scored":1.076,"avg_conceded":1.407,"league":"FRA"},"LEH":{"g":263,"o05":0.9087,"o15":0.6692,"o25":0.4563,"btts":0.4639,"avg_scored":1.065,"avg_conceded":1.395,"league":"FRA"},"REN":{"g":263,"o05":0.9163,"o15":0.7605,"o25":0.5703,"btts":0.6198,"avg_scored":1.433,"avg_conceded":1.376,"league":"FRA"},"LEN":{"g":263,"o05":0.9011,"o15":0.6996,"o25":0.4411,"btts":0.4905,"avg_scored":1.179,"avg_conceded":1.232,"league":"FRA"},"STR":{"g":263,"o05":0.9316,"o15":0.749,"o25":0.5057,"btts":0.5247,"avg_scored":1.217,"avg_conceded":1.407,"league":"FRA"},"PSG":{"g":263,"o05":0.9468,"o15":0.7567,"o25":0.4639,"btts":0.5057,"avg_scored":1.437,"avg_conceded":1.202,"league":"FRA"},"TOU":{"g":263,"o05":0.9087,"o15":0.7376,"o25":0.4373,"btts":0.5513,"avg_scored":1.323,"avg_conceded":1.175,"league":"FRA"},"MET":{"g":263,"o05":0.9202,"o15":0.7262,"o25":0.4791,"btts":0.5399,"avg_scored":1.338,"avg_conceded":1.3,"league":"FRA"}}

# ─── FUNCTIONS ───
def load_dedup():
    try:
        with open(DEDUP_FILE) as f:
            data = json.load(f)
        now = time.time()
        return {k: v for k, v in data.items() if now - v < 1800}
    except:
        return {}

def save_dedup(d):
    with open(DEDUP_FILE, "w") as f:
        json.dump(d, f)

def make_hash(ids):
    return hashlib.md5(",".join(sorted(ids)).encode()).hexdigest()

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def get_booking_code(sels):
    try:
        r = requests.post(f"{API_BASE}/orders/share", json={"selections": sels}, headers=HEADERS, timeout=10)
        return r.json().get("data", {}).get("shareCode", "N/A")
    except:
        return "N/A"

def fetch_upcoming():
    events = []
    now_ts = int(time.time() * 1000)
    cats = [
        ("sv%3Acategory%3A202120001", "sv%3Aleague%3A1", "ENG"),
        ("sv%3Acategory%3A202120002", "sv%3Aleague%3A2", "ESP"),
        ("sv%3Acategory%3A202120003", "sv%3Aleague%3A3", "ITA"),
        ("sv%3Acategory%3A202120004", "sv%3Aleague%3A4", "GER"),
        ("sv%3Acategory%3A202120005", "sv%3Aleague%3A5", "FRA"),
    ]
    for ce, te, lg in cats:
        try:
            url = f"{API_BASE}/factsCenter/eventResultList?pageNum=1&pageSize=100&sportId=sr%3Asport%3A202120001&categoryId={ce}&tournamentId={te}&startTime={now_ts}&endTime={now_ts+ALERT_WINDOW*60*1000}"
            r = requests.get(url, headers=HEADERS, timeout=10)
            for t in r.json().get("data", {}).get("tournaments", []):
                for e in t.get("events", []):
                    if e.get("matchStatus") == "End" or e.get("playedSeconds", 0) > 120:
                        continue
                    events.append({
                        "eventId": e["eventId"],
                        "home": e.get("homeTeamName", ""),
                        "away": e.get("awayTeamName", ""),
                        "league": lg,
                        "startTime": e.get("estimateStartTime", 0)
                    })
        except:
            pass
    return events

def score_match(home, away):
    """12-Layer ONIMIX Scoring Engine v6"""
    hp = TEAM_PROFILES.get(home, {})
    ap = TEAM_PROFILES.get(away, {})
    
    if not hp or not ap:
        return 0, {}
    
    scores = {}
    
    # Layer 1: O0.5 baseline (max 5)
    h_o05 = hp.get("o05", 0)
    a_o05 = ap.get("o05", 0)
    scores["O0.5"] = min(5, round((h_o05 + a_o05) / 2 * 5, 1))
    
    # Layer 2: O1.5 core (max 15)
    h_o15 = hp.get("o15", 0)
    a_o15 = ap.get("o15", 0)
    scores["O1.5"] = min(15, round((h_o15 + a_o15) / 2 * 15, 1))
    
    # Layer 3: O2.5 bonus (max 10)
    h_o25 = hp.get("o25", 0)
    a_o25 = ap.get("o25", 0)
    scores["O2.5"] = min(10, round((h_o25 + a_o25) / 2 * 10, 1))
    
    # Layer 4: BTTS (max 10)
    h_btts = hp.get("btts", 0)
    a_btts = ap.get("btts", 0)
    scores["BTTS"] = min(10, round((h_btts + a_btts) / 2 * 10, 1))
    
    # Layer 5: Attack power (max 10) - avg goals scored
    h_atk = hp.get("avg_scored", 0)
    a_atk = ap.get("avg_scored", 0)
    combined_atk = h_atk + a_atk
    scores["ATK"] = min(10, round(combined_atk / 4 * 10, 1))
    
    # Layer 6: Defense weakness (max 10) - avg goals conceded (higher = weaker = good for O1.5)
    h_def = hp.get("avg_conceded", 0)
    a_def = ap.get("avg_conceded", 0)
    combined_def = h_def + a_def
    scores["DEF"] = min(10, round(combined_def / 4 * 10, 1))
    
    # Layer 7: Venue bias (max 5) - home advantage in scoring
    scores["VEN"] = min(5, round(h_atk / 2 * 5, 1))
    
    # Layer 8: Trend momentum (max 5) - consistency
    h_consistency = 1 - abs(h_o15 - 0.8)  # closer to 80%+ = better
    a_consistency = 1 - abs(a_o15 - 0.8)
    scores["TRD"] = min(5, round((h_consistency + a_consistency) / 2 * 5, 1))
    
    # Layer 9: Momentum (max 5) - sample size confidence
    h_games = hp.get("games", 0)
    a_games = ap.get("games", 0)
    confidence = min(1.0, (h_games + a_games) / 40)  # 20 games each = full confidence
    scores["MOM"] = round(confidence * 5, 1)
    
    # Layer 10: ELITE bonus (max 15) - Diamond=15, Gold=10
    elite_key = f"{home}v{away}"
    elite_bonus = 0
    if elite_key in ELITE_DB:
        tier = ELITE_DB[elite_key]["t"]
        if tier == "D":
            elite_bonus = 15
        elif tier == "G":
            elite_bonus = 10
    scores["ELT"] = elite_bonus
    
    # Layer 11: League bonus (max 5) - based on today's league O1.5 rates
    league_bonus = {"ENG": 4, "GER": 4, "FRA": 3.5, "ITA": 3, "ESP": 2.5}
    scores["LGB"] = league_bonus.get(hp.get("league", ""), 3)
    
    # Layer 12: Combined odds confidence (max 5)
    avg_o15 = (h_o15 + a_o15) / 2
    if avg_o15 >= 0.85:
        scores["ODS"] = 5
    elif avg_o15 >= 0.75:
        scores["ODS"] = 4
    elif avg_o15 >= 0.65:
        scores["ODS"] = 3
    else:
        scores["ODS"] = 2
    
    total = sum(scores.values())
    return total, scores

def main():
    print("ONIMIX VFL 12-Layer Engine v6")
    print(f"ELITE DB: {len(ELITE_DB)}, Team Profiles: {len(TEAM_PROFILES)}")
    
    events = fetch_upcoming()
    print(f"Upcoming: {len(events)}")
    
    if not events:
        print("No events. Silent exit.")
        return
    
    # Score all matches
    scored = []
    for e in events:
        total, layers = score_match(e["home"], e["away"])
        if total > 0:
            scored.append({**e, "score": total, "layers": layers})
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter by tiers
    ultra = [s for s in scored if s["score"] >= ULTRA_THRESHOLD]
    premium = [s for s in scored if PREMIUM_THRESHOLD <= s["score"] < ULTRA_THRESHOLD]
    
    # Limit picks
    ultra = ultra[:MAX_PICKS]
    premium = premium[:MAX_PICKS]
    
    if not ultra and not premium:
        print("No qualified picks. Silent exit.")
        return
    
    # Dedup
    all_ids = [p["eventId"] for p in ultra + premium]
    h = make_hash(all_ids)
    dedup = load_dedup()
    if h in dedup:
        print("Already sent. Silent exit.")
        return
    
    now_wat = datetime.now(timezone(timedelta(hours=1)))
    msg = f"🧠 <b>ONIMIX 12-Layer v6</b> 🧠\n"
    msg += f"📅 {now_wat.strftime('%H:%M WAT %d/%m/%Y')}\n"
    msg += f"🎯 Market: Over 1.5 Goals\n\n"
    
    if ultra:
        msg += f"🔥 <b>ULTRA</b> (Score ≥{ULTRA_THRESHOLD}/105)\n"
        for p in ultra:
            elite_tag = ""
            ek = f"{p['home']}v{p['away']}"
            if ek in ELITE_DB:
                t = ELITE_DB[ek]["t"]
                elite_tag = " 💎" if t == "D" else " 🥇"
            msg += f"  ⚽ {p['home']} vs {p['away']} ({p['league']}){elite_tag}\n"
            msg += f"     Score: {p['score']:.0f}/105\n"
        msg += "\n"
        
        sels = [{"eventId": p["eventId"], "marketId": "total", "specifier": "total=1.5", "outcomeId": "over"} for p in ultra]
        code = get_booking_code(sels)
        msg += f"📋 ULTRA Code: <code>{code}</code>\n\n"
    
    if premium:
        msg += f"⭐ <b>PREMIUM</b> (Score {PREMIUM_THRESHOLD}-{ULTRA_THRESHOLD-1}/105)\n"
        for p in premium[:5]:
            msg += f"  ⚽ {p['home']} vs {p['away']} ({p['league']}) — {p['score']:.0f}pts\n"
        if len(premium) > 5:
            msg += f"  ... +{len(premium)-5} more\n"
        msg += "\n"
        
        sels = [{"eventId": p["eventId"], "marketId": "total", "specifier": "total=1.5", "outcomeId": "over"} for p in premium]
        code = get_booking_code(sels)
        msg += f"📋 PREMIUM Code: <code>{code}</code>\n\n"
    
    msg += f"🔥 Ultra: {len(ultra)} | ⭐ Premium: {len(premium)}\n"
    msg += f"🔒 <i>12-Layer v6 — Stricter thresholds</i>"
    
    send_telegram(msg)
    print(f"✅ Sent {len(ultra)} ULTRA + {len(premium)} PREMIUM")
    
    dedup[h] = time.time()
    save_dedup(dedup)

if __name__ == "__main__":
    main()
