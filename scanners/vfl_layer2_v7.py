#!/usr/bin/env python3
"""
VFL 12-Layer Scoring Engine v7 — BULLETPROOF EDITION
=====================================================
Uses team profiles + ELITE matchup data for secondary scoring
Only sends ULTRA tier (score ≥85) — the safest picks
Min 7 games requirement inherited from ELITE v3
"""
import json, urllib.request, hashlib, time
from datetime import datetime, timezone, timedelta

WAT = timezone(timedelta(hours=1))
BOT_TOKEN = "8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
CHAT_ID = "1745848158"
DEDUP_FILE = "/tmp/vfl_dedup_L2_v7.json"
DEDUP_COOLDOWN = 1800

LEAGUES = {
    "E": {"name": "England 🏴", "cat": "sv%3Acategory%3A202120001", "tid": "sv%3Aleague%3A1"},
    "S": {"name": "Spain 🇪🇸", "cat": "sv%3Acategory%3A202120002", "tid": "sv%3Aleague%3A2"},
    "I": {"name": "Italy 🇮🇹", "cat": "sv%3Acategory%3A202120003", "tid": "sv%3Aleague%3A3"},
    "G": {"name": "Germany 🇩🇪", "cat": "sv%3Acategory%3A202120004", "tid": "sv%3Aleague%3A4"},
    "F": {"name": "France 🇫🇷", "cat": "sv%3Acategory%3A202120005", "tid": "sv%3Aleague%3A5"},
}

ELITE = {"BOUvTOT":["E","D",8,1.0],"FORvSUN":["E","D",8,1.0],"LIVvMUN":["E","D",8,1.0],"WOLvNEW":["E","D",8,1.0],"CRYvCHE":["E","D",8,1.0],"WOLvBUR":["E","D",8,1.0],"ASTvARS":["E","D",8,1.0],"BREvTOT":["E","D",8,1.0],"CRYvMCI":["E","D",8,1.0],"MUNvCHE":["E","D",8,1.0],"SUNvNEW":["E","D",8,1.0],"NEWvARS":["E","D",9,1.0],"CHEvEVE":["E","D",8,1.0],"CRYvWOL":["E","D",8,1.0],"NEWvBUR":["E","D",8,1.0],"TOTvARS":["E","D",8,1.0],"ASTvFUL":["E","D",8,1.0],"LIVvWOL":["E","D",8,1.0],"NEWvLEE":["E","D",8,1.0],"CHEvFUL":["E","D",8,1.0],"BOUvCHE":["E","D",8,1.0],"CRYvSUN":["E","D",8,1.0],"LIVvBRE":["E","D",8,1.0],"ARSvLEE":["E","D",8,1.0],"ARSvFUL":["E","D",8,1.0],"CRYvTOT":["E","D",8,1.0],"MUNvNEW":["E","D",8,1.0],"WHUvLEE":["E","D",8,1.0],"WOLvMCI":["E","D",8,1.0],"MUNvTOT":["E","D",8,1.0],"BREvMCI":["E","D",8,1.0],"LIVvLEE":["E","D",8,1.0],"NEWvCHE":["E","D",8,1.0],"CHEvTOT":["E","D",8,1.0],"NEWvEVE":["E","D",8,1.0],"ARSvCRY":["E","D",8,1.0],"CHEvBUR":["E","D",8,1.0],"LIVvWHU":["E","D",8,1.0],"ASTvBHA":["E","D",8,1.0],"LIVvCRY":["E","D",8,1.0],"TOTvMCI":["E","D",8,1.0],"ASTvWHU":["E","D",8,1.0],"ASTvCRY":["E","D",8,1.0],"CHEvWHU":["E","D",8,1.0],"ASTvLIV":["E","D",8,1.0],"NEWvFOR":["E","D",8,1.0],"ARSvSUN":["E","D",8,1.0],"CHEvAST":["E","D",8,1.0],"ARSvCHE":["E","D",8,1.0],"FULvLIV":["E","D",8,1.0],"ARSvTOT":["E","D",8,1.0],"EVEvCHE":["E","D",8,1.0],"FULvAST":["E","D",8,1.0],"LEEvNEW":["E","D",8,1.0],"FULvCHE":["E","D",8,1.0],"MCIvEVE":["E","D",8,1.0],"OVIvELC":["S","D",8,1.0],"BILvELC":["S","D",8,1.0],"RAYvLEV":["S","D",8,1.0],"ATMvRMA":["S","D",8,1.0],"MALvGIR":["S","D",8,1.0],"SEVvRAY":["S","D",8,1.0],"RBBvRMA":["S","D",8,1.0],"RBBvFCB":["S","D",8,1.0],"ALAvVIL":["S","D",8,1.0],"OVIvFCB":["S","D",8,1.0],"SEVvLEV":["S","D",8,1.0],"BILvOVI":["S","D",8,1.0],"ATMvLEV":["S","D",8,1.0],"CELvFCB":["S","D",8,1.0],"VCFvOVI":["S","D",8,1.0],"VCFvELC":["S","D",8,1.0],"INTvUSC":["I","D",8,1.0],"UDIvINT":["I","D",8,1.0],"ROMvNAP":["I","D",8,1.0],"ATAvBFC":["I","D",8,1.0],"FIOvGEN":["I","D",8,1.0],"PISvGEN":["I","D",8,1.0],"ATAvUSC":["I","D",8,1.0],"CAGvINT":["I","D",8,1.0],"PISvLAZ":["I","D",8,1.0],"ATAvUDI":["I","D",8,1.0],"VERvFIO":["I","D",8,1.0],"UDIvUSC":["I","D",8,1.0],"FIOvCOM":["I","D",8,1.0],"ATAvNAP":["I","D",8,1.0],"CAGvUSC":["I","D",8,1.0],"PISvFIO":["I","D",8,1.0],"CAGvLAZ":["I","D",8,1.0],"ACMvSAS":["I","D",8,1.0],"PARvATA":["I","D",8,1.0],"NAPvCAG":["I","D",8,1.0],"FIOvLAZ":["I","D",8,1.0],"LEVvHDH":["G","D",8,1.0],"TSGvRBL":["G","D",8,1.0],"UNIvHSV":["G","D",8,1.0],"KOEvRBL":["G","D",8,1.0],"HDHvBMU":["G","D",8,1.0],"MAIvSVW":["G","D",8,1.0],"SCFvTSG":["G","D",8,1.0],"BVBvTSG":["G","D",8,1.0],"SCFvKOE":["G","D",8,1.0],"SVWvBMU":["G","D",8,1.0],"MAIvHSV":["G","D",8,1.0],"WOBvTSG":["G","D",8,1.0],"TSGvHSV":["G","D",8,1.0],"BVBvBMG":["G","D",8,1.0],"KOEvHSV":["G","D",8,1.0],"BVBvFCA":["G","D",8,1.0],"KOEvTSG":["G","D",8,1.0],"LEVvVFB":["G","D",8,1.0],"SCFvRBL":["G","D",8,1.0],"WOBvBMG":["G","D",8,1.0],"BVBvRBL":["G","D",8,1.0],"LEVvTSG":["G","D",8,1.0],"BVBvSCF":["G","D",8,1.0],"BMGvTSG":["G","D",8,1.0],"UNIvSGE":["G","D",8,1.0],"RENvMET":["F","D",8,1.0],"STRvOLM":["F","D",8,1.0],"ANGvLIL":["F","D",8,1.0],"LENvAUX":["F","D",8,1.0],"OLMvLIL":["F","D",8,1.0],"LORvLYO":["F","D",8,1.0],"ANGvLOR":["F","D",8,1.0],"TOUvNCE":["F","D",8,1.0],"LYOvMET":["F","D",8,1.0],"NANvAUX":["F","D",8,1.0],"PSGvAMO":["F","D",8,1.0],"ANGvAUX":["F","D",8,1.0],"LYOvAMO":["F","D",8,1.0],"OLMvMET":["F","D",8,1.0],"PSGvREN":["F","D",8,1.0],"LEHvAUX":["F","D",8,1.0],"PSGvANG":["F","D",8,1.0],"AUXvB29":["F","D",8,1.0],"LILvAMO":["F","D",8,1.0],"OLMvANG":["F","D",8,1.0],"AMOvB29":["F","D",8,1.0],"AUXvTOU":["F","D",8,1.0],"LENvPFC":["F","D",8,1.0],"LILvLYO":["F","D",8,1.0],"AUXvLOR":["F","D",8,1.0],"NCEvOLM":["F","D",8,1.0],"PSGvNCE":["F","D",8,1.0],"NANvLOR":["F","D",8,1.0],"AMOvLEN":["F","D",8,1.0],"NANvPFC":["F","D",8,1.0],"TOUvSTR":["F","D",8,1.0],"CHEvNEW":["E","D",7,1.0],"CRYvARS":["E","D",7,1.0],"CHEvSUN":["E","D",7,1.0],"CRYvLIV":["E","D",7,1.0],"BOUvARS":["E","D",7,1.0],"EVEvNEW":["E","D",7,1.0],"FULvFOR":["E","D",7,1.0],"WHUvMUN":["E","D",7,1.0],"NEWvAST":["E","D",7,1.0],"BOUvSUN":["E","D",7,1.0],"WHUvLIV":["E","D",7,1.0],"FCBvELC":["S","D",7,1.0],"ATMvRBB":["S","D",7,1.0],"LAZvPAR":["I","D",7,1.0],"ACMvLEC":["I","D",7,1.0],"USCvGEN":["I","D",7,1.0],"USCvNAP":["I","D",7,1.0],"INTvACM":["I","D",7,1.0],"BVBvBMU":["G","D",7,1.0],"HDHvMAI":["G","D",7,1.0],"SCFvBVB":["G","D",7,1.0],"RBLvBMU":["G","D",7,1.0],"KOEvBMU":["G","D",7,1.0],"LENvOLM":["F","D",7,1.0],"AUXvOLM":["F","D",7,1.0],"LILvREN":["F","D",7,1.0],"AUXvSTR":["F","D",7,1.0],"LILvMET":["F","D",7,1.0],"LILvLEN":["F","D",7,1.0],"B29vLEN":["F","D",7,1.0],"NANvPSG":["F","D",7,1.0],"RENvLOR":["F","D",7,1.0],"NANvSTR":["F","D",7,1.0],"CRYvAST":["E","G",8,0.875],"FULvBUR":["E","G",8,0.875],"WOLvTOT":["E","G",8,0.875],"WOLvLEE":["E","G",8,0.875],"ASTvCHE":["E","G",8,0.875],"LIVvMCI":["E","G",8,0.875],"MUNvEVE":["E","G",8,0.875],"ASTvEVE":["E","G",8,0.875],"CRYvBOU":["E","G",8,0.875],"LIVvFUL":["E","G",8,0.875],"NEWvTOT":["E","G",8,0.875],"LIVvBOU":["E","G",8,0.875],"MUNvFUL":["E","G",8,0.875],"CHEvMCI":["E","G",8,0.875],"EVEvARS":["E","G",8,0.875],"FORvCRY":["E","G",9,0.8889],"MUNvBOU":["E","G",8,0.875],"ASTvBOU":["E","G",8,0.875],"BREvCRY":["E","G",8,0.875],"LIVvFOR":["E","G",8,0.875],"MUNvWOL":["E","G",8,0.875],"TOTvLEE":["E","G",8,0.875],"FORvMUN":["E","G",8,0.875],"FULvEVE":["E","G",8,0.875],"BHAvBUR":["E","G",8,0.875],"FULvMCI":["E","G",8,0.875],"BOUvMCI":["E","G",8,0.875],"LIVvNEW":["E","G",8,0.875],"MUNvSUN":["E","G",8,0.875],"WOLvEVE":["E","G",8,0.875],"BREvCHE":["E","G",9,0.8889],"LIVvBUR":["E","G",8,0.875],"WHUvBHA":["E","G",8,0.875],"CRYvBHA":["E","G",8,0.875],"MUNvBUR":["E","G",8,0.875],"FORvBOU":["E","G",8,0.875],"MUNvLEE":["E","G",8,0.875],"ASTvLEE":["E","G",8,0.875],"SUNvFUL":["E","G",8,0.875],"CHEvLEE":["E","G",8,0.875],"MUNvWHU":["E","G",8,0.875],"ARSvLIV":["E","G",8,0.875],"BURvMCI":["E","G",8,0.875],"CHEvBHA":["E","G",8,0.875],"SUNvWOL":["E","G",8,0.875],"BURvFUL":["E","G",8,0.875],"MUNvLIV":["E","G",9,0.8889],"ARSvMUN":["E","G",8,0.875],"LEEvFUL":["E","G",9,0.8889],"TOTvWOL":["E","G",8,0.875],"ASTvMUN":["E","G",8,0.875],"EVEvCRY":["E","G",8,0.875],"FULvBHA":["E","G",8,0.875],"LEEvBOU":["E","G",8,0.875],"TOTvFOR":["E","G",8,0.875],"BURvFOR":["E","G",8,0.875],"CHEvMUN":["E","G",8,0.875],"MCIvCRY":["E","G",8,0.875],"TOTvBRE":["E","G",8,0.875],"BHAvFOR":["E","G",8,0.875],"BOUvCRY":["E","G",8,0.875],"BURvSUN":["E","G",8,0.875],"FULvMUN":["E","G",8,0.875],"WHUvFOR":["E","G",8,0.875],"WOLvCRY":["E","G",8,0.875],"BHAvSUN":["E","G",8,0.875],"BURvTOT":["E","G",8,0.875],"MCIvCHE":["E","G",8,0.875],"WOLvLIV":["E","G",8,0.875],"BHAvNEW":["E","G",8,0.875],"FORvLIV":["E","G",8,0.875],"WHUvSUN":["E","G",8,0.875],"GETvATM":["S","G",8,0.875],"GETvRMA":["S","G",8,0.875],"RBBvCEL":["S","G",8,0.875],"BILvVCF":["S","G",8,0.875],"RBBvLEV":["S","G",8,0.875],"RSOvVIL":["S","G",8,0.875],"SEVvATM":["S","G",8,0.875],"ELCvVCF":["S","G",8,0.875],"ESPvRBB":["S","G",8,0.875],"SEVvRMA":["S","G",8,0.875],"ESPvRAY":["S","G",8,0.875],"RSOvRMA":["S","G",8,0.875],"VILvATM":["S","G",8,0.875],"RSOvRBB":["S","G",8,0.875],"VILvFCB":["S","G",8,0.875],"GETvELC":["S","G",8,0.875],"LEVvMAL":["S","G",8,0.875],"OSAvALA":["S","G",8,0.875],"GIRvFCB":["S","G",8,0.875],"GETvCEL":["S","G",8,0.875],"RAYvRMA":["S","G",8,0.875],"RSOvELC":["S","G",8,0.875],"ESPvLEV":["S","G",8,0.875],"RAYvRBB":["S","G",8,0.875],"SEVvMAL":["S","G",8,0.875],"BILvRBB":["S","G",8,0.875],"OSAvGET":["S","G",8,0.875],"OVIvRAY":["S","G",8,0.875],"RSOvCEL":["S","G",8,0.875],"ATMvMAL":["S","G",8,0.875],"BILvRAY":["S","G",8,0.875],"GIRvOVI":["S","G",8,0.875],"OSAvESP":["S","G",8,0.875],"VCFvRMA":["S","G",8,0.875],"VILvCEL":["S","G",8,0.875],"ATMvCEL":["S","G",8,0.875],"GIRvOSA":["S","G",8,0.875],"MALvFCB":["S","G",8,0.875],"ATMvGET":["S","G",8,0.875],"GIRvSEV":["S","G",9,0.8889],"MALvRAY":["S","G",8,0.875],"ELCvALA":["S","G",8,0.875],"FCBvGET":["S","G",8,0.875],"CELvOVI":["S","G",8,0.875],"RMAvOSA":["S","G",8,0.875],"CELvALA":["S","G",8,0.875],"LEVvBIL":["S","G",8,0.875],"CELvELC":["S","G",8,0.875],"GETvBIL":["S","G",8,0.875],"VERvPAR":["I","G",8,0.875],"GENvCOM":["I","G",8,0.875],"LAZvNAP":["I","G",8,0.875],"PISvBFC":["I","G",8,0.875],"FIOvUSC":["I","G",8,0.875],"PISvACM":["I","G",8,0.875],"PISvUSC":["I","G",8,0.875],"VERvCOM":["I","G",8,0.875],"TORvUSC":["I","G",8,0.875],"LECvCOM":["I","G",8,0.875],"ROMvFIO":["I","G",8,0.875],"PISvVER":["I","G",8,0.875],"FIOvLEC":["I","G",8,0.875],"PARvUSC":["I","G",8,0.875],"PISvCAG":["I","G",8,0.875],"ROMvTOR":["I","G",8,0.875],"UDIvACM":["I","G",8,0.875],"PISvINT":["I","G",8,0.875],"ROMvUSC":["I","G",8,0.875],"CAGvACM":["I","G",8,0.875],"ATAvCOM":["I","G",8,0.875],"TORvINT":["I","G",8,0.875],"ACMvCOM":["I","G",8,0.875],"BFCvINT":["I","G",8,0.875],"ATAvFIO":["I","G",8,0.875],"BFCvJUV":["I","G",8,0.875],"PARvSAS":["I","G",8,0.875],"ACMvJUV":["I","G",8,0.875],"ATAvPIS":["I","G",8,0.875],"ATAvSAS":["I","G",8,0.875],"NAPvLAZ":["I","G",8,0.875],"PARvTOR":["I","G",8,0.875],"BFCvSAS":["I","G",8,0.875],"USCvFIO":["I","G",8,0.875],"LECvCAG":["I","G",8,0.875],"COMvVER":["I","G",8,0.875],"INTvVER":["I","G",8,0.875],"COMvLEC":["I","G",8,0.875],"GENvSAS":["I","G",8,0.875],"USCvATA":["I","G",8,0.875],"LAZvSAS":["I","G",8,0.875],"USCvBFC":["I","G",8,0.875],"LEVvBMU":["G","G",8,0.875],"TSGvBMG":["G","G",8,0.875],"KOEvBMG":["G","G",8,0.875],"SCFvSVW":["G","G",8,0.875],"UNIvVFB":["G","G",8,0.875],"KOEvFCA":["G","G",8,0.875],"SGEvBMG":["G","G",8,0.875],"WOBvMAI":["G","G",8,0.875],"MAIvBMU":["G","G",8,0.875],"BVBvHSV":["G","G",8,0.875],"LEVvRBL":["G","G",9,0.8889],"BVBvKOE":["G","G",8,0.875],"HDHvFCA":["G","G",8,0.875],"SGEvSCF":["G","G",8,0.875],"STPvRBL":["G","G",8,0.875],"SVWvVFB":["G","G",8,0.875],"BMUvVFB":["G","G",8,0.875],"SGEvBVB":["G","G",8,0.875],"UNIvSTP":["G","G",8,0.875],"BVBvLEV":["G","G",8,0.875],"SCFvSTP":["G","G",8,0.875],"SGEvWOB":["G","G",8,0.875],"SCFvHDH":["G","G",8,0.875],"BMUvRBL":["G","G",8,0.875],"KOEvVFB":["G","G",8,0.875],"WOBvSTP":["G","G",8,0.875],"BMUvTSG":["G","G",9,0.8889],"SCFvFCA":["G","G",8,0.875],"UNIvRBL":["G","G",8,0.875],"MAIvBMG":["G","G",8,0.875],"BVBvUNI":["G","G",8,0.875],"SGEvKOE":["G","G",8,0.875],"STPvHSV":["G","G",8,0.875],"SVWvBMG":["G","G",8,0.875],"BMGvVFB":["G","G",8,0.875],"BMUvSGE":["G","G",8,0.875],"HDHvHSV":["G","G",8,0.875],"LEVvSGE":["G","G",8,0.875],"VFBvRBL":["G","G",8,0.875],"WOBvBVB":["G","G",8,0.875],"BMGvKOE":["G","G",8,0.875],"STPvLEV":["G","G",8,0.875],"HDHvLEV":["G","G",8,0.875],"HSVvUNI":["G","G",8,0.875],"RBLvTSG":["G","G",8,0.875],"VFBvSCF":["G","G",8,0.875],"BMUvMAI":["G","G",8,0.875],"SVWvWOB":["G","G",8,0.875],"FCAvLEV":["G","G",8,0.875],"VFBvWOB":["G","G",8,0.875],"BMGvHDH":["G","G",9,0.8889],"KOEvSCF":["G","G",8,0.875],"RBLvLEV":["G","G",8,0.875],"RBLvSTP":["G","G",8,0.875],"TSGvWOB":["G","G",8,0.875],"UNIvLEV":["G","G",8,0.875],"AMOvLIL":["F","G",8,0.875],"ANGvOLM":["F","G",8,0.875],"STRvPSG":["F","G",8,0.875],"TOUvMET":["F","G",8,0.875],"NANvLIL":["F","G",8,0.875],"LYOvLIL":["F","G",8,0.875],"NANvB29":["F","G",8,0.875],"RENvAUX":["F","G",8,0.875],"STRvNCE":["F","G",8,0.875],"LENvPSG":["F","G",8,0.875],"LORvAUX":["F","G",9,0.8889],"LYOvB29":["F","G",8,0.875],"STRvLEH":["F","G",8,0.875],"LORvAMO":["F","G",8,0.875],"NCEvPSG":["F","G",8,0.875],"LORvNAN":["F","G",8,0.875],"NCEvLEH":["F","G",8,0.875],"PFCvAMO":["F","G",8,0.875],"STRvB29":["F","G",8,0.875],"METvAUX":["F","G",8,0.875],"LILvLEH":["F","G",8,0.875],"ANGvMET":["F","G",8,0.875],"LYOvAUX":["F","G",8,0.875],"NANvAMO":["F","G",8,0.875],"PSGvB29":["F","G",8,0.875],"TOUvLIL":["F","G",8,0.875],"LENvNCE":["F","G",8,0.875],"PFCvLEH":["F","G",8,0.875],"LENvLEH":["F","G",8,0.875],"LORvB29":["F","G",8,0.875],"PSGvLYO":["F","G",8,0.875],"ANGvLYO":["F","G",8,0.875],"LORvTOU":["F","G",8,0.875],"METvLEH":["F","G",8,0.875],"STRvNAN":["F","G",8,0.875],"LORvREN":["F","G",8,0.875],"NCEvAMO":["F","G",8,0.875],"PFCvTOU":["F","G",8,0.875],"STRvLYO":["F","G",8,0.875],"LENvTOU":["F","G",8,0.875],"PSGvLOR":["F","G",8,0.875],"STRvANG":["F","G",9,0.8889],"LENvREN":["F","G",8,0.875],"PFCvLOR":["F","G",8,0.875],"LEHvLYO":["F","G",8,0.875],"NCEvANG":["F","G",8,0.875],"OLMvSTR":["F","G",8,0.875],"PSGvPFC":["F","G",8,0.875],"AMOvTOU":["F","G",8,0.875],"AUXvREN":["F","G",8,0.875],"AUXvPFC":["F","G",8,0.875],"B29vANG":["F","G",8,0.875],"NANvREN":["F","G",8,0.875],"LYOvREN":["F","G",8,0.875],"TOUvANG":["F","G",8,0.875],"AUXvMET":["F","G",8,0.875],"B29vOLM":["F","G",8,0.875],"LYOvLOR":["F","G",8,0.875],"PSGvLEH":["F","G",8,0.875],"METvOLM":["F","G",8,0.875]}
# Team profiles: [o15_rate, o25_rate, avg_goals, games]
TEAMS = {"BHA": [0.684, 0.409, 2.39, 291], "EVE": [0.722, 0.447, 2.48, 291], "BOU": [0.742, 0.467, 2.69, 291], "TOT": [0.804, 0.581, 2.97, 291], "BRE": [0.753, 0.546, 2.85, 291], "ARS": [0.759, 0.529, 2.88, 291], "CRY": [0.821, 0.591, 3.25, 291], "AST": [0.77, 0.55, 3.12, 291], "FOR": [0.746, 0.546, 2.82, 291], "SUN": [0.711, 0.464, 2.53, 291], "FUL": [0.794, 0.54, 2.77, 291], "BUR": [0.68, 0.515, 2.72, 291], "LEE": [0.739, 0.454, 2.54, 291], "MCI": [0.753, 0.505, 2.85, 291], "LIV": [0.814, 0.588, 3.01, 291], "MUN": [0.804, 0.598, 3.01, 291], "WHU": [0.725, 0.498, 2.71, 291], "CHE": [0.856, 0.687, 3.22, 291], "WOL": [0.749, 0.512, 2.64, 291], "NEW": [0.845, 0.619, 3.24, 291], "BIL": [0.703, 0.417, 2.27, 290], "ALA": [0.693, 0.448, 2.36, 290], "ESP": [0.641, 0.383, 2.23, 290], "VIL": [0.652, 0.424, 2.33, 290], "FCB": [0.724, 0.49, 2.51, 290], "CEL": [0.676, 0.4, 2.21, 290], "GET": [0.683, 0.438, 2.37, 290], "ATM": [0.697, 0.462, 2.43, 290], "LEV": [0.733, 0.516, 2.65, 550], "RMA": [0.697, 0.431, 2.41, 290], "OSA": [0.603, 0.345, 2.09, 290], "RSO": [0.655, 0.434, 2.28, 290], "OVI": [0.641, 0.369, 2.18, 290], "ELC": [0.707, 0.466, 2.5, 290], "RAY": [0.641, 0.331, 2.09, 290], "VCF": [0.652, 0.324, 2.1, 290], "RBB": [0.645, 0.434, 2.31, 290], "MAL": [0.638, 0.379, 2.19, 290], "SEV": [0.669, 0.476, 2.44, 290], "GIR": [0.648, 0.438, 2.27, 290], "FIO": [0.732, 0.467, 2.52, 291], "BFC": [0.619, 0.385, 2.14, 291], "GEN": [0.636, 0.416, 2.28, 291], "NAP": [0.632, 0.392, 2.19, 291], "INT": [0.708, 0.454, 2.51, 291], "USC": [0.711, 0.44, 2.38, 291], "JUV": [0.643, 0.351, 2.2, 291], "ACM": [0.704, 0.43, 2.49, 291], "LAZ": [0.66, 0.381, 2.26, 291], "LEC": [0.643, 0.416, 2.25, 291], "PIS": [0.711, 0.481, 2.54, 291], "ATA": [0.756, 0.433, 2.59, 291], "ROM": [0.66, 0.426, 2.41, 291], "CAG": [0.701, 0.502, 2.5, 291], "SAS": [0.622, 0.371, 2.23, 291], "TOR": [0.598, 0.323, 2.04, 291], "UDI": [0.608, 0.381, 2.19, 291], "COM": [0.701, 0.412, 2.4, 291], "VER": [0.653, 0.402, 2.33, 291], "PAR": [0.622, 0.337, 2.14, 291], "BVB": [0.731, 0.469, 2.57, 260], "WOB": [0.723, 0.45, 2.53, 260], "HSV": [0.719, 0.515, 2.68, 260], "FCA": [0.712, 0.465, 2.57, 260], "KOE": [0.735, 0.488, 2.59, 260], "HDH": [0.688, 0.388, 2.33, 260], "BMU": [0.765, 0.515, 2.75, 260], "RBL": [0.781, 0.515, 2.71, 260], "VFB": [0.712, 0.469, 2.59, 260], "SCF": [0.765, 0.485, 2.7, 260], "MAI": [0.688, 0.419, 2.33, 260], "SGE": [0.731, 0.508, 2.62, 260], "STP": [0.669, 0.442, 2.35, 260], "TSG": [0.812, 0.519, 2.95, 260], "BMG": [0.738, 0.519, 2.68, 260], "UNI": [0.688, 0.404, 2.32, 260], "SVW": [0.658, 0.404, 2.28, 260], "AMO": [0.749, 0.506, 2.68, 259], "LIL": [0.745, 0.486, 2.71, 259], "ANG": [0.741, 0.486, 2.67, 259], "OLM": [0.753, 0.456, 2.61, 259], "B29": [0.687, 0.459, 2.63, 259], "AUX": [0.768, 0.502, 2.68, 259], "LOR": [0.799, 0.51, 2.93, 259], "PFC": [0.73, 0.494, 2.64, 259], "LYO": [0.741, 0.467, 2.63, 259], "NCE": [0.691, 0.448, 2.46, 259], "NAN": [0.726, 0.463, 2.49, 259], "LEH": [0.687, 0.471, 2.48, 259], "REN": [0.753, 0.568, 2.76, 259], "LEN": [0.722, 0.475, 2.53, 259], "STR": [0.737, 0.51, 2.56, 259], "PSG": [0.768, 0.498, 2.71, 259], "TOU": [0.73, 0.444, 2.5, 259], "MET": [0.714, 0.483, 2.62, 259]}

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

def score_match(home, away):
    """12-layer scoring for a match. Returns score 0-100."""
    key = f"{home}v{away}"
    h_prof = TEAMS.get(home, [0.65, 0.35, 2.0, 0])
    a_prof = TEAMS.get(away, [0.65, 0.35, 2.0, 0])
    
    score = 0
    
    # Layer 1: ELITE matchup bonus (0-30)
    if key in ELITE:
        info = ELITE[key]
        rate = info[3]
        if info[1] == "D":  # DIAMOND
            score += 30
        elif info[1] == "G":  # GOLD
            score += 25
    
    # Layer 2: Home team O1.5 rate (0-10)
    score += min(10, h_prof[0] * 12)
    
    # Layer 3: Away team O1.5 rate (0-10)
    score += min(10, a_prof[0] * 12)
    
    # Layer 4: Combined avg goals (0-10)
    combined_avg = (h_prof[2] + a_prof[2]) / 2
    score += min(10, combined_avg * 3)
    
    # Layer 5: Both teams O1.5 > 70% (0-8)
    if h_prof[0] >= 0.70 and a_prof[0] >= 0.70:
        score += 8
    elif h_prof[0] >= 0.65 and a_prof[0] >= 0.65:
        score += 5
    
    # Layer 6: O2.5 rate bonus (0-7)
    avg_o25 = (h_prof[1] + a_prof[1]) / 2
    score += min(7, avg_o25 * 14)
    
    # Layer 7: Sample size confidence (0-5)
    min_games = min(h_prof[3], a_prof[3])
    if min_games >= 200:
        score += 5
    elif min_games >= 100:
        score += 3
    elif min_games >= 50:
        score += 2
    
    # Layer 8: League baseline (0-5)
    # All VFL leagues ~67-71% O1.5 baseline
    score += 3
    
    # Layer 9: High-scoring matchup (0-5)
    if combined_avg >= 3.0:
        score += 5
    elif combined_avg >= 2.5:
        score += 3
    
    # Layer 10: Goal-difference factor (0-5)
    # Teams that score AND concede = more likely O1.5
    score += 3  # neutral baseline for VFL
    
    # Layer 11: Consistency penalty (-5 to 0)
    # Penalize if either team has high variance
    if h_prof[0] < 0.60 or a_prof[0] < 0.60:
        score -= 5
    
    # Layer 12: ELITE exclusion penalty (-10 to 0)  
    # If matchup has ≥7 games but ISN'T in ELITE, that's a warning
    if key not in ELITE and min_games >= 50:
        score -= 5
    
    return max(0, min(100, round(score)))

def fetch_upcoming():
    now_wat = datetime.now(WAT)
    now_ms = int(now_wat.timestamp() * 1000)
    window_ms = 30 * 60 * 1000
    
    all_matches = []
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
                    
                    start_dt = datetime.fromtimestamp(start_time / 1000, tz=WAT)
                    all_matches.append({
                        "home": home, "away": away,
                        "league": lg["name"], "lg_code": lg_code,
                        "start_time": start_dt.strftime("%H:%M"),
                        "event_id": ev.get("eventId", ""),
                    })
        except Exception as e:
            print(f"Error {lg['name']}: {e}")
        time.sleep(0.3)
    
    return all_matches

def main():
    now = datetime.now(WAT)
    print(f"VFL 12-Layer v7 — {now.strftime('%Y-%m-%d %H:%M')} WAT")
    
    matches = fetch_upcoming()
    if not matches:
        print("No upcoming matches. Silent exit.")
        return
    
    # Score all matches
    scored = []
    for m in matches:
        s = score_match(m["home"], m["away"])
        key = f"{m['home']}v{m['away']}"
        in_elite = key in ELITE
        tier = ELITE[key][1] if in_elite else "-"
        scored.append({**m, "score": s, "in_elite": in_elite, "tier": tier})
    
    # Only send ULTRA tier (score ≥85)
    ultra = [s for s in scored if s["score"] >= 85]
    ultra.sort(key=lambda x: -x["score"])
    
    if not ultra:
        print(f"No ULTRA picks (scored {len(scored)} matches, max score: {max(s['score'] for s in scored)}). Silent exit.")
        return
    
    # Dedup
    dedup = load_dedup()
    picks_str = ",".join(f"{p['home']}v{p['away']}_{p['start_time']}" for p in ultra)
    if is_duplicate(picks_str, dedup):
        print("Duplicate. Silent exit.")
        save_dedup(dedup)
        return
    save_dedup(dedup)
    
    # Message
    lines = [f"🧠 *VFL 12-LAYER ULTRA PICKS* — {now.strftime('%H:%M')} WAT"]
    lines.append(f"_Score ≥85/100 — {len(ultra)} picks_\n")
    
    for p in ultra[:15]:
        tier_icon = "💎" if p["tier"] == "D" else "🥇" if p["tier"] == "G" else "📊"
        lines.append(f"  {tier_icon} {p['home']} vs {p['away']} — O1.5 *[{p['score']}]*  [{p['league']} {p['start_time']}]")
    
    lines.append(f"\n_Engine: 12-layer scoring | ULTRA threshold: 85/100_")
    lines.append("_@Virtualonimix\\_bot — Layer2 v7_")
    
    msg = "\n".join(lines)
    print(msg)
    
    if send_telegram(msg):
        print(f"\n✅ Sent {len(ultra)} ULTRA picks")
    else:
        print("\n❌ Send failed")

if __name__ == "__main__":
    main()
