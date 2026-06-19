"""
WC 2026 Fantasy Pool — Streamlit Dashboard
==========================================
Deploy: push to GitHub → share.streamlit.io → connect repo → add secret
Local:  streamlit run app.py
Secret: FOOTBALL_API_TOKEN = "your_token"
"""

import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timezone, date as dt_date
from collections import defaultdict

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG — must be first Streamlit call
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WC 2026 Fantasy Pool",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# CSS — pixel-faithful to the original HTML design
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --ag:    #007B63;
  --ag-h:  #006652;
  --ag5:   #E6F2F0;
  --ag10:  #CCE5E1;
  --wh:    #FFFFFF;
  --le:    #FEF8F3;
  --ecru:  #CAC2BA;
  --e100:  #E0DBD4;
  --e300:  #B8AEA5;
  --e600:  #6B635C;
  --grey:  #55585A;
  --sb:    #333333;
  --mint:  #BAFFC5;
  --saxe:  #395878;
  --ice:   #E3ECF6;
  --coral: #F67A6D;
  --c100:  #FFE9DE;
  --gold:  #B8960C;
}

/* ── Base ── */
.stApp { background: var(--le) !important; font-family: "Inter", "Segoe UI", Arial, sans-serif; font-size: 14px; line-height: 1.5; }
.stApp > header { display: none !important; }
#MainMenu, footer { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Remove default Streamlit padding ── */
.block-container { padding-top: 0 !important; padding-bottom: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* ── Header bar ── */
.wc-header {
  background: var(--ag);
  padding: 0 20px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2px solid #005e4c;
  margin-bottom: 0;
}
.wc-header-logo {
  font-family: "EB Garamond", "Times New Roman", serif;
  font-size: 20px;
  color: white;
  letter-spacing: 1px;
  font-weight: 500;
}
.wc-header-right {
  font-size: 11px;
  color: rgba(255,255,255,0.65);
  text-align: right;
  line-height: 1.5;
}
.wc-header-right strong { color: rgba(255,255,255,0.9); }

/* ── Status bar ── */
.wc-status {
  background: var(--ag5);
  border-bottom: 1px solid var(--ag10);
  padding: 4px 20px;
  font-size: 11px;
  color: var(--grey);
  display: flex;
  align-items: center;
  gap: 10px;
}
.wc-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--ag); display: inline-block;
  box-shadow: 0 0 5px var(--ag);
}
.wc-status-note { color: var(--ag); font-weight: 600; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: white !important;
  border-bottom: 2px solid var(--ag) !important;
  padding: 0 12px;
  gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--grey) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  padding: 8px 14px !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--ag) !important; }
.stTabs [aria-selected="true"] {
  color: var(--ag) !important;
  border-bottom: 2px solid var(--ag) !important;
  font-weight: 700 !important;
  background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
  padding: 0 !important;
  background: var(--le) !important;
}

/* ── Podium ── */
.podium-wrap {
  display: flex; gap: 10px; margin: 20px 0 16px; align-items: flex-end;
}
.pod {
  flex: 1; border-radius: 3px; padding: 16px 12px;
  text-align: center; border: 1px solid var(--e100);
  background: white; cursor: pointer;
  transition: box-shadow .15s;
}
.pod:hover { box-shadow: 0 4px 16px rgba(0,123,99,.12); }
.pod-gold {
  background: var(--ag); border-color: var(--ag);
  padding-top: 22px; order: 2;
}
.pod-silver { order: 1; }
.pod-bronze { order: 3; }
.pod-medal { font-size: 22px; margin-bottom: 6px; }
.pod-name {
  font-size: 11px; font-weight: 700;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  margin-bottom: 4px; color: var(--sb);
}
.pod-gold .pod-name { color: white; }
.pod-score {
  font-family: "EB Garamond", serif;
  font-size: 36px; line-height: 1;
  color: var(--ag); font-weight: 500;
}
.pod-gold .pod-score { color: var(--mint); }
.pod-pts { font-size: 10px; color: var(--grey); margin-top: 2px; }
.pod-gold .pod-pts { color: rgba(255,255,255,.6); }
.pod-picks { font-size: 11px; color: var(--e300); margin-top: 5px; line-height: 1.6; }
.pod-gold .pod-picks { color: rgba(255,255,255,.45); }

/* ── Search box ── */
.stTextInput input {
  background: white !important;
  border: 1px solid var(--e100) !important;
  border-radius: 3px !important;
  font-size: 12px !important;
  color: var(--sb) !important;
}
.stTextInput input:focus { border-color: var(--ag) !important; box-shadow: none !important; }
.stTextInput label { font-size: 11px !important; color: var(--grey) !important; }

/* ── Leaderboard table ── */
.lb-table { width: 100%; border-collapse: collapse; }
.lb-table thead th {
  font-size: 12px; letter-spacing: .3px; text-transform: uppercase;
  color: var(--sb); padding: 9px 8px; border-bottom: 2px solid var(--ag);
  font-weight: 700; background: white; text-align: left;
  position: sticky; top: 0; z-index: 1;
}
.lb-table thead th.r { text-align: right; }
.lb-row {
  border-bottom: 1px solid rgba(224,219,212,.6);
  transition: background .1s;
}
.lb-row:hover { background: var(--ag5); }
.lb-row.self { border-left: 3px solid var(--ag); background: var(--ag5); }
.lb-row.ai   { border-left: 3px solid var(--saxe); background: var(--ice); font-style: italic; }
.lb-row td   { padding: 9px 8px; font-size: 13px; vertical-align: middle; line-height: 1.4; }
.rank  { font-size: 12px; color: var(--e300); font-weight: 600; width: 26px; }
.pname { font-weight: 700; color: var(--sb); font-size: 13px; }
.pname.ai { color: var(--saxe); }
.picks { font-size: 11px; color: var(--e300); line-height: 1.6; }
.stat  { font-size: 12px; color: var(--grey); text-align: right; font-weight: 500; }
.score { font-size: 15px; font-weight: 700; text-align: right; color: var(--ag); }
.score.neg  { color: var(--coral); }
.score.zero { color: var(--e300); }
.yc  { color: #9a7d0a; font-weight: 700; }
.rc  { color: #c0392b; font-weight: 700; }
.ai-hdr td {
  padding: 5px 8px; font-size: 9px; letter-spacing: 1.5px;
  text-transform: uppercase; color: var(--saxe); font-weight: 700;
  background: var(--ice); border-bottom: 1px solid #c5d8ee;
}
.human-hdr td {
  padding: 5px 8px; font-size: 9px; letter-spacing: 1.5px;
  text-transform: uppercase; color: var(--grey); font-weight: 700;
  background: var(--le); border-bottom: 2px solid var(--ag);
}

/* ── Group cards ── */
.groups-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 20px;
}
.group-card {
  background: white; border: 1px solid var(--e100);
  border-radius: 3px; overflow: hidden; margin-bottom: 0;
}
.group-hdr {
  background: var(--ag); padding: 8px 14px;
  display: flex; justify-content: space-between; align-items: center;
}
.group-hdr span { font-size: 12px; font-weight: 700; color: white; letter-spacing: 0.5px; text-transform: uppercase; }
.group-hdr small { font-size: 10px; color: rgba(255,255,255,.6); }
.grp-table { width: 100%; border-collapse: collapse; }
.grp-table thead th {
  font-size: 11px; letter-spacing: 0.5px; text-transform: uppercase;
  color: var(--grey); padding: 7px 12px; border-bottom: 1px solid var(--e100);
  font-weight: 700; text-align: left;
}
.grp-table thead th.r { text-align: right; }
.grp-table tbody tr { border-bottom: 1px solid rgba(224,219,212,.4); transition: background .1s; }
.grp-table tbody tr:last-child { border-bottom: none; }
.grp-table tbody tr:hover { background: var(--ag5); }
.grp-table tbody td { padding: 7px 10px; font-size: 12px; vertical-align: middle; }
.grp-table tbody tr.myteam { background: var(--ag5); }
.fantasy-score { font-weight: 700; color: var(--ag); text-align: right; }
.fantasy-neg   { color: var(--coral) !important; font-weight: 700; text-align: right; }
.fantasy-zero  { color: var(--e300) !important; font-weight: 700; text-align: right; }
.stat-mini     { font-size: 12px; color: var(--grey); text-align: right; font-weight: 500; }

/* ── Fixture cards ── */
.fx-day-label {
  font-size: 10px; color: var(--grey); font-weight: 700;
  letter-spacing: .5px; text-transform: uppercase;
  margin: 14px 0 6px; padding-bottom: 4px;
  border-bottom: 1px solid var(--e100);
}
.fx-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap: 8px; margin-bottom: 4px; }
.fx-card {
  background: white; border: 1px solid var(--e100);
  border-radius: 3px; padding: 10px 14px;
}
.fx-card.played  { border-left: 3px solid var(--ag); }
.fx-card.live    { border-left: 3px solid var(--coral); background: #fff8f7; }
.fx-card.today   { border-left: 3px solid var(--gold); background: #fffbf0; }
.fx-card.upcoming{ border-left: 3px solid var(--e100); }
.fx-top { display: flex; justify-content: space-between; font-size: 11px; color: var(--grey); margin-bottom: 6px; }
.fx-grp { font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }
.fx-teams { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
.fx-team { font-size: 13px; font-weight: 600; color: var(--sb); flex: 1; }
.fx-team.away { text-align: right; }
.fx-score {
  font-family: "EB Garamond", serif;
  font-size: 20px; font-weight: 500; color: var(--ag);
  text-align: center; min-width: 50px; line-height: 1;
}
.fx-score.tbd { font-size: 12px; color: var(--e300); font-family: inherit; font-weight: 400; }
.fx-score.live-score { color: var(--coral); }
.fx-bottom { display: flex; justify-content: space-between; margin-top: 5px; font-size: 11px; }
.fx-venue { color: var(--e300); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 180px; }
.fx-status { color: var(--grey); font-weight: 600; }
.fx-notable { font-size: 9px; color: var(--coral); margin-top: 3px; font-weight: 500; }

/* ── Filter buttons ── */
.stRadio [data-testid="stRadio"] label { font-size: 12px !important; }
.stSelectbox select { font-size: 12px !important; }
[data-testid="stHorizontalBlock"] { gap: 6px !important; }

/* ── Breakdown expander ── */
.breakdown-item {
  display: flex; justify-content: space-between;
  padding: 5px 10px; font-size: 12px;
  border-bottom: 1px solid rgba(224,219,212,.5);
  color: var(--grey);
}
.breakdown-item.pos span:last-child { color: var(--ag); font-weight: 700; }
.breakdown-item.neg span:last-child { color: var(--coral); font-weight: 700; }
.breakdown-item.zero span:last-child { color: var(--e300); font-weight: 700; }

/* ── Scoring rules ── */
.scoring-section {
  background: white; border: 1px solid var(--e100);
  border-radius: 3px; padding: 14px 16px; margin-bottom: 10px;
}
.scoring-section h4 {
  font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
  color: var(--grey); font-weight: 700; padding-bottom: 8px;
  border-bottom: 2px solid var(--ag); margin-bottom: 10px;
}
.scoring-row {
  display: flex; justify-content: space-between;
  padding: 6px 0; border-bottom: 1px solid rgba(224,219,212,.5);
  font-size: 13px; color: var(--grey);
}
.scoring-row:last-child { border-bottom: none; }
.scoring-row .v { font-weight: 700; }
.vpos { color: var(--ag) !important; }
.vneg { color: var(--coral) !important; }
.vbon { color: var(--saxe) !important; }
.eg-box {
  background: var(--ag5); border: 1px solid var(--ag10);
  border-left: 3px solid var(--ag); border-radius: 3px;
  padding: 10px 12px; font-size: 11px; color: var(--grey); line-height: 1.8;
}
.eg-box strong { color: var(--ag); }

/* ── Streamlit overrides ── */
[data-testid="stMetric"] { display: none; }
.stSpinner > div { border-top-color: var(--ag) !important; }
div[data-testid="stExpander"] {
  border: 1px solid var(--e100) !important;
  border-radius: 3px !important;
  background: white !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# STATIC DATA
# ─────────────────────────────────────────────────────────────
PLAYERS = [
    {"id":1,  "name":"Vivek Dasani",      "picks":["Spain","Germany","Uruguay","Ecuador","Sweden","Norway","Ghana","Jordan"]},
    {"id":2,  "name":"Abhinna Mehta",     "picks":["Argentina","Germany","USA","South Korea","Qatar","Norway","Saudi Arabia","New Zealand"],"self":True},
    {"id":3,  "name":"Alice Darry",       "picks":["France","Germany","USA","Austria","Canada","Norway","Ghana","New Zealand"]},
    {"id":4,  "name":"Hallie Farber",     "picks":["England","Germany","USA","Ecuador","Sweden","Scotland","Panama","New Zealand"]},
    {"id":5,  "name":"Olha Svidrun",      "picks":["France","Germany","Switzerland","Australia","Sweden","Norway","South Africa","New Zealand"]},
    {"id":6,  "name":"Adrian Alcina",     "picks":["Spain","Morocco","Senegal","Egypt","Ivory Coast","Türkiye","Paraguay","Cape Verde"]},
    {"id":7,  "name":"Vishnu Kaushik",    "picks":["Spain","Germany","Japan","Ecuador","Algeria","Norway","South Africa","Uzbekistan"]},
    {"id":8,  "name":"Holly Dellar",      "picks":["England","Netherlands","USA","South Korea","Sweden","Türkiye","Saudi Arabia","New Zealand"]},
    {"id":9,  "name":"Saahil Sheth",      "picks":["France","Germany","Japan","Austria","Ivory Coast","Norway","Panama","Uzbekistan"]},
    {"id":10, "name":"Olivier Vervoot",   "picks":["France","Belgium","USA","South Korea","Sweden","Türkiye","South Africa","Uzbekistan"]},
    {"id":11, "name":"Mattia Baroni",     "picks":["Spain","Netherlands","Uruguay","Ecuador","Algeria","Norway","South Africa","Uzbekistan"]},
    {"id":12, "name":"George Kirkpatrick","picks":["France","Germany","Japan","South Korea","Ivory Coast","Türkiye","South Africa","Cape Verde"]},
    {"id":13, "name":"Justin Cheng",      "picks":["Spain","Germany","Switzerland","Ecuador","Canada","Norway","South Africa","Cape Verde"]},
    {"id":14, "name":"Matthijs Van",      "picks":["France","Netherlands","USA","Austria","Ivory Coast","Norway","South Africa","New Zealand"]},
    {"id":15, "name":"Olli Karjalainen",  "picks":["France","Germany","Mexico","Ecuador","Canada","Norway","South Africa","Uzbekistan"]},
    {"id":16, "name":"Ross Davidson",     "picks":["France","Belgium","Mexico","Egypt","Ivory Coast","Norway","Ghana","Cape Verde"]},
    {"id":17, "name":"Franco Luchisani",  "picks":["Brazil","Germany","Switzerland","Iran","Algeria","Türkiye","Panama","Uzbekistan"]},
    {"id":18, "name":"Arnaud Gayet",      "picks":["France","Netherlands","Switzerland","South Korea","Ivory Coast","Norway","Paraguay","New Zealand"]},
    {"id":19, "name":"Abishek Naguleswaran","picks":["France","Germany","USA","Australia","Canada","Norway","Saudi Arabia","Uzbekistan"]},
    {"id":20, "name":"Elodie Jeuffroy",   "picks":["France","Germany","Switzerland","Austria","Canada","Türkiye","Paraguay","New Zealand"]},
    {"id":21, "name":"Chris Hesford",     "picks":["England","Netherlands","USA","Ecuador","Sweden","Norway","Paraguay","Cape Verde"]},
    {"id":22, "name":"Amari Drysdale",    "picks":["France","Germany","Japan","Austria","Sweden","Norway","Paraguay","Uzbekistan"]},
    {"id":23, "name":"Sam Roberts",       "picks":["France","Germany","USA","South Korea","Ivory Coast","Norway","Paraguay","New Zealand"]},
    {"id":24, "name":"Charlie Newman",    "picks":["Spain","Germany","Switzerland","Ecuador","Canada","Türkiye","South Africa","Cape Verde"]},
    {"id":25, "name":"Shaun Collins",     "picks":["France","Morocco","USA","South Korea","Algeria","Czechia","Paraguay","New Zealand"]},
    {"id":26, "name":"Jesal Mistry",      "picks":["France","Germany","Mexico","Egypt","Ivory Coast","Norway","Ghana","New Zealand"]},
    {"id":27, "name":"Rishwith Reddy",    "picks":["France","Morocco","Uruguay","Egypt","Ivory Coast","Norway","Saudi Arabia","Curaçao"]},
    {"id":28, "name":"Kabir Mann",        "picks":["Spain","Germany","Japan","Austria","Sweden","Norway","South Africa","Cape Verde"]},
    {"id":29, "name":"Florian Feder",     "picks":["England","Germany","USA","Ecuador","Sweden","Norway","South Africa","Cape Verde"]},
    {"id":30, "name":"Jonathan Brown",    "picks":["Spain","Germany","Switzerland","South Korea","Canada","Türkiye","South Africa","New Zealand"]},
    {"id":31, "name":"Alexander S. Christensen","picks":["France","Netherlands","Senegal","South Korea","Canada","Türkiye","Paraguay","Cape Verde"]},
    {"id":32, "name":"Guillaume Droesch", "picks":["France","Germany","Japan","Austria","Canada","Türkiye","Ghana","Cape Verde"]},
    {"id":33, "name":"Brian O'Connell",   "picks":["France","Germany","USA","South Korea","Canada","Norway","Saudi Arabia","New Zealand"]},
    {"id":34, "name":"David Candlish",    "picks":["Spain","Germany","Japan","South Korea","Sweden","Norway","Ghana","Cape Verde"]},
    {"id":35, "name":"Jessica Davis",     "picks":["France","Germany","Japan","South Korea","Ivory Coast","Norway","Paraguay","Cape Verde"]},
    {"id":36, "name":"Philip Cuff",       "picks":["Argentina","Germany","Mexico","South Korea","Ivory Coast","Norway","Ghana","New Zealand"]},
    {"id":37, "name":"Henry Crowther",    "picks":["France","Germany","Japan","South Korea","Canada","Norway","South Africa","Cape Verde"]},
    {"id":38, "name":"Guy Boyd",          "picks":["Spain","Belgium","Uruguay","Egypt","Sweden","Scotland","Paraguay","Uzbekistan"]},
    {"id":39, "name":"Shalini Sultania",  "picks":["France","Germany","USA","Ecuador","Algeria","DR Congo","Paraguay","Jordan"]},
    {"id":40, "name":"Jad Bitar",         "picks":["Argentina","Morocco","Mexico","Egypt","Ivory Coast","Norway","Saudi Arabia","Jordan"]},
    {"id":41, "name":"Bruce Rennie",      "picks":["Spain","Germany","Japan","South Korea","Ivory Coast","Scotland","Paraguay","New Zealand"]},
    {"id":42, "name":"Jeremy Honeth",     "picks":["Argentina","Morocco","Uruguay","Ecuador","Canada","Norway","Paraguay","Uzbekistan"]},
    {"id":43, "name":"Stephen Lavoi",     "picks":["France","Colombia","USA","Ecuador","Canada","Scotland","Panama","New Zealand"]},
    {"id":44, "name":"Luc Carpinelli",    "picks":["France","Morocco","Switzerland","Egypt","Ivory Coast","Norway","Ghana","Uzbekistan"]},
    {"id":45, "name":"Riccardo Rattellini","picks":["Spain","Germany","USA","South Korea","Sweden","Norway","Ghana","Cape Verde"]},
    {"id":46, "name":"Leo Hotham",        "picks":["France","Belgium","Senegal","South Korea","Ivory Coast","Norway","Saudi Arabia","Uzbekistan"]},
    {"id":47, "name":"Sena Salman",       "picks":["France","Germany","Uruguay","Austria","Canada","Türkiye","Paraguay","Uzbekistan"]},
    {"id":48, "name":"Melissa Schoennagel","picks":["Portugal","Germany","Uruguay","Ecuador","Tunisia","DR Congo","Saudi Arabia","Uzbekistan"]},
    {"id":49, "name":"Sam Rawlings",      "picks":["England","Germany","USA","Egypt","Sweden","Scotland","Ghana","New Zealand"]},
    {"id":50, "name":"Joerund Holterud",  "picks":["France","Morocco","Switzerland","Egypt","Sweden","Norway","South Africa","New Zealand"]},
    {"id":51, "name":"Alex So",           "picks":["France","Netherlands","Japan","Australia","Algeria","Türkiye","Saudi Arabia","New Zealand"]},
    {"id":52, "name":"Sergio Gaya",       "picks":["Portugal","Germany","Senegal","Ecuador","Ivory Coast","Türkiye","Ghana","New Zealand"]},
    {"id":53, "name":"Richard Whitfield", "picks":["France","Germany","Switzerland","Austria","Canada","Norway","Paraguay","Uzbekistan"]},
    {"id":54, "name":"Karim Hussain",     "picks":["England","Germany","Japan","South Korea","Sweden","Scotland","Saudi Arabia","New Zealand"]},
    {"id":55, "name":"Karolina Shepanzyk","picks":["France","Germany","Uruguay","Ecuador","Sweden","Norway","Paraguay","Cape Verde"]},
    {"id":56, "name":"Bhavin Patel",      "picks":["France","Germany","Japan","Australia","Ivory Coast","Norway","Saudi Arabia","New Zealand"]},
    {"id":57, "name":"Jonathon Orr",      "picks":["France","Belgium","USA","Egypt","Ivory Coast","Türkiye","Ghana","Uzbekistan"]},
    {"id":58, "name":"Daniel Mayfield",   "picks":["Spain","Netherlands","Mexico","Ecuador","Sweden","Norway","Paraguay","New Zealand"]},
    {"id":59, "name":"Alexander Fyfe",    "picks":["Spain","Germany","USA","Ecuador","Canada","Türkiye","Paraguay","Uzbekistan"]},
    {"id":60, "name":"Tim Divietri",      "picks":["France","Netherlands","Switzerland","Ecuador","Ivory Coast","Türkiye","Saudi Arabia","New Zealand"]},
    {"id":61, "name":"Robert Pepper",     "picks":["Spain","Germany","Mexico","Ecuador","Tunisia","Türkiye","Ghana","Curaçao"]},
    {"id":62, "name":"Kai Aschick",       "picks":["France","Morocco","Japan","Austria","Sweden","Czechia","Ghana","New Zealand"]},
    {"id":63, "name":"Azmat Medov",       "picks":["Spain","Germany","Mexico","Iran","Algeria","Türkiye","South Africa","Jordan"]},
    {"id":64, "name":"Moritz Duembgen",   "picks":["Spain","Germany","Switzerland","Austria","Sweden","Norway","Ghana","New Zealand"]},
    {"id":65, "name":"🤖 ChatGPT",        "picks":["France","Germany","Uruguay","Austria","Sweden","Norway","Paraguay","Uzbekistan"],"ai":True},
    {"id":66, "name":"🤖 Google Gemini",  "picks":["France","Germany","Uruguay","Ecuador","Sweden","Norway","Paraguay","New Zealand"],"ai":True},
    {"id":67, "name":"🤖 Claude",         "picks":["Spain","Germany","USA","Ecuador","Canada","Norway","Paraguay","Uzbekistan"],"ai":True},
]

GROUPS = {
    "A":["Mexico","South Africa","South Korea","Czechia"],
    "B":["Canada","Bosnia & Herz.","Qatar","Switzerland"],
    "C":["Brazil","Morocco","Haiti","Scotland"],
    "D":["USA","Paraguay","Australia","Türkiye"],
    "E":["Germany","Curaçao","Ivory Coast","Ecuador"],
    "F":["Netherlands","Japan","Sweden","Tunisia"],
    "G":["Belgium","Egypt","Iran","New Zealand"],
    "H":["Spain","Cape Verde","Saudi Arabia","Uruguay"],
    "I":["France","Senegal","Iraq","Norway"],
    "J":["Argentina","Algeria","Austria","Jordan"],
    "K":["Portugal","DR Congo","Uzbekistan","Colombia"],
    "L":["England","Croatia","Ghana","Panama"],
}
FLAGS = {
    "Mexico":"🇲🇽","South Africa":"🇿🇦","South Korea":"🇰🇷","Czechia":"🇨🇿",
    "Canada":"🇨🇦","Bosnia & Herz.":"🇧🇦","Qatar":"🇶🇦","Switzerland":"🇨🇭",
    "Brazil":"🇧🇷","Morocco":"🇲🇦","Haiti":"🇭🇹","Scotland":"🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "USA":"🇺🇸","Paraguay":"🇵🇾","Australia":"🇦🇺","Türkiye":"🇹🇷",
    "Germany":"🇩🇪","Curaçao":"🇨🇼","Ivory Coast":"🇨🇮","Ecuador":"🇪🇨",
    "Netherlands":"🇳🇱","Japan":"🇯🇵","Sweden":"🇸🇪","Tunisia":"🇹🇳",
    "Belgium":"🇧🇪","Egypt":"🇪🇬","Iran":"🇮🇷","New Zealand":"🇳🇿",
    "Spain":"🇪🇸","Cape Verde":"🇨🇻","Saudi Arabia":"🇸🇦","Uruguay":"🇺🇾",
    "France":"🇫🇷","Senegal":"🇸🇳","Iraq":"🇮🇶","Norway":"🇳🇴",
    "Argentina":"🇦🇷","Algeria":"🇩🇿","Austria":"🇦🇹","Jordan":"🇯🇴",
    "Portugal":"🇵🇹","DR Congo":"🇨🇩","Uzbekistan":"🇺🇿","Colombia":"🇨🇴",
    "England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Croatia":"🇭🇷","Ghana":"🇬🇭","Panama":"🇵🇦",
}
NAME_MAP = {
    "United States":"USA","Korea Republic":"South Korea",
    "Côte d'Ivoire":"Ivory Coast","Cote d'Ivoire":"Ivory Coast",
    "Bosnia and Herzegovina":"Bosnia & Herz.",
    "Bosnia-Herzegovina":         "Bosnia & Herz.",
    "Curaçao":"Curaçao","Curacao":"Curaçao",
    "Czech Republic":"Czechia","Turkey":"Türkiye",
    "Congo DR":"DR Congo","Democratic Republic of Congo":"DR Congo",
    "Cape Verde Islands":"Cape Verde",
}
MY_TEAMS = {"Argentina","Germany","USA","South Korea","Qatar","Norway","Saudi Arabia","New Zealand"}

# Wikipedia group pages for card scraping
WIKI_GROUPS = {
    "A":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_A",
    "B":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_B",
    "C":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_C",
    "D":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_D",
    "E":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_E",
    "F":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_F",
    "G":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_G",
    "H":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_H",
    "I":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_I",
    "J":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_J",
    "K":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_K",
    "L":"https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_L",
}
CARD_ALTS = {"Yellow card", "Red card", "Yellow-red card"}
WIKI_UA   = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

def norm(n): return NAME_MAP.get(n, n)
def flag(n): return FLAGS.get(norm(n), "🏳️")
def fmt(n):
    if n is None: return "—"
    return str(int(n)) if n == int(n) else f"{n:.1f}"
def score_cls(s):
    if s > 0: return "score"
    if s < 0: return "score neg"
    return "score zero"
def get_group(t):
    for g, teams in GROUPS.items():
        if t in teams: return g
    return "?"
def today_str():
    d = datetime.now()
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{d.day} {months[d.month-1]}"

# ─────────────────────────────────────────────────────────────
# DATA FETCH — cached 5 min
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def scrape_cards():
    """Scrape yellow/red card data from Wikipedia group pages. Cached 5 min."""
    all_cards = {}
    for group, url in WIKI_GROUPS.items():
        try:
            r = requests.get(url, headers=WIKI_UA, timeout=10)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            boxes = soup.find_all("div", {"class": "footballbox"})
            lineup_tables = [
                t for t in soup.find_all("table")
                if len(t.find_all("img", {"alt": lambda a: a in CARD_ALTS})) > 0
                and "Manager:" in t.get_text()
                and len(t.find_all("tr")) > 10
            ]
            for tbl in lineup_tables:
                prev_box = None
                for box in boxes:
                    if box.sourceline < tbl.sourceline:
                        prev_box = box
                    else:
                        break
                if not prev_box:
                    continue
                home_th = prev_box.find("th", {"class": "fhome"})
                away_th = prev_box.find("th", {"class": "faway"})
                if not home_th or not away_th:
                    continue
                home_a = home_th.find("a")
                away_a = away_th.find("a")
                home_name = norm(home_a.get_text(strip=True) if home_a else home_th.get_text(strip=True))
                away_name = norm(away_a.get_text(strip=True) if away_a else away_th.get_text(strip=True))
                first_row = tbl.find("tr")
                if not first_row:
                    continue
                tds = first_row.find_all("td", recursive=False)
                if len(tds) < 3:
                    continue
                for team, td in [(home_name, tds[0]), (away_name, tds[2])]:
                    if team not in all_cards:
                        all_cards[team] = {"yc": 0, "rc": 0}
                    for img in td.find_all("img", {"alt": lambda a: a in CARD_ALTS}):
                        alt = img.get("alt", "")
                        if alt == "Yellow card":
                            all_cards[team]["yc"] += 1
                        elif alt in ("Red card", "Yellow-red card"):
                            all_cards[team]["rc"] += 1
        except Exception:
            continue
    return all_cards


@st.cache_data(ttl=300)
def fetch_data():
    try:
        token = st.secrets["FOOTBALL_API_TOKEN"]
    except Exception:
        token = "715a8137efc14ac0b72173f9572bc5a9"

    try:
        r = requests.get(
            "https://api.football-data.org/v4/competitions/WC/matches",
            headers={"X-Auth-Token": token}, timeout=15
        )
        r.raise_for_status()
        matches = r.json().get("matches", [])
    except Exception as e:
        return None, str(e)

    # Initialise ALL 48 nations (not just picked ones) so every team
    # shows correct stats in the Nation Scores tab
    all_nations = set(t for teams in GROUPS.values() for t in teams)
    all_picked  = set(t for p in PLAYERS for t in p["picks"])
    all_teams   = all_nations | all_picked
    scores = {t: {"score":0.0,"goals":0,"cs":0,"gd":0,"wins":0,"draws":0,"losses":0,"yc":0,"rc":0}
              for t in all_teams}

    finished = [m for m in matches if m["status"] == "FINISHED"]
    live      = [m for m in matches if m["status"] in ("IN_PLAY","PAUSED")]

    for m in finished:
        home = norm(m["homeTeam"]["name"])
        away = norm(m["awayTeam"]["name"])
        hg   = m["score"]["fullTime"]["home"] or 0
        ag   = m["score"]["fullTime"]["away"] or 0
        h_in = home in scores
        a_in = away in scores
        if not h_in and not a_in: continue
        if h_in: scores[home]["goals"] += hg
        if a_in: scores[away]["goals"] += ag
        if h_in and ag == 0: scores[home]["cs"] += 1
        if a_in and hg == 0: scores[away]["cs"] += 1
        if h_in: scores[home]["gd"] += (hg - ag)
        if a_in: scores[away]["gd"] += (ag - hg)
        if hg > ag:
            if h_in: scores[home]["wins"]   += 1
            if a_in: scores[away]["losses"] += 1
        elif ag > hg:
            if h_in: scores[home]["losses"] += 1
            if a_in: scores[away]["wins"]   += 1
        else:
            if h_in: scores[home]["draws"] += 1
            if a_in: scores[away]["draws"] += 1
        for b in m.get("bookings", []):
            t = norm((b.get("team") or {}).get("name", ""))
            if t not in scores: continue
            c = b.get("card", "")
            if c == "YELLOW_CARD": scores[t]["yc"] += 1
            elif c in ("RED_CARD","YELLOW_RED_CARD"): scores[t]["rc"] += 1

    for t, s in scores.items():
        pts  = s["goals"]*1.5 + s["cs"]*2.0 + s["wins"]*2.0
        pts += s["gd"] * 0.5
        pts -= s["yc"]*0.5 + s["rc"]*2.0
        s["score"] = round(pts, 1)

    player_scores = []
    for p in PLAYERS:
        total = 0.0; bd = {}
        for i, pick in enumerate(p["picks"]):
            s = scores.get(pick, {}).get("score", 0.0)
            total += s
            bd[f"P{i+1} · {pick}"] = s
        player_scores.append({**p, "total": round(total,1), "breakdown": bd})

    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    fx_list = []
    for m in matches:
        st_  = m["status"]
        played  = st_ == "FINISHED"
        is_live = st_ in ("IN_PLAY","PAUSED")
        hg = m["score"]["fullTime"]["home"]
        ag = m["score"]["fullTime"]["away"]
        ds = m.get("utcDate","")[:10]
        try:
            d = dt_date.fromisoformat(ds)
            dl = f"{d.day} {months[d.month-1]}"
        except: dl = ds
        grp = (m.get("group") or "?").replace("GROUP_","")
        fx_list.append({
            "date":dl,"group":grp,
            "home":norm(m["homeTeam"]["name"]),
            "away":norm(m["awayTeam"]["name"]),
            "homeScore":hg,"awayScore":ag,
            "venue":m.get("venue","") or "",
            "played":played,"live":is_live,
        })

    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    # Merge Wikipedia card data into nation scores
    card_data = scrape_cards()
    for team, cards in card_data.items():
        if team in scores:
            scores[team]["yc"] = cards.get("yc", 0)
            scores[team]["rc"] = cards.get("rc", 0)
    # Recompute fantasy points with cards included
    for t, s in scores.items():
        pts  = s["goals"]*1.5 + s["cs"]*2.0 + s["wins"]*2.0
        pts += s["gd"] * 0.5
        pts -= s["yc"]*0.5 + s["rc"]*2.0
        s["score"] = round(pts, 1)
    # Recompute player scores with updated nation scores
    player_scores = []
    for p in PLAYERS:
        total = 0.0; bd = {}
        for i, pick in enumerate(p["picks"]):
            sv = scores.get(pick, {}).get("score", 0.0)
            total += sv
            bd[f"P{i+1} · {pick}"] = sv
        player_scores.append({**p, "total": round(total,1), "breakdown": bd})

    return {
        "ns": scores, "ps": player_scores, "fx": fx_list,
        "played": len(finished), "live_count": len(live),
        "total": len(matches), "updated": now,
    }, None

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def pick_stats(p, ns):
    g=mp=w=d=l=cs=gd=yc=rc=0
    for t in p["picks"]:
        s = ns.get(t, {})
        g  += s.get("goals",0)
        mp += s.get("wins",0)+s.get("draws",0)+s.get("losses",0)
        w  += s.get("wins",0);  d  += s.get("draws",0);  l  += s.get("losses",0)
        cs += s.get("cs",0);    gd += s.get("gd",0)
        yc += s.get("yc",0);    rc += s.get("rc",0)
    return g,mp,w,d,l,cs,gd,yc,rc

def lb_row_html(rank, p, ns, ai=False):
    g,mp,w,d,l,cs,gd,yc,rc = pick_stats(p, ns)
    sc = p["total"]
    row_cls = "ai" if ai else ("self" if p.get("self") else "")
    rank_str = "—" if ai else str(rank)
    name_cls = "pname ai" if ai else "pname"
    star = " ★" if p.get("self") else ""
    yc_html = f'<span class="yc">{yc}🟨</span>' if yc else ""
    rc_html = f'<span class="rc">{rc}🟥</span>' if rc else ""
    cards = (yc_html + " " + rc_html).strip() or "—"
    picks_str = " · ".join(p["picks"])
    return f"""<tr class="lb-row {row_cls}">
      <td class="rank">{rank_str}</td>
      <td class="{name_cls}">{p['name']}{star}</td>
      <td class="picks">{picks_str}</td>
      <td class="stat">{g or '—'}</td>
      <td class="stat">{mp or '—'}</td>
      <td class="stat">{w or '—'}</td>
      <td class="stat">{d or '—'}</td>
      <td class="stat">{l or '—'}</td>
      <td class="stat">{cs or '—'}</td>
      <td class="stat">{gd if gd else '—'}</td>
      <td class="stat">{cards}</td>
      <td class="{score_cls(sc)}">{fmt(sc)}</td>
    </tr>"""

# ─────────────────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────────────────
DATA, err = fetch_data()

# ── Header ──
updated = DATA["updated"] if DATA else "—"
status_txt = f"{DATA['played']}/{DATA['total']} matches completed" if DATA else "Error loading data"
live_txt = f" · 🔴 {DATA['live_count']} LIVE" if DATA and DATA['live_count'] else ""

st.markdown(f"""
<div class="wc-header">
  <div class="wc-header-logo">⚽ The Unofficial World Cup Pool</div>
  <div class="wc-header-right">
    <strong>{updated}</strong><br>Auto-refreshes every 5 min
  </div>
</div>
<div class="wc-status">
  <span class="wc-dot"></span>
  <span>{status_txt}{live_txt}</span>
  <span class="wc-status-note">Data from football-data.org</span>
</div>
""", unsafe_allow_html=True)

if err:
    st.error(f"⚠️ Could not load data: {err}")
    st.stop()

ns = DATA["ns"]
ps = DATA["ps"]
fx = DATA["fx"]
humans = sorted([p for p in ps if not p.get("ai")], key=lambda x: x["total"], reverse=True)
ais    = sorted([p for p in ps if p.get("ai")],     key=lambda x: x["total"], reverse=True)

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏅  Leaderboard", "🌍  Nation Scores", "📅  Fixtures", "ℹ️  Scoring Rules"
])

# ══════════════════════════════════════════════ TAB 1
with tab1:
    st.markdown('<div style="padding:0 20px">', unsafe_allow_html=True)

    # ── Podium ──
    if len(humans) >= 3:
        p1,p2,p3 = humans[0], humans[1], humans[2]
        def pod_picks(p): return " · ".join(p["picks"])
        st.markdown(f"""
        <div class="podium-wrap">
          <div class="pod pod-silver">
            <div class="pod-medal">🥈</div>
            <div class="pod-name">{p2['name']}</div>
            <div class="pod-score">{fmt(p2['total'])}</div>
            <div class="pod-pts">pts</div>
            <div class="pod-picks">{pod_picks(p2)}</div>
          </div>
          <div class="pod pod-gold">
            <div class="pod-medal">🥇</div>
            <div class="pod-name">{p1['name']}</div>
            <div class="pod-score">{fmt(p1['total'])}</div>
            <div class="pod-pts">pts</div>
            <div class="pod-picks">{pod_picks(p1)}</div>
          </div>
          <div class="pod pod-bronze">
            <div class="pod-medal">🥉</div>
            <div class="pod-name">{p3['name']}</div>
            <div class="pod-score">{fmt(p3['total'])}</div>
            <div class="pod-pts">pts</div>
            <div class="pod-picks">{pod_picks(p3)}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Search ──
    search = st.text_input("", placeholder="🔍  Search player…", label_visibility="collapsed")

    # ── Table ──
    ai_rows    = "".join(lb_row_html(0, p, ns, ai=True) for p in ais)
    human_rows = "".join(
        lb_row_html(i+1, p, ns)
        for i, p in enumerate(humans)
        if not search or search.lower() in p["name"].lower()
    )
    st.markdown(f"""
    <table class="lb-table">
      <thead><tr>
        <th style="width:28px">#</th>
        <th>Player</th>
        <th>Picks (P1→P8)</th>
        <th class="r" style="width:40px">⚽</th>
        <th class="r" style="width:36px">MP</th>
        <th class="r" style="width:32px">W</th>
        <th class="r" style="width:32px">D</th>
        <th class="r" style="width:32px">L</th>
        <th class="r" style="width:32px">CS</th>
        <th class="r" style="width:32px">GD</th>
        <th class="r" style="width:52px">🟨🟥</th>
        <th class="r" style="width:58px">Score</th>
      </tr></thead>
      <tbody>
        <tr class="ai-hdr"><td colspan="12">🤖 AI Benchmarks</td></tr>
        {ai_rows}
        <tr class="human-hdr"><td colspan="12">👤 Players — Ranked</td></tr>
        {human_rows}
      </tbody>
    </table>
    """, unsafe_allow_html=True)

    # ── Breakdown expander ──
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📊 Score breakdown by pick"):
        sel = st.selectbox("Player", [p["name"] for p in humans], label_visibility="collapsed")
        player = next((p for p in humans if p["name"] == sel), None)
        if player:
            items = list(player["breakdown"].items())
            cols  = st.columns(4)
            for i, (k, v) in enumerate(items):
                cls = "pos" if v > 0 else ("neg" if v < 0 else "zero")
                with cols[i % 4]:
                    color = "#007B63" if v > 0 else ("#F67A6D" if v < 0 else "#B8AEA5")
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #E0DBD4;border-radius:3px;
                                padding:10px;text-align:center;margin-bottom:8px">
                      <div style="font-size:10px;color:#55585A;margin-bottom:4px">{k}</div>
                      <div style="font-size:22px;font-weight:700;color:{color};line-height:1">{fmt(v)}</div>
                      <div style="font-size:9px;color:#B8AEA5;margin-top:2px">pts</div>
                    </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════ TAB 2
with tab2:
    st.markdown('<div style="padding:4px 20px 0">', unsafe_allow_html=True)
    gf = st.selectbox("Group", ["All Groups"] + [f"Group {g}" for g in sorted(GROUPS.keys())],
                      label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    groups_show = list(GROUPS.keys()) if gf == "All Groups" else [gf.replace("Group ","")]

    # Build all group cards then wrap in grid
    all_group_cards_html = ""
    for g in groups_show:
        teams = GROUPS[g]
        sorted_t = sorted(teams, key=lambda t: ns.get(t,{}).get("score",0), reverse=True)
        played_count = sum(1 for t in teams if ns.get(t,{}).get("wins",0)+ns.get(t,{}).get("draws",0)+ns.get(t,{}).get("losses",0) > 0)
        rows_html = ""
        for t in sorted_t:
            s = ns.get(t, {})
            played = bool(s.get("wins",0)+s.get("draws",0)+s.get("losses",0))
            sc = s.get("score",0)
            sc_cls = "fantasy-score" if sc >= 0 else "fantasy-neg"
            is_my = t in MY_TEAMS
            yc_style = 'style="color:#9a7d0a;font-weight:700"' if s.get("yc",0) else ""
            rc_style = 'style="color:#c0392b;font-weight:700"' if s.get("rc",0) else ""
            rows_html += f"""<tr{"class='myteam'" if is_my else ""}>
              <td style="color:#000000;font-weight:600"><span style="font-size:16px;margin-right:6px">{flag(t)}</span>{t}{"  ★" if is_my else ""}</td>
              <td class="stat-mini">{"—" if not played else s.get("goals",0)}</td>
              <td class="stat-mini">{"—" if not played else s.get("cs",0)}</td>
              <td class="stat-mini">{"—" if not played else s.get("gd",0)}</td>
              <td class="stat-mini" {yc_style}>{"—" if not played else s.get("yc",0)}</td>
              <td class="stat-mini" {rc_style}>{"—" if not played else s.get("rc",0)}</td>
              <td class="{sc_cls}">{"—" if not played else fmt(sc)}</td>
            </tr>"""
        all_group_cards_html += f"""
        <div class="group-card">
          <div class="group-hdr">
            <span>Group {g}</span>
            <small>{played_count}/{len(teams)} played</small>
          </div>
          <table class="grp-table">
            <thead><tr>
              <th>Team</th>
              <th class="r">Goals</th><th class="r">CS</th><th class="r">GD</th>
              <th class="r" style="color:#c8a800">🟨</th>
              <th class="r" style="color:#c0392b">🟥</th>
              <th class="r" style="color:#BAFFC5;background:#007B63;padding:4px 10px;border-radius:2px">Fantasy</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>"""

    # Render all cards inside the 2-column grid
    st.markdown(f'<div class="groups-grid">{all_group_cards_html}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════ TAB 3
with tab3:
    st.markdown('<div style="padding:0 20px">', unsafe_allow_html=True)
    ff = st.radio("", ["All","Played","Upcoming","My Teams ★"], horizontal=True,
                  label_visibility="collapsed")
    filtered = fx
    if ff == "Played":       filtered = [f for f in fx if f["played"]]
    elif ff == "Upcoming":   filtered = [f for f in fx if not f["played"] and not f["live"]]
    elif ff == "My Teams ★": filtered = [f for f in fx if f["home"] in MY_TEAMS or f["away"] in MY_TEAMS]

    by_date = defaultdict(list)
    for f in filtered:
        by_date[f["date"]].append(f)
    today = today_str()

    for date, matches in by_date.items():
        is_today = date == today
        label = f"📍 {date} — Today" if is_today else date
        cards_html = ""
        for m in matches:
            hMy = m["home"] in MY_TEAMS
            aMy = m["away"] in MY_TEAMS
            if m["live"]:   cls = "live"
            elif m["played"]: cls = "played"
            elif is_today:  cls = "today"
            else:           cls = "upcoming"
            if m["played"]:
                score_html = f'<div class="fx-score">{m["homeScore"]}–{m["awayScore"]}</div>'
                status = "FT"
            elif m["live"]:
                score_html = '<div class="fx-score live-score">🔴</div>'
                status = "LIVE"
            else:
                score_html = '<div class="fx-score tbd">vs</div>'
                status = "Upcoming"
            cards_html += f"""
            <div class="fx-card {cls}">
              <div class="fx-top">
                <span class="fx-grp">Group {m['group']}</span>
                <span>{m['date']}</span>
              </div>
              <div class="fx-teams">
                <div class="fx-team">{flag(m['home'])} {m['home']}{"  ★" if hMy else ""}</div>
                {score_html}
                <div class="fx-team away">{m['away']} {flag(m['away'])}{"  ★" if aMy else ""}</div>
              </div>
              <div class="fx-bottom">
                <span class="fx-venue">{m.get('venue','')}</span>
                <span class="fx-status">{status}</span>
              </div>
            </div>"""
        st.markdown(f'<div class="fx-day-label">{label}</div><div class="fx-grid">{cards_html}</div>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════ TAB 4
with tab4:
    st.markdown('<div style="padding:20px">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="scoring-section">
          <h4>Per Match</h4>
          <div class="scoring-row"><span>Goal scored</span><span class="v vpos">+1.5 pts</span></div>
          <div class="scoring-row"><span>Clean sheet</span><span class="v vpos">+2 pts</span></div>
          <div class="scoring-row"><span>Match win</span><span class="v vpos">+2 pts</span></div>
          <div class="scoring-row"><span>Positive GD (per goal)</span><span class="v vpos">+0.5 pt</span></div>
          <div class="scoring-row"><span>Yellow card</span><span class="v vneg">−0.5 pt</span></div>
          <div class="scoring-row"><span>Red card</span><span class="v vneg">−2 pts</span></div>
        </div>
        <div class="scoring-section">
          <h4>Individual Awards (end of tournament)</h4>
          <div class="scoring-row"><span>Player of Tournament</span><span class="v vbon">+15 pts</span></div>
          <div class="scoring-row"><span>Golden Boot</span><span class="v vbon">+12 pts</span></div>
          <div class="scoring-row"><span>Golden Glove</span><span class="v vbon">+10 pts</span></div>
          <div class="scoring-row"><span>Best Young Player</span><span class="v vbon">+8 pts</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="scoring-section">
          <h4>Knockout Stage Bonuses</h4>
          <div class="scoring-row"><span>Round of 32</span><span class="v vbon">+2.5 pts</span></div>
          <div class="scoring-row"><span>Round of 16</span><span class="v vbon">+5 pts</span></div>
          <div class="scoring-row"><span>Quarter-final</span><span class="v vbon">+7.5 pts</span></div>
          <div class="scoring-row"><span>Semi-final</span><span class="v vbon">+10 pts</span></div>
          <div class="scoring-row"><span>Final (runners-up)</span><span class="v vbon">+15 pts</span></div>
          <div class="scoring-row"><span>Champions 🏆</span><span class="v vbon">+25 pts</span></div>
        </div>
        <div class="eg-box">
          3–0 win by your team:<br>
          <strong>Goals +4.5 · CS +2 · GD +1.5 · Win +2 = 10 pts</strong><br><br>
          Quarter-final + 2 yellow cards:<br>
          <strong>QF +7.5 − 1 pt cards = +6.5 pts</strong>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)