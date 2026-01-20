"""Shared utilities for Streamlit pages"""
import requests
from pathlib import Path
import streamlit as st

# API base URL - use relative path for cloud deployment
API_BASE = "http://127.0.0.1:8000"  # For local development, can be changed to "" for cloud

def api_call(endpoint: str, method: str = "GET", json_data: dict = None, files: dict = None, params: dict = None):
    """Make API call to FastAPI backend"""
    try:
        url = f"{API_BASE}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, data=params, timeout=30)
            else:
                response = requests.post(url, json=json_data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, params=params, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                return {"success": True, "data": response.text}
        else:
            try:
                error_data = response.json()
                return {"error": error_data.get("detail", f"HTTP {response.status_code}")}
            except:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to server. Please ensure the backend is running."}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout. Please try again."}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def check_login():
    """Check if user is logged in"""
    if "user_id" not in st.session_state or "user_type" not in st.session_state:
        return False
    return True

def require_login():
    """Redirect to login if not logged in"""
    if not check_login():
        st.switch_page("app.py")

def require_teacher():
    """Redirect to home if not teacher"""
    require_login()
    if st.session_state.get("user_type") != "teacher":
        st.error("Access denied. Teacher access required.")
        st.switch_page("pages/1_🏠_Home.py")
        st.stop()

