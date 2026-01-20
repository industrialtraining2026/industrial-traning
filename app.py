"""Main login page for Industrial Training FIST Chatbot"""
import streamlit as st
from pathlib import Path
from utils import api_call, check_login

# Page configuration
st.set_page_config(
    page_title="Industrial Training FIST - Login",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for login page
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Center content */
    .main {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
    }
    
    /* Login container styling */
    .login-container {
        background: white;
        border-radius: 16px;
        padding: 40px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        max-width: 400px;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Check if already logged in
if check_login():
    st.switch_page("pages/1_🏠_Home.py")

# Display MMU logo if exists
logo_path = Path("web/assets/mmu logo.png")
if logo_path.exists():
    st.image(str(logo_path), width=320)

# Login container
with st.container():
    # Logo section
    col1, col2 = st.columns([1, 3])
    with col1:
        bot_logo_path = Path("web/assets/bot 3.png")
        if bot_logo_path.exists():
            st.image(str(bot_logo_path), width=80)
    
    with col2:
        st.markdown("### Industrial Training")
        st.markdown("### FIST")
    
    st.markdown("---")
    
    # Initialize session state for signup mode
    if "signup_mode" not in st.session_state:
        st.session_state.signup_mode = False
    
    # Toggle signup/login mode
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True, disabled=not st.session_state.signup_mode):
            st.session_state.signup_mode = False
            st.rerun()
    with col2:
        if st.button("Sign Up", use_container_width=True, disabled=st.session_state.signup_mode):
            st.session_state.signup_mode = True
            st.rerun()
    
    # Form
    with st.form("login_form"):
        user_id = st.text_input("ID", key="login_user_id")
        password = st.text_input("Password", type="password", key="login_password")
        
        submit_button = st.form_submit_button(
            "Sign Up" if st.session_state.signup_mode else "Login",
            use_container_width=True
        )
        
        if submit_button:
            if not user_id or not password:
                st.error("Please fill in all fields")
            else:
                # Show loading
                with st.spinner("Processing..."):
                    endpoint = "/api/register" if st.session_state.signup_mode else "/api/login"
                    result = api_call(endpoint, method="POST", json_data={
                        "user_id": user_id.strip(),
                        "password": password,
                        "user_type": "student" if st.session_state.signup_mode else None
                    })
                    
                    if result.get("success"):
                        # Store user info in session state
                        st.session_state.user_id = result["user_id"]
                        st.session_state.user_type = result["user_type"]
                        
                        if st.session_state.signup_mode:
                            st.success("Registration successful! Redirecting to login...")
                            st.session_state.signup_mode = False
                            st.rerun()
                        else:
                            # Redirect to home
                            st.success("Login successful! Redirecting...")
                            st.rerun()
                            st.switch_page("pages/1_🏠_Home.py")
                    else:
                        st.error(result.get("message", result.get("error", "Login failed")))

