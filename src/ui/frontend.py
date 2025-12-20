# frontend.py
import os
import sys
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import requests
from config.config import load_config

conf = load_config()

# Backend API URL
API_URL = f"http://{conf.get_value(conf.environment.fast_api.server)}:{str(conf.get_value(conf.environment.fast_api.port))}"

st.title("Streamlit + FastAPI Demo")

# Check backend status
try:
    status = requests.get(API_URL).json()
    st.success(f"Backend says: {status['message']}")
except Exception as e:
    st.error(f"Could not connect to backend: {e}")

# User input
# Input fields
text = st.text_input("Enter text to process")
task_id = st.number_input("Enter task_id", step=1)

if st.button("Process"):
    if text.strip():
        try:
            payload = {"text": text, "task_id": int(task_id)}
            response = requests.post(f"{API_URL}/process_data", json=payload)
            if response.status_code == 200:
                data = response.json()
                st.success("Data sent successfully!")
                st.json(response.json())  # Display JSON response
            else:
                st.error(f"Error: {response.status_code}")
        except Exception as e:
            st.error(f"Request failed: {e}")
    else:
        st.warning("Please enter some text.")

