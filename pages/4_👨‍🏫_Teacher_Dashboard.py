"""Teacher Dashboard - PDF Management"""
import streamlit as st
from utils import require_teacher, api_call
from pathlib import Path

require_teacher()

# Page configuration
st.set_page_config(
    page_title="Teacher Dashboard - PDF Management",
    page_icon="👨‍🏫",
    layout="wide"
)

# Initialize session state
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "chatbot"

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← Back", key="back_teacher"):
        st.switch_page("pages/1_🏠_Home.py")
with col2:
    st.title("Teacher Dashboard - PDF Management")
with col3:
    if st.button("Logout", key="logout_teacher"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["📚 Chatbot PDFs", "📄 Verification CV/Resume PDFs", "🔔 Notification PDFs"])

pdf_types = {
    "📚 Chatbot PDFs": "chatbot",
    "📄 Verification CV/Resume PDFs": "submission",
    "🔔 Notification PDFs": "notification"
}

def render_pdf_tab(pdf_type: str, tab_label: str):
    """Render PDF management tab"""
    st.markdown(f"### Upload {tab_label}")
    st.caption(f"Upload PDF files that will be used as knowledge base for {tab_label.lower()}.")
    
    uploaded_file = st.file_uploader(
        "Choose a file or drag & drop it here",
        type=["pdf"],
        key=f"upload_{pdf_type}",
        help="PDF format only, up to 50MB"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(f"Upload", key=f"btn_upload_{pdf_type}", disabled=not uploaded_file):
            if uploaded_file:
                with st.spinner("Uploading PDF..."):
                    user_id = st.session_state.get("user_id", "teacher")
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    params = {"pdf_type": pdf_type, "user_id": user_id}
                    result = api_call("/api/teacher/upload-pdf", method="POST", files=files, params=params)
                    
                    if result.get("success"):
                        st.success(f"Successfully uploaded: {result.get('file_name', uploaded_file.name)}")
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {result.get('error', 'Unknown error')}")
    
    with col2:
        if st.button(f"Rebuild FAISS Index", key=f"btn_rebuild_{pdf_type}"):
            with st.spinner("Rebuilding FAISS index..."):
                result = api_call("/api/teacher/rebuild-faiss-index", method="POST", json_data={"pdf_type": pdf_type})
                if result.get("success"):
                    st.success("FAISS index rebuilt successfully!")
                else:
                    st.error(f"Rebuild failed: {result.get('error', 'Unknown error')}")
    
    st.markdown("---")
    
    # File list
    st.markdown(f"### {tab_label} Files")
    
    with st.spinner("Loading PDF list..."):
        result = api_call("/api/teacher/list-pdfs", method="GET", params={"pdf_type": pdf_type})
        
        if result.get("success"):
            files = result.get("files", [])
            st.metric("Total Files", len(files))
            
            if files:
                # File list with status
                for file_info in files:
                    with st.expander(f"📄 {file_info['file_name']} ({file_info.get('file_size', 0) / 1024:.1f} KB)", expanded=False):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            status = file_info.get("status", "pending")
                            status_colors = {
                                "success": "✅",
                                "failed": "❌",
                                "pending": "⏳"
                            }
                            st.write(f"Status: {status_colors.get(status, '⏳')} {status}")
                            if file_info.get("upload_time"):
                                st.caption(f"Uploaded: {file_info['upload_time']}")
                        
                        with col2:
                            if st.button(f"View", key=f"view_{pdf_type}_{file_info['file_name']}"):
                                # View PDF (would open in new tab in real implementation)
                                st.info(f"Viewing: {file_info['file_name']}")
                        
                        with col3:
                            if st.button(f"Delete", key=f"delete_{pdf_type}_{file_info['file_name']}"):
                                with st.spinner("Deleting..."):
                                    delete_result = api_call(
                                        "/api/teacher/delete-pdf",
                                        method="DELETE",
                                        params={"filename": file_info['file_name'], "pdf_type": pdf_type}
                                    )
                                    if delete_result.get("success"):
                                        st.success("File deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Delete failed: {delete_result.get('error', 'Unknown error')}")
            else:
                st.info("No files uploaded yet.")
        else:
            st.error(f"Error loading files: {result.get('error', 'Unknown error')}")
    
    # Student submissions (only for submission tab)
    if pdf_type == "submission":
        st.markdown("---")
        st.markdown("### Student Submission CV/Resume PDFs")
        
        with st.spinner("Loading student submissions..."):
            result = api_call("/api/teacher/list-student-submissions", method="GET")
            
            if result.get("success"):
                files = result.get("files", [])
                st.metric("Student Submissions", len(files))
                
                if files:
                    for file_info in files:
                        with st.expander(
                            f"👤 {file_info['file_name']} - Student: {file_info.get('uploaded_by', 'Unknown')}",
                            expanded=False
                        ):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"Student ID: {file_info.get('uploaded_by', 'Unknown')}")
                                if file_info.get("upload_time"):
                                    st.caption(f"Submitted: {file_info['upload_time']}")
                                if file_info.get("file_size"):
                                    st.caption(f"Size: {file_info['file_size'] / 1024:.1f} KB")
                            
                            with col2:
                                if st.button(f"View", key=f"view_student_{file_info['file_name']}"):
                                    st.info(f"Viewing: {file_info['file_name']}")
                else:
                    st.info("No student submissions yet.")

# Render tabs
with tab1:
    render_pdf_tab("chatbot", "Chatbot PDFs")

with tab2:
    render_pdf_tab("submission", "Verification CV/Resume PDFs")

with tab3:
    render_pdf_tab("notification", "Notification PDFs")

