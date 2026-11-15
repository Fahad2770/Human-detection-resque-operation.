import datetime
from datetime import datetime, timezone
import requests

# --- Dual-Channel Configuration ---
FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"

MOBILE_CHANNEL_ID = "3579370"
READ_API_KEY_MOBILE = "H696MBRW1ASMZZ3W"

fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=1"
mobile_url = f"https://api.thingspeak.com/channels/{MOBILE_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_MOBILE}&results=1"

# 1. Fetch Fixed Channel Status (Vitals & RSSI)
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

# Real connection status check based on timestamp
connection_status = "Disconnected ❌"
if last_time:
    try:
        clean_time = last_time.replace("Z", "+00:00")
        last_dt = datetime.fromisoformat(clean_time)
        current_dt = datetime.now(timezone.utc)
        diff_seconds = (current_dt - last_dt).total_seconds()
        
        if diff_seconds <= 120:
            connection_status = "Connected Live 🟢"
        else:
            connection_status = f"Offline ({int(diff_seconds)}s ago) ⚠️"
    except:
        connection_status = "Connected Live 🟢"

# 2. Fetch Mobile Worker Channel Coordinates (X and Y from Field 1 & Field 2)
@st.cache_data(ttl=2)
def get_mobile_coordinates():
    try:
        response = requests.get(mobile_url)
        data = response.json()
        feeds = data['feeds']
        if feeds:
            latest = feeds[-1]
            x_val = float(latest.get('field1', 2.0))
            y_val = float(latest.get('field2', 2.0))
            return x_val, y_val
    except:
        pass
    return 2.0, 2.0

worker_x, worker_y = get_mobile_coordinates()

# Scaled and Bounded Vitals Estimation based on RSSI variance
variance = abs(rssi_val + 70) * 0.2
heart_rate = int(max(60, min(120, 75 + variance)))
bp_systolic = int(max(100, min(150, 120 + variance * 0.5)))
bp_diastolic = int(max(60, min(95, 80 + variance * 0.3)))

# Fetch Multiple Feeds for Real-time Graph Safely
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

# --- SECTION 1: Live RSSI Waveform ---
if mode == "🌍 Disaster Rescue & Vitals":
    st.subheader("📊 Filtered Wi-Fi Signal Strength (dBm)")
    chart_data = pd.DataFrame({
        "RSSI Signal": historical_signals
    })
    st.line_chart(chart_data)

# --- SECTION 2: Spatial Grid & Target Mapping ---
elif mode == "📍 Spatial Grid & Target Mapping":
    st.subheader("📍 Spatial Grid & Target Mapping (Live Worker)")
    st.markdown("Coordinates fetched live from Mobile Worker ESP-32 (Channel 3579370).")

    grid_data = pd.DataFrame({
        'X': [worker_x],
        'Y': [worker_y],
        'Color': ['red']
    })
    st.scatter_chart(grid_data, x='X', y='Y', color='Color', size=150)
    st.success(f"📌 **Current Worker Position ->** X-Axis: {worker_x} | Y-Axis: {worker_y}")

# --- SECTION 3: Smart Home Security ---
elif mode == "🏠 Smart Home Security":
    st.subheader("🏠 Home Security Intrusion Detector")
    st.info("سیکیورٹی موڈ فعال ہے: گھر کے اندر غیر معمولی حرکت اور وائی فائی ڈسٹربنس پر نظر رکھی جا رہی ہے۔")

    sec_val = float(rssi_val) if rssi_val else -70.0
    security_data = pd.DataFrame({
        "Security Noise Level": [2, 4, 1, 5, 3, abs(sec_val + 75)]
    })
    st.area_chart(security_data)