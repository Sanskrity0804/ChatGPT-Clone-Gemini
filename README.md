# 🤖 ChatGPT Clone with Gemini

A ChatGPT-style conversational AI built with **Streamlit** and **Google Gemini API**, featuring:

- 🔐 **User authentication** (login & registration)
- 💬 **Personalized chat history** (per-user, never shared)
- 📁 **Document analysis** (PDF & DOCX support)
- 🎨 Modern **dark theme UI** with responsive design
- 📊 **Multiple Gemini models** (Flash, Pro, etc.)
- 🔍 **Summarization & Q&A** from uploaded documents

---

## 🚀 Features

- ChatGPT-like interface powered by **Google Gemini**
- Secure **login system** with hashed passwords
- **Per-user chat history** (stored locally, isolated per account)
- Upload and analyze **PDFs & Word documents**
- Export chat history anytime
- Optimized UI for desktop & mobile

---

## 🛠️ Setup Instructions

### ✅ Prerequisites
- Python **3.8+**
- A [Google Gemini API key](https://makersuite.google.com/app/apikey)
- (Optional) A [Streamlit Cloud](https://streamlit.io/cloud) account for deployment

---

### 🔧 Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/your-username/chatgpt-clone-gemini.git
   cd chatgpt-clone-gemini
2. Install dependencies:
    pip install -r requirements.txt

3. Set your Gemini API key as an environment variable:
    Windows (Powershell):

    setx GEMINI_API_KEY "your-api-key-here"

   ▶️ Running Locally
streamlit run app.py
