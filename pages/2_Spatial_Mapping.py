import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Advanced Rescue Command Hub", layout="wide")

# ==========================================
# 🎛️ سائیڈ بار: ایڈجسٹمنٹ بار (Adjustment Bar)
# ==========================================
st.sidebar.header("⚙️ سسٹم کنٹرول پینل")

# 1. آپریشنل موڈ (آن لائن یا آف لائن خودکار/مینوئل انتخاب)
op_mode = st.sidebar.radio("آپریشنل موڈ منتخب کریں:", ["🌐 Online (ThingSpeak Cloud)", "📡 Offline (Local AP / Direct)"])

# 2. آٹو ریفریش کا وقت (سیکنڈز میں ایڈجسٹ کرنے کے لیے)
refresh_sec = st.sidebar.slider("لائیو ریفریش کا وقفہ (سیکنڈز):", min_value=2, max_value=15, value=3)
count = st_autorefresh(interval=refresh_sec * 1000, limit=None, key="command_hub_refresh")

st.sidebar.markdown("---")
st.sidebar.subheader("📐 سگنل اور کیलिब्रیشن پیامیٹرز")
measured_power = st.sidebar.slider("مقررہ پاور (RSSI at 1m):", min_value=-60, max_value=-40, value=-50)
path_loss_n = st.sidebar.slider("پاتھ لاس ایکسپوننٹ (n):", min_value=1.5, max_value=4.0, value=2.5, step=0.1)
max_stale_mins = st.sidebar.slider("پرانا ڈیٹا خارج کرنے کی حد (منٹ):", min_value=1, max_value=10, value=3)

st.title("📍 Advanced Multi-Node Rescue Command Hub")
st.markdown(f"### 🌐 لائیو میپنگ و ڈوئل موڈ کنٹرول (ریفریش ریٹ: `{refresh_sec}s` | کاؤنٹر: `{count}`)")

# Channel Configurations
FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"
fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=1"

MOBILE_CHANNEL_ID = "3579370"
READ_API_KEY_MOBILE = "H696MBRW1ASMZZ3W"
mobile_url = f"https://api.thingspeak.com/channels/{MOBILE_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_MOBILE}&results=1"

# --- فنکشن: صرف تازہ ترین (Current) لائیو ڈیٹا چیک کرنے کے لیے ---
def fetch_fresh_node_data(url):
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            feeds = data.get('feeds', [])
            if feeds:
                latest = feeds[-1]
                created_at_str = latest.get('created_at') # مثال: '2026-06-06T12:00:00Z'
                
                # وقت کا موازنہ (صرف کرنٹ ڈیٹا قبول کرنے کے لیے)
                if created_at_str:
                    # 'Z' کو ہٹا کر UTC ٹائم بنانا
                    clean_time_str = created_at_str.replace('Z', '+00:00')
                    entry_time = datetime.fromisoformat(clean_time_str)
                    current_time = datetime.now(timezone.utc)
                    
                    diff_minutes = (current_time - entry_time).total_seconds() / 60.0
                    
                    # اگر ڈیٹا مقررہ وقت (مثلاً 3 منٹ) سے پرانا ہے تو اسے مسترد کر دیں (Stale Data Protection)
                    if diff_minutes > max_stale_mins:
                        return -99.0, 0.0, "Stale / Offline ⚠️"
                
                rssi_val = float(latest.get('field1', -70.0))
                # اگر فیلڈ 2 میں CSI یا دوسرا ڈیٹا آرہا ہے تو اسے بھی اٹھا لیں
                csi_val = float(latest.get('field2', 0.0))
                
                return rssi_val, csi_val, "Online 🟢"
    except:
        pass
    return -99.0, 0.0, "Offline 🔴"

# --- ڈیٹا حاصل کرنا ---
if "Online" in op_mode:
    rssi_1, csi_1, status_1 = fetch_fresh_node_data(fixed_url)
    rssi_2, csi_2, status_2 = fetch_fresh_node_data(mobile_url)
else:
    # آف لائن یا لوکل موڈ (مینوئل سمولیشن یا ڈائرैक्ट IP فیچ)
    rssi_1, csi_1, status_1 = -65.0, 15.0, "Local AP 📡"
    rssi_2, csi_2, status_2 = -68.0, 12.0, "Local AP 📡"

# --- فاصلہ اور پوزیشن کا حساب (Path-Loss Formula) ---
if rssi_1 <= -90 or rssi_2 <= -90 or status_1 != "Online 🟢":
    target_active = False
    dist_x, dist_y = 0.0, 0.0
else:
    target_active = True
    dist_x = 10 ** ((measured_power - rssi_1) / (10 * path_loss_n))
    dist_x = max(0.2, min(10.0, dist_x))

    dist_y = 10 ** ((measured_power - rssi_2) / (10 * path_loss_n))
    dist_y = max(0.2, min(10.0, dist_y))

# --- میٹرکس ڈسپلے ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("ESP-1 (RSSI / CSI)", f"{rssi_1} dBm / {csi_1}", status_1)
with col2:
    st.metric("ESP-2 (RSSI / CSI)", f"{rssi_2} dBm / {csi_2}", status_2)
with col3:
    st.metric("Calculated X-Distance", f"{dist_x:.2f} m" if target_active else "No Target")
with col4:
    st.metric("Calculated Y-Distance", f"{dist_y:.2f} m" if target_active else "No Target")

st.markdown("---")

# --- Plotly Graph (Strictly Live Data Only) ---
fig = go.Figure()

if target_active:
    # 1. اصلی لائیو ٹارگٹ پوائنٹ
    fig.add_trace(go.Scatter(
        x=[dist_x], y=[dist_y],
        mode='markers+text',
        marker=dict(size=25, color='red', symbol='circle', line=dict(width=2, color='white')),
        text=[f'🎯 Live Target ({dist_x:.1f}m, {dist_y:.1f}m)'],
        textposition="top center",
        name='Active Live Target'
    ))

    # 2. کراس لائنیں (Square Grid Intersections)
    fig.add_shape(type="line", x0=dist_x, y0=0, x1=dist_x, y1=dist_y,
                  line=dict(color="orange", width=2, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=dist_y, x1=dist_x, y1=dist_y,
                  line=dict(color="orange", width=2, dash="dash"))
else:
    # کوئی فرضی ڈیٹا نہیں، صرف الرٹ میسج
    fig.add_trace(go.Scatter(
        x=[5], y=[5],
        mode='text',
        text=["⚠️ کوئی فعال اور تازہ ہدف (Current Target) رینج میں موجود نہیں ہے"],
        textfont=dict(size=16, color='yellow'),
        name='Status'
    ))

# Layout Settings
fig.update_layout(
    title="<b>Cross-Axis Grid Mapping (Real-Time Synchronized)</b>",
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
    st.success("🟢 **System Active:** فریشنس اور ٹائم اسٹیمپ چیک کامیاب ہے۔ سسٹم صرف خالص لائیو اور موجودہ (Current) ڈیٹا دکھا رہا ہے!")
else:
    st.warning("⚠️ **Safety Notice:** پرانا یا مردہ ڈیٹا خارج کر دیا گیا ہے۔ نوڈز کی رینج یا انٹرنیٹ کنکشن چیک کریں۔")
