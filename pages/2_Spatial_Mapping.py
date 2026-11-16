import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Cross-Grid Intersection Mapping", layout="wide")

# --- Auto-Refresh ---
count = st_autorefresh(interval=3000, limit=None, key="cross_grid_refresh")

st.add_rows if hasattr(st, 'add_rows') else None
st.title("📍 True Cross-Axis Grid & Target Intersection")
st.markdown(f"### 🌐 ESP-1 (X-Axis) اور ESP-2 (Y-Axis) کی لائیو کراس میپنگ (کاؤنٹر: `{count}`)")

# Channel Configurations
FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"
fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=1"

MOBILE_CHANNEL_ID = "3579370"
READ_API_KEY_MOBILE = "H696MBRW1ASMZZ3W"
mobile_url = f"https://api.thingspeak.com/channels/{MOBILE_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_MOBILE}&results=1"

# 1. Fetch ESP-1 Data (Fixed Node -> X Distance)
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

# 2. Fetch ESP-2 Data (Mobile Node -> Y Distance)
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

# ESP-1 سے فاصلہ (حتّیٰ الامکان حدود میں: 0 سے 10 میٹر)
dist_x = 10 ** ((measured_power - safe_rssi_1) / (10 * n))
dist_x = max(0.5, min(10.0, dist_x))

# ESP-2 سے فاصلہ (حتیٰ الامکان حدود میں: 0 سے 10 میٹر)
dist_y = 10 ** ((measured_power - safe_rssi_2) / (10 * n))
dist_y = max(0.5, min(10.0, dist_y))

# Metrics Display
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("ESP-1 (X-Axis RSSI)", f"{rssi_1} dBm", status_1)
with col2:
    st.metric("ESP-2 (Y-Axis RSSI)", f"{rssi_2} dBm", status_2)
with col3:
    st.metric("Calculated X Distance", f"{dist_x:.2f} m")
with col4:
    st.metric("Calculated Y Distance", f"{dist_y:.2f} m")

st.markdown("---")

# --- Advanced Plotly Figure with Cross Lines & Intersection Dot ---
fig = go.Figure()

# 1. ESP-1 (Origin Anchor 0,0) اور بنیادی نوڈز
fig.add_trace(go.Scatter(
    x=[0.0, dist_x], y=[0.0, 0.0],
    mode='markers+text',
    marker=dict(size=14, color='dodgerblue'),
    text=['ESP-1 (Origin)', 'X-Distance Mark'],
    textposition="bottom center",
    name='Anchors'
))

# 2. True Intersection Target Dot (جہاں دونوں لائنیں آپس میں کاٹیں گی)
fig.add_trace(go.Scatter(
    x=[dist_x], y=[dist_y],
    mode='markers+text',
    marker=dict(size=25, color='red', symbol='circle', line=dict(width=2, color='white')),
    text=[f'Target ({dist_x:.1f}m, {dist_y:.1f}m)'],
    textposition="top center",
    name='🎯 True Target Intersection'
))

# 3. Cross Lines (پرپینڈکولر لائنیں جو آپس میں مل کر کراس بنائیں گی)
# X پوائنٹ سے اوپر کی طرف جانے والی لکیر
fig.add_shape(type="line", x0=dist_x, y0=0, x1=dist_x, y1=dist_y,
              line=dict(color="orange", width=2, dash="dash"))
# Y پوائنٹ سے دائیں طرف آنے والی لکیر
fig.add_shape(type="line", x0=0, y0=dist_y, x1=dist_x, y1=dist_y,
              line=dict(color="orange", width=2, dash="dash"))

# --- Graph Layout & Equal Scale Setup ---
fig.update_layout(
    title="<b>Cross-Axis Grid: ESP-1 (X) vs ESP-2 (Y) Intersection</b>",
    xaxis=dict(title="ESP-1 X-Axis Distance (Meters)", range=[0, 10], showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    yaxis=dict(title="ESP-2 Y-Axis Distance (Meters)", range=[0, 10], showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)', scaleanchor="x", scaleratio=1),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='white',
    height=550
)

st.plotly_chart(fig, use_container_width=True)

st.success(f"🎯 **Intersection Active:** ESP-1 سے حاصل کردہ فاصلہ X-Axis (`{dist_x:.2f}m`) اور ESP-2 سے حاصل کردہ فاصلہ Y-Axis (`{dist_y:.2f}m`) پر لکیروں کے ذریعے آپس میں مل رہے ہیں اور سرخ رنگ کا واضح نقطہ درست پوزیشن ظاہر کر رہا ہے!")
