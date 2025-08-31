import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="ChatGPT Clone with Gemini", page_icon="🤖", layout="wide")

genai.configure(api_key="AIzaSyCgXMaApaRCVy3SmMZZxD-TL74COecTsgQ")  # Replace with your key
MODEL = "gemini-1.5-flash"

HISTORY_FILE = "chat_history.json"


# --------------------------
# LOAD & SAVE CHAT HISTORY
# --------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


# --------------------------
# INIT SESSION STATE
# --------------------------
if "history" not in st.session_state:
    st.session_state.history = load_history()

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None


# --------------------------
# SIDEBAR - CHAT LIST
# --------------------------
st.sidebar.title("💬 Chats")
if st.session_state.history:
    for chat_id in st.session_state.history.keys():
        if st.sidebar.button(chat_id):
            st.session_state.current_chat = chat_id

if st.sidebar.button("➕ New Chat"):
    chat_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.history[chat_id] = []
    st.session_state.current_chat = chat_id
    save_history(st.session_state.history)


# --------------------------
# MAIN CHAT WINDOW
# --------------------------
st.title("🤖 ChatGPT Clone (Gemini)")

if st.session_state.current_chat:
    chat_id = st.session_state.current_chat
    messages = st.session_state.history[chat_id]

    # Display old messages
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input for new user message
    if prompt := st.chat_input("Type your message..."):
        # Show user msg
        with st.chat_message("user"):
            st.markdown(prompt)

        # Store user msg
        messages.append({"role": "user", "content": prompt})

        # Gemini response
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        reply = response.text

        # Show AI reply
        with st.chat_message("assistant"):
            st.markdown(reply)

        # Store AI reply
        messages.append({"role": "assistant", "content": reply})

        # Save history
        st.session_state.history[chat_id] = messages
        save_history(st.session_state.history)

else:
    st.info("👉 Select or create a chat from the sidebar to start.")
