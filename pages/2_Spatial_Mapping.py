import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Grid Intersection Mapping", layout="wide")

# --- Auto-Refresh ---
count = st_autorefresh(interval=3000, limit=None, key="grid_spatial_refresh")

st.title("📍 True Dual-ESP Grid Intersection & Spatial Mapping")
st.markdown(f"### 🌐 ESP-1 (X-Axis) اور ESP-2 (Y-Axis) فاصلاتی میپنگ (لائیو کاؤنٹر: `{count}`)")

# Channel Configurations
FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"
fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=1"

MOBILE_CHANNEL_ID = "3579370"
READ_API_KEY_MOBILE = "H696MBRW1ASMZZ3W"
mobile_url = f"https://api.thingspeak.com/channels/{MOBILE_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_MOBILE}&results=1"

# 1. Fetch ESP-1 Data (Fixed Node RSSI -> X-Distance)
def fetch_esp1():
    try:
        res = requests.get(fixed_url, timeout=3)
        if res.status_code == 200:
            feeds = res.json().get('feeds', [])
            if feeds:
                return float(feeds[-1].get('field1', -70.0)), "Online 🟢"
    except:
        pass
    return -70.0, "Offline 🔴"

# 2. Fetch ESP-2 Data (Mobile Node RSSI / Field -> Y-Distance)
def fetch_esp2():
    try:
        res = requests.get(mobile_url, timeout=3)
        if res.status_code == 200:
            feeds = res.json().get('feeds', [])
            if feeds:
                latest = feeds[-1]
                # اگر فیلڈ 1 میں RSSI ہے یا کوآर्डिनेट ہے تو اسے لے لیں
                val = float(latest.get('field1', -70.0))
                return val, "Online 🟢"
    except:
        pass
    return -70.0, "Offline 🔴"

rssi_1, status_1 = fetch_esp1()
rssi_2, status_2 = fetch_esp2()

# --- Path-Loss Distance Formula for Both ESPs ---
measured_power = -50
n = 2.5

safe_rssi_1 = rssi_1 if rssi_1 < 0 else -70.0
safe_rssi_2 = rssi_2 if rssi_2 < 0 else -70.0

# ESP-1 سے حاصل ہونے والا فاصلہ (X-Axis بنے گا)
distance_x = 10 ** ((measured_power - safe_rssi_1) / (10 * n))
distance_x = max(0.1, min(10.0, distance_x)) # حدود میں رکھنے کے لیے

# ESP-2 سے حاصل ہونے والا فاصلہ (Y-Axis بنے گا)
distance_y = 10 ** ((measured_power - safe_rssi_2) / (10 * n))
distance_y = max(0.1, min(10.0, distance_y)) # حدود میں رکھنے کے لیے

# Metrics Display
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("ESP-1 (X-Axis Source)", f"{rssi_1} dBm", status_1)
with col2:
    st.metric("ESP-2 (Y-Axis Source)", f"{rssi_2} dBm", status_2)
with col3:
    st.metric("Calculated X (Distance)", f"{distance_x:.2f} m")
with col4:
    st.metric("Calculated Y (Distance)", f"{distance_y:.2f} m")

st.markdown("---")

# --- Plotly Square Grid Scatter Chart ---
# ڈیٹا فریم جس میں ESP-1, ESP-2 اور ان کا درمیانی انٹرسیکشن پوائنٹ ہوگا
map_data = pd.DataFrame({
    'X': [0.0, distance_x, distance_x],
    'Y': [0.0, 0.0, distance_y],
    'Node': [
        'ESP-1 Anchor (Origin 0,0)', 
        'ESP-1 Proximity Point (X)', 
        'True Target Intersection (X & Y Merged)'
    ],
    'Type': ['Anchor', 'Sensor Node', 'Target']
})

fig = px.scatter(
    map_data, x='X', y='Y', color='Node', size=[150, 150, 250],
    title="<b>Grid Square Intersection Map (X-Axis vs Y-Axis Fusion)</b>",
    labels={'X': 'ESP-1 X-Distance (Meters)', 'Y': 'ESP-2 Y-Distance (Meters)'}
)

# اسکوائر گرڈ لائنز (Square Grid Lines) کی سیٹنگز
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)', range=[0, 12])
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)', range=[0, 12])
fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')

st.plotly_chart(fig, use_container_width=True)

st.success(f"🎯 **Grid Fusion Active:** اب ESP-1 کو X-Axis اور ESP-2 کو Y-Axis مان کر ان کا حقیقی انٹرسیکشن پوائنٹ (`{distance_x:.2f}, {distance_y:.2f}`) اسکوائر گرڈ پر دکھایا جا رہا ہے!")
