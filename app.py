import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

# 1. Config and Auto-Refresh (Essential for real-time updates)
st.set_page_config(page_title="Real-Time Auction", page_icon="🔨")
st_autorefresh(interval=2000, key="datarefresh") 

st.title("🔨 Real-Time Auction House")

