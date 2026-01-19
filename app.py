import streamlit as st
import sys
from pathlib import Path
import os

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.messages = []
    st.session_state.user_type = None
    st.session_state.user_id = None

# Import server components
from server.config import settings
from server.ingest.indexer import DocumentIndexer
from server.qa.retriever import DocumentRetriever
from server.qa.llm import LLMClient
from server.cv.checker import check_cv
from server.teacher.pdf_manager import PDFManager
from server.teacher.pdf_metadata import PDFMetadataManager

# Initialize components (only once)
@st.cache_resource
def init_components():
    """Initialize RAG components"""
    indexer = DocumentIndexer()
    retriever = DocumentRetriever(indexer)
    
    # Initialize LLM client
    if settings.GROQ_API_KEY:
        llm_client = LLMClient(use_groq=True)
    elif settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "PUT_YOUR_GOOGLE_API_KEY_HERE":
        llm_client = LLMClient(use_google=True)
    else:
        llm_client = LLMClient(use_google=False)
    
    # Initialize PDF managers
    pdf_manager = PDFManager()
    pdf_metadata_manager = PDFMetadataManager()
    
    return indexer, retriever, llm_client, pdf_manager, pdf_metadata_manager

# Page configuration
st.set_page_config(
    page_title="Industrial Training FIST Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Initialize components
if not st.session_state.initialized:
    with st.spinner("Initializing system..."):
        indexer, retriever, llm_client, pdf_manager, pdf_metadata_manager = init_components()
        st.session_state.indexer = indexer
        st.session_state.retriever = retriever
        st.session_state.llm_client = llm_client
        st.session_state.pdf_manager = pdf_manager
        st.session_state.pdf_metadata_manager = pdf_metadata_manager
        st.session_state.initialized = True

# Sidebar for login
with st.sidebar:
    st.title("🔐 Login")
    
    if st.session_state.user_type is None:
        user_type = st.radio("User Type", ["Student", "Teacher"], key="login_type")
        user_id = st.text_input("User ID", key="login_id")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            # Teacher login
            if user_type == "Teacher" and user_id == "admin" and password == "admin123@":
                st.session_state.user_type = "teacher"
                st.session_state.user_id = "admin"
                st.success("Teacher login successful!")
                st.rerun()
            # Student login (simplified - you can add user database check)
            elif user_type == "Student":
                st.session_state.user_type = "student"
                st.session_state.user_id = user_id
                st.success("Student login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        st.success(f"Logged in as: {st.session_state.user_id}")
        st.write(f"Type: {st.session_state.user_type}")
        if st.button("Logout"):
            st.session_state.user_type = None
            st.session_state.user_id = None
            st.session_state.messages = []
            st.rerun()

# Main content
st.title("🤖 Industrial Training FIST Chatbot")

if st.session_state.user_type is None:
    st.info("Please login from the sidebar to continue.")
else:
    # Chat interface
    st.header("💬 Chat")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about Industrial Training..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    retriever = st.session_state.retriever
                    llm_client = st.session_state.llm_client
                    
                    if retriever and llm_client:
                        # Retrieve relevant chunks
                        chunks = retriever.retrieve_relevant_chunks(prompt, k=8)
                        
                        if chunks:
                            # Format context
                            context = retriever.format_context(chunks)
                            
                            # Generate response
                            llm_result = llm_client.generate_response(prompt, context, "en")
                            response = llm_result.get('response', 'Sorry, I could not generate a response.')
                        else:
                            response = "I couldn't find that in the Industrial Training documents. Please rephrase or ask another question."
                    else:
                        response = "System is still initializing. Please wait a moment and try again."
                    
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Teacher features
    if st.session_state.user_type == "teacher":
        st.divider()
        st.header("👨‍🏫 Teacher Dashboard")
        
        tab1, tab2, tab3 = st.tabs(["PDF Management", "Student Submissions", "Notifications"])
        
        with tab1:
            st.subheader("Upload PDF")
            uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
            pdf_type = st.selectbox("PDF Type", ["chatbot", "submission", "notification"])
            
            if st.button("Upload PDF") and uploaded_file:
                try:
                    pdf_manager = st.session_state.pdf_manager
                    pdf_content = uploaded_file.read()
                    result = pdf_manager.upload_pdf(
                        file_content=pdf_content,
                        filename=uploaded_file.name,
                        pdf_type=pdf_type,
                        uploaded_by="admin"
                    )
                    if result.get("success"):
                        st.success(f"PDF uploaded: {result['file_name']}")
                    else:
                        st.error(f"Upload failed: {result.get('error')}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            st.subheader("List PDFs")
            if st.button("Refresh PDF List"):
                try:
                    pdf_manager = st.session_state.pdf_manager
                    pdf_list = pdf_manager.list_pdfs(pdf_type)
                    st.write(f"Found {len(pdf_list)} PDFs")
                    for pdf in pdf_list:
                        st.write(f"- {pdf['file_name']}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with tab2:
            st.subheader("Student CV Submissions")
            st.info("Student submission management will be available here.")
        
        with tab3:
            st.subheader("Notifications")
            st.info("Notification management will be available here.")
    
    # Student features
    elif st.session_state.user_type == "student":
        st.divider()
        st.header("👨‍🎓 Student Dashboard")
        
        st.subheader("Submit CV")
        cv_file = st.file_uploader("Upload your CV (PDF)", type="pdf")
        if st.button("Submit CV") and cv_file:
            try:
                pdf_content = cv_file.read()
                pdf_manager = st.session_state.pdf_manager
                result = pdf_manager.upload_pdf(
                    file_content=pdf_content,
                    filename=cv_file.name,
                    pdf_type="submission",
                    uploaded_by=st.session_state.user_id
                )
                if result.get("success"):
                    st.success(f"CV submitted: {result['file_name']}")
                else:
                    st.error(f"Submission failed: {result.get('error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
