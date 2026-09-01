# app.py
import datetime
import numpy as __np
import pandas as __pd
import requests
import streamlit as st

st.set_page_title("Tennis Total Games Model - Dabble Hammer")
st.title("🎾 Dabble Tennis Total Games Model (SofaScore Integration)")

# SofaScore API Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sofascore.com/",
}

# Preloaded Dabble Tennis Matches & Lines from current slate
DABBLE_MATCHES = [
    {"player1": "Ben Shelton", "player2": "Hubert Hurkacz", "line": 41.5},
    {"player1": "Alexei Popyrin", "player2": "Alejandro Tabilo", "line": 40.5},
    {"player1": "Brandon Nakashima", "player2": "Alex Michelsen", "line": 40.5},
    {"player1": "Lloyd Harris", "player2": "Stefanos Tsitsipas", "line": 40.5},
    {"player1": "Jesper De Jong", "player2": "Francesco Passaro", "line": 39.5},
    {"player1": "Zachary Svajda", "player2": "Daniel Altmaier", "line": 39.5},
    {
        "player1": "Felix Auger-Aliassime",
        "player2": "Karen Khachanov",
        "line": 39.5,
    },
    {"player1": "James Duckworth", "player2": "Yibing Wu", "line": 39.5},
    {"player1": "Jaume Munar", "player2": "Arthur Rinderknech", "line": 39.5},
    {
        "player1": "Juan Manuel Cerundolo",
        "player2": "Arthur Gea",
        "line": 39.0,
    },
    {"player1": "Marcos Giron", "player2": "Ignacio Buse", "line": 39.0},
    {"player1": "Fabian Marozsan", "player2": "Michael Zheng", "line": 38.5},
    {
        "player1": "Adolfo Daniel Vallejo",
        "player2": "Gael Monfils",
        "line": 38.5,
    },
    {
        "player1": "Daniel Merida Aguilar",
        "player2": "Andrey Rublev",
        "line": 38.5,
    },
    {"player1": "Denis Shapovalov", "player2": "Luca Van Assche", "line": 38.5},
    {"player1": "Luciano Darderi", "player2": "Dalibor Svrcina", "line": 38.5},
    {"player1": "Matteo Berrettini", "player2": "Mariano Navone", "line": 38.5},
    {
        "player1": "Tomas Martin Etcheverry",
        "player2": "Jacob Fearnley",
        "line": 38.5,
    },
    {"player1": "Camilo Ugo Carabelli", "player2": "Jan-Lennard Struff", "line": 38.0},
    {"player1": "Jiri Lehecka", "player2": "Toby Samuel", "line": 38.0},
    {"player1": "Mattia Bellucci", "player2": "Zsombor Piros", "line": 37.0},
    {
        "player1": "Nishesh Basavareddy",
        "player2": "Tristan Schoolkate",
        "line": 37.0,
    },
    {"player1": "Alex Molcan", "player2": "Benjamin Bonzi", "line": 37.0},
    {"player1": "Alexander Blockx", "player2": "Marco Trungelliti", "line": 37.0},
    {"player1": "Francisco Comesana", "player2": "Flavio Cobolli", "line": 36.0},
    {"player1": "Arthur Fery", "player2": "Lorenzo Musetti", "line": 35.5},
    {"player1": "Dino Prizmic", "player2": "Tommy Paul", "line": 35.0},
    {"player1": "Dane Sweeny", "player2": "Corentin Moutet", "line": 34.5},
    {"player1": "Alexander Zverev", "player2": "Lorenzo Sonego", "line": 33.5},
    {"player1": "Jaime Faria", "player2": "Carlos Alcaraz", "line": 33.5},
    {"player1": "Jakub Mensik", "player2": "Jurij Rodionov", "line": 33.5},
    {"player1": "Rafael Jodar", "player2": "Thanasi Kokkinakis", "line": 32.5},
    {"player1": "Taylor Fritz", "player2": "Darwin Blanch", "line": 30.5},
    {"player1": "Filip Misolic", "player2": "Francisco Cerundolo", "line": 30.0},
    {"player1": "Daniil Medvedev", "player2": "Sebastian Gorzny", "line": 29.5},
    {"player1": "Zizou Bergs", "player2": "Carlos Taberner", "line": 29.0},
]


def search_sofascore_player(player_name):
  search_url = f"https://api.sofascore.com/api/v1/search/all?q={player_name}"
  try:
    res = requests.get(search_url, headers=HEADERS, timeout=5)
    if res.status_code == 200:
      results = res.json().get("results", [])
      for r in results:
        if r.get("type") == "player":
          return r.get("entity", {}).get("id")
  except Exception:
    pass
  return None


def fetch_player_recent_game_totals(player_id):
  if not player_id:
    return []
  url = f"https://api.sofascore.com/api/v1/player/{player_id}/events/last/0"
  try:
    res = requests.get(url, headers=HEADERS, timeout=5)
    if res.status_code == 200:
      events = res.json().get("events", [])
      totals = []
      for ev in events:
        if ev.get("status", {}).get("type") == "finished":
          hs = ev.get("homeScore", {}).get("current", 0)
          as_ = ev.get("awayScore", {}).get("current", 0)
          if isinstance(hs, int) and isinstance(as_, int):
            totals.append(hs + as_)
      return totals
  except Exception:
    pass
  return []


# Sidebar Controls
st.sidebar.header("Model Parameters")
confidence_threshold = st.sidebar.slider(
    "Strict Consistency Threshold (%)", 60, 95, 75
)

if st.sidebar.button("Scan All Dabble Tennis Lines"):
  with st.spinner(
      "Pulling SofaScore data and evaluating strict over/under trends..."
  ):
    evaluated_results = []

    for match in DABBLE_MATCHES:
      p1, p2, line = match["player1"], match["player2"], match["line"]

      # Fetch IDs and recent matches
      id1 = search_sofascore_player(p1)
      id2 = search_sofascore_player(p2)

      history1 = fetch_player_recent_game_totals(id1)
      history2 = fetch_player_recent_game_totals(id2)
      combined = history1 + history2

      if len(combined) >= 4:
        avg_games = __np.mean(combined)
        over_count = sum(1 for g in combined if g > line)
        under_count = sum(1 for g in combined if g < line)
        total_samples = len(combined)

        over_pct = (over_count / total_samples) * 100
        under_pct = (under_count / total_samples) * 100

        # Strict Rule Enforcement: Only pick if consistently over or under the line
        if over_pct >= confidence_threshold:
          signal = "HAMMER MORE (OVER) 🔒"
          confidence = f"{over_pct:.1f}% Over Line"
        elif under_pct >= confidence_threshold:
          signal = "HAMMER LESS (UNDER) 🔒"
          confidence = f"{under_pct:.1f}% Under Line"
        else:
          signal = "SKIP"
          confidence = "Mixed Trend"

        if signal != "SKIP":
          evaluated_results.append({
              "Match": f"{p1} vs {p2}",
              "Dabble Line": line,
              "Model Avg Total": round(avg_games, 1),
              "Signal": signal,
              "Consistency": confidence,
          })

    if evaluated_results:
      df = __pd.DataFrame(evaluated_results)
      st.success(
          f"Found {len(df)} strict locks meeting your consistency threshold!"
      )
      st.dataframe(df, use_container_width=True)
    else:
      st.warning(
          "No matches cleared the strict consistency threshold. Try lowering"
          " the slider."
      )
else:
  st.info(
      "Click 'Scan All Dabble Tennis Lines' in the sidebar to begin processing"
      " live data."
  )
