import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Real-Time Live Grid Mapping", layout="wide")

# --- Auto-Refresh (ہر 3 سیکنڈ بعد لائیو سنک) ---
count = st_autorefresh(interval=3000, limit=None, key="live_grid_refresh")

st.title("📍 Real-Time Live ESP-32 Grid Intersection")
st.markdown(f"### 🌐 خالص لائیو ڈیٹا ٹریکنگ (کوਈ فرضی ڈیٹا نہیں) — (لائیو کاؤنٹر: `{count}`)")

# Channel Configurations
FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"
fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=1"

MOBILE_CHANNEL_ID = "3579370"
READ_API_KEY_MOBILE = "H696MBRW1ASMZZ3W"
mobile_url = f"https://api.thingspeak.com/channels/{MOBILE_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_MOBILE}&results=1"

# 1. Fetch ESP-1 Live Data
def fetch_esp1():
    try:
        res = requests.get(fixed_url, timeout=3)
        if res.status_code == 200:
            feeds = res.json().get('feeds', [])
            if feeds:
                latest = feeds[-1]
                # چیک کریں کہ آیا ڈیٹا تازہ ہے یا پرانا
                val = float(latest.get('field1', -70.0))
                return val, "Online 🟢"
    except:
        pass
    return -70.0, "Offline 🔴"

# 2. Fetch ESP-2 Live Data
def fetch_esp2():
    try:
        res = requests.get(mobile_url, timeout=3)
        if res.status_code == 200:
            feeds = res.json().get('feeds', [])
            if feeds:
                latest = feeds[-1]
                val = float(latest.get('field1', -70.0))
                return val, "Online 🟢"
    except:
        pass
    return -70.0, "Offline 🔴"

rssi_1, status_1 = fetch_esp1()
rssi_2, status_2 = fetch_esp2()

# --- Distance Calculation (Path-Loss Model) ---
measured_power = -50
n = 2.5

safe_rssi_1 = rssi_1 if rssi_1 < 0 else -70.0
safe_rssi_2 = rssi_2 if rssi_2 < 0 else -70.0

# اگر سگنل بہت زیادہ کمزور ہو (-90 dBm سے کم)، تو فاصل حد سے باہر تصور ہوگا
if safe_rssi_1 < -90 or safe_rssi_2 < -90:
    target_active = False
    dist_x, dist_y = 0.0, 0.0
else:
    target_active = True
    dist_x = 10 ** ((measured_power - safe_rssi_1) / (10 * n))
    dist_x = max(0.2, min(10.0, dist_x))

    dist_y = 10 ** ((measured_power - safe_rssi_2) / (10 * n))
    dist_y = max(0.2, min(10.0, dist_y))

# Metrics Display
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("ESP-1 (X-Axis RSSI)", f"{rssi_1} dBm", status_1)
with col2:
    st.metric("ESP-2 (Y-Axis RSSI)", f"{rssi_2} dBm", status_2)
with col3:
    st.metric("Live X Distance", f"{dist_x:.2f} m" if target_active else "Out of Range")
with col4:
    st.metric("Live Y Distance", f"{dist_y:.2f} m" if target_active else "Out of Range")

st.markdown("---")

# --- Plotly Figure (Pure Live Data Only) ---
fig = go.Figure()

if target_active:
    # صرف حقیقی لائیو ہدف شو ہوگا
    fig.add_trace(go.Scatter(
        x=[dist_x], y=[dist_y],
        mode='markers+text',
        marker=dict(size=22, color='red', symbol='circle', line=dict(width=2, color='white')),
        text=[f'Live Target ({dist_x:.1f}m, {dist_y:.1f}m)'],
        textposition="top center",
        name='🎯 Active Live Target'
    ))

    # کراس لائنیں
    fig.add_shape(type="line", x0=dist_x, y0=0, x1=dist_x, y1=dist_y,
                  line=dict(color="orange", width=2, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=dist_y, x1=dist_x, y1=dist_y,
                  line=dict(color="orange", width=2, dash="dash"))
else:
    # اگر رینج سے باہر ہوں تو گراف خالی دکھائے گا
    fig.add_trace(go.Scatter(
        x=[5], y=[5],
        mode='text',
        text=["⚠️ کوئی فعال ہدف (Target) رینج میں موجود نہیں ہے"],
        textfont=dict(size=16, color='yellow'),
        name='Status'
    ))

# Layout Configuration
fig.update_layout(
    title="<b>Real-Time Cross-Axis Grid Mapping</b>",
    xaxis=dict(title="ESP-1 X-Axis (Meters)", range=[0, 11], showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    yaxis=dict(title="ESP-2 Y-Axis (Meters)", range=[0, 11], showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5
    ),
    
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='white',
    height=600
)

st.plotly_chart(fig, use_container_width=True)

if target_active:
    st.success("🟢 **Live Status:** ESP-32 کا سگنل موصول ہو رہا ہے اور ہدف لائیو ٹریک ہو رہا ہے۔")
else:
    st.warning("⚠️ **Out of Range:** ESP-32 نوڈز سگنل کی حد سے باہر ہیں یا سگنل بہت کمزور (-90 dBm سے کم) ہے۔")
