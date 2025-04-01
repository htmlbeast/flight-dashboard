import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import plotly.express as px

# === CONFIG ===
st.set_page_config(page_title="O'Hare Live Flight Delays", layout="wide")
API_KEY = "d266d79cc749a21a6a2de3c3dfd16eb5"  # Replace if needed

# === AUTO-REFRESH ===
st_autorefresh(interval=60 * 1000, key="auto_refresh")

# === GET LIVE DATA ===
@st.cache_data(ttl=60)
def fetch_live_delays():
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": API_KEY,
        "dep_iata": "ORD",
        "flight_status": "active",  # Only get active flights
        "limit": 100,
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None, "API request failed"
    data = response.json().get("data", [])
    delays = []
    for flight in data:
        delay = flight.get("departure", {}).get("delay")
        if delay and delay > 0:
            delays.append({
                "Airline": flight["airline"]["name"],
                "Flight": flight["flight"]["iata"],
                "Destination": flight["arrival"]["airport"],
                "Scheduled": flight["departure"]["scheduled"],
                "Delay (min)": delay,
                "Terminal": flight.get("departure", {}).get("terminal", "Unknown"),
            })
    df = pd.DataFrame(delays)
    return df, None

# === MAIN UI ===
st.title("🛫 O'Hare Live Flight Delays Dashboard")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Auto-refreshes every 60 sec)")

df, error = fetch_live_delays()

if error:
    st.error(f"❌ {error}")
elif df.empty:
    st.success("✅ No current delays at O'Hare!")
else:
    severe = df[df["Delay (min)"] >= 60]
    st.metric(label="Total Delayed Flights", value=len(df))
    st.metric(label="Severely Delayed (60+ min)", value=len(severe))

    def highlight_delay(val):
        if val >= 60:
            return 'background-color: red; color: white'
        elif val >= 30:
            return 'background-color: orange'
        return ''

    st.dataframe(
        df.style.applymap(highlight_delay, subset=["Delay (min)"]),
        use_container_width=True
    )

    # === Chart: Delays by Airline ===
    airline_counts = df["Airline"].value_counts().reset_index()
    airline_counts.columns = ["Airline", "Delayed Flights"]
    st.subheader("✈️ Delays by Airline")
    fig_airlines = px.bar(airline_counts, x="Airline", y="Delayed Flights", color="Airline")
    st.plotly_chart(fig_airlines, use_container_width=True)

    # === Chart: Delays by Terminal ===
    terminal_counts = df["Terminal"].value_counts().reset_index()
    terminal_counts.columns = ["Terminal", "Delayed Flights"]
    st.subheader("🧭 Delays by Terminal")
    fig_terminals = px.bar(terminal_counts, x="Terminal", y="Delayed Flights", color="Terminal")
    st.plotly_chart(fig_terminals, use_container_width=True)

