import streamlit as st
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# === CONFIG ===
st.set_page_config(page_title="Call-Off Command Center", layout="wide")
WEATHER_KEY = "4cc93eeebf406d8b11fb2f24142bde9d"

# === AUTO-REFRESH ===
st_autorefresh(interval=60 * 1000, key="refresh")

# === Get Live Flight Count from OpenSky ===
@st.cache_data(ttl=60)
def get_opensky_departures():
    url = "https://opensky-network.org/api/states/all"
    params = {"lamin": 41.95, "lamax": 42.05, "lomin": -87.95, "lomax": -87.80}  # O'Hare bounding box
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        flights = data.get("states", [])
        return len(flights)
    except Exception as e:
        print("OpenSky error:", e)
        return None

# === Get Weather Conditions ===
@st.cache_data(ttl=60)
def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Chicago&appid={WEATHER_KEY}&units=imperial"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        weather = data["weather"][0]["main"]
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        visibility = data.get("visibility", 10000)  # meters
        return {
            "summary": f"{weather} ({desc})",
            "temp": f"{temp}°F",
            "visibility_mi": round(visibility / 1609, 1)
        }
    except Exception as e:
        print("Weather error:", e)
        return None

# === Call-Off Score (ML-style logic) ===
def calculate_calloff_score(flight_count, weather):
    score = 0

    if flight_count is not None and flight_count < 10:
        score += 40

    if weather and weather["visibility_mi"] < 1.5:
        score += 25

    if weather and any(term in weather["summary"].lower() for term in ["fog", "storm", "snow", "rain"]):
        score += 25

    if weather:
        temp = float(weather["temp"].replace("°F", ""))
        if temp < 15 or temp > 90:
            score += 10

    return min(score, 100)

# === MAIN UI ===
st.title("📵 Call-Off Command Center (OpenSky + Weather)")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

flight_count = get_opensky_departures()
weather = get_weather()

col1, col2 = st.columns(2)

with col1:
    st.subheader("🛫 Live Departures near O'Hare")
    if flight_count is not None:
        st.metric("Live Aircraft Tracked", flight_count)
        st.caption("From OpenSky Network (within O’Hare airspace)")
    else:
        st.error("❌ Could not retrieve flight data.")

with col2:
    st.subheader("🌦️ Current Weather (Chicago)")
    if weather:
        st.text(f"Condition: {weather['summary']}")
        st.text(f"Temperature: {weather['temp']}")
        st.text(f"Visibility: {weather['visibility_mi']} mi")
    else:
        st.error("❌ Weather data unavailable")

# === Final Verdict ===
st.markdown("---")
score = calculate_calloff_score(flight_count, weather)
st.subheader("🧠 Call-Off Score")

if score >= 70:
    st.error(f"🚨 {score}/100 — Call-Off Recommended")
elif 40 <= score < 70:
    st.warning(f"⚠️ {score}/100 — Borderline. Use your best judgment.")
else:
    st.success(f"✅ {score}/100 — Safe to report in today")

