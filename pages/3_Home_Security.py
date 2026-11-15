import streamlit as st
import pandas as pd
import requests

st.title("🏠 Smart Home Security")
st.info("سیکیورٹی موڈ فعال ہے: گھر کے اندر غیر معمولی حرکت اور وائی فائی ڈسٹربنس پر نظر رکھی جا رہی ہے۔")

FIXED_CHANNEL_ID = "3579002"
READ_API_KEY_FIXED = "PVZCSGAU291YE5CF"
fixed_url = f"https://api.thingspeak.com/channels/{FIXED_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_FIXED}&results=1"

@st.cache_data(ttl=2)
def get_rssi():
    try:
        response = requests.get(fixed_url)
        data = response.json()
        feeds = data['feeds']
        if feeds:
            return float(feeds[-1]['field1'])
    except:
        pass
    return -70.0

rssi_val = get_rssi()
sec_val = float(rssi_val) if rssi_val else -70.0

security_data = pd.DataFrame({
    "Security Noise Level": [2, 4, 1, 5, 3, abs(sec_val + 75)]
})
st.area_chart(security_data)
