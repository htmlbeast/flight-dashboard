import pandas as pd
import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# MUST BE FIRST
st.set_page_config(page_title="O'Hare Delay Dashboard", layout="wide")

# 🔁 Auto-refresh every 60 seconds
st_autorefresh(interval=60000, key="refresh")

# 📄 Load CSV
df = pd.read_csv('ord_delays_log.csv', header=None)
df.columns = ['Timestamp', 'Airline', 'Flight', 'Destination', 'Scheduled', 'Delay (min)']

# 🧹 Clean & prep data
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df['Scheduled'] = pd.to_datetime(df['Scheduled'], errors='coerce')
df['Delay (min)'] = pd.to_numeric(df['Delay (min)'], errors='coerce')
df['Severe'] = df['Delay (min)'] >= 60
df['Hour'] = df['Timestamp'].dt.hour

# 🌐 App title
st.title("🛫 O'Hare Flight Delay Dashboard")
st.markdown("Track live departure delays from Chicago O'Hare (ORD)")

# 📅 Date filter
date_options = df['Timestamp'].dt.date.unique()
selected_date = st.selectbox("📅 Select a date:", sorted(date_options, reverse=True))
df_filtered = df[df['Timestamp'].dt.date == selected_date]

# ⏱️ Time range filter
hour_range = st.slider("⏰ Filter by hour of day:", 0, 23, (0, 23))
df_filtered = df_filtered[(df_filtered['Hour'] >= hour_range[0]) & (df_filtered['Hour'] <= hour_range[1])]

# 📊 Metrics
total_delays = len(df_filtered)
severe_delays = df_filtered['Severe'].sum()
avg_delay = df_filtered['Delay (min)'].mean()

col1, col2, col3 = st.columns(3)
col1.metric("✈️ Total Delays", total_delays)
col2.metric("🚨 Severe Delays (60+ min)", severe_delays)
col3.metric("⏱️ Avg Delay (min)", f"{avg_delay:.1f}")

# 📈 Bar chart of delays by airline
st.subheader("📊 Delays by Airline")
airline_counts = df_filtered['Airline'].value_counts().reset_index()
airline_counts.columns = ['Airline', 'Delays']
st.bar_chart(airline_counts.set_index('Airline'))

# 🔴 Highlight severe delays in table
def highlight_severe(row):
    return ['background-color: red; color: white' if row['Severe'] else '' for _ in row]

# 📋 Delay details table
st.subheader("📋 Delay Details")
st.dataframe(df_filtered.sort_values(by="Delay (min)", ascending=False).style.apply(highlight_severe, axis=1))
