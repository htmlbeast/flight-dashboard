import streamlit as st
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIG ===
st.set_page_config(page_title="Call-Off Command Center", layout="wide")
WEATHER_KEY = "4cc93eeebf406d8b11fb2f24142bde9d"
LOG_FILE = "calloff_log.csv"

# === EMAIL SETTINGS ===
EMAIL_FROM = "christianrivas799@gmail.com"
EMAIL_TO = "christianrivas799@gmail.com"
EMAIL_PASSWORD = "dyrkayjijwjxwzlp"
EMAIL_SENT_MARKER = "/tmp/calloff_email_sent.flag"

# === AUTO-REFRESH ===
st_autorefresh(interval=60 * 1000, key="refresh")

# === Get Live Flight Count from OpenSky ===
@st.cache_data(ttl=60)
def get_opensky_departures():
    url = "https://opensky-network.org/api/states/all"
    params = {"lamin": 41.95, "lamax": 42.05, "lomin": -87.95, "lomax": -87.80}
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
        visibility = data.get("visibility", 10000)
        return {
            "summary": f"{weather} ({desc})",
            "temp": f"{temp}°F",
            "visibility_mi": round(visibility / 1609, 1)
        }
    except Exception as e:
        print("Weather error:", e)
        return None

# === Call-Off Score ===
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

# === Email Alert System ===
def send_email_alert(score, weather, flights):
    try:
        subject = f"🚨 Call-Off Score Alert: {score}/100"
        body = f"""🚨 Today's Call-Off Score is {score}/100

Live flights near O'Hare: {flights}
Weather: {weather['summary']}
Visibility: {weather['visibility_mi']} mi
Temperature: {weather['temp']}

Check the dashboard:
https://flight-dashboard-mweb2fgh8te8z4soedrrx4.streamlit.app/

– Call-Off Command Center
"""
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)

        with open(EMAIL_SENT_MARKER, "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d"))

        print("✅ Email sent!")

    except Exception as e:
        print("❌ Email failed:", e)

# === Log Scores + Actions ===
def log_score(score, flight_count, weather, user_action):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": now,
        "score": score,
        "flights": flight_count,
        "condition": weather["summary"] if weather else "N/A",
        "visibility_mi": weather["visibility_mi"] if weather else "N/A",
        "temp": weather["temp"] if weather else "N/A",
        "called_off": user_action
    }

    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        if not df.empty and now in df["timestamp"].values:
            return
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    else:
        df = pd.DataFrame([entry])

    df.to_csv(LOG_FILE, index=False)

# === UI ===
st.title("📵 Call-Off Command Center")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

flight_count = get_opensky_departures()
weather = get_weather()

col1, col2 = st.columns(2)
with col1:
    st.subheader("🛫 Live Departures near O'Hare")
    if flight_count is not None:
        st.metric("Live Aircraft Tracked", flight_count)
        st.caption("Data from OpenSky Network")
    else:
        st.error("❌ Could not retrieve flight data.")

with col2:
    st.subheader("🌦️ Current Weather")
    if weather:
        st.text(f"Condition: {weather['summary']}")
        st.text(f"Temperature: {weather['temp']}")
        st.text(f"Visibility: {weather['visibility_mi']} mi")
    else:
        st.error("❌ Weather unavailable")

# === Ask if user actually called off ===
user_action = st.radio(
    "Did you call off today?",
    options=["Not yet", "Yes", "No"],
    index=0,
    horizontal=True
)

# === Score Logic ===
st.markdown("---")
score = calculate_calloff_score(flight_count, weather)
log_score(score, flight_count, weather, user_action)

# Email alert logic
today = datetime.now().strftime("%Y-%m-%d")
if score >= 70:
    if not os.path.exists(EMAIL_SENT_MARKER) or open(EMAIL_SENT_MARKER).read().strip() != today:
        send_email_alert(score, weather, flight_count)

# === Final Score Display ===
st.subheader("🧠 Call-Off Score")
if score >= 70:
    st.error(f"🚨 {score}/100 — Call-Off Recommended")
elif 40 <= score < 70:
    st.warning(f"⚠️ {score}/100 — Borderline. Use your best judgment.")
else:
    st.success(f"✅ {score}/100 — Safe to report in today")

# === Score History Chart ===
if os.path.exists(LOG_FILE):
    log_df = pd.read_csv(LOG_FILE)
    log_df["timestamp"] = pd.to_datetime(log_df["timestamp"])
    log_df = log_df.sort_values("timestamp", ascending=True)

    st.markdown("---")
    st.subheader("📈 Score History")
    st.line_chart(log_df.set_index("timestamp")["score"])
    with st.expander("📋 Full Log"):
        st.dataframe(log_df[::-1], use_container_width=True)
