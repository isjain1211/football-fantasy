"""
WC 2026 Fantasy Pool — Streamlit Dashboard
==========================================
Deploy to Streamlit Cloud:
  1. Push this repo to GitHub
  2. Go to share.streamlit.io
  3. Connect your GitHub repo
  4. Set FOOTBALL_API_TOKEN in Streamlit secrets
  5. Done — anyone with the URL sees live scores

Local dev:
  pip install streamlit requests
  streamlit run app.py
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WC 2026 Fantasy Pool",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS — matches the original green/cream aesthetic
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Main background */
  .stApp { background-color: #FEF8F3; }

  /* Hide streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: white;
    border: 1px solid #E0DBD4;
    border-radius: 6px;
    padding: 12px 16px;
  }
  [data-testid="metric-container"] label {
    color: #55585A !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #007B63 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
  }

  /* Dataframe styling */
  [data-testid="stDataFrame"] { border: 1px solid #E0DBD4; border-radius: 6px; }

  /* Tab styling */
  .stTabs [data-baseweb="tab-list"] {
    background: white;
    border-bottom: 2px solid #007B63;
    gap: 0;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #55585A;
    font-weight: 500;
    padding: 8px 16px;
    border-bottom: 2px solid transparent;
  }
  .stTabs [aria-selected="true"] {
    color: #007B63 !important;
    border-bottom: 2px solid #007B63 !important;
    background: transparent !important;
  }

  /* Header banner */
  .header-banner {
    background: #007B63;
    color: white;
    padding: 14px 20px;
    border-radius: 6px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .header-title {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .header-sub { font-size: 11px; opacity: 0.75; margin-top: 2px; }

  /* Podium cards */
  .podium-gold {
    background: #007B63; color: white;
    padding: 20px; border-radius: 8px; text-align: center;
  }
  .podium-silver, .podium-bronze {
    background: white; border: 1px solid #E0DBD4;
    padding: 16px; border-radius: 8px; text-align: center;
  }
  .podium-score {
    font-size: 36px; font-weight: 800; line-height: 1;
  }
  .podium-name { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
  .podium-picks { font-size: 10px; opacity: 0.7; margin-top: 4px; }

  /* Nation card */
  .nation-card {
    background: white; border: 1px solid #E0DBD4;
    border-radius: 6px; padding: 10px 14px;
    margin-bottom: 6px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .nation-card.myteam { border-left: 3px solid #007B63; background: #E6F2F0; }

  /* Status pill */
  .live-pill {
    background: #FFE9DE; color: #b85a50;
    padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700;
  }
  .ok-pill {
    background: #E6F2F0; color: #007B63;
    padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700;
  }

  /* Fixture card */
  .fixture-card {
    background: white; border: 1px solid #E0DBD4;
    border-radius: 6px; padding: 10px 14px; margin-bottom: 6px;
  }
  .fixture-card.played { border-left: 3px solid #007B63; }
  .fixture-card.live   { border-left: 3px solid #F67A6D; background: #fff5f5; }
  .fixture-card.upcoming { border-left: 3px solid #E0DBD4; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# STATIC DATA
# ─────────────────────────────────────────────────────────────
PLAYERS = [
    {"id":1,  "name":"Vivek Dasani",      "picks":["Spain","Germany","Uruguay","Ecuador","Sweden","Norway","Ghana","Jordan"]},
    {"id":2,  "name":"Abhinna Mehta",     "picks":["Argentina","Germany","USA","South Korea","Qatar","Norway","Saudi Arabia","New Zealand"], "self":True},
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
    {"id":65, "name":"🤖 ChatGPT",        "picks":["France","Germany","Uruguay","Austria","Sweden","Norway","Paraguay","Uzbekistan"], "ai":True},
    {"id":66, "name":"🤖 Google Gemini",  "picks":["France","Germany","Uruguay","Ecuador","Sweden","Norway","Paraguay","New Zealand"], "ai":True},
    {"id":67, "name":"🤖 Claude",         "picks":["Spain","Germany","USA","Ecuador","Canada","Norway","Paraguay","Uzbekistan"], "ai":True},
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
    "Curaçao":"Curaçao","Curacao":"Curaçao",
    "Czech Republic":"Czechia","Turkey":"Türkiye",
    "Congo DR":"DR Congo","Democratic Republic of Congo":"DR Congo",
}

MY_TEAMS = {"Argentina","Germany","USA","South Korea","Qatar","Norway","Saudi Arabia","New Zealand"}

def norm(name): return NAME_MAP.get(name, name)
def flag(name): return FLAGS.get(norm(name), "🏳️")
def fmt(n): return "—" if n is None else (str(int(n)) if n == int(n) else f"{n:.1f}")

# ─────────────────────────────────────────────────────────────
# DATA FETCHING — cached for 5 minutes so every visitor
# gets fresh data without hammering the API
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)  # refresh every 5 minutes
def fetch_all_data():
    """Fetch all WC 2026 data from football-data.org and compute fantasy scores."""

    # Get API token from Streamlit secrets (set in Streamlit Cloud dashboard)
    # For local dev: create .streamlit/secrets.toml with:
    #   FOOTBALL_API_TOKEN = "your_token_here"
    try:
        token = st.secrets["FOOTBALL_API_TOKEN"]
    except Exception:
        token = "715a8137efc14ac0b72173f9572bc5a9"  # fallback for local dev

    headers = {"X-Auth-Token": token}
    base    = "https://api.football-data.org/v4"

    try:
        r = requests.get(f"{base}/competitions/WC/matches", headers=headers, timeout=15)
        r.raise_for_status()
        matches = r.json().get("matches", [])
    except Exception as e:
        st.error(f"API fetch failed: {e}")
        return None

    # ── collect all picked teams ──
    all_picked = set(t for p in PLAYERS for t in p["picks"])
    scores = {t: {"score":0.0,"goals":0,"cs":0,"gd":0,"wins":0,"draws":0,"losses":0,"yc":0,"rc":0}
              for t in all_picked}

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
            team = norm((b.get("team") or {}).get("name",""))
            if team not in scores: continue
            if b.get("card") == "YELLOW_CARD":       scores[team]["yc"] += 1
            elif b.get("card") in ("RED_CARD","YELLOW_RED_CARD"): scores[team]["rc"] += 1

    # ── fantasy points ──
    for t, s in scores.items():
        pts  = s["goals"]*1.5 + s["cs"]*2.0 + s["wins"]*2.0
        pts += max(0, s["gd"]) * 0.5
        pts -= s["yc"]*0.5 + s["rc"]*2.0
        s["score"] = round(pts, 1)

    # ── player scores ──
    player_scores = []
    for p in PLAYERS:
        total = 0.0
        breakdown = {}
        for i, pick in enumerate(p["picks"]):
            s = scores.get(pick, {}).get("score", 0.0)
            total += s
            breakdown[f"P{i+1} · {pick}"] = s
        player_scores.append({**p, "total": round(total,1), "breakdown": breakdown})

    # ── fixtures ──
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    fixture_list = []
    for m in matches:
        status  = m["status"]
        played  = status == "FINISHED"
        is_live = status in ("IN_PLAY","PAUSED")
        hg = m["score"]["fullTime"]["home"]
        ag = m["score"]["fullTime"]["away"]
        date_str = m.get("utcDate","")[:10]
        try:
            from datetime import date
            d = date.fromisoformat(date_str)
            date_label = f"{d.day} {months[d.month-1]}"
        except: date_label = date_str
        grp = (m.get("group") or "?").replace("GROUP_","")
        fixture_list.append({
            "date": date_label, "group": grp,
            "home": norm(m["homeTeam"]["name"]),
            "away": norm(m["awayTeam"]["name"]),
            "homeScore": hg, "awayScore": ag,
            "venue": m.get("venue","") or "",
            "played": played, "live": is_live,
        })

    return {
        "nation_scores":  scores,
        "player_scores":  player_scores,
        "fixtures":       fixture_list,
        "matches_played": len(finished),
        "matches_live":   len(live),
        "matches_total":  len(matches),
        "updated_at":     datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC"),
    }

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
  <div>
    <div class="header-title">⚽ The Unofficial World Cup Pool</div>
    <div class="header-sub">FIFA World Cup 2026 · Fantasy Leaderboard</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
with st.spinner("Loading live scores…"):
    DATA = fetch_all_data()

if DATA is None:
    st.error("Could not load match data. Check your API token in Streamlit secrets.")
    st.stop()

ns = DATA["nation_scores"]
ps = DATA["player_scores"]
fx = DATA["fixtures"]

humans = sorted([p for p in ps if not p.get("ai")], key=lambda x: x["total"], reverse=True)
ais    = sorted([p for p in ps if p.get("ai")],    key=lambda x: x["total"], reverse=True)

# ─────────────────────────────────────────────────────────────
# STATUS ROW
# ─────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Matches Played",  f"{DATA['matches_played']} / {DATA['matches_total']}")
c2.metric("Live Now",        DATA["matches_live"], delta="🔴 LIVE" if DATA["matches_live"] else None)
c3.metric("Players",         len(humans))
c4.metric("Last Updated",    DATA["updated_at"].split(" ")[:-1][-1] + " UTC")

st.caption(f"🕐 Data refreshes automatically every 5 minutes · Last fetch: {DATA['updated_at']}")

if DATA["matches_live"]:
    st.warning(f"🔴 **{DATA['matches_live']} match(es) currently LIVE** — scores updating every 5 minutes")

st.divider()

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏅 Leaderboard", "🌍 Nation Scores", "📅 Fixtures", "ℹ️ Scoring Rules"
])

# ══════════════════════════════════════════ TAB 1: LEADERBOARD
with tab1:

    # ── Podium ──
    if len(humans) >= 3:
        col_silver, col_gold, col_bronze = st.columns([1, 1.2, 1])
        with col_silver:
            p = humans[1]
            picks_str = " · ".join(p["picks"])
            st.markdown(f"""
            <div class="podium-silver">
              <div style="font-size:24px">🥈</div>
              <div class="podium-name">{p['name']}</div>
              <div class="podium-score" style="color:#007B63">{fmt(p['total'])}</div>
              <div style="font-size:10px;color:#55585A">pts</div>
              <div class="podium-picks">{picks_str}</div>
            </div>""", unsafe_allow_html=True)
        with col_gold:
            p = humans[0]
            picks_str = " · ".join(p["picks"])
            st.markdown(f"""
            <div class="podium-gold">
              <div style="font-size:28px">🥇</div>
              <div class="podium-name">{p['name']}</div>
              <div class="podium-score" style="color:#BAFFC5">{fmt(p['total'])}</div>
              <div style="font-size:10px;opacity:0.7">pts</div>
              <div class="podium-picks">{picks_str}</div>
            </div>""", unsafe_allow_html=True)
        with col_bronze:
            p = humans[2]
            picks_str = " · ".join(p["picks"])
            st.markdown(f"""
            <div class="podium-bronze">
              <div style="font-size:24px">🥉</div>
              <div class="podium-name">{p['name']}</div>
              <div class="podium-score" style="color:#9E6B42">{fmt(p['total'])}</div>
              <div style="font-size:10px;color:#55585A">pts</div>
              <div class="podium-picks">{picks_str}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Search ──
    search = st.text_input("🔍 Search player", placeholder="Type a name…", label_visibility="collapsed")

    # ── AI Benchmarks ──
    st.markdown("##### 🤖 AI Benchmarks")
    ai_rows = []
    for p in ais:
        s = ns
        goals = sum(s.get(t,{}).get("goals",0) for t in p["picks"])
        mp    = sum((s.get(t,{}).get("wins",0)+s.get(t,{}).get("draws",0)+s.get(t,{}).get("losses",0)) for t in p["picks"])
        yc    = sum(s.get(t,{}).get("yc",0) for t in p["picks"])
        rc    = sum(s.get(t,{}).get("rc",0) for t in p["picks"])
        ai_rows.append({
            "Name": p["name"],
            "Picks": " · ".join(p["picks"]),
            "MP": mp or "—", "⚽": goals or "—",
            "🟨": yc or "—", "🟥": rc or "—",
            "Score": fmt(p["total"]),
        })
    if ai_rows:
        import pandas as pd
        st.dataframe(pd.DataFrame(ai_rows), use_container_width=True, hide_index=True)

    st.markdown("##### 👤 Players — Ranked")

    # ── Full leaderboard ──
    import pandas as pd
    rows = []
    for rank, p in enumerate(humans, 1):
        if search and search.lower() not in p["name"].lower():
            continue
        s = ns
        goals  = sum(s.get(t,{}).get("goals",0)  for t in p["picks"])
        mp     = sum((s.get(t,{}).get("wins",0)+s.get(t,{}).get("draws",0)+s.get(t,{}).get("losses",0)) for t in p["picks"])
        wins   = sum(s.get(t,{}).get("wins",0)   for t in p["picks"])
        draws  = sum(s.get(t,{}).get("draws",0)  for t in p["picks"])
        losses = sum(s.get(t,{}).get("losses",0) for t in p["picks"])
        cs     = sum(s.get(t,{}).get("cs",0)     for t in p["picks"])
        gd     = sum(s.get(t,{}).get("gd",0)     for t in p["picks"])
        yc     = sum(s.get(t,{}).get("yc",0)     for t in p["picks"])
        rc     = sum(s.get(t,{}).get("rc",0)     for t in p["picks"])
        star   = " ★" if p.get("self") else ""
        rows.append({
            "#":      rank,
            "Player": p["name"] + star,
            "Picks":  " · ".join(p["picks"]),
            "MP":     mp or "—",
            "⚽":     goals or "—",
            "W":      wins or "—",
            "D":      draws or "—",
            "L":      losses or "—",
            "CS":     cs or "—",
            "GD":     gd if gd != 0 else "—",
            "🟨":     yc or "—",
            "🟥":     rc or "—",
            "Score":  fmt(p["total"]),
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.1f", width="small"),
                "#":     st.column_config.NumberColumn(width="small"),
            }
        )

    # ── Score breakdown expander ──
    with st.expander("📊 View score breakdown by pick"):
        selected = st.selectbox("Select player", [p["name"] for p in humans])
        player = next((p for p in humans if p["name"] == selected), None)
        if player:
            bd_cols = st.columns(4)
            for i, (pick, score) in enumerate(player["breakdown"].items()):
                with bd_cols[i % 4]:
                    color = "#007B63" if score > 0 else ("#c0392b" if score < 0 else "#B8AEA5")
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #E0DBD4;border-radius:6px;
                                padding:10px;text-align:center;margin-bottom:8px">
                      <div style="font-size:10px;color:#55585A">{pick}</div>
                      <div style="font-size:20px;font-weight:700;color:{color}">{fmt(score)}</div>
                      <div style="font-size:9px;color:#B8AEA5">pts</div>
                    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════ TAB 2: NATION SCORES
with tab2:
    group_filter = st.selectbox(
        "Filter by group",
        ["All Groups"] + [f"Group {g}" for g in sorted(GROUPS.keys())],
        label_visibility="collapsed"
    )

    groups_to_show = GROUPS.keys() if group_filter == "All Groups" else [group_filter.replace("Group ","")]

    for g in groups_to_show:
        teams = GROUPS[g]
        st.markdown(f"#### Group {g}")
        cols = st.columns(len(teams))
        sorted_teams = sorted(teams, key=lambda t: ns.get(t,{}).get("score",0), reverse=True)
        for i, team in enumerate(sorted_teams):
            s = ns.get(team, {})
            played = bool(s.get("wins",0) + s.get("draws",0) + s.get("losses",0))
            score  = s.get("score", 0)
            is_my  = team in MY_TEAMS
            color  = "#007B63" if score > 0 else ("#c0392b" if score < 0 else "#B8AEA5")
            border = "3px solid #007B63" if is_my else "1px solid #E0DBD4"
            bg     = "#E6F2F0" if is_my else "white"
            with cols[i]:
                st.markdown(f"""
                <div style="background:{bg};border:{border};border-radius:6px;
                            padding:12px;text-align:center;margin-bottom:8px">
                  <div style="font-size:24px">{flag(team)}</div>
                  <div style="font-size:11px;font-weight:600;margin:4px 0">{team}{"  ★" if is_my else ""}</div>
                  <div style="font-size:22px;font-weight:800;color:{color}">{fmt(score) if played else "—"}</div>
                  <div style="font-size:9px;color:#55585A">pts</div>
                  {f'<div style="font-size:9px;color:#55585A;margin-top:4px">{s.get("goals",0)}G · {s.get("cs",0)}CS · 🟨{s.get("yc",0)} 🟥{s.get("rc",0)}</div>' if played else '<div style="font-size:9px;color:#B8AEA5">Not played</div>'}
                </div>""", unsafe_allow_html=True)
        st.divider()

# ══════════════════════════════════════════ TAB 3: FIXTURES
with tab3:
    fx_filter = st.radio(
        "Filter",
        ["All", "Played", "Upcoming", "My Teams ★"],
        horizontal=True, label_visibility="collapsed"
    )

    filtered_fx = fx
    if fx_filter == "Played":    filtered_fx = [f for f in fx if f["played"]]
    elif fx_filter == "Upcoming":filtered_fx = [f for f in fx if not f["played"] and not f["live"]]
    elif fx_filter == "My Teams ★":
        filtered_fx = [f for f in fx if f["home"] in MY_TEAMS or f["away"] in MY_TEAMS]

    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    for f in filtered_fx:
        by_date[f["date"]].append(f)

    for date, matches in by_date.items():
        st.markdown(f"**{date}**")
        cols_per_row = 3
        for i in range(0, len(matches), cols_per_row):
            row_matches = matches[i:i+cols_per_row]
            cols = st.columns(cols_per_row)
            for j, m in enumerate(row_matches):
                with cols[j]:
                    hMy = m["home"] in MY_TEAMS
                    aMy = m["away"] in MY_TEAMS
                    if m["live"]:
                        status_html = '<span style="color:#c0392b;font-weight:700">🔴 LIVE</span>'
                        card_bg = "#fff5f5"
                        border  = "2px solid #F67A6D"
                    elif m["played"]:
                        status_html = '<span style="color:#007B63;font-weight:600">FT</span>'
                        card_bg = "white"
                        border  = "3px solid #007B63"
                    else:
                        status_html = '<span style="color:#B8AEA5">Upcoming</span>'
                        card_bg = "white"
                        border  = "1px solid #E0DBD4"

                    score_html = (
                        f'<span style="font-size:20px;font-weight:700;color:#007B63">'
                        f'{m["homeScore"]}–{m["awayScore"]}</span>'
                        if m["played"] or m["live"]
                        else '<span style="font-size:14px;color:#B8AEA5">vs</span>'
                    )

                    st.markdown(f"""
                    <div style="background:{card_bg};border:{border};border-radius:6px;
                                padding:10px 14px;margin-bottom:8px">
                      <div style="display:flex;justify-content:space-between;
                                  font-size:9px;color:#55585A;margin-bottom:6px">
                        <span>Group {m['group']}</span>
                        <span>{m['date']}</span>
                      </div>
                      <div style="display:flex;align-items:center;justify-content:space-between;gap:6px">
                        <span style="font-size:12px;font-weight:600">
                          {flag(m['home'])} {m['home']}{"  ★" if hMy else ""}
                        </span>
                        {score_html}
                        <span style="font-size:12px;font-weight:600;text-align:right">
                          {m['away']} {flag(m['away'])}{"  ★" if aMy else ""}
                        </span>
                      </div>
                      <div style="margin-top:4px;font-size:9px;color:#B8AEA5">
                        {m.get('venue','') or ''} · {status_html}
                      </div>
                    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════ TAB 4: SCORING RULES
with tab4:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Per Match")
        st.markdown("""
| Event | Points |
|-------|--------|
| Goal scored | +1.5 |
| Clean sheet | +2.0 |
| Match win | +2.0 |
| Positive GD (per goal) | +0.5 |
| Yellow card | −0.5 |
| Red card | −2.0 |
        """)
    with col_b:
        st.markdown("#### Knockout Bonuses")
        st.markdown("""
| Stage | Bonus |
|-------|-------|
| Round of 32 | +2.5 |
| Round of 16 | +5.0 |
| Quarter-final | +7.5 |
| Semi-final | +10.0 |
| Runners-up | +15.0 |
| Champions 🏆 | +25.0 |
        """)
        st.markdown("#### Individual Awards")
        st.markdown("""
| Award | Bonus |
|-------|-------|
| Player of Tournament | +15 |
| Golden Boot | +12 |
| Golden Glove | +10 |
| Best Young Player | +8 |
        """)
    st.info("**Example:** 3–0 win → Goals +4.5 · CS +2 · GD +1.5 · Win +2 = **10 pts**")