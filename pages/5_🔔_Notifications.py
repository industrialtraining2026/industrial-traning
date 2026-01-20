"""Notifications Management page"""
import streamlit as st
from utils import require_teacher, api_call

require_teacher()

# Page configuration
st.set_page_config(
    page_title="Notification Management",
    page_icon="🔔",
    layout="wide"
)

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← Back", key="back_notif"):
        st.switch_page("pages/1_🏠_Home.py")
with col2:
    st.title("Notification Management")
with col3:
    if st.button("Logout", key="logout_notif"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

st.markdown("---")

# Section 1: Upload Student Email List
st.markdown("### 📧 Upload Student Email List")
st.caption("Upload a CSV or TXT file containing student email addresses.")

uploaded_email_file = st.file_uploader(
    "Choose a CSV or TXT file",
    type=["csv", "txt"],
    key="email_upload",
    help="CSV or TXT format"
)

if uploaded_email_file:
    st.info(f"Selected: {uploaded_email_file.name}")
    
    if st.button("Upload Email File", key="btn_upload_emails"):
        with st.spinner("Uploading email file..."):
            files = {"file": (uploaded_email_file.name, uploaded_email_file.getvalue(), uploaded_email_file.type)}
            result = api_call("/api/teacher/upload-emails", method="POST", files=files)
            
            if result.get("success"):
                st.success(
                    f"Successfully uploaded {result.get('valid_emails', 0)} valid email(s). "
                    f"{result.get('invalid_emails', 0)} invalid email(s) found."
                )
                if result.get("invalid_emails", 0) > 0 and result.get("invalid_email_list"):
                    with st.expander("View Invalid Emails"):
                        for email in result["invalid_email_list"]:
                            st.text(email)
            else:
                st.error(f"Upload failed: {result.get('error', 'Unknown error')}")

# List uploaded email files
st.markdown("---")
st.markdown("### 📋 Uploaded Email Files")

with st.spinner("Loading email files..."):
    result = api_call("/api/teacher/list-email-files", method="GET")
    
    if result.get("success"):
        files = result.get("files", [])
        st.metric("Total Email Files", len(files))
        
        if files:
            for file_info in files:
                with st.expander(f"📄 {file_info.get('filename', 'Unknown')}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"Valid Emails: {file_info.get('valid_emails', 0)}")
                        st.caption(f"Uploaded: {file_info.get('upload_time', 'Unknown')}")
                    with col2:
                        if st.button("Delete", key=f"delete_email_{file_info.get('filename', '')}"):
                            with st.spinner("Deleting..."):
                                delete_result = api_call(
                                    "/api/teacher/delete-email-file",
                                    method="DELETE",
                                    params={"filename": file_info.get('filename', '')}
                                )
                                if delete_result.get("success"):
                                    st.success("File deleted!")
                                    st.rerun()
                                else:
                                    st.error(f"Delete failed: {delete_result.get('error', 'Unknown error')}")
        else:
            st.info("No email files uploaded yet.")

# Section 2: Parse Deadline PDF
st.markdown("---")
st.markdown("### 📅 Parse Deadline Information")

col1, col2 = st.columns([2, 1])
with col1:
    st.caption("Parse deadline information from the latest notification PDF.")
with col2:
    if st.button("Parse Deadline PDF", key="btn_parse_deadline"):
        with st.spinner("Parsing deadline PDF..."):
            result = api_call("/api/teacher/parse-deadline-pdf", method="POST")
            
            if result.get("error"):
                st.error(f"Parse failed: {result['error']}")
            else:
                st.success("Deadline information parsed successfully!")
                
                if result.get("deadlines"):
                    with st.expander("View Parsed Deadlines"):
                        for deadline in result["deadlines"]:
                            st.write(f"**{deadline.get('title', 'Unknown')}**")
                            st.write(f"Deadline: {deadline.get('deadline_date', 'Unknown')}")
                            st.write(f"Description: {deadline.get('description', 'N/A')}")
                            st.markdown("---")

# Section 3: Notification Status
st.markdown("---")
st.markdown("### 📊 Notification Status")

with st.spinner("Loading notification status..."):
    result = api_call("/api/teacher/notification-status", method="GET")
    
    if result.get("error"):
        st.error(f"Error loading status: {result['error']}")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Students", result.get("total_students", 0))
        with col2:
            st.metric("Deadlines Found", result.get("deadlines_count", 0))
        with col3:
            status = result.get("scheduler_status", "unknown")
            st.metric("Scheduler Status", "🟢 Active" if status == "active" else "🔴 Inactive")
        
        if result.get("next_notification"):
            st.info(f"Next notification: {result['next_notification']}")
        
        if result.get("deadlines"):
            with st.expander("View Deadline Schedule"):
                for deadline in result["deadlines"]:
                    st.write(f"**{deadline.get('title', 'Unknown')}**")
                    st.write(f"Deadline: {deadline.get('deadline_date', 'Unknown')}")
                    st.write(f"Reminder Schedule: {deadline.get('reminder_schedule', 'N/A')}")
                    st.markdown("---")

# Section 4: Send Notification Manually
st.markdown("---")
st.markdown("### ✉️ Send Notification Manually")

col1, col2 = st.columns([2, 1])
with col1:
    reminder_type = st.selectbox(
        "Reminder Type",
        ["general", "deadline_reminder", "form_a", "form_b"],
        key="reminder_type_select"
    )
    st.caption("Select the type of notification to send.")
with col2:
    if st.button("Send Notification", key="btn_send_manual"):
        with st.spinner("Sending notification..."):
            result = api_call(
                "/api/teacher/send-notification",
                method="POST",
                json_data={"reminder_type": reminder_type}
            )
            
            if result.get("success"):
                st.success(f"Notification sent! {result.get('sent_count', 0)} email(s) sent.")
            else:
                st.error(f"Send failed: {result.get('error', 'Unknown error')}")

# Section 5: Notification History
st.markdown("---")
st.markdown("### 📜 Notification History")

with st.spinner("Loading notification history..."):
    result = api_call("/api/teacher/notification-history", method="GET", params={"limit": 50})
    
    if result.get("success"):
        history = result.get("history", [])
        st.metric("Total Notifications Sent", len(history))
        
        if history:
            for entry in history[:20]:  # Show last 20
                with st.expander(
                    f"📧 {entry.get('subject', 'Unknown')} - {entry.get('sent_time', 'Unknown')}",
                    expanded=False
                ):
                    st.write(f"**To:** {entry.get('recipient_count', 0)} recipients")
                    st.write(f"**Subject:** {entry.get('subject', 'N/A')}")
                    st.write(f"**Sent Time:** {entry.get('sent_time', 'N/A')}")
                    if entry.get("deadline_title"):
                        st.write(f"**Deadline:** {entry.get('deadline_title', 'N/A')}")
        else:
            st.info("No notification history yet.")
    else:
        st.error(f"Error loading history: {result.get('error', 'Unknown error')}")

