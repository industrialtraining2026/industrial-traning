"""CV/Resume submission and verification page"""
import streamlit as st
from pathlib import Path
from utils import require_login, api_call

require_login()

# Page configuration
st.set_page_config(
    page_title="Industrial Training FIST - CV Verification",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .success-box {
        padding: 15px;
        border-radius: 8px;
        background: #d1fae5;
        color: #065f46;
        margin: 10px 0;
    }
    .warning-box {
        padding: 15px;
        border-radius: 8px;
        background: #fef3c7;
        color: #92400e;
        margin: 10px 0;
    }
    .error-box {
        padding: 15px;
        border-radius: 8px;
        background: #fee2e2;
        color: #991b1b;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← Back", key="back_submission"):
        st.switch_page("pages/1_🏠_Home.py")
with col2:
    st.title("Industrial Training FIST Verification CV/Resume")
with col3:
    if st.button("Logout", key="logout_submission"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

st.markdown("---")

def display_cv_result(result):
    """Display CV verification result"""
    if result.get("error"):
        st.markdown(f'<div class="error-box">{result["error"]}</div>', unsafe_allow_html=True)
        return
    
    if result.get("is_complete"):
        st.markdown(
            '<div class="success-box">✅ Your CV appears to be complete! It contains all the required sections.</div>',
            unsafe_allow_html=True
        )
        
        if result.get("missing_optional_sections"):
            st.markdown(
                '<div class="warning-box">💡 Suggestion: Consider adding Activities section to make your CV more impressive!</div>',
                unsafe_allow_html=True
            )
        
        if result.get("found_sections"):
            st.success(f"**Found required sections:** {', '.join(result['found_sections'])}")
    else:
        st.markdown(
            f'<div class="warning-box">⚠️ Your CV seems to be missing {len(result.get("missing_sections", []))} required section(s):</div>',
            unsafe_allow_html=True
        )
        
        reqs = result.get("section_requirements", {})
        
        for section in result.get("missing_sections", []):
            if section == "CGPA/GPA":
                with st.expander(f"❌ CGPA/GPA", expanded=True):
                    st.markdown("**Description:** Your academic performance indicator (required regardless of score).")
                    st.markdown("**This section should include:**")
                    st.markdown("- CGPA/GPA score (e.g., 3.5/4.0, 3.75, 2.8)")
                    st.markdown("- Must be included in your CV (regardless of score)")
                    st.markdown("- Can be placed in Education section")
            elif reqs.get(section):
                req = reqs[section]
                with st.expander(f"❌ {req.get('title', section)}", expanded=True):
                    st.markdown(f"**Description:** {req.get('description', '')}")
                    st.markdown("**This section should include:**")
                    for item in req.get("should_include", []):
                        st.markdown(f"- {item}")
        
        if result.get("found_sections"):
            st.success(f"**✅ Found required sections:** {', '.join(result['found_sections'])}")
    
    if result.get("text_length"):
        st.caption(f"Text extracted: {result['text_length']:,} characters")

# Two columns layout
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📤 Upload Files")
    st.markdown("Select and upload the files of your choice.")
    
    uploaded_file = st.file_uploader(
        "Choose a file or drag & drop it here",
        type=["pdf"],
        help="PDF format only, up to 50MB"
    )
    
    if uploaded_file:
        st.info(f"Selected: {uploaded_file.name}")

with col2:
    st.markdown("### 📋 Verification CV/Resume Result")
    
    if "cv_result" not in st.session_state:
        st.info("Upload a CV file to check")
    else:
        result = st.session_state.cv_result
        display_cv_result(result)
    
    # Robot image
    bot_path = Path("web/assets/bot 2.png")
    if bot_path.exists():
        st.image(str(bot_path), width=80)

st.markdown("---")

# Buttons
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Verify CV", use_container_width=True, disabled=not uploaded_file):
        if uploaded_file:
            with st.spinner("Checking your CV..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                result = api_call("/api/cv-check", method="POST", files=files)
                st.session_state.cv_result = result
                st.rerun()

with col2:
    if st.button("Submit to Teacher", use_container_width=True, disabled=not uploaded_file):
        if uploaded_file:
            user_id = st.session_state.get("user_id")
            if not user_id:
                st.error("Please login again.")
                st.switch_page("app.py")
                st.stop()
            
            with st.spinner("Submitting your CV to teacher..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                params = {"user_id": user_id}
                result = api_call("/api/student/submit-cv", method="POST", files=files, params=params)
                
                if result.get("success"):
                    st.success(f"Successfully submitted to teacher: {result.get('file_name', uploaded_file.name)}")
                else:
                    st.error(f"Error submitting CV: {result.get('error', 'Unknown error')}")

