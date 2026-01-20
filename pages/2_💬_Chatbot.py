"""Chatbot page - Interactive Q&A with RAG"""
import streamlit as st
from utils import require_login, api_call

require_login()

# Page configuration
st.set_page_config(
    page_title="Industrial Training FIST - Chatbot",
    page_icon="💬",
    layout="wide"
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your Industrial Training assistant. Pick a topic or ask anything."}
    ]

# Initialize categories
if "categories" not in st.session_state:
    st.session_state.categories = [
        {
            "id": "overview",
            "label": "Internship Overview 📅",
            "keywords": ["internship", "industrial training", "overview"],
            "pool": [
                "What are the start and end dates of the ITP?",
                "What is the total duration of the ITP in weeks?",
                "What is the minimum credit hour requirement to join the ITP?",
                "Who must a student inform if they relocate to a different branch during the internship?",
                "What student behaviors in the first week are considered poor?",
                "What is the grading standard for the internship?"
            ]
        },
        {
            "id": "formA",
            "label": "Form A 📄",
            "keywords": ["form a", "forma", "form-a"],
            "pool": [
                "What is the submission deadline and time for Form A?",
                "What are the three required documents for Form A submission?",
                "What key information must be shown on the insurance document?",
                "How long does it take to prepare the ITP letter after submitting Form A?",
                "Besides the CV and academic transcript, what must students attach when applying to companies?",
                "What is the minimum number of companies students are advised to apply to?"
            ]
        },
        {
            "id": "formB",
            "label": "Form B 📋",
            "keywords": ["form b", "formb", "form-b"],
            "pool": [
                "What is the submission deadline for Form B?",
                "What are the four documents required for Form B submission?",
                "What specific internship duration must be stated in the company offer letter?",
                "Whose signature is required on the company offer letter besides the sender's?",
                "What is the critical submission constraint for Form B?",
                "Can a student change companies once placement is confirmed?"
            ]
        },
        {
            "id": "assessment",
            "label": "Assessment ✅",
            "keywords": ["assessment", "grading", "evaluation", "report", "presentation"],
            "pool": [
                "How many supervisors does a student have?",
                "Who is responsible for signing the Weekly Log and completing the Company Evaluation Form?",
                "Who determines the student's PASS/FAIL grade?",
                "What will automatically result in an ITP FAIL grade?",
                "When will the Faculty Visitation typically be held?",
                "How often must the Weekly Log be emailed to the Faculty Supervisor?"
            ]
        },
        {
            "id": "company",
            "label": "Company Search 🏢",
            "keywords": ["company", "host", "placement", "internship company", "employer"],
            "pool": [
                "What is the minimum number of permanent staff required for a company?",
                "Can the company supervisor be a student's close relative?",
                "Is the payment of an allowance by the company mandatory?",
                "Are non-IT jobs like sales or driver allowed for the ITP?",
                "Who must approve a student if they wish to leave their current placement?",
                "Can international students apply to a company in their home country?"
            ]
        }
    ]
    st.session_state.seen_questions = {cat["id"]: set() for cat in st.session_state.categories}
    st.session_state.current_category = None

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
    }
    .suggestion-btn {
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header with back button
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← Back", key="back_home"):
        st.switch_page("pages/1_🏠_Home.py")
with col2:
    st.title("Industrial Training FIST Chatbot")
with col3:
    if st.button("Logout", key="logout_chat"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

st.markdown("---")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Suggested questions section
st.markdown("### Suggested Questions")

# Show category buttons
if st.session_state.current_category is None:
    cols = st.columns(5)
    for i, cat in enumerate(st.session_state.categories):
        with cols[i % 5]:
            if st.button(cat["label"], key=f"cat_{cat['id']}"):
                st.session_state.current_category = cat["id"]
                st.rerun()
else:
    # Show questions for selected category
    cat = next((c for c in st.session_state.categories if c["id"] == st.session_state.current_category), None)
    if cat:
        if st.button("← Back to Categories", key="back_cat"):
            st.session_state.current_category = None
            st.rerun()
        
        st.markdown(f"**{cat['label']} questions:**")
        
        # Get questions that haven't been asked
        asked_questions = set()
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                asked_questions.add(msg["content"])
        
        available_questions = [q for q in cat["pool"] if q not in asked_questions][:3]
        if not available_questions:
            available_questions = cat["pool"][:3]  # Reset if all asked
        
        for q in available_questions:
            if st.button(q, key=f"q_{hash(q)}"):
                # Add user message and get response
                st.session_state.messages.append({"role": "user", "content": q})
                st.session_state.seen_questions[cat["id"]].add(q)
                st.rerun()

# Chat input
if prompt := st.chat_input("Type a new message here"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Process last user message if it's new
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_message = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = api_call("/api/chat", method="POST", json_data={"message": user_message})
            
            if "error" in result:
                response = f"⚠️ {result['error']}"
            else:
                response = result.get("reply", "Sorry, I couldn't generate a response.")
            
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Reset category selection after asking a question
            st.session_state.current_category = None
            st.rerun()

# Robot image in sidebar
with st.sidebar:
    from pathlib import Path
    robot_path = Path("web/assets/bot.png")
    if robot_path.exists():
        st.image(str(robot_path))

