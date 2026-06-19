"""
WC 2026 Fantasy Pool — Score Fetcher
=====================================
Data sources:
  - football-data.org  → match scores, fixtures, results (existing token)
  - Wikipedia          → yellow/red cards per team (free, no token needed)
                         scraped with BeautifulSoup — no Selenium, no JS

Usage:
    pip install requests beautifulsoup4
    python fetch_scores.py

Then open wc2026_dashboard.html in your browser.
"""

import requests
import json
import sys
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
FD_TOKEN    = "715a8137efc14ac0b72173f9572bc5a9"  # football-data.org
FD_BASE     = "https://api.football-data.org/v4"
OUTPUT_FILE = "scores_data.json"

# Wikipedia group pages — one per group, pure HTML, no JS needed
WIKI_GROUPS = {
    "A": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_A",
    "B": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_B",
    "C": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_C",
    "D": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_D",
    "E": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_E",
    "F": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_F",
    "G": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_G",
    "H": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_H",
    "I": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_I",
    "J": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_J",
    "K": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_K",
    "L": "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_L",
}
WIKI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}
CARD_ALTS = {"Yellow card", "Red card", "Yellow-red card"}

# ─────────────────────────────────────────────────────────────
# PLAYERS — all 67 participants + AI benchmarks
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

# ─────────────────────────────────────────────────────────────
# TEAM NAME NORMALISATION
# api-football uses slightly different names in some cases
# ─────────────────────────────────────────────────────────────
NAME_MAP = {
    "United States":              "USA",
    "Korea Republic":             "South Korea",
    "South Korea":                "South Korea",
    "Côte d'Ivoire":              "Ivory Coast",
    "Cote d'Ivoire":              "Ivory Coast",
    "Bosnia and Herzegovina":     "Bosnia & Herz.",
    "Bosnia-Herzegovina":         "Bosnia & Herz.",
    "Bosnia":                     "Bosnia & Herz.",
    "Curaçao":                    "Curaçao",
    "Curacao":                    "Curaçao",
    "Czech Republic":             "Czechia",
    "Czechia":                    "Czechia",
    "Turkey":                     "Türkiye",
    "Türkiye":                    "Türkiye",
    "Congo DR":                   "DR Congo",
    "DR Congo":                   "DR Congo",
    "Democratic Republic of Congo":"DR Congo",
    "New Zealand":                "New Zealand",
    "Saudi Arabia":               "Saudi Arabia",
    "Cape Verde":                 "Cape Verde",
    "Scotland":                   "Scotland",
    "England":                    "England",
    "Iran":                       "Iran",
    "Islamic Republic of Iran":   "Iran",
    "Cape Verde Islands":          "Cape Verde",
}

def norm(name):
    return NAME_MAP.get(name, name)


# ─────────────────────────────────────────────────────────────
# STEP 1: FETCH MATCH SCORES from football-data.org
# 1 API call, returns all 104 fixtures with scores
# ─────────────────────────────────────────────────────────────
def fetch_matches():
    print("📡 Step 1: Fetching match scores from football-data.org…")
    r = requests.get(
        f"{FD_BASE}/competitions/WC/matches",
        headers={"X-Auth-Token": FD_TOKEN},
        timeout=15
    )
    if r.status_code == 403:
        print("ERROR: Invalid football-data.org token")
        sys.exit(1)
    r.raise_for_status()
    matches = r.json().get("matches", [])
    finished = [m for m in matches if m["status"] == "FINISHED"]
    live     = [m for m in matches if m["status"] in ("IN_PLAY","PAUSED")]
    print(f"   → {len(matches)} fixtures | {len(finished)} finished | {len(live)} live")
    return matches


# ─────────────────────────────────────────────────────────────
# STEP 2: SCRAPE CARDS from Wikipedia
# 12 requests (one per group page), pure HTML, no token needed
# Wikipedia lineup tables use card icon images with alt="Yellow card" etc.
# ─────────────────────────────────────────────────────────────
def scrape_all_cards():
    print("\n🔍 Step 2: Scraping card data from Wikipedia…")
    all_cards = {}

    for group, url in WIKI_GROUPS.items():
        try:
            r = requests.get(url, headers=WIKI_HEADERS, timeout=10)
            if r.status_code != 200:
                print(f"   Group {group}: HTTP {r.status_code} — skipping")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            group_cards = {}

            # Each played match has a footballbox (score header) + lineup table
            # Lineup table row[0] has td[0]=home lineup, td[2]=away lineup
            # Card images have alt="Yellow card", "Red card", or "Yellow-red card"
            boxes = soup.find_all("div", {"class": "footballbox"})

            # Get all lineup tables: must have Manager: text + card images + 10+ rows
            lineup_tables = [
                t for t in soup.find_all("table")
                if len(t.find_all("img", {"alt": lambda a: a in CARD_ALTS})) > 0
                and "Manager:" in t.get_text()
                and len(t.find_all("tr")) > 10
            ]

            for tbl in lineup_tables:
                # Find the footballbox that precedes this lineup table in the DOM
                prev_box = None
                for box in boxes:
                    if box.sourceline < tbl.sourceline:
                        prev_box = box
                    else:
                        break
                if not prev_box:
                    continue

                # Get team names from footballbox header
                home_th = prev_box.find("th", {"class": "fhome"})
                away_th = prev_box.find("th", {"class": "faway"})
                if not home_th or not away_th:
                    continue
                home_a = home_th.find("a")
                away_a = away_th.find("a")
                home_name = norm(home_a.get_text(strip=True) if home_a else home_th.get_text(strip=True))
                away_name = norm(away_a.get_text(strip=True) if away_a else away_th.get_text(strip=True))

                # First row of lineup table: td[0]=home, td[2]=away
                first_row = tbl.find("tr")
                if not first_row:
                    continue
                tds = first_row.find_all("td", recursive=False)
                if len(tds) < 3:
                    continue

                for team, td in [(home_name, tds[0]), (away_name, tds[2])]:
                    if team not in group_cards:
                        group_cards[team] = {"yc": 0, "rc": 0}
                    for img in td.find_all("img", {"alt": lambda a: a in CARD_ALTS}):
                        alt = img.get("alt", "")
                        if alt == "Yellow card":
                            group_cards[team]["yc"] += 1
                        elif alt in ("Red card", "Yellow-red card"):
                            group_cards[team]["rc"] += 1

            all_cards.update(group_cards)
            played_teams = {t: c for t, c in group_cards.items() if c["yc"] > 0 or c["rc"] > 0}
            if played_teams:
                for team, c in played_teams.items():
                    print(f"   Group {group} | {team}: 🟨{c['yc']} 🟥{c['rc']}")
            else:
                print(f"   Group {group}: no cards yet")

            time.sleep(0.4)  # polite delay between Wikipedia requests

        except Exception as e:
            print(f"   Group {group}: ERROR — {e}")

    return all_cards


# ─────────────────────────────────────────────────────────────
# STEP 3: COMPUTE NATION SCORES
# Merge match data (football-data.org) + cards (Wikipedia)
# ─────────────────────────────────────────────────────────────
def compute_nation_scores(matches, card_data):
    print("\n⚽ Step 3: Computing nation fantasy scores…")

    # Initialise ALL 48 nations so unpicked teams (e.g. Haiti) still show stats
    all_nations = set(t for teams in GROUPS.values() for t in teams)
    all_picked  = set(t for p in PLAYERS for t in p["picks"])
    all_teams   = all_nations | all_picked
    scores = {}
    for team in all_teams:
        scores[team] = {
            "score": 0.0, "goals": 0, "cs": 0, "gd": 0,
            "wins": 0, "draws": 0, "losses": 0, "yc": 0, "rc": 0, "stage": "GS"
        }

    finished = [m for m in matches if m["status"] == "FINISHED"]

    for m in finished:
        home = norm(m["homeTeam"]["name"])
        away = norm(m["awayTeam"]["name"])
        hg   = m["score"]["fullTime"]["home"] or 0
        ag   = m["score"]["fullTime"]["away"] or 0
        h_in = home in scores
        a_in = away in scores
        if not h_in and not a_in:
            continue

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

    # ── Merge Wikipedia card data ──
    card_teams_merged = 0
    for team, cards in card_data.items():
        if team in scores:
            scores[team]["yc"] = cards["yc"]
            scores[team]["rc"] = cards["rc"]
            card_teams_merged += 1
    print(f"   → Cards merged for {card_teams_merged} teams")

    # ── Compute fantasy points ──
    for team, s in scores.items():
        pts  = s["goals"] * 1.5
        pts += s["cs"]    * 2.0
        pts += s["wins"]  * 2.0
        pts += s["gd"] * 0.5
        pts -= s["yc"]    * 0.5
        pts -= s["rc"]    * 2.0
        s["score"] = round(pts, 1)

    # Print top 5
    top5 = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)[:5]
    print("\n   Top 5 nations:")
    for name, s in top5:
        print(f"   {name}: {s['score']} pts  ({s['goals']}G · {s['cs']}CS · {s['wins']}W · 🟨{s['yc']} 🟥{s['rc']})")

    return scores


# ─────────────────────────────────────────────────────────────
# STEP 4: COMPUTE PLAYER SCORES
# ─────────────────────────────────────────────────────────────
def compute_player_scores(nation_scores):
    results = []
    for p in PLAYERS:
        total = 0.0
        breakdown = {}
        for i, pick in enumerate(p["picks"]):
            ns = nation_scores.get(pick, {})
            s  = ns.get("score", 0.0)
            total += s
            breakdown[f"P{i+1} · {pick}"] = s
        results.append({**p, "total": round(total, 1), "breakdown": breakdown})
    return results


# ─────────────────────────────────────────────────────────────
# STEP 5: FORMAT FIXTURES
# ─────────────────────────────────────────────────────────────
def format_fixtures(matches):
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    out = []
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
        except:
            date_label = date_str
        grp = (m.get("group") or "?").replace("GROUP_","")
        out.append({
            "date":date_label, "group":grp,
            "home":norm(m["homeTeam"]["name"]),
            "away":norm(m["awayTeam"]["name"]),
            "homeScore":hg, "awayScore":ag,
            "venue":m.get("venue","") or "",
            "played":played, "live":is_live, "notable":""
        })
    return out


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  WC 2026 Fantasy Pool — Score Fetcher")
    print("  Scores: football-data.org | Cards: Wikipedia")
    print("=" * 55)

    matches       = fetch_matches()
    card_data     = scrape_all_cards()
    nation_scores = compute_nation_scores(matches, card_data)
    player_scores = compute_player_scores(nation_scores)
    fixtures      = format_fixtures(matches)

    finished_count = sum(1 for m in matches if m["status"] == "FINISHED")
    live_count     = sum(1 for m in matches if m["status"] in ("IN_PLAY","PAUSED"))

    humans = sorted([p for p in player_scores if not p.get("ai")], key=lambda x: x["total"], reverse=True)
    print("\n🏅 Top 5 players:")
    for p in humans[:5]:
        print(f"   {p['name']}: {p['total']} pts")

    now_str = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    output = {
        "updated_at":     now_str,
        "matches_played": finished_count,
        "matches_live":   live_count,
        "matches_total":  len(matches),
        "data_sources":   "Scores: football-data.org | Cards: Wikipedia (scraped)",
        "nation_scores":  nation_scores,
        "player_scores":  player_scores,
        "fixtures":       fixtures,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! Written to {OUTPUT_FILE}")
    print(f"   {finished_count}/{len(matches)} matches · {live_count} live")
    print(f"   Open wc2026_dashboard.html in your browser")
    print("=" * 55)


if __name__ == "__main__":
    main()