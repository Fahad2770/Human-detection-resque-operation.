import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Filtered Live Grid Mapping", layout="wide")

# --- Auto-Refresh (ہر 3 سیکنڈ بعد لائیو سنک) ---
count = st_autorefresh(interval=3000, limit=None, key="filtered_live_refresh")

st.title("📍 Filtered & Stabilized Live Grid Intersection")
st.markdown(f"### 🌐 اسمارٹ فلٹرڈ لائیو ڈیٹا ٹریکنگ (مشن کریٹیکل موڈ) — (لائیو کاؤنٹر: `{count}`)")

# Channel Configurations
FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"
fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=5" # پچھلی 5 ریڈنگز تاکہ اوسط نکالی جا سکے

MOBILE_CHANNEL_ID = "3579370"
READ_API_KEY_MOBILE = "H696MBRW1ASMZZ3W"
mobile_url = f"https://api.thingspeak.com/channels/{MOBILE_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_MOBILE}&results=5"

# --- Robust Data Fetcher with Moving Average Smoothing ---
def fetch_smoothed_rssi(url):
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            feeds = res.json().get('feeds', [])
            if feeds:
                # پچھلی تمام دستیاب ویلیوز کو جمع کر के ان کی اوسط (Average) نکالنا (Noise Filtering)
                valid_vals = []
                for f in feeds:
                    val = f.get('field1')
                    if val is not None:
                        try:
                            valid_vals.append(float(val))
                        except:
                            pass
                if valid_vals:
                    smoothed_val = sum(valid_vals) / len(valid_vals)
                    return smoothed_val, "Online 🟢"
    except:
        pass
    return -70.0, "Offline 🔴"

rssi_1, status_1 = fetch_smoothed_rssi(fixed_url)
rssi_2, status_2 = fetch_smoothed_rssi(mobile_url)

# --- Path-Loss Model & Distance Calculation ---
measured_power = -50
n = 2.5

safe_rssi_1 = rssi_1 if rssi_1 < 0 else -70.0
safe_rssi_2 = rssi_2 if rssi_2 < 0 else -70.0

# اگر سگنل بہت زیادہ کمزور ہو تو حد سے باہر تصور ہوگا
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
    st.metric("ESP-1 (Smoothed RSSI)", f"{rssi_1:.1f} dBm", status_1)
with col2:
    st.metric("ESP-2 (Smoothed RSSI)", f"{rssi_2:.1f} dBm", status_2)
with col3:
    st.metric("Filtered X Distance", f"{dist_x:.2f} m" if target_active else "Out of Range")
with col4:
    st.metric("Filtered Y Distance", f"{dist_y:.2f} m" if target_active else "Out of Range")

st.markdown("---")

# --- Plotly Figure ---
fig = go.Figure()

if target_active:
    # لائیو فلٹرڈ ٹارگٹ پوائنٹ
    fig.add_trace(go.Scatter(
        x=[dist_x], y=[dist_y],
        mode='markers+text',
        marker=dict(size=22, color='red', symbol='circle', line=dict(width=2, color='white')),
        text=[f'Stable Target ({dist_x:.1f}m, {dist_y:.1f}m)'],
        textposition="top center",
        name='🎯 Stabilized Target'
    ))

    # کراس لائنیں
    fig.add_shape(type="line", x0=dist_x, y0=0, x1=dist_x, y1=dist_y,
                  line=dict(color="orange", width=2, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=dist_y, x1=dist_x, y1=dist_y,
                  line=dict(color="orange", width=2, dash="dash"))
else:
    fig.add_trace(go.Scatter(
        x=[5], y=[5],
        mode='text',
        text=["⚠️ کوئی فعال ہدف رینج میں نہیں ہے"],
        textfont=dict(size=16, color='yellow'),
        name='Status'
    ))

# Layout Configuration
fig.update_layout(
    title="<b>Stabilized Cross-Axis Grid Mapping (Moving Average Filtered)</b>",
    xaxis=dict(title="ESP-1 X-Axis (Meters)", range=[0, 20], showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    yaxis=dict(title="ESP-2 Y-Axis (Meters)", range=[0, 20], showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    
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
    st.success("🟢 **System Stabilized:** مووننگ ایوریج فلٹر فعال ہے، جس سے سگنل کے بے قاعدہ جھٹکے ختم ہو گئے ہیں اور پوائنٹ بالکل مستحکم لائیو نظر آ رہا ہے۔")
else:
    st.warning("⚠️ **Out of Range:** سگنل کمزور ہیں یا نوڈز حد سے باہر ہیں۔")
