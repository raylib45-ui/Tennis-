# app.py
import datetime
import time
import numpy as __np
import pandas as __pd
import requests
import streamlit as st

st.set_page_title("Tennis Total Games Model - Hammer More / Less")
st.title("🎾 Tennis Total Games Model (SofaScore Live Scanner)")

# SofaScore API Headers to mimic a browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sofascore.com/",
}


@st.cache_data(ttl=1800)
def fetch_sofascore_tennis_schedule(date_str):
  url = f"https://api.sofascore.com/api/v1/sport/tennis/scheduled-events/{date_str}"
  try:
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
      return response.json().get("events", [])
  except Exception as e:
    st.error(f"Error fetching schedule: {e}")
  return []


def fetch_player_recent_games(player_id):
  url = (
      f"https://api.sofascore.com/api/v1/player/{player_id}/events/last/0"
  )
  try:
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
      events = response.json().get("events", [])
      total_games_list = []
      for ev in events:
        if ev.get("status", {}).get("type") == "finished":
          home_score = ev.get("homeScore", {}).get("current", 0)
          away_score = ev.get("awayScore", {}).get("current", 0)
          # Some scores might be dicts for sets
          # Fallback to summing set scores if available
          if isinstance(home_score, int) and isinstance(away_score, int):
            total_games_list.append(home_score + away_score)
      return total_games_list
  except Exception:
    pass
  return []


# Sidebar Controls
st.sidebar.header("Model Controls")
target_date = st.sidebar.date_input(
    "Select Date", datetime.date.today()
).strftime("%Y-%m-%d")
confidence_threshold = st.sidebar.slider(
    "Consistency Threshold (%)", 60, 95, 75
)

if st.sidebar.button("Run Live Scan"):
  with st.spinner("Fetching live data from SofaScore..."):
    events = fetch_sofascore_tennis_schedule(target_date)
    processed_data = []

    for event in events:
      home_player = event.get("homeTeam", {}).get("name", "Unknown")
      home_id = event.get("homeTeam", {}).get("id")
      away_player = event.get("awayTeam", {}).get("name", "Unknown")
      away_id = event.get("awayTeam", {}).get("id")
      tournament = (
          event.get("tournament", {}).get("name", "ATP/WTA")
      )

      # Fetch history
      home_history = (
          fetch_player_recent_games(home_id) if home_id else []
      )
      away_history = (
          fetch_player_recent_games(away_id) if away_id else []
      )

      combined_history = home_history + away_history
      if len(combined_history) >= 4:
        avg_games = __np.mean(combined_history)
        # Apply strict consistency check (Over/Under trend)
        over_count = sum(1 for g in combined_history if g > avg_games)
        trend_pct = (over_count / len(combined_history)) * 100

        if trend_pct >= confidence_threshold:
          signal = "HAMMER MORE (OVER)"
        elif trend_pct <= (100 - confidence_threshold):
          signal = "HAMMER LESS (UNDER)"
        else:
          signal = "SKIP (No Clear Trend)"

        if signal != "SKIP (No Clear Trend)":
          processed_data.append({
              "Tournament": tournament,
              "Match": f"{home_player} vs {away_player}",
              "Projected Avg Games": round(avg_games, 1),
              "Signal": signal,
              "Trend Confidence": f"{max(trend_pct, 100-trend_pct):.1f}%",
          })

    if processed_data:
      df = __pd.DataFrame(processed_data)
      st.success(
          f"Scan Complete! Found {len(df)} strict trend opportunities."
      )
      st.dataframe(df, use_container_width=True)
    else:
      st.warning(
          "No matches met the strict consistency threshold for Hammer More /"
          " Less."
      )
else:
  st.info(
      "Click 'Run Live Scan' in the sidebar to pull live SofaScore tennis data"
      " and evaluate lines."
  )
