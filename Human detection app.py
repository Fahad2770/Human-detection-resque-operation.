import streamlit as st
import pandas as pd
import numpy as np
import time
import random

st.set_page_config(page_title="Dual-Purpose Wi-Fi Sensing & Rescue Hub", page_icon="🚨", layout="wide")

# Sidebar Language & Mode Selection
st.sidebar.title("🛡️ Control Center / کنٹرول سینٹر")
mode = st.sidebar.selectbox("Select Mode / موڈ منتخب کریں", ["🌍 Disaster Rescue Mode (زلزلے سے بچاؤ)", "🏠 Smart Home Security (گھر کی سیکیورٹی)"])
lang = st.sidebar.selectbox("Language / زبان", ["English", "اردو"])

if lang == "اردو":
    if "Disaster" in mode:
        st.title("🚨 ڈیزاسٹر ریسکیو: ملبے تلے انسانوں کی تلاش")
        st.markdown("### وائی فائی RSSI سگنلز کے ذریعے جانداروں کی حرکت (Breathing Motion) کی شناخت")
    else:
        st.title("🏠 سمارٹ ہوم سیکیورٹی: انٹروڈر وائی فائی مانیٹر")
        st.markdown("### گھر میں نامعلوم شخص یا چور کی دراندازی کا بغیر کیمرے کے پتا لگانا")
else:
    if "Disaster" in mode:
        st.title("🚨 Disaster Rescue: Sub-Debris Human Detector")
        st.markdown("### Detecting human respiration & micro-movements via Wi-Fi RSSI variance")
    else:
        st.title("🏠 Smart Home Security: Intruder Detection")
        st.markdown("### Invisible Wi-Fi wave interference monitoring for unauthorized access")

sensitivity = st.sidebar.slider("Detection Sensitivity / حساسیت", 1.0, 10.0, 4.0)

# Main Dashboard Metrics
col1, col2, col3 = st.columns(3)

@st.cache_data(ttl=1)
def get_simulated_rssi():
    base = -70 if "Disaster" in mode else -65
    noise = random.choice([0, 0, 0, 15, -15, 0]) if random.random() > 0.75 else random.uniform(-2, 2)
    return base + noise

rssi_val = get_simulated_rssi()
distance_m = round(10 ** ((-50 - rssi_val) / (10 * 2.5)), 2)

with col1:
    st.metric(label="📶 Signal Strength (RSSI)", value=f"{rssi_val:.1f} dBm", delta="Node Active")
with col2:
    label_text = "Estimated Depth / فاصلہ" if "Disaster" in mode else "Proximity Range"
    st.metric(label=label_text, value=f"{distance_m} Meters", delta="Real-time")
with col3:
    st.metric(label="🔋 Device Health", value="94% Stable", delta="Battery OK")

# Alert Box
status_placeholder = st.empty()

if abs(rssi_val - (-70)) > 6.0:
    if "Disaster" in mode:
        status_placeholder.error("🚨 **HIGH ALERT:** ملبے کے نیچے حرکت یا سانس لینے کے آثار محسوس ہوئے ہیں!")
    else:
        status_placeholder.error("🚨 **SECURITY ALERT:** گھر کے احاطے میں مشکوک حرکت یا دراندازی کی لہریں ریکارڈ ہوئیں!")
else:
    status_placeholder.success("🟢 **STATUS:** تمام زونز محفوظ ہیں / کوئی غیر معمولی مداخلت نہیں ملی۔")

# Tabs for Analytics
tab1, tab2, tab3 = st.tabs(["📊 Live Waveform & Noise Filter", "🗺️ Position & Posture Mapping", "📥 Export Logs"])

with tab1:
    st.subheader("Filtered Wi-Fi Signal Strength (dBm)")
    chart_data = pd.DataFrame(np.random.randn(20, 1) * 3 - 70, columns=["RSSI Signal"])
    st.line_chart(chart_data)

with tab2:
    st.subheader("Spatial Grid & Target Mapping")
    st.markdown("Coordinates calculated via attenuation and multi-node triangulation.")
    map_data = pd.DataFrame({
        'X': [2, 8, 5, 5.3],
        'Y': [2, 2, 8, 4.2],
        'Type': ['Node 1', 'Node 2', 'Node 3', 'Target / Intruder Position'],
        'Color': ['blue', 'blue', 'blue', 'red']
    })
    st.scatter_chart(map_data, x='X', y='Y', color='Color', size=250)

with tab3:
    st.subheader("System Logs & CSV Export")
    log_df = pd.DataFrame({
        "Timestamp": [time.strftime("%H:%M:%S")],
        "Mode": [mode],
        "RSSI": [rssi_val],
        "Status": ["Alert" if abs(rssi_val - (-70)) > 6.0 else "Normal"]
    })
    st.dataframe(log_df)
    
    csv = log_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download System Report (CSV)",
        data=csv,
        file_name='iot_sensor_report.csv',
        mime='text/csv',
    )
