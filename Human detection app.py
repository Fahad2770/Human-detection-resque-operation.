import streamlit as st
import pandas as pd
import requests
import time

st.set_page_config(page_title="Human Detector", page_icon="🚨", layout="centered")

st.title("🚨 Disaster Rescue: Wi-Fi Life Sign Monitor")
st.markdown("### ESP32 Sub-Debris Human Movement Tracker")

# Streamlit sidebar controls
st.sidebar.header("Control Panel")
sensitivity = st.sidebar.slider("Detection Sensitivity", 1.0, 10.0, 4.0)
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 2, 10, 5)

# Container for live status
status_placeholder = st.empty()
chart_placeholder = st.empty()

def fetch_esp32_data():
    try:
        # ThingSpeak public feed se data fetch kar rahe hain (Aap ise apne server se bhi badal sakte hain)
        url = "https://api.thingspeak.com/channels/YOUR_CHANNEL_ID/feeds.json?results=20"
        response = requests.get(url)
        data = response.json()
        
        rssi_values = []
        for feed in data['feeds']:
            val = feed['field1']
            if val is not None:
                rssi_values.append(float(val))
        return rssi_values
    except:
        # Agar internet ya server connection na ho to simulation data dikھaye ga
        return [-70, -71, -72, -69, -85, -60, -82, -70, -71, -70]

# Real-time monitoring loop
if st.button("Start Live Monitoring"):
    st.write("Connecting to ESP32 Cloud Feed...")
    
    for i in range(50):
        rssi_data = fetch_esp32_data()
        
        if len(rssi_data) > 2:
            # Variance / Fluctuation calculation (Insaan ki harkat check karne ke liye)
            mean_val = sum(rssi_data) / len(rssi_data)
            variance = sum((x - mean_val) ** 2 for x in rssi_data) / len(rssi_data)
            
            # Status check
            if variance > sensitivity:
                status_placeholder.error(f"🚨 **HIGH ALERT!** Malbe k neechy harakat mehsoos hui! (Variance: {variance:.2f})")
            else:
                status_placeholder.success(f"🟢 Status: Normal / Area Clear (Variance: {variance:.2f})")
                
            # Live Line Chart
            chart_data = pd.DataFrame(rssi_data, columns=["RSSI Signal Strength (dBm)"])
            chart_placeholder.line_chart(chart_data)
            
        time.sleep(refresh_rate)
else:
    st.info("Monitoring shuru karne ke liye upar diye gaye button par click کریں.")
