"""Home page - Main navigation hub"""
import streamlit as st
from pathlib import Path
from utils import require_login

require_login()

# Page configuration
st.set_page_config(
    page_title="Industrial Training FIST - Home",
    page_icon="🏠",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        height: 80px;
        font-size: 18px;
        font-weight: 600;
        border-radius: 50px;
        border: 3px solid #111827;
        background: white;
        color: #111827;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: #111827;
        color: white;
        transform: scale(1.05);
    }
    .robot-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 40px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("Welcome to Industrial Training")
    st.title("FIST")

# Logout button
col1, col2, col3 = st.columns([3, 1, 1])
with col3:
    if st.button("Logout", key="logout_btn"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

st.markdown("---")

# Robot image
robot_path = Path("web/assets/bot 1.png")
if robot_path.exists():
    st.image(str(robot_path), width=400)

# Navigation buttons based on user type
user_type = st.session_state.get("user_type", "student")

if user_type == "teacher":
    # Teacher interface
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📚 PDF Management", key="teacher_pdf", use_container_width=True):
            st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")
    with col2:
        if st.button("🔔 Notifications", key="teacher_notif", use_container_width=True):
            st.switch_page("pages/5_🔔_Notifications.py")
else:
    # Student interface
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🤖 Chatbot", key="student_chatbot", use_container_width=True):
            st.switch_page("pages/2_💬_Chatbot.py")
    with col2:
        if st.button("📄 Submission", key="student_submission", use_container_width=True):
            st.switch_page("pages/3_📄_Submission.py")

