import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime
import hashlib
import PyPDF2
import docx
from docx import Document
import time
import base64

# --------------------------
# CONFIG - API KEY SETUP
# --------------------------
st.set_page_config(
    page_title="Advanced ChatGPT Clone", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for enhanced styling with improved sidebar
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #1a2530 100%);
        color: white;
    }
    [data-testid="stSidebar"] .stButton button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #2980b9;
    }
    [data-testid="stSidebar"] .stDownloadButton button {
        background-color: #27ae60;
        color: white;
        border: none;
        border-radius: 5px;
    }
    [data-testid="stSidebar"] .stDownloadButton button:hover {
        background-color: #219653;
    }
    [data-testid="stSidebar"] .stExpander {
        background-color: #34495e;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    [data-testid="stSidebar"] .stExpander summary {
        color: white;
        font-weight: bold;
    }
    [data-testid="stSidebar"] .stTextInput input {
        background-color: #2c3e50;
        color: white;
        border: 1px solid #34495e;
    }
    [data-testid="stSidebar"] .stSelectbox select {
        background-color: #2c3e50;
        color: white;
        border: 1px solid #34495e;
    }
    [data-testid="stSidebar"] .stFileUploader {
        background-color: #34495e;
        border-radius: 0.5rem;
        padding: 1rem;
    }
    .document-info {
        background-color: #e6f7ff;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1890ff;
    }
    .sidebar-section {
        background-color: #34495e;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: white;
    }
    .chat-header {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .feature-button {
        margin-bottom: 0.5rem;
    }
    .typing-indicator {
        display: flex;
        padding: 0.5rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .typing-dot {
        width: 8px;
        height: 8px;
        background-color: #6c757d;
        border-radius: 50%;
        margin: 0 2px;
        animation: typing 1.4s infinite;
    }
    .typing-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-5px); }
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p {
        color: white;
    }
    [data-testid="stSidebar"] .stInfo {
        background-color: #34495e;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Direct API key configuration
GEMINI_API_KEY = "AIzaSyCgXMaApaRCVy3SmMZZxD-TL74COecTsgQ"

# Configure the API if a key is provided
if GEMINI_API_KEY and GEMINI_API_KEY.strip():
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        API_KEY_CONFIGURED = True
    except Exception as e:
        st.error(f"Error configuring API: {str(e)}")
        API_KEY_CONFIGURED = False
else:
    API_KEY_CONFIGURED = False

# Available models
MODELS = {
    "Gemini 1.5 Flash (Fast)": "gemini-1.5-flash",
    "Gemini 1.5 Pro (Advanced)": "gemini-1.5-pro",
    "Gemini Pro (Standard)": "gemini-pro"
}

DEFAULT_MODEL = "gemini-1.5-flash"

# File paths
USERS_FILE = "users.json"
HISTORY_DIR = "chat_histories"
USER_PROFILES_FILE = "user_profiles.json"

# Create directories if they don't exist
os.makedirs(HISTORY_DIR, exist_ok=True)

# --------------------------
# TEXT EXTRACTION FUNCTIONS
# --------------------------
def extract_text_from_file(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        else:
            st.error("Unsupported file format. Please upload a PDF or DOCX file.")
            return None
    except Exception as e:
        st.error(f"Error extracting text from file: {str(e)}")
        return None

# --------------------------
# USER MANAGEMENT
# --------------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def load_user_profiles():
    if os.path.exists(USER_PROFILES_FILE):
        with open(USER_PROFILES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_profiles(profiles):
    with open(USER_PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4, ensure_ascii=False)

def get_user_profile(username):
    profiles = load_user_profiles()
    return profiles.get(username, {"name": None, "preferences": {}})

def update_user_profile(username, updates):
    profiles = load_user_profiles()
    if username not in profiles:
        profiles[username] = {"name": None, "preferences": {}}
    
    profiles[username].update(updates)
    save_user_profiles(profiles)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_history_file(username):
    return os.path.join(HISTORY_DIR, f"{username}_history.json")

def load_user_history(username):
    history_file = get_user_history_file(username)
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_history(username, history):
    history_file = get_user_history_file(username)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def delete_user_chat(username, chat_id):
    history = load_user_history(username)
    if chat_id in history:
        del history[chat_id]
        save_user_history(username, history)
        return True
    return False

# --------------------------
# NEW FEATURES
# --------------------------
def create_chat_download_link(chat_data, filename):
    """Generate a download link for chat history"""
    b64 = base64.b64encode(chat_data.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download Chat History</a>'

def summarize_document(text):
    """Generate a summary of the document"""
    try:
        model = genai.GenerativeModel(DEFAULT_MODEL)
        prompt = f"Please provide a concise summary (3-4 bullet points) of the following document:\n\n{text[:3000]}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not generate summary: {str(e)}"

def get_model_response(model_name, prompt):
    """Get response from the selected model"""
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --------------------------
# INIT SESSION STATE
# --------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.history = {}
    st.session_state.current_chat = None
    st.session_state.user_profile = {}
    
# Initialize knowledge_base in session state
if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = None

# Initialize document name in session state
if "document_name" not in st.session_state:
    st.session_state.document_name = None

# Initialize selected model
if "selected_model" not in st.session_state:
    st.session_state.selected_model = DEFAULT_MODEL

# Initialize document summaries
if "document_summaries" not in st.session_state:
    st.session_state.document_summaries = {}

# Initialize multiple documents
if "documents" not in st.session_state:
    st.session_state.documents = {}

# --------------------------
# AUTHENTICATION
# --------------------------
def login_form():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='chat-header'><h1 style='text-align: center; margin: 0;'>🔐 ChatGPT Clone</h1></div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    users = load_users()
                    if username in users and users[username]["password"] == hash_password(password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.history = load_user_history(username)
                        st.session_state.user_profile = get_user_profile(username)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username")
                new_name = st.text_input("Your Name (Optional)")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit = st.form_submit_button("Register", use_container_width=True)
                
                if submit:
                    users = load_users()
                    if new_username in users:
                        st.error("Username already exists")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        users[new_username] = {"password": hash_password(new_password)}
                        save_users(users)
                        
                        # Create profile for new user
                        if new_name:
                            update_user_profile(new_username, {"name": new_name})
                        
                        # Create empty history for new user
                        save_user_history(new_username, {})
                        st.success("Registration successful! Please login.")

# --------------------------
# MAIN APP
# --------------------------
def main_app():
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.title(f"💬 ChatGPT Clone")
        
        # User info
        if st.session_state.user_profile.get("name"):
            st.write(f"👤 Welcome, {st.session_state.user_profile['name']}!")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Model selection
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.subheader("Model Selection")
        model_display_name = list(MODELS.keys())[list(MODELS.values()).index(st.session_state.selected_model)]
        selected_model = st.selectbox(
            "Choose AI Model",
            options=list(MODELS.keys()),
            index=list(MODELS.values()).index(st.session_state.selected_model),
            help="Select which Gemini model to use for responses"
        )
        st.session_state.selected_model = MODELS[selected_model]
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Document upload section
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.subheader("📁 Document Analysis")
        st.write("Upload PDF or DOCX files for analysis")
        uploaded_files = st.file_uploader(
            "Choose files", 
            type=['pdf', 'docx'], 
            label_visibility="collapsed",
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.documents:
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        doc_text = extract_text_from_file(uploaded_file)
                        if doc_text:
                            st.session_state.documents[uploaded_file.name] = doc_text[:4000]
                            # Generate summary
                            summary = summarize_document(doc_text)
                            st.session_state.document_summaries[uploaded_file.name] = summary
                            st.success(f"'{uploaded_file.name}' uploaded successfully!")
        
        # Display uploaded documents
        if st.session_state.documents:
            st.subheader("Uploaded Documents")
            for doc_name in list(st.session_state.documents.keys()):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"📄 {doc_name}")
                with col2:
                    if st.button("❌", key=f"remove_{doc_name}"):
                        del st.session_state.documents[doc_name]
                        if doc_name in st.session_state.document_summaries:
                            del st.session_state.document_summaries[doc_name]
                        st.rerun()
            
            # Show document summaries
            with st.expander("View Document Summaries"):
                for doc_name, summary in st.session_state.document_summaries.items():
                    st.write(f"**{doc_name}**")
                    st.write(summary)
                    st.divider()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Chat history
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        st.subheader("Chat History")
        if st.session_state.history:
            for chat_id in list(st.session_state.history.keys()):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    if st.button(chat_id, key=f"btn_{chat_id}", use_container_width=True):
                        st.session_state.current_chat = chat_id
                        st.rerun()
                with col2:
                    # Export chat button
                    chat_data = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.history[chat_id]])
                    st.download_button(
                        label="💾",
                        data=chat_data,
                        file_name=f"chat_{chat_id}.txt",
                        key=f"export_{chat_id}",
                        help="Export chat history"
                    )
                with col3:
                    if st.button("🗑️", key=f"del_{chat_id}"):
                        if delete_user_chat(st.session_state.username, chat_id):
                            st.session_state.history = load_user_history(st.session_state.username)
                            if st.session_state.current_chat == chat_id:
                                st.session_state.current_chat = None
                            st.rerun()
        else:
            st.info("No chat history yet")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # New chat button - FIXED: removed duplicate parameter
        if st.button("➕ New Chat", use_container_width=True):
            chat_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.history[chat_id] = []
            st.session_state.current_chat = chat_id
            save_user_history(st.session_state.username, st.session_state.history)
            st.rerun()
        
        # Profile settings
        st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
        with st.expander("⚙️ Profile Settings"):
            new_name = st.text_input("Your Name", value=st.session_state.user_profile.get("name", ""))
            if st.button("Update Profile", use_container_width=True):
                update_user_profile(st.session_state.username, {"name": new_name})
                st.session_state.user_profile["name"] = new_name
                st.success("Profile updated!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Logout button - FIXED: removed duplicate parameter
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.history = {}
            st.session_state.current_chat = None
            st.session_state.user_profile = {}
            st.session_state.knowledge_base = None
            st.session_state.document_name = None
            st.session_state.documents = {}
            st.session_state.document_summaries = {}
            st.rerun()
    
    # Main chat area
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.markdown("<div class='chat-header'><h1 style='text-align: center; margin: 0;'>ChatGPT Clone</h1></div>", unsafe_allow_html=True)
        
        # Show document analysis status
        if st.session_state.documents:
            doc_names = list(st.session_state.documents.keys())
            st.markdown(f"""
            <div class="document-info">
                📚 <b>Document Analysis Active:</b> Analyzing {len(doc_names)} document(s)
            </div>
            """, unsafe_allow_html=True)
        
        if not API_KEY_CONFIGURED:
            st.error("API key not configured or invalid")
            st.info("Please check that your Gemini API key is valid and properly formatted")
            return
        
        if st.session_state.current_chat:
            chat_id = st.session_state.current_chat
            messages = st.session_state.history[chat_id]
            
            # Display old messages
            for msg in messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Input for new user message
            if prompt := st.chat_input("Message ChatGPT..."):
                # Personalize response if we know user's name
                user_name = st.session_state.user_profile.get("name")
                personalized_prompt = prompt
                if user_name and ("my name" in prompt.lower() or "who am i" in prompt.lower()):
                    personalized_prompt = f"My name is {user_name}. {prompt}"
                
                # Enhance prompt with knowledge base if available
                final_prompt = personalized_prompt
                if st.session_state.documents:
                    documents_text = "\n\n".join([f"DOCUMENT: {name}\nCONTENT:\n{content}" for name, content in st.session_state.documents.items()])
                    final_prompt = f"""Please analyze the following documents and answer the question based on their content.

                    DOCUMENTS:
                    {documents_text}

                    QUESTION: {personalized_prompt}

                    Please provide a comprehensive answer based on the documents. 
                    If the documents don't contain relevant information, please state that clearly.
                    If referring to specific documents, please mention which document you're referencing."""
                
                # Show user msg
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Store user msg
                messages.append({"role": "user", "content": prompt})
                
                # Show typing indicator
                with st.empty():
                    st.markdown("""
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Get AI response
                    try:
                        reply = get_model_response(st.session_state.selected_model, final_prompt)
                    except Exception as e:
                        reply = f"Sorry, I encountered an error: {str(e)}"
                        st.error(f"API Error: {str(e)}")
                
                # Show AI reply
                with st.chat_message("assistant"):
                    st.markdown(reply)
                
                # Store AI reply
                messages.append({"role": "assistant", "content": reply})
                
                # Save history
                st.session_state.history[chat_id] = messages
                save_user_history(st.session_state.username, st.session_state.history)
                st.rerun()
        
        else:
            # Welcome message when no chat is selected
            st.markdown("""
            <div style='text-align: center; padding: 3rem; background-color: #f8f9fa; border-radius: 0.5rem;'>
                <h2>Welcome to ChatGPT Clone</h2>
                <p>Start a new conversation or select an existing one from the sidebar.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Quick start buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💻 Technology Questions", use_container_width=True, help="Ask about technology"):
                    st.session_state.history["Technology Discussion"] = []
                    st.session_state.current_chat = "Technology Discussion"
                    st.rerun()
            with col2:
                if st.button("🔬 Science Questions", use_container_width=True, help="Ask about science"):
                    st.session_state.history["Science Discussion"] = []
                    st.session_state.current_chat = "Science Discussion"
                    st.rerun()
            with col3:
                if st.button("💡 Creative Ideas", use_container_width=True, help="Get creative suggestions"):
                    st.session_state.history["Creative Brainstorming"] = []
                    st.session_state.current_chat = "Creative Brainstorming"
                    st.rerun()
            
            # Document analysis tips
            if st.session_state.documents:
                st.info("💡 You have documents uploaded. Start a new chat to ask questions about them!")

# --------------------------
# APP FLOW
# --------------------------
if not st.session_state.authenticated:
    login_form()
else:
    main_app()
