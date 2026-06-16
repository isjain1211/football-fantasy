"""
WC 2026 Fantasy Pool — Score Fetcher
=====================================
Run this script to fetch live World Cup data from football-data.org,
compute all fantasy scores, and write scores_data.json.

The HTML dashboard reads scores_data.json — no API calls in the browser at all.

Usage:
    python fetch_scores.py

Requirements:
    pip install requests
"""

import requests
import json
import sys
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# CONFIG — paste your football-data.org token here
# ─────────────────────────────────────────────────────────────
API_TOKEN = "715a8137efc14ac0b72173f9572bc5a9"
API_BASE  = "https://api.football-data.org/v4"
OUTPUT_FILE = "scores_data.json"

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
# football-data.org uses different names than our app
# ─────────────────────────────────────────────────────────────
NAME_MAP = {
    "United States":          "USA",
    "Korea Republic":         "South Korea",
    "Côte d'Ivoire":          "Ivory Coast",
    "Bosnia and Herzegovina": "Bosnia & Herz.",
    "Curaçao":                "Curaçao",
    "Curacao":                "Curaçao",
    "Czech Republic":         "Czechia",
    "Turkey":                 "Türkiye",
    "Congo DR":               "DR Congo",
    "Democratic Republic of Congo": "DR Congo",
    "England":                "England",
    "Scotland":               "Scotland",
}

def norm(name):
    return NAME_MAP.get(name, name)

# ─────────────────────────────────────────────────────────────
# FETCH MATCHES FROM FOOTBALL-DATA.ORG
# ─────────────────────────────────────────────────────────────
def fetch_matches():
    headers = {"X-Auth-Token": API_TOKEN}
    url = f"{API_BASE}/competitions/WC/matches"
    print(f"Fetching: {url}")
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 403:
        print("ERROR: Invalid API token. Check your token at football-data.org")
        sys.exit(1)
    if r.status_code == 429:
        print("ERROR: Rate limit hit. Wait a minute and try again.")
        sys.exit(1)
    r.raise_for_status()
    data = r.json()
    matches = data.get("matches", [])
    print(f"  → {len(matches)} total matches fetched")
    finished = [m for m in matches if m["status"] == "FINISHED"]
    live     = [m for m in matches if m["status"] in ("IN_PLAY","PAUSED")]
    upcoming = [m for m in matches if m["status"] in ("SCHEDULED","TIMED")]
    print(f"  → {len(finished)} finished, {len(live)} live, {len(upcoming)} upcoming")
    return matches

# ─────────────────────────────────────────────────────────────
# COMPUTE NATION FANTASY SCORES
# ─────────────────────────────────────────────────────────────
def compute_nation_scores(matches):
    # Collect all teams picked by anyone
    all_picked = set()
    for p in PLAYERS:
        for t in p["picks"]:
            all_picked.add(t)

    # Initialise scores
    scores = {}
    for team in all_picked:
        scores[team] = {
            "score": 0.0, "goals": 0, "cs": 0, "gd": 0,
            "wins": 0, "draws": 0, "losses": 0,
            "yc": 0, "rc": 0, "stage": "GS"
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
            continue  # neither team picked by anyone

        # Goals
        if h_in: scores[home]["goals"] += hg
        if a_in: scores[away]["goals"] += ag

        # Clean sheets
        if h_in and ag == 0: scores[home]["cs"] += 1
        if a_in and hg == 0: scores[away]["cs"] += 1

        # Goal difference
        if h_in: scores[home]["gd"] += (hg - ag)
        if a_in: scores[away]["gd"] += (ag - hg)

        # Win / Draw / Loss
        if hg > ag:
            if h_in: scores[home]["wins"]   += 1
            if a_in: scores[away]["losses"] += 1
        elif ag > hg:
            if h_in: scores[home]["losses"] += 1
            if a_in: scores[away]["wins"]   += 1
        else:
            if h_in: scores[home]["draws"] += 1
            if a_in: scores[away]["draws"] += 1

        # Cards
        for booking in m.get("bookings", []):
            team = norm(booking.get("team", {}).get("name", ""))
            if team not in scores:
                continue
            card = booking.get("card", "")
            if card == "YELLOW_CARD":
                scores[team]["yc"] += 1
            elif card in ("RED_CARD", "YELLOW_RED_CARD"):
                scores[team]["rc"] += 1

    # ── Compute fantasy points ──
    for team, s in scores.items():
        pts  = s["goals"] * 1.5          # goals
        pts += s["cs"]    * 2.0          # clean sheets
        pts += s["wins"]  * 2.0          # wins
        pts += max(0, s["gd"]) * 0.5     # positive goal difference only
        pts -= s["yc"]    * 0.5          # yellow cards
        pts -= s["rc"]    * 2.0          # red cards
        s["score"] = round(pts, 1)

    return scores


# ─────────────────────────────────────────────────────────────
# COMPUTE PLAYER SCORES
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
        results.append({
            **p,
            "total":     round(total, 1),
            "breakdown": breakdown
        })
    return results


# ─────────────────────────────────────────────────────────────
# FORMAT FIXTURES FOR THE DASHBOARD
# ─────────────────────────────────────────────────────────────
def format_fixtures(matches):
    out = []
    for m in matches:
        home_score = m["score"]["fullTime"]["home"]
        away_score = m["score"]["fullTime"]["away"]
        played     = m["status"] == "FINISHED"
        is_live    = m["status"] in ("IN_PLAY", "PAUSED")

        # Parse date string "2026-06-11" → "11 Jun"
        date_str = m.get("utcDate","")[:10]
        try:
            from datetime import date
            d = date.fromisoformat(date_str)
            months = ["Jan","Feb","Mar","Apr","May","Jun",
                      "Jul","Aug","Sep","Oct","Nov","Dec"]
            date_label = f"{d.day} {months[d.month-1]}"
        except:
            date_label = date_str

        out.append({
            "date":       date_label,
            "group":      (m.get("group") or "?").replace("GROUP_",""),
            "home":       norm(m["homeTeam"]["name"]),
            "away":       norm(m["awayTeam"]["name"]),
            "homeScore":  home_score,
            "awayScore":  away_score,
            "venue":      m.get("venue",""),
            "played":     played,
            "live":       is_live,
            "notable":    ""
        })
    return out


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("WC 2026 Fantasy Pool — Score Fetcher")
    print("=" * 50)

    # 1. Fetch
    matches = fetch_matches()

    # 2. Compute nation scores
    print("\nComputing nation scores…")
    nation_scores = compute_nation_scores(matches)
    top5 = sorted(nation_scores.items(), key=lambda x: x[1]["score"], reverse=True)[:5]
    print("  Top 5 nations:")
    for name, s in top5:
        print(f"    {name}: {s['score']} pts ({s['goals']}G, {s['cs']}CS, {s['wins']}W)")

    # 3. Compute player scores
    print("\nComputing player scores…")
    player_scores = compute_player_scores(nation_scores)
    humans = [p for p in player_scores if not p.get("ai")]
    humans_sorted = sorted(humans, key=lambda x: x["total"], reverse=True)
    print("  Top 5 players:")
    for p in humans_sorted[:5]:
        print(f"    {p['name']}: {p['total']} pts")

    # 4. Format fixtures
    fixtures = format_fixtures(matches)

    # 5. Build output
    live_count     = sum(1 for m in matches if m["status"] in ("IN_PLAY","PAUSED"))
    finished_count = sum(1 for m in matches if m["status"] == "FINISHED")
    now_str        = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    output = {
        "updated_at":     now_str,
        "matches_played": finished_count,
        "matches_live":   live_count,
        "matches_total":  len(matches),
        "nation_scores":  nation_scores,
        "player_scores":  player_scores,
        "fixtures":       fixtures,
    }

    # 6. Write JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! Written to {OUTPUT_FILE}")
    print(f"   {finished_count}/{len(matches)} matches · {live_count} live")
    print(f"   Now open wc2026_dashboard.html in your browser")
    print("=" * 50)


if __name__ == "__main__":
    main()