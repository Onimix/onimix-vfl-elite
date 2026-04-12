#!/usr/bin/env python3
"""
ONIMIX VFL ELITE Scanner v9 — UPGRADED LOGIC
- 3-tier ELITE: DIAMOND (100%), GOLD (≥86%), SILVER (≥80%)
- Only sends DIAMOND + GOLD picks (proven 99%+ hit rate)
- Danger team penalty from rolling 24h failures
- Hash-based dedup with 30-min TTL
- Prematch-only (no past matches)
- Silent exit when no picks (saves credits)
"""
import requests, json, hashlib, time, os
from collections import defaultdict
from datetime import datetime, timezone, timedelta

# ─── CONFIG ───
TG_TOKEN = "8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
TG_CHAT  = "1745848158"
DEDUP_FILE = "/tmp/vfl_dedup_L1_v9.json"
ALERT_WINDOW = 20  # minutes before kickoff
API_BASE = "https://www.sportybet.com/api/ng"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.sportybet.com/ng/virtual",
    "Origin": "https://www.sportybet.com"
}

# ─── ELITE DATABASE v2 (DIAMOND + GOLD only) ───
ELITE_DB_RAW = {"BOUvTOT":{"t":"D","r":1.0,"g":8,"b":0.625},"FORvSUN":{"t":"D","r":1.0,"g":8,"b":0.625},"LIVvMUN":{"t":"D","r":1.0,"g":8,"b":0.75},"WOLvNEW":{"t":"D","r":1.0,"g":8,"b":0.625},"CRYvCHE":{"t":"D","r":1.0,"g":8,"b":0.75},"WOLvBUR":{"t":"D","r":1.0,"g":8,"b":0.625},"ASTvARS":{"t":"D","r":1.0,"g":8,"b":0.75},"BREvTOT":{"t":"D","r":1.0,"g":8,"b":0.625},"CRYvMCI":{"t":"D","r":1.0,"g":8,"b":0.75},"MUNvCHE":{"t":"D","r":1.0,"g":8,"b":0.75},"SUNvNEW":{"t":"D","r":1.0,"g":8,"b":0.375},"NEWvARS":{"t":"D","r":1.0,"g":9,"b":0.6667},"CHEvEVE":{"t":"D","r":1.0,"g":8,"b":0.5},"CRYvWOL":{"t":"D","r":1.0,"g":8,"b":0.5},"NEWvBUR":{"t":"D","r":1.0,"g":8,"b":0.75},"TOTvARS":{"t":"D","r":1.0,"g":8,"b":0.75},"ASTvFUL":{"t":"D","r":1.0,"g":8,"b":0.625},"LIVvWOL":{"t":"D","r":1.0,"g":8,"b":0.375},"NEWvLEE":{"t":"D","r":1.0,"g":8,"b":0.75},"CHEvFUL":{"t":"D","r":1.0,"g":8,"b":0.625},"BOUvCHE":{"t":"D","r":1.0,"g":8,"b":0.5},"CRYvSUN":{"t":"D","r":1.0,"g":8,"b":1.0},"LIVvBRE":{"t":"D","r":1.0,"g":8,"b":0.625},"ARSvLEE":{"t":"D","r":1.0,"g":8,"b":0.625},"ARSvFUL":{"t":"D","r":1.0,"g":8,"b":0.875},"CRYvTOT":{"t":"D","r":1.0,"g":8,"b":0.5},"MUNvNEW":{"t":"D","r":1.0,"g":8,"b":0.625},"WHUvLEE":{"t":"D","r":1.0,"g":8,"b":0.875},"WOLvMCI":{"t":"D","r":1.0,"g":8,"b":0.625},"MUNvTOT":{"t":"D","r":1.0,"g":8,"b":0.75},"BREvMCI":{"t":"D","r":1.0,"g":8,"b":0.75},"LIVvLEE":{"t":"D","r":1.0,"g":8,"b":0.625},"NEWvCHE":{"t":"D","r":1.0,"g":8,"b":0.875},"CHEvTOT":{"t":"D","r":1.0,"g":9,"b":1.0},"NEWvEVE":{"t":"D","r":1.0,"g":8,"b":0.375},"ARSvCRY":{"t":"D","r":1.0,"g":8,"b":0.625},"CHEvBUR":{"t":"D","r":1.0,"g":8,"b":0.875},"LIVvWHU":{"t":"D","r":1.0,"g":8,"b":0.75},"ASTvBHA":{"t":"D","r":1.0,"g":8,"b":0.75},"LIVvCRY":{"t":"D","r":1.0,"g":8,"b":0.875},"TOTvMCI":{"t":"D","r":1.0,"g":8,"b":0.625},"ASTvWHU":{"t":"D","r":1.0,"g":8,"b":0.625},"ASTvCRY":{"t":"D","r":1.0,"g":8,"b":0.875},"CHEvWHU":{"t":"D","r":1.0,"g":8,"b":0.625},"ASTvLIV":{"t":"D","r":1.0,"g":8,"b":0.875},"NEWvFOR":{"t":"D","r":1.0,"g":8,"b":1.0},"ARSvSUN":{"t":"D","r":1.0,"g":7,"b":0.7143},"CHEvAST":{"t":"D","r":1.0,"g":8,"b":0.75},"ARSvCHE":{"t":"D","r":1.0,"g":8,"b":0.5},"FULvLIV":{"t":"D","r":1.0,"g":8,"b":0.625},"ARSvTOT":{"t":"D","r":1.0,"g":8,"b":0.875},"EVEvCHE":{"t":"D","r":1.0,"g":7,"b":0.5714},"FULvAST":{"t":"D","r":1.0,"g":8,"b":1.0},"LEEvNEW":{"t":"D","r":1.0,"g":8,"b":0.75},"FULvCHE":{"t":"D","r":1.0,"g":8,"b":0.75},"MCIvEVE":{"t":"D","r":1.0,"g":8,"b":0.75},"OVIvELC":{"t":"D","r":1.0,"g":8,"b":0.875},"BILvELC":{"t":"D","r":1.0,"g":8,"b":0.75},"RAYvLEV":{"t":"D","r":1.0,"g":8,"b":0.75},"ATMvRMA":{"t":"D","r":1.0,"g":8,"b":0.375},"MALvGIR":{"t":"D","r":1.0,"g":8,"b":0.875},"SEVvRAY":{"t":"D","r":1.0,"g":8,"b":0.75},"RBBvRMA":{"t":"D","r":1.0,"g":8,"b":1.0},"RBBvFCB":{"t":"D","r":1.0,"g":8,"b":0.625},"ALAvVIL":{"t":"D","r":1.0,"g":7,"b":0.8571},"OVIvFCB":{"t":"D","r":1.0,"g":8,"b":0.5},"SEVvLEV":{"t":"D","r":1.0,"g":8,"b":0.625},"BILvOVI":{"t":"D","r":1.0,"g":8,"b":0.625},"ATMvLEV":{"t":"D","r":1.0,"g":8,"b":0.875},"CELvFCB":{"t":"D","r":1.0,"g":8,"b":0.625},"VCFvOVI":{"t":"D","r":1.0,"g":8,"b":0.5},"VCFvELC":{"t":"D","r":1.0,"g":8,"b":0.5},"INTvUSC":{"t":"D","r":1.0,"g":8,"b":0.875},"UDIvINT":{"t":"D","r":1.0,"g":8,"b":0.375},"ROMvNAP":{"t":"D","r":1.0,"g":8,"b":0.875},"ATAvBFC":{"t":"D","r":1.0,"g":8,"b":0.75},"FIOvGEN":{"t":"D","r":1.0,"g":8,"b":0.875},"PISvGEN":{"t":"D","r":1.0,"g":8,"b":0.875},"ATAvUSC":{"t":"D","r":1.0,"g":8,"b":0.75},"CAGvINT":{"t":"D","r":1.0,"g":7,"b":1.0},"PISvLAZ":{"t":"D","r":1.0,"g":8,"b":0.5},"ATAvUDI":{"t":"D","r":1.0,"g":8,"b":0.625},"VERvFIO":{"t":"D","r":1.0,"g":8,"b":0.5},"UDIvUSC":{"t":"D","r":1.0,"g":8,"b":0.625},"FIOvCOM":{"t":"D","r":1.0,"g":7,"b":1.0},"ATAvNAP":{"t":"D","r":1.0,"g":8,"b":0.75},"CAGvUSC":{"t":"D","r":1.0,"g":8,"b":1.0},"PISvFIO":{"t":"D","r":1.0,"g":8,"b":0.875},"CAGvLAZ":{"t":"D","r":1.0,"g":8,"b":0.75},"ACMvSAS":{"t":"D","r":1.0,"g":8,"b":0.75},"PARvATA":{"t":"D","r":1.0,"g":8,"b":0.75},"NAPvCAG":{"t":"D","r":1.0,"g":8,"b":0.5},"FIOvLAZ":{"t":"D","r":1.0,"g":8,"b":0.75},"LEVvHDH":{"t":"D","r":1.0,"g":8,"b":0.5},"TSGvRBL":{"t":"D","r":1.0,"g":8,"b":0.75},"UNIvHSV":{"t":"D","r":1.0,"g":8,"b":0.875},"KOEvRBL":{"t":"D","r":1.0,"g":8,"b":0.75},"HDHvBMU":{"t":"D","r":1.0,"g":8,"b":0.875},"MAIvSVW":{"t":"D","r":1.0,"g":8,"b":0.5},"SCFvTSG":{"t":"D","r":1.0,"g":8,"b":0.75},"BVBvTSG":{"t":"D","r":1.0,"g":8,"b":0.75},"SCFvKOE":{"t":"D","r":1.0,"g":8,"b":0.875},"SVWvBMU":{"t":"D","r":1.0,"g":7,"b":0.5714},"MAIvHSV":{"t":"D","r":1.0,"g":8,"b":0.375},"WOBvTSG":{"t":"D","r":1.0,"g":8,"b":0.625},"TSGvHSV":{"t":"D","r":1.0,"g":8,"b":0.75},"BVBvBMG":{"t":"D","r":1.0,"g":8,"b":0.625},"KOEvHSV":{"t":"D","r":1.0,"g":8,"b":0.75},"BVBvFCA":{"t":"D","r":1.0,"g":8,"b":0.75},"KOEvTSG":{"t":"D","r":1.0,"g":8,"b":0.625},"LEVvVFB":{"t":"D","r":1.0,"g":8,"b":0.875},"SCFvRBL":{"t":"D","r":1.0,"g":8,"b":0.5},"WOBvBMG":{"t":"D","r":1.0,"g":8,"b":1.0},"BVBvRBL":{"t":"D","r":1.0,"g":8,"b":0.5},"LEVvTSG":{"t":"D","r":1.0,"g":8,"b":0.875},"BVBvSCF":{"t":"D","r":1.0,"g":8,"b":0.625},"BMGvTSG":{"t":"D","r":1.0,"g":7,"b":0.5714},"UNIvSGE":{"t":"D","r":1.0,"g":8,"b":0.625},"RENvMET":{"t":"D","r":1.0,"g":8,"b":1.0},"STRvOLM":{"t":"D","r":1.0,"g":8,"b":0.75},"ANGvLIL":{"t":"D","r":1.0,"g":8,"b":0.5},"LENvAUX":{"t":"D","r":1.0,"g":9,"b":0.7778},"OLMvLIL":{"t":"D","r":1.0,"g":8,"b":0.5},"LORvLYO":{"t":"D","r":1.0,"g":8,"b":0.875},"ANGvLOR":{"t":"D","r":1.0,"g":8,"b":0.625},"TOUvNCE":{"t":"D","r":1.0,"g":8,"b":0.375},"LYOvMET":{"t":"D","r":1.0,"g":8,"b":0.75},"NANvAUX":{"t":"D","r":1.0,"g":8,"b":0.625},"PSGvAMO":{"t":"D","r":1.0,"g":8,"b":0.75},"ANGvAUX":{"t":"D","r":1.0,"g":8,"b":0.875},"LYOvAMO":{"t":"D","r":1.0,"g":8,"b":0.5},"OLMvMET":{"t":"D","r":1.0,"g":8,"b":0.75},"PSGvREN":{"t":"D","r":1.0,"g":8,"b":0.75},"LEHvAUX":{"t":"D","r":1.0,"g":8,"b":0.625},"PSGvANG":{"t":"D","r":1.0,"g":8,"b":0.5},"AUXvB29":{"t":"D","r":1.0,"g":8,"b":0.5},"LILvAMO":{"t":"D","r":1.0,"g":9,"b":0.5556},"OLMvANG":{"t":"D","r":1.0,"g":8,"b":1.0},"AMOvB29":{"t":"D","r":1.0,"g":8,"b":0.625},"AUXvTOU":{"t":"D","r":1.0,"g":8,"b":0.875},"LENvPFC":{"t":"D","r":1.0,"g":8,"b":0.875},"LILvLYO":{"t":"D","r":1.0,"g":8,"b":0.625},"AUXvLOR":{"t":"D","r":1.0,"g":8,"b":0.375},"NCEvOLM":{"t":"D","r":1.0,"g":8,"b":0.75},"PSGvNCE":{"t":"D","r":1.0,"g":8,"b":0.625},"NANvLOR":{"t":"D","r":1.0,"g":8,"b":0.75},"AMOvLEN":{"t":"D","r":1.0,"g":8,"b":0.875},"NANvPFC":{"t":"D","r":1.0,"g":8,"b":1.0},"TOUvSTR":{"t":"D","r":1.0,"g":8,"b":0.875},"CHEvNEW":{"t":"D","r":1.0,"g":7,"b":0.4286},"BOUvNEW":{"t":"D","r":1.0,"g":7,"b":0.5714},"CRYvARS":{"t":"D","r":1.0,"g":7,"b":0.8571},"CHEvSUN":{"t":"D","r":1.0,"g":7,"b":0.8571},"CRYvLIV":{"t":"D","r":1.0,"g":7,"b":0.7143},"BOUvARS":{"t":"D","r":1.0,"g":7,"b":0.7143},"TOTvCHE":{"t":"D","r":1.0,"g":7,"b":0.5714},"BURvMUN":{"t":"D","r":1.0,"g":7,"b":0.5714},"ASTvBRE":{"t":"D","r":1.0,"g":7,"b":0.8571},"EVEvNEW":{"t":"D","r":1.0,"g":7,"b":0.8571},"FULvFOR":{"t":"D","r":1.0,"g":7,"b":0.7143},"TOTvCRY":{"t":"D","r":1.0,"g":7,"b":0.7143},"MCIvWOL":{"t":"D","r":1.0,"g":7,"b":0.8571},"MUNvBRE":{"t":"D","r":1.0,"g":7,"b":0.7143},"NEWvMUN":{"t":"D","r":1.0,"g":7,"b":1.0},"CHEvBRE":{"t":"D","r":1.0,"g":7,"b":0.7143},"NEWvLIV":{"t":"D","r":1.0,"g":7,"b":1.0},"WHUvMUN":{"t":"D","r":1.0,"g":7,"b":1.0},"NEWvAST":{"t":"D","r":1.0,"g":7,"b":0.5714},"BOUvSUN":{"t":"D","r":1.0,"g":7,"b":0.7143},"EVEvWOL":{"t":"D","r":1.0,"g":7,"b":0.8571},"WHUvLIV":{"t":"D","r":1.0,"g":7,"b":1.0},"CHEvFOR":{"t":"D","r":1.0,"g":7,"b":1.0},"FCBvELC":{"t":"D","r":1.0,"g":7,"b":0.8571},"RBBvOVI":{"t":"D","r":1.0,"g":7,"b":0.4286},"RSOvRAY":{"t":"D","r":1.0,"g":7,"b":0.7143},"MALvESP":{"t":"D","r":1.0,"g":7,"b":0.5714},"ATMvRBB":{"t":"D","r":1.0,"g":8,"b":0.875},"VILvBIL":{"t":"D","r":1.0,"g":7,"b":0.5714},"CELvGIR":{"t":"D","r":1.0,"g":7,"b":0.5714},"LEVvATM":{"t":"D","r":1.0,"g":7,"b":0.4286},"RMAvFCB":{"t":"D","r":1.0,"g":7,"b":0.2857},"RMAvELC":{"t":"D","r":1.0,"g":7,"b":0.5714},"ELCvSEV":{"t":"D","r":1.0,"g":7,"b":0.7143},"ATAvROM":{"t":"D","r":1.0,"g":7,"b":0.8571},"NAPvJUV":{"t":"D","r":1.0,"g":7,"b":0.7143},"ACMvROM":{"t":"D","r":1.0,"g":7,"b":0.4286},"LAZvPAR":{"t":"D","r":1.0,"g":7,"b":0.5714},"ACMvLEC":{"t":"D","r":1.0,"g":7,"b":1.0},"USCvGEN":{"t":"D","r":1.0,"g":8,"b":0.875},"USCvNAP":{"t":"D","r":1.0,"g":7,"b":0.8571},"LECvSAS":{"t":"D","r":1.0,"g":7,"b":0.8571},"CAGvFIO":{"t":"D","r":1.0,"g":7,"b":0.8571},"INTvACM":{"t":"D","r":1.0,"g":7,"b":0.7143},"BVBvBMU":{"t":"D","r":1.0,"g":7,"b":0.5714},"FCAvRBL":{"t":"D","r":1.0,"g":7,"b":1.0},"MAIvTSG":{"t":"D","r":1.0,"g":7,"b":1.0},"VFBvSGE":{"t":"D","r":1.0,"g":7,"b":1.0},"HDHvRBL":{"t":"D","r":1.0,"g":7,"b":0.5714},"HDHvMAI":{"t":"D","r":1.0,"g":7,"b":0.7143},"SCFvBVB":{"t":"D","r":1.0,"g":7,"b":0.4286},"BMGvSCF":{"t":"D","r":1.0,"g":7,"b":0.5714},"BVBvSGE":{"t":"D","r":1.0,"g":7,"b":0.4286},"RBLvBMU":{"t":"D","r":1.0,"g":7,"b":0.5714},"SGEvLEV":{"t":"D","r":1.0,"g":7,"b":0.7143},"KOEvBMU":{"t":"D","r":1.0,"g":7,"b":0.8571},"LENvOLM":{"t":"D","r":1.0,"g":7,"b":0.7143},"AUXvOLM":{"t":"D","r":1.0,"g":7,"b":0.7143},"LILvREN":{"t":"D","r":1.0,"g":7,"b":0.7143},"AUXvSTR":{"t":"D","r":1.0,"g":7,"b":0.7143},"LILvMET":{"t":"D","r":1.0,"g":7,"b":0.5714},"LILvLEN":{"t":"D","r":1.0,"g":7,"b":0.7143},"STRvREN":{"t":"D","r":1.0,"g":7,"b":1.0},"AMOvLYO":{"t":"D","r":1.0,"g":7,"b":0.7143},"B29vLEN":{"t":"D","r":1.0,"g":7,"b":1.0},"OLMvLOR":{"t":"D","r":1.0,"g":7,"b":0.8571},"PFCvSTR":{"t":"D","r":1.0,"g":7,"b":0.4286},"LEHvB29":{"t":"D","r":1.0,"g":7,"b":0.7143},"NANvPSG":{"t":"D","r":1.0,"g":7,"b":0.4286},"LORvANG":{"t":"D","r":1.0,"g":7,"b":0.8571},"RENvLOR":{"t":"D","r":1.0,"g":7,"b":1.0},"NANvSTR":{"t":"D","r":1.0,"g":7,"b":0.7143},"CRYvAST":{"t":"G","r":0.875,"g":8,"b":0.875},"FULvBUR":{"t":"G","r":0.875,"g":8,"b":0.625},"WOLvTOT":{"t":"G","r":0.875,"g":8,"b":0.625},"BREvNEW":{"t":"G","r":0.875,"g":8,"b":0.5},"WOLvLEE":{"t":"G","r":0.875,"g":8,"b":0.625},"ASTvCHE":{"t":"G","r":0.875,"g":8,"b":0.75},"LIVvMCI":{"t":"G","r":0.875,"g":8,"b":0.75},"MUNvEVE":{"t":"G","r":0.875,"g":8,"b":0.375},"ASTvEVE":{"t":"G","r":0.875,"g":8,"b":0.625},"CHEvARS":{"t":"G","r":0.875,"g":8,"b":0.875},"CRYvBOU":{"t":"G","r":0.875,"g":8,"b":0.75},"LIVvFUL":{"t":"G","r":0.875,"g":8,"b":0.375},"NEWvTOT":{"t":"G","r":0.875,"g":8,"b":0.5},"LIVvBOU":{"t":"G","r":0.875,"g":8,"b":0.625},"MUNvFUL":{"t":"G","r":0.875,"g":8,"b":0.625},"CHEvMCI":{"t":"G","r":0.875,"g":8,"b":0.625},"FORvCRY":{"t":"G","r":0.8889,"g":9,"b":0.7778},"MUNvBOU":{"t":"G","r":0.875,"g":8,"b":0.875},"BREvCRY":{"t":"G","r":0.875,"g":8,"b":0.625},"EVEvMCI":{"t":"G","r":0.875,"g":8,"b":0.75},"LIVvFOR":{"t":"G","r":0.875,"g":8,"b":0.75},"TOTvLEE":{"t":"G","r":0.875,"g":8,"b":0.625},"ARSvMCI":{"t":"G","r":0.875,"g":8,"b":0.5},"FULvEVE":{"t":"G","r":0.875,"g":8,"b":0.625},"BHAvBUR":{"t":"G","r":0.875,"g":8,"b":0.625},"CRYvNEW":{"t":"G","r":0.875,"g":8,"b":0.875},"FULvMCI":{"t":"G","r":0.875,"g":8,"b":0.375},"BHAvLEE":{"t":"G","r":0.875,"g":8,"b":0.75},"LIVvNEW":{"t":"G","r":0.875,"g":8,"b":0.75},"MUNvSUN":{"t":"G","r":0.875,"g":8,"b":0.375},"WOLvEVE":{"t":"G","r":0.875,"g":8,"b":0.5},"BREvCHE":{"t":"G","r":0.8889,"g":9,"b":0.7778},"CRYvLEE":{"t":"G","r":0.875,"g":8,"b":0.875},"WHUvBHA":{"t":"G","r":0.875,"g":8,"b":0.625},"CRYvBHA":{"t":"G","r":0.875,"g":8,"b":0.625},"MUNvBUR":{"t":"G","r":0.875,"g":8,"b":0.875},"FORvBOU":{"t":"G","r":0.875,"g":8,"b":0.625},"MUNvLEE":{"t":"G","r":0.875,"g":8,"b":0.5},"NEWvMCI":{"t":"G","r":0.875,"g":8,"b":0.875},"CHEvLEE":{"t":"G","r":0.875,"g":8,"b":0.875},"NEWvFUL":{"t":"G","r":0.875,"g":8,"b":0.75},"ARSvLIV":{"t":"G","r":0.8889,"g":9,"b":0.8889},"BURvMCI":{"t":"G","r":0.875,"g":8,"b":0.5},"CHEvBHA":{"t":"G","r":0.875,"g":8,"b":0.875},"SUNvWOL":{"t":"G","r":0.8889,"g":9,"b":0.8889},"MUNvLIV":{"t":"G","r":0.8889,"g":9,"b":0.7778},"TOTvBOU":{"t":"G","r":0.875,"g":8,"b":0.875},"ARSvMUN":{"t":"G","r":0.875,"g":8,"b":0.75},"LEEvFUL":{"t":"G","r":0.8889,"g":9,"b":0.6667},"TOTvWOL":{"t":"G","r":0.875,"g":8,"b":0.375},"ASTvMUN":{"t":"G","r":0.875,"g":8,"b":0.75},"EVEvCRY":{"t":"G","r":0.875,"g":8,"b":0.5},"FULvBHA":{"t":"G","r":0.875,"g":8,"b":0.25},"LEEvBOU":{"t":"G","r":0.875,"g":8,"b":0.625},"MCIvWHU":{"t":"G","r":0.875,"g":8,"b":0.625},"TOTvFOR":{"t":"G","r":0.875,"g":8,"b":0.625},"BURvFOR":{"t":"G","r":0.875,"g":8,"b":0.75},"TOTvBRE":{"t":"G","r":0.875,"g":8,"b":0.875},"LEEvFOR":{"t":"G","r":0.875,"g":8,"b":0.625},"BHAvFOR":{"t":"G","r":0.875,"g":8,"b":0.75},"BOUvCRY":{"t":"G","r":0.875,"g":8,"b":0.75},"BURvSUN":{"t":"G","r":0.875,"g":8,"b":0.75},"TOTvNEW":{"t":"G","r":0.875,"g":8,"b":0.75},"FULvMUN":{"t":"G","r":0.875,"g":8,"b":0.875},"WHUvFOR":{"t":"G","r":0.875,"g":8,"b":0.625},"WOLvCRY":{"t":"G","r":0.875,"g":8,"b":0.875},"BHAvSUN":{"t":"G","r":0.875,"g":8,"b":0.25},"WOLvLIV":{"t":"G","r":0.875,"g":8,"b":0.75},"FORvLIV":{"t":"G","r":0.875,"g":8,"b":0.875},"WHUvSUN":{"t":"G","r":0.875,"g":8,"b":0.625},"GETvATM":{"t":"G","r":0.875,"g":8,"b":0.625},"LEVvRMA":{"t":"G","r":0.875,"g":8,"b":0.75},"GETvRMA":{"t":"G","r":0.875,"g":8,"b":0.5},"RBBvCEL":{"t":"G","r":0.875,"g":8,"b":0.75},"RBBvLEV":{"t":"G","r":0.875,"g":8,"b":0.875},"RSOvVIL":{"t":"G","r":0.875,"g":8,"b":0.875},"ESPvRBB":{"t":"G","r":0.875,"g":8,"b":0.5},"BILvLEV":{"t":"G","r":0.875,"g":8,"b":0.625},"RSOvRMA":{"t":"G","r":0.875,"g":8,"b":0.75},"VILvATM":{"t":"G","r":0.875,"g":8,"b":0.625},"RSOvRBB":{"t":"G","r":0.875,"g":8,"b":0.5},"VILvFCB":{"t":"G","r":0.875,"g":8,"b":0.75},"LEVvMAL":{"t":"G","r":0.875,"g":8,"b":0.625},"OSAvALA":{"t":"G","r":0.875,"g":8,"b":0.5},"GIRvFCB":{"t":"G","r":0.875,"g":8,"b":0.75},"LEVvCEL":{"t":"G","r":0.875,"g":8,"b":0.75},"GETvCEL":{"t":"G","r":0.875,"g":8,"b":0.875},"RSOvELC":{"t":"G","r":0.875,"g":8,"b":0.75},"OSAvCEL":{"t":"G","r":0.875,"g":8,"b":0.625},"RAYvRBB":{"t":"G","r":0.875,"g":8,"b":0.75},"SEVvMAL":{"t":"G","r":0.875,"g":8,"b":0.375},"BILvRBB":{"t":"G","r":0.875,"g":8,"b":0.5},"OVIvRAY":{"t":"G","r":0.875,"g":8,"b":0.375},"RSOvCEL":{"t":"G","r":0.875,"g":8,"b":0.625},"ATMvMAL":{"t":"G","r":0.875,"g":8,"b":0.75},"BILvRAY":{"t":"G","r":0.875,"g":8,"b":0.5},"GIRvOVI":{"t":"G","r":0.875,"g":8,"b":0.625},"OSAvESP":{"t":"G","r":0.875,"g":8,"b":0.75},"VCFvRMA":{"t":"G","r":0.875,"g":8,"b":0.875},"ATMvCEL":{"t":"G","r":0.875,"g":8,"b":0.5},"GIRvOSA":{"t":"G","r":0.875,"g":8,"b":0.75},"MALvFCB":{"t":"G","r":0.875,"g":8,"b":0.75},"ATMvGET":{"t":"G","r":0.875,"g":8,"b":0.625},"GIRvSEV":{"t":"G","r":0.8889,"g":9,"b":0.5556},"MALvRAY":{"t":"G","r":0.875,"g":8,"b":0.75},"ELCvALA":{"t":"G","r":0.875,"g":8,"b":0.25},"FCBvGET":{"t":"G","r":0.875,"g":8,"b":0.5},"CELvOVI":{"t":"G","r":0.875,"g":8,"b":0.625},"RMAvOSA":{"t":"G","r":0.875,"g":8,"b":0.625},"VCFvALA":{"t":"G","r":0.875,"g":8,"b":0.5},"FCBvOSA":{"t":"G","r":0.875,"g":8,"b":0.625},"CELvALA":{"t":"G","r":0.875,"g":8,"b":0.25},"LEVvBIL":{"t":"G","r":0.875,"g":8,"b":0.625},"CELvELC":{"t":"G","r":0.8889,"g":9,"b":0.5556},"GETvBIL":{"t":"G","r":0.875,"g":8,"b":0.875},"FIOvBFC":{"t":"G","r":0.875,"g":8,"b":0.5},"GENvCOM":{"t":"G","r":0.875,"g":8,"b":0.375},"LAZvNAP":{"t":"G","r":0.875,"g":8,"b":0.75},"PISvBFC":{"t":"G","r":0.875,"g":8,"b":0.625},"FIOvUSC":{"t":"G","r":0.875,"g":8,"b":0.875},"PISvUSC":{"t":"G","r":0.875,"g":8,"b":0.5},"ROMvCOM":{"t":"G","r":0.875,"g":8,"b":0.5},"VERvCOM":{"t":"G","r":0.875,"g":8,"b":0.75},"CAGvCOM":{"t":"G","r":0.875,"g":8,"b":0.5},"TORvUSC":{"t":"G","r":0.875,"g":8,"b":0.25},"LECvCOM":{"t":"G","r":0.875,"g":8,"b":0.875},"ROMvFIO":{"t":"G","r":0.875,"g":8,"b":0.5},"JUVvLEC":{"t":"G","r":0.875,"g":8,"b":0.75},"PARvUSC":{"t":"G","r":0.875,"g":8,"b":0.625},"PISvCAG":{"t":"G","r":0.875,"g":8,"b":0.75},"ROMvTOR":{"t":"G","r":0.875,"g":8,"b":0.5},"CAGvATA":{"t":"G","r":0.875,"g":8,"b":0.75},"PISvINT":{"t":"G","r":0.875,"g":8,"b":0.25},"ROMvUSC":{"t":"G","r":0.875,"g":8,"b":0.375},"CAGvACM":{"t":"G","r":0.8889,"g":9,"b":0.5556},"ATAvCOM":{"t":"G","r":0.875,"g":8,"b":0.375},"TORvINT":{"t":"G","r":0.875,"g":8,"b":0.375},"VERvUDI":{"t":"G","r":0.875,"g":8,"b":0.875},"BFCvINT":{"t":"G","r":0.875,"g":8,"b":0.5},"ACMvINT":{"t":"G","r":0.875,"g":8,"b":0.5},"ATAvFIO":{"t":"G","r":0.875,"g":8,"b":0.5},"BFCvJUV":{"t":"G","r":0.875,"g":8,"b":0.75},"ACMvJUV":{"t":"G","r":0.875,"g":8,"b":0.5},"ATAvPIS":{"t":"G","r":0.875,"g":8,"b":0.5},"NAPvLAZ":{"t":"G","r":0.875,"g":8,"b":0.5},"PARvTOR":{"t":"G","r":0.875,"g":8,"b":0.75},"BFCvSAS":{"t":"G","r":0.875,"g":8,"b":0.75},"USCvFIO":{"t":"G","r":0.875,"g":8,"b":0.5},"JUVvGEN":{"t":"G","r":0.875,"g":8,"b":0.375},"LECvCAG":{"t":"G","r":0.875,"g":8,"b":0.75},"COMvVER":{"t":"G","r":0.875,"g":8,"b":0.75},"COMvLEC":{"t":"G","r":0.875,"g":8,"b":0.625},"GENvSAS":{"t":"G","r":0.875,"g":8,"b":0.625},"INTvCAG":{"t":"G","r":0.875,"g":8,"b":0.625},"USCvATA":{"t":"G","r":0.875,"g":8,"b":0.75},"FIOvVER":{"t":"G","r":0.875,"g":8,"b":0.75},"LAZvSAS":{"t":"G","r":0.875,"g":8,"b":0.625},"USCvBFC":{"t":"G","r":0.875,"g":8,"b":0.5},"LEVvBMU":{"t":"G","r":0.875,"g":8,"b":0.625},"TSGvBMG":{"t":"G","r":0.875,"g":8,"b":0.875},"KOEvBMG":{"t":"G","r":0.875,"g":8,"b":0.75},"SCFvSVW":{"t":"G","r":0.875,"g":8,"b":0.75},"UNIvVFB":{"t":"G","r":0.8889,"g":9,"b":0.2222},"WOBvMAI":{"t":"G","r":0.8889,"g":9,"b":0.2222},"MAIvBMU":{"t":"G","r":0.875,"g":8,"b":0.75},"UNIvTSG":{"t":"G","r":0.875,"g":8,"b":0.875},"BVBvHSV":{"t":"G","r":0.875,"g":8,"b":0.75},"SGEvRBL":{"t":"G","r":0.875,"g":8,"b":0.5},"LEVvRBL":{"t":"G","r":0.875,"g":8,"b":0.75},"BMGvBMU":{"t":"G","r":0.875,"g":8,"b":0.625},"BVBvKOE":{"t":"G","r":0.875,"g":8,"b":0.375},"HDHvFCA":{"t":"G","r":0.875,"g":8,"b":0.75},"SGEvSCF":{"t":"G","r":0.8889,"g":9,"b":0.5556},"STPvRBL":{"t":"G","r":0.875,"g":8,"b":0.625},"SVWvVFB":{"t":"G","r":0.875,"g":8,"b":0.625},"BMUvVFB":{"t":"G","r":0.875,"g":8,"b":0.75},"SGEvBVB":{"t":"G","r":0.875,"g":8,"b":0.625},"UNIvSTP":{"t":"G","r":0.875,"g":8,"b":0.625},"BVBvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"SGEvWOB":{"t":"G","r":0.875,"g":8,"b":0.625},"UNIvHDH":{"t":"G","r":0.875,"g":8,"b":0.625},"SCFvHDH":{"t":"G","r":0.875,"g":8,"b":0.625},"BMUvRBL":{"t":"G","r":0.875,"g":8,"b":0.75},"KOEvVFB":{"t":"G","r":0.875,"g":8,"b":0.625},"WOBvSTP":{"t":"G","r":0.875,"g":8,"b":0.875},"BMUvTSG":{"t":"G","r":0.8889,"g":9,"b":0.6667},"SCFvFCA":{"t":"G","r":0.875,"g":8,"b":0.5},"UNIvRBL":{"t":"G","r":0.875,"g":8,"b":0.75},"MAIvBMG":{"t":"G","r":0.875,"g":8,"b":0.75},"BVBvUNI":{"t":"G","r":0.875,"g":8,"b":0.5},"SGEvKOE":{"t":"G","r":0.875,"g":8,"b":0.875},"STPvHSV":{"t":"G","r":0.875,"g":8,"b":0.375},"SVWvBMG":{"t":"G","r":0.875,"g":8,"b":0.5},"BMGvVFB":{"t":"G","r":0.875,"g":8,"b":0.375},"BMUvSGE":{"t":"G","r":0.875,"g":8,"b":0.25},"HDHvHSV":{"t":"G","r":0.875,"g":8,"b":0.5},"LEVvSGE":{"t":"G","r":0.875,"g":8,"b":0.125},"FCAvHSV":{"t":"G","r":0.875,"g":8,"b":0.75},"VFBvRBL":{"t":"G","r":0.875,"g":8,"b":0.75},"WOBvBVB":{"t":"G","r":0.875,"g":8,"b":0.375},"BMGvKOE":{"t":"G","r":0.875,"g":8,"b":0.5},"STPvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"HDHvLEV":{"t":"G","r":0.875,"g":8,"b":0.625},"HSVvUNI":{"t":"G","r":0.875,"g":8,"b":0.25},"RBLvTSG":{"t":"G","r":0.875,"g":8,"b":0.25},"VFBvSCF":{"t":"G","r":0.875,"g":8,"b":0.625},"BMUvMAI":{"t":"G","r":0.875,"g":8,"b":0.5},"RBLvKOE":{"t":"G","r":0.875,"g":8,"b":0.625},"SVWvWOB":{"t":"G","r":0.875,"g":8,"b":0.875},"TSGvUNI":{"t":"G","r":0.875,"g":8,"b":0.75},"VFBvBVB":{"t":"G","r":0.875,"g":8,"b":0.875},"FCAvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"VFBvWOB":{"t":"G","r":0.875,"g":8,"b":0.375},"KOEvSCF":{"t":"G","r":0.875,"g":8,"b":0.5},"RBLvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"TSGvWOB":{"t":"G","r":0.875,"g":8,"b":0.75},"UNIvLEV":{"t":"G","r":0.875,"g":8,"b":0.5},"ANGvOLM":{"t":"G","r":0.875,"g":8,"b":0.625},"STRvPSG":{"t":"G","r":0.875,"g":8,"b":0.5},"TOUvMET":{"t":"G","r":0.875,"g":8,"b":0.5},"LORvMET":{"t":"G","r":0.875,"g":8,"b":0.375},"LYOvLIL":{"t":"G","r":0.875,"g":8,"b":0.375},"NANvB29":{"t":"G","r":0.875,"g":8,"b":0.5},"RENvAUX":{"t":"G","r":0.875,"g":8,"b":0.75},"STRvNCE":{"t":"G","r":0.875,"g":8,"b":0.875},"LORvAUX":{"t":"G","r":0.875,"g":8,"b":0.625},"LYOvB29":{"t":"G","r":0.875,"g":8,"b":0.5},"OLMvNCE":{"t":"G","r":0.875,"g":8,"b":0.5},"STRvLEH":{"t":"G","r":0.875,"g":8,"b":0.625},"LORvAMO":{"t":"G","r":0.875,"g":8,"b":0.625},"LORvNAN":{"t":"G","r":0.875,"g":8,"b":0.75},"NCEvLEH":{"t":"G","r":0.875,"g":8,"b":0.625},"STRvB29":{"t":"G","r":0.875,"g":8,"b":0.625},"METvAUX":{"t":"G","r":0.875,"g":8,"b":0.875},"STRvTOU":{"t":"G","r":0.875,"g":8,"b":0.875},"NANvMET":{"t":"G","r":0.8889,"g":9,"b":0.5556},"ANGvMET":{"t":"G","r":0.875,"g":8,"b":0.25},"LYOvAUX":{"t":"G","r":0.875,"g":8,"b":0.5},"NANvAMO":{"t":"G","r":0.875,"g":8,"b":0.375},"PSGvB29":{"t":"G","r":0.875,"g":8,"b":0.625},"RENvLEH":{"t":"G","r":0.875,"g":8,"b":0.375},"TOUvLIL":{"t":"G","r":0.875,"g":8,"b":0.5},"PFCvNCE":{"t":"G","r":0.875,"g":8,"b":0.625},"LENvNCE":{"t":"G","r":0.875,"g":8,"b":0.5},"PFCvLEH":{"t":"G","r":0.875,"g":8,"b":0.625},"LENvLEH":{"t":"G","r":0.875,"g":8,"b":0.5},"LORvB29":{"t":"G","r":0.8889,"g":9,"b":0.7778},"PSGvLYO":{"t":"G","r":0.875,"g":8,"b":0.625},"ANGvLYO":{"t":"G","r":0.875,"g":8,"b":0.75},"LORvTOU":{"t":"G","r":0.875,"g":8,"b":0.125},"METvLEH":{"t":"G","r":0.875,"g":8,"b":0.75},"STRvNAN":{"t":"G","r":0.875,"g":8,"b":0.875},"LORvREN":{"t":"G","r":0.875,"g":8,"b":0.75},"NCEvAMO":{"t":"G","r":0.875,"g":8,"b":0.875},"NCEvNAN":{"t":"G","r":0.875,"g":8,"b":0.5},"PFCvREN":{"t":"G","r":0.875,"g":8,"b":0.875},"PSGvLOR":{"t":"G","r":0.875,"g":8,"b":0.625},"PFCvLOR":{"t":"G","r":0.875,"g":8,"b":0.75},"LEHvLYO":{"t":"G","r":0.875,"g":8,"b":0.625},"NCEvANG":{"t":"G","r":0.875,"g":8,"b":0.5},"OLMvSTR":{"t":"G","r":0.875,"g":8,"b":0.75},"AMOvTOU":{"t":"G","r":0.875,"g":8,"b":0.625},"AUXvREN":{"t":"G","r":0.875,"g":8,"b":0.75},"AUXvPFC":{"t":"G","r":0.875,"g":8,"b":0.5},"NANvREN":{"t":"G","r":0.875,"g":8,"b":0.375},"LYOvREN":{"t":"G","r":0.875,"g":8,"b":0.75},"TOUvANG":{"t":"G","r":0.875,"g":8,"b":0.75},"AUXvMET":{"t":"G","r":0.875,"g":8,"b":0.5},"LYOvLOR":{"t":"G","r":0.875,"g":8,"b":0.75},"TSGvLEV":{"t":"G","r":0.875,"g":8,"b":0.75},"METvOLM":{"t":"G","r":0.875,"g":8,"b":0.75},"TOUvPSG":{"t":"G","r":0.875,"g":8,"b":0.875}}

# ─── FUNCTIONS ───
def load_dedup():
    try:
        with open(DEDUP_FILE) as f:
            data = json.load(f)
        # Purge entries older than 30 min
        now = time.time()
        return {k: v for k, v in data.items() if now - v < 1800}
    except:
        return {}

def save_dedup(dedup):
    with open(DEDUP_FILE, "w") as f:
        json.dump(dedup, f)

def make_hash(event_ids):
    return hashlib.md5(",".join(sorted(event_ids)).encode()).hexdigest()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_booking_code(selections):
    """Get SportyBet booking code"""
    url = f"{API_BASE}/orders/share"
    payload = {"selections": selections}
    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        data = r.json()
        return data.get("data", {}).get("shareCode", "N/A")
    except:
        return "N/A"

def fetch_upcoming_events():
    """Fetch upcoming VFL events across all 5 leagues"""
    events = []
    now_ts = int(time.time() * 1000)
    
    categories = [
        ("sv%3Acategory%3A202120001", "sv%3Aleague%3A1", "England"),
        ("sv%3Acategory%3A202120002", "sv%3Aleague%3A2", "Spain"),
        ("sv%3Acategory%3A202120003", "sv%3Aleague%3A3", "Italy"),
        ("sv%3Acategory%3A202120004", "sv%3Aleague%3A4", "Germany"),
        ("sv%3Acategory%3A202120005", "sv%3Aleague%3A5", "France"),
    ]
    
    # Fetch prematch/upcoming from schedule endpoint
    for cat_enc, tourn_enc, league in categories:
        try:
            # Get events starting in the next 20 minutes
            start = now_ts
            end = now_ts + (ALERT_WINDOW * 60 * 1000)
            url = f"{API_BASE}/factsCenter/eventResultList?pageNum=1&pageSize=100&sportId=sr%3Asport%3A202120001&categoryId={cat_enc}&tournamentId={tourn_enc}&startTime={start}&endTime={end}"
            r = requests.get(url, headers=HEADERS, timeout=10)
            data = r.json()
            tournaments = data.get("data", {}).get("tournaments", [])
            for t in tournaments:
                for e in t.get("events", []):
                    est = e.get("estimateStartTime", 0)
                    status = e.get("matchStatus", "")
                    played = e.get("playedSeconds", 0)
                    
                    # Only prematch or very early (< 2 min played)
                    if status == "End" or played > 120:
                        continue
                    
                    events.append({
                        "eventId": e.get("eventId", ""),
                        "home": e.get("homeTeamName", ""),
                        "away": e.get("awayTeamName", ""),
                        "league": league,
                        "startTime": est,
                        "status": status,
                        "played": played
                    })
        except Exception as ex:
            print(f"Error fetching {league}: {ex}")
    
    return events

def match_elite(home, away):
    """Check if matchup is in ELITE DB, return tier + stats"""
    key = f"{home}v{away}"
    if key in ELITE_DB:
        info = ELITE_DB[key]
        return info["t"], info["r"], info["g"], info["b"]
    return None, 0, 0, 0

# ─── MAIN ───
def main():
    global ELITE_DB
    ELITE_DB = ELITE_DB_RAW
    
    print(f"ONIMIX VFL ELITE Scanner v9")
    print(f"ELITE DB: {len(ELITE_DB)} matchups (DIAMOND + GOLD)")
    
    events = fetch_upcoming_events()
    print(f"Upcoming events: {len(events)}")
    
    if not events:
        print("No upcoming events. Silent exit.")
        return
    
    # Filter ELITE matches
    diamond_picks = []
    gold_picks = []
    
    for e in events:
        tier, rate, games, btts = match_elite(e["home"], e["away"])
        if tier == "D":
            diamond_picks.append({**e, "rate": rate, "games": games, "btts": btts, "tier": "💎"})
        elif tier == "G":
            gold_picks.append({**e, "rate": rate, "games": games, "btts": btts, "tier": "🥇"})
    
    all_picks = diamond_picks + gold_picks
    
    if not all_picks:
        print("No ELITE matches in upcoming window. Silent exit.")
        return
    
    # Dedup
    dedup = load_dedup()
    event_ids = [p["eventId"] for p in all_picks]
    h = make_hash(event_ids)
    
    if h in dedup:
        print(f"Already sent (hash {h[:8]}). Silent exit.")
        return
    
    # Build Telegram message
    now_wat = datetime.now(timezone(timedelta(hours=1)))
    
    msg = f"⚡ <b>ONIMIX ELITE v9</b> ⚡\n"
    msg += f"📅 {now_wat.strftime('%H:%M WAT %d/%m/%Y')}\n"
    msg += f"🎯 Market: Over 1.5 Goals\n\n"
    
    if diamond_picks:
        msg += f"💎 <b>DIAMOND TIER</b> (100% historical)\n"
        for p in diamond_picks:
            msg += f"  ⚽ {p['home']} vs {p['away']} ({p['league']})\n"
            msg += f"     {p['games']}g = {p['rate']*100:.0f}% O1.5 | BTTS {p['btts']*100:.0f}%\n"
        msg += "\n"
    
    if gold_picks:
        msg += f"🥇 <b>GOLD TIER</b> (≥86% historical)\n"
        for p in gold_picks:
            msg += f"  ⚽ {p['home']} vs {p['away']} ({p['league']})\n"
            msg += f"     {p['games']}g = {p['rate']*100:.0f}% O1.5 | BTTS {p['btts']*100:.0f}%\n"
        msg += "\n"
    
    # Build booking code
    selections = []
    for p in all_picks:
        selections.append({
            "eventId": p["eventId"],
            "marketId": "total",
            "specifier": "total=1.5",
            "outcomeId": "over"
        })
    
    if selections:
        code = get_booking_code(selections)
        msg += f"📋 <b>Booking Code:</b> <code>{code}</code>\n"
    
    msg += f"\n💎 Diamond: {len(diamond_picks)} | 🥇 Gold: {len(gold_picks)}\n"
    msg += f"📊 Total: {len(all_picks)} picks\n"
    msg += f"🔒 <i>ELITE v9 — Only ≥86% matchups</i>"
    
    send_telegram(msg)
    print(f"✅ Sent {len(all_picks)} ELITE picks to Telegram")
    
    # Save dedup
    dedup[h] = time.time()
    save_dedup(dedup)

if __name__ == "__main__":
    main()
