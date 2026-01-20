"""Shared utilities for Streamlit pages"""
from pathlib import Path
import streamlit as st

# Import direct backend functions (no HTTP API needed)
from backend_direct import (
    backend_login,
    backend_register,
    backend_chat,
    backend_cv_check,
    backend_student_submit_cv,
    backend_teacher_upload_pdf,
    backend_teacher_list_pdfs,
    backend_teacher_delete_pdf,
    backend_teacher_rebuild_faiss_index,
    backend_teacher_list_student_submissions,
    backend_teacher_upload_emails,
    backend_teacher_list_email_files,
    backend_teacher_delete_email_file,
    backend_teacher_parse_deadline_pdf,
    backend_teacher_notification_status,
    backend_teacher_send_notification,
    backend_teacher_notification_history,
)

def api_call(endpoint: str, method: str = "GET", json_data: dict = None, files: dict = None, params: dict = None):
    """Call backend functions directly (no HTTP API needed)"""
    try:
        # Login endpoints
        if endpoint == "/api/login" and method == "POST":
            return backend_login(json_data.get("user_id", ""), json_data.get("password", ""))
        
        elif endpoint == "/api/register" and method == "POST":
            return backend_register(json_data.get("user_id", ""), json_data.get("password", ""))
        
        # Chat endpoint
        elif endpoint == "/api/chat" and method == "POST":
            return backend_chat(json_data.get("message", ""))
        
        # CV check endpoint
        elif endpoint == "/api/cv-check" and method == "POST":
            if files and "file" in files:
                file_tuple = files["file"]
                if isinstance(file_tuple, tuple) and len(file_tuple) >= 2:
                    filename = file_tuple[0]
                    file_content = file_tuple[1]
                    return backend_cv_check(file_content, filename)
            return {"error": "No file provided"}
        
        # Student submit CV endpoint
        elif endpoint == "/api/student/submit-cv" and method == "POST":
            if files and "file" in files:
                file_tuple = files["file"]
                if isinstance(file_tuple, tuple) and len(file_tuple) >= 2:
                    filename = file_tuple[0]
                    file_content = file_tuple[1]
                    user_id = params.get("user_id", "") if params else ""
                    return backend_student_submit_cv(file_content, filename, user_id)
            return {"error": "No file provided"}
        
        # Teacher PDF management endpoints
        elif endpoint == "/api/teacher/upload-pdf" and method == "POST":
            if files and "file" in files:
                file_tuple = files["file"]
                if isinstance(file_tuple, tuple) and len(file_tuple) >= 2:
                    filename = file_tuple[0]
                    file_content = file_tuple[1]
                    pdf_type = params.get("pdf_type", "") if params else ""
                    user_id = params.get("user_id", "teacher") if params else "teacher"
                    return backend_teacher_upload_pdf(file_content, filename, pdf_type, user_id)
            return {"error": "No file provided"}
        
        elif endpoint == "/api/teacher/list-pdfs" and method == "GET":
            pdf_type = params.get("pdf_type", "") if params else ""
            return backend_teacher_list_pdfs(pdf_type)
        
        elif endpoint == "/api/teacher/delete-pdf" and method == "DELETE":
            filename = params.get("filename", "") if params else ""
            pdf_type = params.get("pdf_type", "") if params else ""
            return backend_teacher_delete_pdf(filename, pdf_type)
        
        elif endpoint == "/api/teacher/rebuild-faiss-index" and method == "POST":
            pdf_type = json_data.get("pdf_type", "") if json_data else ""
            return backend_teacher_rebuild_faiss_index(pdf_type)
        
        elif endpoint == "/api/teacher/list-student-submissions" and method == "GET":
            return backend_teacher_list_student_submissions()
        
        # Teacher notification endpoints
        elif endpoint == "/api/teacher/upload-emails" and method == "POST":
            if files and "file" in files:
                file_tuple = files["file"]
                if isinstance(file_tuple, tuple) and len(file_tuple) >= 2:
                    filename = file_tuple[0]
                    file_content = file_tuple[1]
                    return backend_teacher_upload_emails(file_content, filename)
            return {"error": "No file provided"}
        
        elif endpoint == "/api/teacher/list-email-files" and method == "GET":
            return backend_teacher_list_email_files()
        
        elif endpoint == "/api/teacher/delete-email-file" and method == "DELETE":
            filename = params.get("filename", "") if params else ""
            return backend_teacher_delete_email_file(filename)
        
        elif endpoint == "/api/teacher/parse-deadline-pdf" and method == "POST":
            return backend_teacher_parse_deadline_pdf()
        
        elif endpoint == "/api/teacher/notification-status" and method == "GET":
            return backend_teacher_notification_status()
        
        elif endpoint == "/api/teacher/send-notification" and method == "POST":
            reminder_type = json_data.get("reminder_type", "general") if json_data else "general"
            return backend_teacher_send_notification(reminder_type)
        
        elif endpoint == "/api/teacher/notification-history" and method == "GET":
            limit = params.get("limit", 50) if params else 50
            return backend_teacher_notification_history(limit)
        
        else:
            return {"error": f"Unknown endpoint: {endpoint} {method}"}
    
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

