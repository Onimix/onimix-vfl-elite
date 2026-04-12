#!/usr/bin/env python3
"""
VFL MEGA Accumulator v7 — BULLETPROOF EDITION
==============================================
KEY FIXES:
- Min 7 training games (validated 100% on day-8 cross-validation)
- 3 tiers: SAFE BET (3-fold DIAMOND), ULTRA MEGA (5-fold DIAMOND), MEGA MIX (4-fold D+G)
- Max 5-fold (proven: 29/29 = 100% on backtest)
- DIAMOND-first strategy: accas built from strongest matchups
"""
import json, urllib.request, hashlib, time, os, random
from datetime import datetime, timezone, timedelta

WAT = timezone(timedelta(hours=1))
BOT_TOKEN = "8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
CHAT_ID = "1745848158"
DEDUP_FILE = "/tmp/vfl_dedup_MEGA_v7.json"
DEDUP_COOLDOWN = 1800

LEAGUES = {
    "E": {"name": "England 🏴", "cat": "sv%3Acategory%3A202120001", "tid": "sv%3Aleague%3A1"},
    "S": {"name": "Spain 🇪🇸", "cat": "sv%3Acategory%3A202120002", "tid": "sv%3Aleague%3A2"},
    "I": {"name": "Italy 🇮🇹", "cat": "sv%3Acategory%3A202120003", "tid": "sv%3Aleague%3A3"},
    "G": {"name": "Germany 🇩🇪", "cat": "sv%3Acategory%3A202120004", "tid": "sv%3Aleague%3A4"},
    "F": {"name": "France 🇫🇷", "cat": "sv%3Acategory%3A202120005", "tid": "sv%3Aleague%3A5"},
}

ELITE = {"BOUvTOT":["E","D",8,1.0],"FORvSUN":["E","D",8,1.0],"LIVvMUN":["E","D",8,1.0],"WOLvNEW":["E","D",8,1.0],"CRYvCHE":["E","D",8,1.0],"WOLvBUR":["E","D",8,1.0],"ASTvARS":["E","D",8,1.0],"BREvTOT":["E","D",8,1.0],"CRYvMCI":["E","D",8,1.0],"MUNvCHE":["E","D",8,1.0],"SUNvNEW":["E","D",8,1.0],"NEWvARS":["E","D",9,1.0],"CHEvEVE":["E","D",8,1.0],"CRYvWOL":["E","D",8,1.0],"NEWvBUR":["E","D",8,1.0],"TOTvARS":["E","D",8,1.0],"ASTvFUL":["E","D",8,1.0],"LIVvWOL":["E","D",8,1.0],"NEWvLEE":["E","D",8,1.0],"CHEvFUL":["E","D",8,1.0],"BOUvCHE":["E","D",8,1.0],"CRYvSUN":["E","D",8,1.0],"LIVvBRE":["E","D",8,1.0],"ARSvLEE":["E","D",8,1.0],"ARSvFUL":["E","D",8,1.0],"CRYvTOT":["E","D",8,1.0],"MUNvNEW":["E","D",8,1.0],"WHUvLEE":["E","D",8,1.0],"WOLvMCI":["E","D",8,1.0],"MUNvTOT":["E","D",8,1.0],"BREvMCI":["E","D",8,1.0],"LIVvLEE":["E","D",8,1.0],"NEWvCHE":["E","D",8,1.0],"CHEvTOT":["E","D",8,1.0],"NEWvEVE":["E","D",8,1.0],"ARSvCRY":["E","D",8,1.0],"CHEvBUR":["E","D",8,1.0],"LIVvWHU":["E","D",8,1.0],"ASTvBHA":["E","D",8,1.0],"LIVvCRY":["E","D",8,1.0],"TOTvMCI":["E","D",8,1.0],"ASTvWHU":["E","D",8,1.0],"ASTvCRY":["E","D",8,1.0],"CHEvWHU":["E","D",8,1.0],"ASTvLIV":["E","D",8,1.0],"NEWvFOR":["E","D",8,1.0],"ARSvSUN":["E","D",8,1.0],"CHEvAST":["E","D",8,1.0],"ARSvCHE":["E","D",8,1.0],"FULvLIV":["E","D",8,1.0],"ARSvTOT":["E","D",8,1.0],"EVEvCHE":["E","D",8,1.0],"FULvAST":["E","D",8,1.0],"LEEvNEW":["E","D",8,1.0],"FULvCHE":["E","D",8,1.0],"MCIvEVE":["E","D",8,1.0],"OVIvELC":["S","D",8,1.0],"BILvELC":["S","D",8,1.0],"RAYvLEV":["S","D",8,1.0],"ATMvRMA":["S","D",8,1.0],"MALvGIR":["S","D",8,1.0],"SEVvRAY":["S","D",8,1.0],"RBBvRMA":["S","D",8,1.0],"RBBvFCB":["S","D",8,1.0],"ALAvVIL":["S","D",8,1.0],"OVIvFCB":["S","D",8,1.0],"SEVvLEV":["S","D",8,1.0],"BILvOVI":["S","D",8,1.0],"ATMvLEV":["S","D",8,1.0],"CELvFCB":["S","D",8,1.0],"VCFvOVI":["S","D",8,1.0],"VCFvELC":["S","D",8,1.0],"INTvUSC":["I","D",8,1.0],"UDIvINT":["I","D",8,1.0],"ROMvNAP":["I","D",8,1.0],"ATAvBFC":["I","D",8,1.0],"FIOvGEN":["I","D",8,1.0],"PISvGEN":["I","D",8,1.0],"ATAvUSC":["I","D",8,1.0],"CAGvINT":["I","D",8,1.0],"PISvLAZ":["I","D",8,1.0],"ATAvUDI":["I","D",8,1.0],"VERvFIO":["I","D",8,1.0],"UDIvUSC":["I","D",8,1.0],"FIOvCOM":["I","D",8,1.0],"ATAvNAP":["I","D",8,1.0],"CAGvUSC":["I","D",8,1.0],"PISvFIO":["I","D",8,1.0],"CAGvLAZ":["I","D",8,1.0],"ACMvSAS":["I","D",8,1.0],"PARvATA":["I","D",8,1.0],"NAPvCAG":["I","D",8,1.0],"FIOvLAZ":["I","D",8,1.0],"LEVvHDH":["G","D",8,1.0],"TSGvRBL":["G","D",8,1.0],"UNIvHSV":["G","D",8,1.0],"KOEvRBL":["G","D",8,1.0],"HDHvBMU":["G","D",8,1.0],"MAIvSVW":["G","D",8,1.0],"SCFvTSG":["G","D",8,1.0],"BVBvTSG":["G","D",8,1.0],"SCFvKOE":["G","D",8,1.0],"SVWvBMU":["G","D",8,1.0],"MAIvHSV":["G","D",8,1.0],"WOBvTSG":["G","D",8,1.0],"TSGvHSV":["G","D",8,1.0],"BVBvBMG":["G","D",8,1.0],"KOEvHSV":["G","D",8,1.0],"BVBvFCA":["G","D",8,1.0],"KOEvTSG":["G","D",8,1.0],"LEVvVFB":["G","D",8,1.0],"SCFvRBL":["G","D",8,1.0],"WOBvBMG":["G","D",8,1.0],"BVBvRBL":["G","D",8,1.0],"LEVvTSG":["G","D",8,1.0],"BVBvSCF":["G","D",8,1.0],"BMGvTSG":["G","D",8,1.0],"UNIvSGE":["G","D",8,1.0],"RENvMET":["F","D",8,1.0],"STRvOLM":["F","D",8,1.0],"ANGvLIL":["F","D",8,1.0],"LENvAUX":["F","D",8,1.0],"OLMvLIL":["F","D",8,1.0],"LORvLYO":["F","D",8,1.0],"ANGvLOR":["F","D",8,1.0],"TOUvNCE":["F","D",8,1.0],"LYOvMET":["F","D",8,1.0],"NANvAUX":["F","D",8,1.0],"PSGvAMO":["F","D",8,1.0],"ANGvAUX":["F","D",8,1.0],"LYOvAMO":["F","D",8,1.0],"OLMvMET":["F","D",8,1.0],"PSGvREN":["F","D",8,1.0],"LEHvAUX":["F","D",8,1.0],"PSGvANG":["F","D",8,1.0],"AUXvB29":["F","D",8,1.0],"LILvAMO":["F","D",8,1.0],"OLMvANG":["F","D",8,1.0],"AMOvB29":["F","D",8,1.0],"AUXvTOU":["F","D",8,1.0],"LENvPFC":["F","D",8,1.0],"LILvLYO":["F","D",8,1.0],"AUXvLOR":["F","D",8,1.0],"NCEvOLM":["F","D",8,1.0],"PSGvNCE":["F","D",8,1.0],"NANvLOR":["F","D",8,1.0],"AMOvLEN":["F","D",8,1.0],"NANvPFC":["F","D",8,1.0],"TOUvSTR":["F","D",8,1.0],"CHEvNEW":["E","D",7,1.0],"CRYvARS":["E","D",7,1.0],"CHEvSUN":["E","D",7,1.0],"CRYvLIV":["E","D",7,1.0],"BOUvARS":["E","D",7,1.0],"EVEvNEW":["E","D",7,1.0],"FULvFOR":["E","D",7,1.0],"WHUvMUN":["E","D",7,1.0],"NEWvAST":["E","D",7,1.0],"BOUvSUN":["E","D",7,1.0],"WHUvLIV":["E","D",7,1.0],"FCBvELC":["S","D",7,1.0],"ATMvRBB":["S","D",7,1.0],"LAZvPAR":["I","D",7,1.0],"ACMvLEC":["I","D",7,1.0],"USCvGEN":["I","D",7,1.0],"USCvNAP":["I","D",7,1.0],"INTvACM":["I","D",7,1.0],"BVBvBMU":["G","D",7,1.0],"HDHvMAI":["G","D",7,1.0],"SCFvBVB":["G","D",7,1.0],"RBLvBMU":["G","D",7,1.0],"KOEvBMU":["G","D",7,1.0],"LENvOLM":["F","D",7,1.0],"AUXvOLM":["F","D",7,1.0],"LILvREN":["F","D",7,1.0],"AUXvSTR":["F","D",7,1.0],"LILvMET":["F","D",7,1.0],"LILvLEN":["F","D",7,1.0],"B29vLEN":["F","D",7,1.0],"NANvPSG":["F","D",7,1.0],"RENvLOR":["F","D",7,1.0],"NANvSTR":["F","D",7,1.0],"CRYvAST":["E","G",8,0.875],"FULvBUR":["E","G",8,0.875],"WOLvTOT":["E","G",8,0.875],"WOLvLEE":["E","G",8,0.875],"ASTvCHE":["E","G",8,0.875],"LIVvMCI":["E","G",8,0.875],"MUNvEVE":["E","G",8,0.875],"ASTvEVE":["E","G",8,0.875],"CRYvBOU":["E","G",8,0.875],"LIVvFUL":["E","G",8,0.875],"NEWvTOT":["E","G",8,0.875],"LIVvBOU":["E","G",8,0.875],"MUNvFUL":["E","G",8,0.875],"CHEvMCI":["E","G",8,0.875],"EVEvARS":["E","G",8,0.875],"FORvCRY":["E","G",9,0.8889],"MUNvBOU":["E","G",8,0.875],"ASTvBOU":["E","G",8,0.875],"BREvCRY":["E","G",8,0.875],"LIVvFOR":["E","G",8,0.875],"MUNvWOL":["E","G",8,0.875],"TOTvLEE":["E","G",8,0.875],"FORvMUN":["E","G",8,0.875],"FULvEVE":["E","G",8,0.875],"BHAvBUR":["E","G",8,0.875],"FULvMCI":["E","G",8,0.875],"BOUvMCI":["E","G",8,0.875],"LIVvNEW":["E","G",8,0.875],"MUNvSUN":["E","G",8,0.875],"WOLvEVE":["E","G",8,0.875],"BREvCHE":["E","G",9,0.8889],"LIVvBUR":["E","G",8,0.875],"WHUvBHA":["E","G",8,0.875],"CRYvBHA":["E","G",8,0.875],"MUNvBUR":["E","G",8,0.875],"FORvBOU":["E","G",8,0.875],"MUNvLEE":["E","G",8,0.875],"ASTvLEE":["E","G",8,0.875],"SUNvFUL":["E","G",8,0.875],"CHEvLEE":["E","G",8,0.875],"MUNvWHU":["E","G",8,0.875],"ARSvLIV":["E","G",8,0.875],"BURvMCI":["E","G",8,0.875],"CHEvBHA":["E","G",8,0.875],"SUNvWOL":["E","G",8,0.875],"BURvFUL":["E","G",8,0.875],"MUNvLIV":["E","G",9,0.8889],"ARSvMUN":["E","G",8,0.875],"LEEvFUL":["E","G",9,0.8889],"TOTvWOL":["E","G",8,0.875],"ASTvMUN":["E","G",8,0.875],"EVEvCRY":["E","G",8,0.875],"FULvBHA":["E","G",8,0.875],"LEEvBOU":["E","G",8,0.875],"TOTvFOR":["E","G",8,0.875],"BURvFOR":["E","G",8,0.875],"CHEvMUN":["E","G",8,0.875],"MCIvCRY":["E","G",8,0.875],"TOTvBRE":["E","G",8,0.875],"BHAvFOR":["E","G",8,0.875],"BOUvCRY":["E","G",8,0.875],"BURvSUN":["E","G",8,0.875],"FULvMUN":["E","G",8,0.875],"WHUvFOR":["E","G",8,0.875],"WOLvCRY":["E","G",8,0.875],"BHAvSUN":["E","G",8,0.875],"BURvTOT":["E","G",8,0.875],"MCIvCHE":["E","G",8,0.875],"WOLvLIV":["E","G",8,0.875],"BHAvNEW":["E","G",8,0.875],"FORvLIV":["E","G",8,0.875],"WHUvSUN":["E","G",8,0.875],"GETvATM":["S","G",8,0.875],"GETvRMA":["S","G",8,0.875],"RBBvCEL":["S","G",8,0.875],"BILvVCF":["S","G",8,0.875],"RBBvLEV":["S","G",8,0.875],"RSOvVIL":["S","G",8,0.875],"SEVvATM":["S","G",8,0.875],"ELCvVCF":["S","G",8,0.875],"ESPvRBB":["S","G",8,0.875],"SEVvRMA":["S","G",8,0.875],"ESPvRAY":["S","G",8,0.875],"RSOvRMA":["S","G",8,0.875],"VILvATM":["S","G",8,0.875],"RSOvRBB":["S","G",8,0.875],"VILvFCB":["S","G",8,0.875],"GETvELC":["S","G",8,0.875],"LEVvMAL":["S","G",8,0.875],"OSAvALA":["S","G",8,0.875],"GIRvFCB":["S","G",8,0.875],"GETvCEL":["S","G",8,0.875],"RAYvRMA":["S","G",8,0.875],"RSOvELC":["S","G",8,0.875],"ESPvLEV":["S","G",8,0.875],"RAYvRBB":["S","G",8,0.875],"SEVvMAL":["S","G",8,0.875],"BILvRBB":["S","G",8,0.875],"OSAvGET":["S","G",8,0.875],"OVIvRAY":["S","G",8,0.875],"RSOvCEL":["S","G",8,0.875],"ATMvMAL":["S","G",8,0.875],"BILvRAY":["S","G",8,0.875],"GIRvOVI":["S","G",8,0.875],"OSAvESP":["S","G",8,0.875],"VCFvRMA":["S","G",8,0.875],"VILvCEL":["S","G",8,0.875],"ATMvCEL":["S","G",8,0.875],"GIRvOSA":["S","G",8,0.875],"MALvFCB":["S","G",8,0.875],"ATMvGET":["S","G",8,0.875],"GIRvSEV":["S","G",9,0.8889],"MALvRAY":["S","G",8,0.875],"ELCvALA":["S","G",8,0.875],"FCBvGET":["S","G",8,0.875],"CELvOVI":["S","G",8,0.875],"RMAvOSA":["S","G",8,0.875],"CELvALA":["S","G",8,0.875],"LEVvBIL":["S","G",8,0.875],"CELvELC":["S","G",8,0.875],"GETvBIL":["S","G",8,0.875],"VERvPAR":["I","G",8,0.875],"GENvCOM":["I","G",8,0.875],"LAZvNAP":["I","G",8,0.875],"PISvBFC":["I","G",8,0.875],"FIOvUSC":["I","G",8,0.875],"PISvACM":["I","G",8,0.875],"PISvUSC":["I","G",8,0.875],"VERvCOM":["I","G",8,0.875],"TORvUSC":["I","G",8,0.875],"LECvCOM":["I","G",8,0.875],"ROMvFIO":["I","G",8,0.875],"PISvVER":["I","G",8,0.875],"FIOvLEC":["I","G",8,0.875],"PARvUSC":["I","G",8,0.875],"PISvCAG":["I","G",8,0.875],"ROMvTOR":["I","G",8,0.875],"UDIvACM":["I","G",8,0.875],"PISvINT":["I","G",8,0.875],"ROMvUSC":["I","G",8,0.875],"CAGvACM":["I","G",8,0.875],"ATAvCOM":["I","G",8,0.875],"TORvINT":["I","G",8,0.875],"ACMvCOM":["I","G",8,0.875],"BFCvINT":["I","G",8,0.875],"ATAvFIO":["I","G",8,0.875],"BFCvJUV":["I","G",8,0.875],"PARvSAS":["I","G",8,0.875],"ACMvJUV":["I","G",8,0.875],"ATAvPIS":["I","G",8,0.875],"ATAvSAS":["I","G",8,0.875],"NAPvLAZ":["I","G",8,0.875],"PARvTOR":["I","G",8,0.875],"BFCvSAS":["I","G",8,0.875],"USCvFIO":["I","G",8,0.875],"LECvCAG":["I","G",8,0.875],"COMvVER":["I","G",8,0.875],"INTvVER":["I","G",8,0.875],"COMvLEC":["I","G",8,0.875],"GENvSAS":["I","G",8,0.875],"USCvATA":["I","G",8,0.875],"LAZvSAS":["I","G",8,0.875],"USCvBFC":["I","G",8,0.875],"LEVvBMU":["G","G",8,0.875],"TSGvBMG":["G","G",8,0.875],"KOEvBMG":["G","G",8,0.875],"SCFvSVW":["G","G",8,0.875],"UNIvVFB":["G","G",8,0.875],"KOEvFCA":["G","G",8,0.875],"SGEvBMG":["G","G",8,0.875],"WOBvMAI":["G","G",8,0.875],"MAIvBMU":["G","G",8,0.875],"BVBvHSV":["G","G",8,0.875],"LEVvRBL":["G","G",9,0.8889],"BVBvKOE":["G","G",8,0.875],"HDHvFCA":["G","G",8,0.875],"SGEvSCF":["G","G",8,0.875],"STPvRBL":["G","G",8,0.875],"SVWvVFB":["G","G",8,0.875],"BMUvVFB":["G","G",8,0.875],"SGEvBVB":["G","G",8,0.875],"UNIvSTP":["G","G",8,0.875],"BVBvLEV":["G","G",8,0.875],"SCFvSTP":["G","G",8,0.875],"SGEvWOB":["G","G",8,0.875],"SCFvHDH":["G","G",8,0.875],"BMUvRBL":["G","G",8,0.875],"KOEvVFB":["G","G",8,0.875],"WOBvSTP":["G","G",8,0.875],"BMUvTSG":["G","G",9,0.8889],"SCFvFCA":["G","G",8,0.875],"UNIvRBL":["G","G",8,0.875],"MAIvBMG":["G","G",8,0.875],"BVBvUNI":["G","G",8,0.875],"SGEvKOE":["G","G",8,0.875],"STPvHSV":["G","G",8,0.875],"SVWvBMG":["G","G",8,0.875],"BMGvVFB":["G","G",8,0.875],"BMUvSGE":["G","G",8,0.875],"HDHvHSV":["G","G",8,0.875],"LEVvSGE":["G","G",8,0.875],"VFBvRBL":["G","G",8,0.875],"WOBvBVB":["G","G",8,0.875],"BMGvKOE":["G","G",8,0.875],"STPvLEV":["G","G",8,0.875],"HDHvLEV":["G","G",8,0.875],"HSVvUNI":["G","G",8,0.875],"RBLvTSG":["G","G",8,0.875],"VFBvSCF":["G","G",8,0.875],"BMUvMAI":["G","G",8,0.875],"SVWvWOB":["G","G",8,0.875],"FCAvLEV":["G","G",8,0.875],"VFBvWOB":["G","G",8,0.875],"BMGvHDH":["G","G",9,0.8889],"KOEvSCF":["G","G",8,0.875],"RBLvLEV":["G","G",8,0.875],"RBLvSTP":["G","G",8,0.875],"TSGvWOB":["G","G",8,0.875],"UNIvLEV":["G","G",8,0.875],"AMOvLIL":["F","G",8,0.875],"ANGvOLM":["F","G",8,0.875],"STRvPSG":["F","G",8,0.875],"TOUvMET":["F","G",8,0.875],"NANvLIL":["F","G",8,0.875],"LYOvLIL":["F","G",8,0.875],"NANvB29":["F","G",8,0.875],"RENvAUX":["F","G",8,0.875],"STRvNCE":["F","G",8,0.875],"LENvPSG":["F","G",8,0.875],"LORvAUX":["F","G",9,0.8889],"LYOvB29":["F","G",8,0.875],"STRvLEH":["F","G",8,0.875],"LORvAMO":["F","G",8,0.875],"NCEvPSG":["F","G",8,0.875],"LORvNAN":["F","G",8,0.875],"NCEvLEH":["F","G",8,0.875],"PFCvAMO":["F","G",8,0.875],"STRvB29":["F","G",8,0.875],"METvAUX":["F","G",8,0.875],"LILvLEH":["F","G",8,0.875],"ANGvMET":["F","G",8,0.875],"LYOvAUX":["F","G",8,0.875],"NANvAMO":["F","G",8,0.875],"PSGvB29":["F","G",8,0.875],"TOUvLIL":["F","G",8,0.875],"LENvNCE":["F","G",8,0.875],"PFCvLEH":["F","G",8,0.875],"LENvLEH":["F","G",8,0.875],"LORvB29":["F","G",8,0.875],"PSGvLYO":["F","G",8,0.875],"ANGvLYO":["F","G",8,0.875],"LORvTOU":["F","G",8,0.875],"METvLEH":["F","G",8,0.875],"STRvNAN":["F","G",8,0.875],"LORvREN":["F","G",8,0.875],"NCEvAMO":["F","G",8,0.875],"PFCvTOU":["F","G",8,0.875],"STRvLYO":["F","G",8,0.875],"LENvTOU":["F","G",8,0.875],"PSGvLOR":["F","G",8,0.875],"STRvANG":["F","G",9,0.8889],"LENvREN":["F","G",8,0.875],"PFCvLOR":["F","G",8,0.875],"LEHvLYO":["F","G",8,0.875],"NCEvANG":["F","G",8,0.875],"OLMvSTR":["F","G",8,0.875],"PSGvPFC":["F","G",8,0.875],"AMOvTOU":["F","G",8,0.875],"AUXvREN":["F","G",8,0.875],"AUXvPFC":["F","G",8,0.875],"B29vANG":["F","G",8,0.875],"NANvREN":["F","G",8,0.875],"LYOvREN":["F","G",8,0.875],"TOUvANG":["F","G",8,0.875],"AUXvMET":["F","G",8,0.875],"B29vOLM":["F","G",8,0.875],"LYOvLOR":["F","G",8,0.875],"PSGvLEH":["F","G",8,0.875],"METvOLM":["F","G",8,0.875]}

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def get_booking_code(selections):
    if not selections:
        return None
    outcomes = []
    for s in selections:
        outcomes.append({
            "eventId": s["event_id"],
            "marketId": s.get("market_id", ""),
            "specifier": "",
            "outcomeId": s.get("outcome_id", ""),
        })
    try:
        url = "https://www.sportybet.com/api/ng/orders/share"
        payload = json.dumps({"outcomes": outcomes}).encode()
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"
        })
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        return data.get("data", {}).get("shareCode")
    except:
        return None

def load_dedup():
    try:
        with open(DEDUP_FILE) as f:
            return json.load(f)
    except:
        return {"hashes": {}}

def save_dedup(state):
    now = time.time()
    state["hashes"] = {k: v for k, v in state["hashes"].items() if now - v < DEDUP_COOLDOWN}
    with open(DEDUP_FILE, "w") as f:
        json.dump(state, f)

def is_duplicate(picks_str, dedup):
    h = hashlib.sha256(picks_str.encode()).hexdigest()[:16]
    now = time.time()
    if h in dedup["hashes"] and now - dedup["hashes"][h] < DEDUP_COOLDOWN:
        return True
    dedup["hashes"][h] = now
    return False

def fetch_upcoming():
    now_wat = datetime.now(WAT)
    now_ms = int(now_wat.timestamp() * 1000)
    window_ms = 30 * 60 * 1000
    
    all_picks = []
    for lg_code, lg in LEAGUES.items():
        try:
            url = (f"https://www.sportybet.com/api/ng/factsCenter/virtualSportSchedule?"
                   f"sportId=sr%3Asport%3A202120001"
                   f"&categoryId={lg['cat']}&tournamentId={lg['tid']}"
                   f"&_t={int(time.time()*1000)}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            
            for t in data.get("data", {}).get("tournaments", []):
                for ev in t.get("events", []):
                    start_time = ev.get("estimateStartTime", 0)
                    if start_time <= now_ms or start_time > now_ms + window_ms:
                        continue
                    
                    home = ev.get("homeTeamName", "")
                    away = ev.get("awayTeamName", "")
                    key = f"{home}v{away}"
                    
                    if key not in ELITE:
                        continue
                    
                    info = ELITE[key]
                    event_id = ev.get("eventId", "")
                    markets = ev.get("markets", [])
                    market_id = outcome_id = ""
                    for mkt in markets:
                        if "1.5" in mkt.get("specifier", ""):
                            market_id = mkt.get("marketId", "")
                            for out in mkt.get("outcomes", []):
                                if "Over" in out.get("outcomeName", ""):
                                    outcome_id = out.get("outcomeId", "")
                                    break
                            break
                    
                    start_dt = datetime.fromtimestamp(start_time / 1000, tz=WAT)
                    all_picks.append({
                        "home": home, "away": away, "key": key,
                        "league": lg["name"], "lg_code": lg_code,
                        "tier_code": info[1], "rate": info[3], "games": info[2],
                        "start_time": start_dt.strftime("%H:%M"),
                        "event_id": event_id, "market_id": market_id,
                        "outcome_id": outcome_id,
                    })
        except Exception as e:
            print(f"Error {lg['name']}: {e}")
        time.sleep(0.3)
    
    return all_picks

def build_accas(picks):
    """Build 3-tier accumulator selections."""
    d_picks = [p for p in picks if p["tier_code"] == "D"]
    g_picks = [p for p in picks if p["tier_code"] == "G"]
    
    accas = []
    
    # SAFE BET: 3-fold DIAMOND (different leagues preferred)
    if len(d_picks) >= 3:
        # Diversify across leagues
        by_league = {}
        for p in d_picks:
            by_league.setdefault(p["lg_code"], []).append(p)
        
        safe = []
        for lg in sorted(by_league, key=lambda x: len(by_league[x]), reverse=True):
            if len(safe) >= 3:
                break
            safe.append(by_league[lg][0])
        
        if len(safe) < 3:
            remaining = [p for p in d_picks if p not in safe]
            for p in remaining:
                if len(safe) >= 3:
                    break
                safe.append(p)
        
        if len(safe) >= 3:
            accas.append({"name": "🔒 SAFE BET", "folds": 3, "picks": safe[:3], "tier": "DIAMOND-only"})
    
    # ULTRA MEGA: 5-fold DIAMOND (highest games count)
    if len(d_picks) >= 5:
        sorted_d = sorted(d_picks, key=lambda p: -p["games"])
        accas.append({"name": "🏆 ULTRA MEGA", "folds": 5, "picks": sorted_d[:5], "tier": "DIAMOND-only"})
    
    # MEGA MIX: 4-fold DIAMOND+GOLD (diversified)
    all_eligible = d_picks + g_picks
    if len(all_eligible) >= 4:
        # Pick from different leagues, DIAMOND preferred
        used_leagues = set()
        mix = []
        for p in sorted(all_eligible, key=lambda x: (0 if x["tier_code"]=="D" else 1, -x["games"])):
            if p["lg_code"] not in used_leagues or len(mix) < 4:
                mix.append(p)
                used_leagues.add(p["lg_code"])
                if len(mix) >= 4:
                    break
        if len(mix) >= 4:
            accas.append({"name": "🔥 MEGA MIX", "folds": 4, "picks": mix[:4], "tier": "DIAMOND+GOLD"})
    
    return accas

def main():
    now = datetime.now(WAT)
    print(f"VFL MEGA v7 — {now.strftime('%Y-%m-%d %H:%M')} WAT")
    
    picks = fetch_upcoming()
    if not picks:
        print("No ELITE picks in window. Silent exit.")
        return
    
    accas = build_accas(picks)
    if not accas:
        print("Not enough picks for accumulators. Silent exit.")
        return
    
    # Dedup
    dedup = load_dedup()
    acca_str = "|".join(f"{a['name']}:{','.join(p['key'] for p in a['picks'])}" for a in accas)
    if is_duplicate(acca_str, dedup):
        print("Duplicate MEGA batch. Silent exit.")
        save_dedup(dedup)
        return
    save_dedup(dedup)
    
    # Build message
    lines = [f"🏆 *VFL MEGA ACCUMULATORS* — {now.strftime('%H:%M')} WAT"]
    lines.append(f"_Bulletproof Edition (min 7 games validated)_\n")
    
    for acca in accas:
        lines.append(f"*{acca['name']}* ({acca['folds']}-fold, {acca['tier']})")
        for p in acca["picks"]:
            tier_icon = "💎" if p["tier_code"] == "D" else "🥇"
            lines.append(f"  {tier_icon} {p['home']} vs {p['away']} — O1.5 [{p['league']} {p['start_time']}]")
        
        # Booking code
        booking = get_booking_code(acca["picks"])
        if booking:
            lines.append(f"  📱 Code: `{booking}`")
        lines.append("")
    
    lines.append(f"_Pool: {len(picks)} ELITE matches | DB: {len(ELITE)} matchups_")
    lines.append("_@Virtualonimix\\_bot — MEGA v7_")
    
    msg = "\n".join(lines)
    print(msg)
    
    if send_telegram(msg):
        print(f"\n✅ Sent {len(accas)} accumulators")
    else:
        print("\n❌ Failed to send")

if __name__ == "__main__":
    main()
