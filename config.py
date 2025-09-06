import os
from datetime import datetime

# Email configuration - HARDCODED (Not recommended for production)
EMAIL_CONFIG = {
    'server': 'imap.gmail.com',
    'port': 993,
    'username': 'omshree8205@gmail.com',  # Replace with your email
    'password': 'rjueiwjwswaopqnm',     # Replace with your app password
    'search_terms': ['support', 'query', 'request', 'help', 'issue', 'problem'],
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

# AI Configuration - Updated for GPT-4o Mini
OPENAI_CONFIG = {
    'api_key': '',  # Replace with your actual OpenAI API key
    'model': 'gpt-4o-mini',
    'temperature': 0.1
}

# Knowledge Base Configuration
KNOWLEDGE_BASE = {
    'faqs': [
        "Our product supports multiple authentication methods including OAuth2 and API keys.",
        "For billing inquiries, please contact our finance department at finance@company.com.",
        "Our standard response time for priority support is under 2 hours.",
        "We offer 24/7 support for enterprise customers only.",
        "System maintenance occurs every second Tuesday of the month from 2-4 AM UTC."
    ]
}

# App Configuration
DEBUG = True
SECRET_KEY = 'your-secret-key-change-in-production'  # Replace with a secure key
DATABASE_URI = 'sqlite:///emails.db'  # SQLite database for persistence
