"""Direct backend function calls for Streamlit (no HTTP API needed)"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import io

# Import backend modules
from server.config import settings
from server.ingest.indexer import DocumentIndexer
from server.qa.retriever import DocumentRetriever
from server.qa.llm import LLMClient
from server.cv.checker import check_cv
from server.teacher.pdf_manager import PDFManager
from server.teacher.pdf_metadata import PDFMetadataManager
from server.notification.deadline_parser import DeadlineParser
from server.notification.student_parser import StudentEmailParser
from server.notification.email_sender import EmailSender
from server.notification.scheduler import NotificationScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEACHER_ID = "admin"
TEACHER_PASSWORD = "admin123@"

# Global instances (initialized on first use)
_indexer = None
_retriever = None
_llm_client = None
_pdf_manager = None
_pdf_metadata_manager = None
_notification_scheduler = None

# User storage
USERS_FILE = Path(__file__).parent / "data" / "users.json"
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_users():
    """Load users from JSON file"""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def init_users():
    """Initialize users file if it doesn't exist"""
    users = load_users()
    if not users:
        users = {
            TEACHER_ID: {
                "password": TEACHER_PASSWORD,
                "user_type": "teacher"
            }
        }
        save_users(users)
    return users

def get_indexer():
    """Get or initialize DocumentIndexer"""
    global _indexer
    if _indexer is None:
        _indexer = DocumentIndexer()
        logger.info("DocumentIndexer initialized")
    return _indexer

def get_retriever():
    """Get or initialize DocumentRetriever"""
    global _retriever
    if _retriever is None:
        indexer = get_indexer()
        _retriever = DocumentRetriever(indexer)
        logger.info("DocumentRetriever initialized")
    return _retriever

def get_llm_client():
    """Get or initialize LLMClient"""
    global _llm_client
    if _llm_client is None:
        try:
            if settings.GROQ_API_KEY:
                _llm_client = LLMClient(use_groq=True)
                if _llm_client.use_groq and _llm_client.groq_client:
                    logger.info("Using Groq (Llama)")
                elif _llm_client.use_google:
                    logger.info("Using Google AI (Gemini) as fallback")
                elif _llm_client.api_key:
                    logger.info("Using OpenAI as fallback")
                else:
                    logger.info("Using local fallback")
            elif settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "PUT_YOUR_GOOGLE_API_KEY_HERE":
                _llm_client = LLMClient(use_google=True)
                logger.info("Using Google AI (Gemini)")
            else:
                _llm_client = LLMClient(use_google=False)
                logger.info("Using OpenAI or local fallback")
        except Exception as e:
            logger.error(f"Error initializing LLM client: {str(e)}")
            _llm_client = LLMClient(use_google=False)
            logger.info("Using local fallback due to initialization error")
    return _llm_client

def get_pdf_manager():
    """Get or initialize PDFManager"""
    global _pdf_manager
    if _pdf_manager is None:
        _pdf_manager = PDFManager()
        logger.info("PDFManager initialized")
    return _pdf_manager

def get_pdf_metadata_manager():
    """Get or initialize PDFMetadataManager"""
    global _pdf_metadata_manager
    if _pdf_metadata_manager is None:
        _pdf_metadata_manager = PDFMetadataManager()
        logger.info("PDFMetadataManager initialized")
    return _pdf_metadata_manager

def get_notification_scheduler():
    """Get or initialize NotificationScheduler"""
    global _notification_scheduler
    if _notification_scheduler is None:
        _notification_scheduler = NotificationScheduler()
        _notification_scheduler.start()
        logger.info("NotificationScheduler initialized")
    return _notification_scheduler

# Initialize users on import
init_users()

# Backend functions (matching API endpoints)
def backend_login(user_id: str, password: str) -> Dict[str, Any]:
    """Login function"""
    user_id = user_id.strip()
    
    # Teacher login
    if user_id == TEACHER_ID and password == TEACHER_PASSWORD:
        return {
            "success": True,
            "message": "Teacher login successful",
            "user_id": user_id,
            "user_type": "teacher"
        }
    
    # Student login
    users = load_users()
    if user_id in users and users[user_id]["password"] == password:
        return {
            "success": True,
            "message": "Student login successful",
            "user_id": user_id,
            "user_type": "student"
        }
    
    return {
        "success": False,
        "message": "Invalid user ID or password"
    }

def backend_register(user_id: str, password: str) -> Dict[str, Any]:
    """Register function"""
    users = load_users()
    user_id = user_id.strip()
    
    if not user_id:
        return {"success": False, "message": "User ID cannot be empty"}
    
    if user_id == TEACHER_ID:
        return {"success": False, "message": "This user ID is reserved"}
    
    if user_id in users:
        return {"success": False, "message": "User ID already exists"}
    
    users[user_id] = {
        "password": password,
        "user_type": "student"
    }
    save_users(users)
    
    return {
        "success": True,
        "message": "Student registration successful",
        "user_id": user_id,
        "user_type": "student"
    }

def backend_chat(message: str) -> Dict[str, Any]:
    """Chat function"""
    text = (message or "").strip()
    lang = "en"
    
    retriever = get_retriever()
    llm_client = get_llm_client()
    
    if not retriever or not llm_client:
        return {"reply": "System is still initializing. Please wait a moment and try again.", "language": lang}
    
    if not text:
        return {"reply": "Hi! I'm your Industrial Training assistant. You can start asking questions anytime.", "language": lang}
    
    # Check for farewell keywords
    farewell_map = {"en": ["bye", "goodbye", "thank you", "thanks"]}
    lowered = text.lower()
    if any(k in lowered for k in farewell_map.get(lang, [])):
        return {"reply": "Thanks for chatting! If you have more questions, just ask anytime.", "language": lang}
    
    try:
        # Retrieve relevant chunks
        chunks = retriever.retrieve_relevant_chunks(text, k=8)
        
        if not chunks:
            return {"reply": "I couldn't find that in the Industrial Training documents. Please rephrase or ask another question.", "language": lang}
        
        # Format context
        context = retriever.format_context(chunks)
        
        # Generate response using LLM
        llm_result = llm_client.generate_response(text, context, lang)
        reply = llm_result.get('response', 'Sorry, I could not generate a response.')
        
        # If confidence is low, add a clarification
        confidence = llm_result.get('confidence', 0.0)
        if confidence < 0.3:
            reply += " Could you provide more specific details about what you're looking for?"
        
        return {"reply": reply, "language": lang}
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {"reply": "Sorry, I encountered an error while processing your question. Please try again.", "language": lang}

def backend_cv_check(file_content: bytes, filename: str) -> Dict[str, Any]:
    """CV check function"""
    try:
        result = check_cv(file_content)
        return result
    except Exception as e:
        logger.error(f"CV check error: {str(e)}")
        return {"error": f"Error processing CV: {str(e)}"}

def backend_student_submit_cv(file_content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
    """Student submit CV function"""
    if not filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}
    
    if not user_id:
        return {"error": "Missing user_id"}
    
    try:
        pdf_manager = get_pdf_manager()
        pdf_metadata_manager = get_pdf_metadata_manager()
        
        result = pdf_manager.upload_pdf(
            file_content=file_content,
            filename=filename,
            pdf_type="submission",
            uploaded_by=user_id,
        )
        
        if not result.get("success"):
            return {"error": result.get("error", "Upload failed")}
        
        # Store metadata
        pdf_metadata_manager.add_pdf_metadata(
            filename=result["file_name"],
            pdf_type="submission",
            file_size=result["file_size"],
            uploaded_by=user_id,
        )
        pdf_metadata_manager.update_pdf_status(
            filename=result["file_name"],
            pdf_type="submission",
            status_type="upload_status",
            status="success",
        )
        
        return {
            "success": True,
            "file_name": result["file_name"],
            "pdf_type": "submission",
        }
    except Exception as e:
        logger.error(f"Student CV submit error: {str(e)}")
        return {"error": f"Error submitting CV: {str(e)}"}

# Teacher functions (simplified - add more as needed)
def backend_teacher_upload_pdf(file_content: bytes, filename: str, pdf_type: str, user_id: str = "teacher") -> Dict[str, Any]:
    """Teacher upload PDF function"""
    if pdf_type not in ["chatbot", "submission", "notification"]:
        return {"error": "Invalid pdf_type. Must be: chatbot, submission, or notification"}
    
    if not filename.endswith('.pdf'):
        return {"error": "Only PDF files are supported"}
    
    try:
        pdf_manager = get_pdf_manager()
        pdf_metadata_manager = get_pdf_metadata_manager()
        
        result = pdf_manager.upload_pdf(
            file_content=file_content,
            filename=filename,
            pdf_type=pdf_type,
            uploaded_by=user_id
        )
        
        if not result.get("success"):
            return {"error": result.get("error", "Upload failed")}
        
        # Save metadata
        pdf_metadata_manager.add_pdf_metadata(
            filename=result["file_name"],
            pdf_type=pdf_type,
            file_size=result["file_size"],
            uploaded_by=user_id
        )
        
        pdf_metadata_manager.update_pdf_status(
            filename=result["file_name"],
            pdf_type=pdf_type,
            status_type="upload_status",
            status="success"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"PDF upload error: {str(e)}")
        return {"error": f"Error uploading PDF: {str(e)}"}

def backend_teacher_list_pdfs(pdf_type: str) -> Dict[str, Any]:
    """Teacher list PDFs function"""
    if pdf_type not in ["chatbot", "submission", "notification"]:
        return {"error": "Invalid pdf_type. Must be: chatbot, submission, or notification"}
    
    try:
        pdf_manager = get_pdf_manager()
        pdf_metadata_manager = get_pdf_metadata_manager()
        
        pdf_list = pdf_manager.list_pdfs(pdf_type)
        metadata_list = pdf_metadata_manager.list_pdf_metadata(pdf_type)
        metadata_dict = {item["file_name"]: item for item in metadata_list if "file_name" in item}
        
        # Merge file info with metadata
        for pdf in pdf_list:
            if pdf["file_name"] in metadata_dict:
                pdf["upload_status"] = metadata_dict[pdf["file_name"]].get("upload_status")
                pdf["rebuild_status"] = metadata_dict[pdf["file_name"]].get("rebuild_status")
                pdf["delete_status"] = metadata_dict[pdf["file_name"]].get("delete_status")
                pdf["status"] = pdf.get("delete_status") or pdf.get("rebuild_status") or pdf.get("upload_status") or "pending"
                if pdf.get("delete_status"):
                    pdf["last_action"] = "delete"
                elif pdf.get("rebuild_status"):
                    pdf["last_action"] = "rebuild"
                elif pdf.get("upload_status"):
                    pdf["last_action"] = "upload"
                else:
                    pdf["last_action"] = "none"
            else:
                pdf["status"] = "pending"
                pdf["last_action"] = "none"
        
        return {
            "success": True,
            "pdf_type": pdf_type,
            "files": pdf_list,
            "count": len(pdf_list)
        }
    except Exception as e:
        logger.error(f"List PDFs error: {str(e)}")
        return {"error": f"Error listing PDFs: {str(e)}"}

def backend_teacher_delete_pdf(filename: str, pdf_type: str) -> Dict[str, Any]:
    """Teacher delete PDF function"""
    if pdf_type not in ["chatbot", "submission", "notification"]:
        return {"error": "Invalid pdf_type. Must be: chatbot, submission, or notification"}
    
    try:
        pdf_manager = get_pdf_manager()
        pdf_metadata_manager = get_pdf_metadata_manager()
        
        result = pdf_manager.delete_pdf(filename, pdf_type)
        
        if not result.get("success"):
            return {"error": result.get("error", "File not found")}
        
        # Remove metadata
        pdf_metadata_manager.remove_pdf_metadata(filename, pdf_type)
        
        return result
        
    except Exception as e:
        logger.error(f"Delete PDF error: {str(e)}")
        return {"error": f"Error deleting PDF: {str(e)}"}

def backend_teacher_rebuild_faiss_index(pdf_type: str) -> Dict[str, Any]:
    """Teacher rebuild FAISS index function"""
    if pdf_type not in ["chatbot", "submission", "notification"]:
        return {"error": "Invalid pdf_type. Must be: chatbot, submission, or notification"}
    
    try:
        indexer = get_indexer()
        pdf_manager = get_pdf_manager()
        pdf_metadata_manager = get_pdf_metadata_manager()
        
        target_dir = pdf_manager.get_directory(pdf_type)
        
        # Clear old index
        indexer.clear_index(pdf_type=pdf_type)
        logger.info(f"Cleared old index for {pdf_type}")
        
        # Reindex all PDFs
        result = indexer.index_directory(str(target_dir), pdf_type=pdf_type)
        logger.info(f"Reindexed {pdf_type} PDFs from: {target_dir}")
        
        # Update rebuild status
        pdf_list = pdf_manager.list_pdfs(pdf_type)
        for pdf_info in pdf_list:
            pdf_metadata_manager.update_pdf_status(
                filename=pdf_info["file_name"],
                pdf_type=pdf_type,
                status_type="rebuild_status",
                status="success" if result.get("processed_files", 0) > 0 else "failed"
            )
        
        return {"success": True, "result": result, "pdf_type": pdf_type}
        
    except Exception as e:
        logger.error(f"Rebuild FAISS index error: {str(e)}")
        return {"error": str(e)}

def backend_teacher_list_student_submissions() -> Dict[str, Any]:
    """Teacher list student submissions function"""
    pdf_type = "submission"
    try:
        pdf_manager = get_pdf_manager()
        pdf_metadata_manager = get_pdf_metadata_manager()
        
        pdf_list = pdf_manager.list_pdfs(pdf_type)
        metadata_list = pdf_metadata_manager.list_pdf_metadata(pdf_type)
        metadata_dict = {item["file_name"]: item for item in metadata_list if "file_name" in item}
        
        student_files = []
        for pdf in pdf_list:
            meta = metadata_dict.get(pdf["file_name"])
            if meta and meta.get("uploaded_by") != TEACHER_ID:
                combined = pdf.copy()
                combined["uploaded_by"] = meta.get("uploaded_by")
                combined["upload_time"] = meta.get("upload_time", combined.get("upload_time"))
                student_files.append(combined)
        
        return {
            "success": True,
            "pdf_type": pdf_type,
            "files": student_files,
            "count": len(student_files),
        }
    except Exception as e:
        logger.error(f"List student submissions error: {str(e)}")
        return {"error": f"Error listing student submissions: {str(e)}"}

# Notification functions (simplified)
def backend_teacher_upload_emails(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Teacher upload emails function"""
    try:
        student_parser = StudentEmailParser()
        result = student_parser.parse_email_file(file_content, filename, save_file=True)
        return result if result.get("success") else {"error": result.get("error", "Failed to parse email file")}
    except Exception as e:
        logger.error(f"Upload emails error: {str(e)}")
        return {"error": f"Error uploading emails: {str(e)}"}

def backend_teacher_list_email_files() -> Dict[str, Any]:
    """Teacher list email files function"""
    try:
        student_parser = StudentEmailParser()
        files = student_parser.list_uploaded_files()
        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"List email files error: {str(e)}")
        return {"error": f"Error listing email files: {str(e)}"}

def backend_teacher_delete_email_file(filename: str) -> Dict[str, Any]:
    """Teacher delete email file function"""
    try:
        student_parser = StudentEmailParser()
        result = student_parser.delete_uploaded_file(filename)
        return result if result.get("success") else {"error": result.get("error", "File not found")}
    except Exception as e:
        logger.error(f"Delete email file error: {str(e)}")
        return {"error": f"Error deleting email file: {str(e)}"}

def backend_teacher_parse_deadline_pdf() -> Dict[str, Any]:
    """Teacher parse deadline PDF function"""
    try:
        deadline_parser = DeadlineParser()
        result = deadline_parser.parse_deadline_pdf()
        
        if result.get("error"):
            return {"error": result.get("error")}
        
        # Save deadline info
        scheduler = get_notification_scheduler()
        if scheduler:
            scheduler.save_deadline_info(result)
        
        return result
    except Exception as e:
        logger.error(f"Parse deadline PDF error: {str(e)}")
        return {"error": f"Error parsing deadline PDF: {str(e)}"}

def backend_teacher_notification_status() -> Dict[str, Any]:
    """Teacher get notification status function"""
    scheduler = get_notification_scheduler()
    if not scheduler:
        return {"error": "Notification scheduler not initialized"}
    
    try:
        status = scheduler.get_notification_status()
        return status
    except Exception as e:
        logger.error(f"Get notification status error: {str(e)}")
        return {"error": f"Error getting notification status: {str(e)}"}

def backend_teacher_send_notification(reminder_type: str = "general") -> Dict[str, Any]:
    """Teacher send notification function"""
    scheduler = get_notification_scheduler()
    if not scheduler:
        return {"error": "Notification scheduler not initialized"}
    
    try:
        result = scheduler.manual_send_notification(reminder_type)
        return result
    except Exception as e:
        logger.error(f"Manual send notification error: {str(e)}")
        return {"error": f"Error sending notification: {str(e)}"}

def backend_teacher_notification_history(limit: int = 50) -> Dict[str, Any]:
    """Teacher get notification history function"""
    scheduler = get_notification_scheduler()
    if not scheduler:
        return {"history": []}
    
    try:
        history = scheduler.get_notification_history(limit)
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Get notification history error: {str(e)}")
        return {"error": f"Error getting notification history: {str(e)}"}

