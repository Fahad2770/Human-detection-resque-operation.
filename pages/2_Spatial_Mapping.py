import streamlit as st
import pandas as pd
import requests

st.title("📍 Spatial Grid & Target Mapping")
st.markdown("Coordinates fetched live from Mobile Worker ESP-32 (Channel 3579370).")

MOBILE_CHANNEL_ID = "3579370"
READ_API_KEY_MOBILE = "H696MBRW1ASMZZ3W"
mobile_url = f"https://api.thingspeak.com/channels/{MOBILE_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY_MOBILE}&results=1"

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

grid_data = pd.DataFrame({
    'X': [worker_x],
    'Y': [worker_y],
    'Color': ['red']
})
st.scatter_chart(grid_data, x='X', y='Y', color='Color', size=150)
st.success(f"📌 **Current Worker Position ->** X-Axis: {worker_x} | Y-Axis: {worker_y}")
