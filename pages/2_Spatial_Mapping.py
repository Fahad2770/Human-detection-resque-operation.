import streamlit as st
import pandas as pd
import requests
import datetime
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Live Dual-Node Mapping", layout="wide")

# --- Auto-Refresh Configuration ---
# یہ ہر 3 سیکنڈ (3000 ملی سیکنڈ) بعد خود بخود پیج کو ریفریش کرے گا
count = st_autorefresh(interval=3000, limit=None, key="live_spatial_refresh")

st.title("📍 Real-Time Live Dual-Node Spatial Mapping")
st.markdown(f"### ⚡ لائیو آٹو ریفریش فعال ہے (اپ ڈیٹ کاؤਂٹر: `{count}`)")

# Channel Configurations
FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"
fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=1"

MOBILE_CHANNEL_ID = "3579370"
READ_API_KEY_MOBILE = "H696MBRW1ASMZZ3W"
mobile_url = f"https://api.thingspeak.com/channels/{MOBILE_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_MOBILE}&results=1"

# 1. Fetch Fixed Node RSSI
def fetch_fixed_node():
    try:
        response = requests.get(fixed_url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            feeds = data.get('feeds', [])
            if feeds:
                latest = feeds[-1]
                val = float(latest.get('field1', -70.0))
                time_str = latest.get('created_at', None)
                return val, time_str, "Online 🟢"
    except:
        pass
    return -70.0, None, "Offline 🔴"

# 2. Fetch Mobile Worker Node Coordinates
def fetch_mobile_node():
    try:
        response = requests.get(mobile_url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            feeds = data.get('feeds', [])
            if feeds:
                latest = feeds[-1]
                x = float(latest.get('field1', 2.0))
                y = float(latest.get('field2', 2.0))
                time_str = latest.get('created_at', None)
                return x, y, time_str, "Online 🟢"
    except:
        pass
    return 2.0, 2.0, None, "Offline 🔴"

# Fetching Live Data
fixed_rssi, fixed_time, fixed_status = fetch_fixed_node()
worker_x, worker_y, mobile_time, mobile_status = fetch_mobile_node()

# Distance & Fusion Logic
measured_power = -50
n = 2.5
safe_rssi = fixed_rssi if fixed_rssi < 0 else -70.0
estimated_distance = 10 ** ((measured_power - safe_rssi) / (10 * n))

adjusted_x = worker_x + (estimated_distance * 0.05)
adjusted_y = worker_y + (estimated_distance * 0.05)

# Metrics Display
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Fixed Node RSSI", f"{fixed_rssi} dBm", fixed_status)
with col2:
    st.metric("Mobile Coordinates", f"X: {worker_x} | Y: {worker_y}", mobile_status)
with col3:
    st.metric("Calculated Distance", f"{estimated_distance:.2f} m")
with col4:
    st.metric("Refined Position", f"({adjusted_x:.1f}, {adjusted_y:.1f})")

st.markdown("---")

# Scatter Plot
grid_data = pd.DataFrame({
    'X': [0.0, worker_x, adjusted_x],
    'Y': [0.0, worker_y, adjusted_y],
    'Node Type': ['Fixed Anchor (Node 1)', 'Mobile Worker (Node 2)', 'Fused Target Location']
})

st.subheader("🗺️ Live Spatial Coordinate Mapping (Auto-Updating)")
st.scatter_chart(grid_data, x='X', y='Y', color='Node Type', size=250)

st.success("🚀 **Live Stream Active:** یہ پیج اب ہر 3 سیکنڈ بعد خود بخود ThingSpeak سے نیا ڈیٹا اٹھا کر اسکرین کو لائیو اپ ڈیٹ کر رہا ہے!")