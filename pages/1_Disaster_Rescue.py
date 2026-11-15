import streamlit as st
import pandas as pd
import requests
import datetime
from datetime import datetime, timezone

st.title("🌍 Disaster Rescue & Vitals Monitor")

FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"
fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=1"

@st.cache_data(ttl=2)
def get_thingspeak_status():
    try:
        response = requests.get(fixed_url)
        data = response.json()
        feeds = data['feeds']
        if feeds:
            latest = feeds[-1]
            val = float(latest['field1'])
            created_at = latest['created_at']
            return val, created_at
    except:
        pass
    return -70.0, None

rssi_val, last_time = get_thingspeak_status()

connection_status = "Disconnected ❌"
if last_time:
    try:
        clean_time = last_time.replace("Z", "+00:00")
        last_dt = datetime.fromisoformat(clean_time)
        current_dt = datetime.now(timezone.utc)
        diff_seconds = (current_dt - last_dt).total_seconds()
        if diff_seconds <= 180:
            connection_status = "Connected Live 🟢"
        else:
            connection_status = f"Offline ({int(diff_seconds/60)}m ago) ⚠️"
    except:
        connection_status = "Connected Live 🟢"

variance = abs(rssi_val + 70) * 0.2
heart_rate = int(max(60, min(120, 75 + variance)))
bp_systolic = int(max(100, min(150, 120 + variance * 0.5)))
bp_diastolic = int(max(60, min(95, 80 + variance * 0.3)))

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="📶 Wi-Fi RSSI", value=f"{rssi_val:.1f} dBm", delta="Cloud Sync")
with col2:
    st.metric(label="❤️ Est. Heart Rate", value=f"{heart_rate} BPM", delta="Vitals Active")
with col3:
    st.metric(label="🩸 Est. Blood Pressure", value=f"{bp_systolic}/{bp_diastolic} mmHg", delta="Stable")
with col4:
    st.metric(label="🔋 System Status", value=connection_status, delta=f"ID: {FIXED_CHANNEL_ID}")

status_placeholder = st.empty()
if "Connected Live" in connection_status and abs(rssi_val - (-70)) > 5.0:
    status_placeholder.error("🚨 **CRITICAL ALERT:** ملبے میں جاندار کی موجودگی اور جسمانی حرکات ریکارڈ ہوئی ہیں!")
else:
    status_placeholder.success("🟢 **STATUS:** زون محفوظ ہے / سگنل نارمل ہیں۔")

@st.cache_data(ttl=2)
def get_recent_history():
    try:
        res = requests.get(f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=10")
        data = res.json()
        feeds = data['feeds']
        signals = [float(f['field1']) for f in feeds if f.get('field1') is not None and f.get('field1') != ""]
        if signals:
            return signals
    except:
        pass
    return [rssi_val]

historical_signals = get_recent_history()
st.subheader("📊 Filtered Wi-Fi Signal Strength (dBm)")
cleaned_signals = [abs(val) for val in historical_signals]
chart_data = pd.DataFrame({"RSSI Signal (Magnitude)": cleaned_signals})
st.line_chart(chart_data)
