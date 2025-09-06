# 📧 AI-Powered Communication Assistant

An end-to-end **AI-driven email support assistant** that helps organizations manage customer queries efficiently.  
It automatically retrieves support emails, categorizes & prioritizes them, extracts key information, generates **empathetic AI responses**, and provides analytics through a modern dashboard.  

---

## ✨ Features
- **Email Retrieval & Filtering**
  - Fetches support-related emails from Gmail/IMAP.
  - Filters based on keywords like *support, query, request, help*.  

- **Smart Categorization**
  - Sentiment analysis (Positive / Negative / Neutral).  
  - Urgency detection (Urgent / Not Urgent).  
  - Priority queue ensures urgent tickets appear first.  

- **AI-Powered Responses**
  - Context-aware replies using GPT + Retrieval-Augmented Generation (RAG).  
  - Incorporates knowledge base (FAQs, policies, product info).  
  - Responses editable before sending.  

- **Information Extraction**
  - Extracts requirements, contact details, and sentiment indicators.  
  - Metadata displayed on dashboard alongside email.  

- **Interactive Dashboard**
  - Clean UI for managing emails.  
  - Charts for sentiment distribution, urgency, resolution status, and timeline trends.  
  - Stats (emails received in last 24h, pending, resolved).  

- **End-to-End Workflow**
  - Review AI-suggested replies.  
  - Update / approve / send responses directly from dashboard.  
  - Track progress (Pending → Resolved).  

---

## 🏗️ Architecture
Email Server (IMAP/SMTP)
│
▼
Email Handler → Extract Metadata (sender, subject, body, contacts)
│
▼
AI Processor → Sentiment | Urgency | Requirement Extraction | RAG-based Response
│
▼
SQLite Database → Stores Emails + Stats
│
▼
Flask Backend (REST API)
│
▼
Dashboard (HTML + JS + Chart.js)

---

## ⚙️ Tech Stack
- **Backend:** Python (Flask), SQLite  
- **AI Models:** OpenAI GPT (gpt-4o-mini), TF-IDF (scikit-learn)  
- **Email Handling:** IMAP (imaplib2), SMTP  
- **Frontend:** HTML, CSS, JavaScript, Chart.js  
- **Storage:** SQLite (emails + stats persistence)  

---

## 🚀 Getting Started

### 1. Clone Repository
```bash
git clone https://github.com/bunny8205/linkenite.git
cd linkenite


2. Install Dependencies
pip install -r requirements.txt

3. Configure

Edit config.py with:

Your email (IMAP + SMTP).

OpenAI API key.

Knowledge base (FAQ entries).

4. Run Application
python app.py

5. Open Dashboard

Go to: http://127.0.0.1:5000

📊 Example Dashboard

Email list: shows sender, subject, body, requirements, AI-generated response.

Stats cards: total emails (24h), resolved, pending, last updated.

Charts: sentiment, urgency, resolution status, timeline trends.

📽️ Deliverables

Working end-to-end solution.

Short demo video.

Documentation (this README + architecture overview).

🔮 Future Improvements

Support for Outlook, Slack, and WhatsApp integration.

Replace TF-IDF with vector embeddings (FAISS/Chroma).

Auto-send urgent replies.

OAuth2 authentication for secure email access.

SLA tracking (response time, agent performance).
