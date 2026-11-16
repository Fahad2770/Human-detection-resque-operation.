import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Multi-Target Grid Mapping", layout="wide")

# --- Auto-Refresh ---
count = st_autorefresh(interval=3000, limit=None, key="multi_target_refresh")

st.title("📍 Multi-Target Disaster Rescue & Grid Mapping")
st.markdown(f"### 🌐 ملبے کے نیچے موجود تمام افراد اور ورکرز کی لائیو ملٹی پوائنٹ ٹریکنگ (کاؤنٹر: `{count}`)")

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

dist_x = 10 ** ((measured_power - safe_rssi_1) / (10 * n))
dist_x = max(0.5, min(10.0, dist_x))

dist_y = 10 ** ((measured_power - safe_rssi_2) / (10 * n))
dist_y = max(0.5, min(10.0, dist_y))

# فرض کریں ہمارے پاس سسٹم میں ایک سے زیادہ متاثرہ افراد (Targets) کے ڈیٹا پوائنٹس ہیں
# آپ ان کو مزید ESP بورڈز یا ThingSpeak کے الگ الگ 필드 (Field 2, Field 3) سے بھی جوڑ سکتے ہیں
targets = [
    {"name": "🎯 Victim / Target Alpha", "x": dist_x, "y": dist_y, "color": "red", "size": 22},
    {"name": "⚠️ Victim / Target Beta (Zone 2)", "x": min(9.0, dist_x + 2.5), "y": min(9.0, dist_y + 1.8), "color": "darkorange", "size": 18},
    {"name": "👷 Rescue Worker (Mobile)", "x": 2.0, "y": 8.0, "color": "dodgerblue", "size": 16}
]

# Metrics Display
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("ESP-1 (X-Axis RSSI)", f"{rssi_1} dBm", status_1)
with col2:
    st.metric("ESP-2 (Y-Axis RSSI)", f"{rssi_2} dBm", status_2)
with col3:
    st.metric("Target Alpha X", f"{dist_x:.2f} m")
with col4:
    st.metric("Target Alpha Y", f"{dist_y:.2f} m")

st.markdown("---")

# --- Multi-Target Plotly Figure ---
fig = go.Figure()

# 1. تمام ٹارگٹس اور ورکرز کو ایک ایک کر کے گراف پر پلوٹ کرنا
for t in targets:
    fig.add_trace(go.Scatter(
        x=[t["x"]], y=[t["y"]],
        mode='markers+text',
        marker=dict(size=t["size"], color=t["color"], symbol='circle', line=dict(width=2, color='white')),
        text=[f'{t["name"]} ({t["x"]:.1f}m, {t["y"]:.1f}m)'],
        textposition="top center",
        name=t["name"]
    ))

# 2. گائیڈ لائنز (Cross Lines for Primary Target Alpha)
fig.add_shape(type="line", x0=dist_x, y0=0, x1=dist_x, y1=dist_y,
              line=dict(color="rgba(255,165,0,0.6)", width=2, dash="dash"))
fig.add_shape(type="line", x0=0, y0=dist_y, x1=dist_x, y1=dist_y,
              line=dict(color="rgba(255,165,0,0.6)", width=2, dash="dash"))

# --- Layout Configuration ---
fig.update_layout(
    title="<b>Multi-Target Rescue Zone Mapping (Avoid Secondary Collapses)</b>",
    xaxis=dict(title="X-Axis Grid (Meters)", range=[0, 11], showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    yaxis=dict(title="Y-Axis Grid (Meters)", range=[0, 11], showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.2)'),
    
    # لیجنڈ نیچے تاکہ نقشہ نہ چھپے
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.35,
        xanchor="center",
        x=0.5
    ),
    
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='white',
    height=620
)

st.plotly_chart(fig, use_container_width=True)

st.warning("⚠️ **Safety Precaution:** بھاری مشینری یا کرین کو کسی بھی زون میں حرکت دینے سے پہلے نقشے پر موجود تمام ریڈ اور اورنج ڈاٹس (Targets) کی پوزیشن لازمی چیک کر لیں تاکہ کسی دوسرے دبے ہوئے شخص کو نقصان نہ پہنچے!")
