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

# === Call-Off Logic ===
def should_call_off(flight_count, weather):
    bad_weather = weather and (
        "fog" in weather["summary"].lower()
        or "storm" in weather["summary"].lower()
        or "snow" in weather["summary"].lower()
        or weather["visibility_mi"] < 1.5
    )
    low_traffic = flight_count is not None and flight_count < 10

    return bad_weather or low_traffic

# === MAIN UI ===
st.title("📵 Call-Off Command Center (OpenSky Edition)")
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

# === FINAL CALL-OFF DECISION ===
st.markdown("---")
if should_call_off(flight_count, weather):
    st.error("🚨 Conditions suggest calling off is justified.")
else:
    st.success("✅ Low disruption. You should probably go in today.")

