import requests
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from config import OPENAI_CONFIG, KNOWLEDGE_BASE


class AIProcessor:
    def __init__(self):
        self.api_key = OPENAI_CONFIG['api_key']
        self.model = OPENAI_CONFIG['model']
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Initialize knowledge base
        self.knowledge_base = KNOWLEDGE_BASE['faqs']
        self.vectorizer = TfidfVectorizer().fit(self.knowledge_base)
        self.kb_vectors = self.vectorizer.transform(self.knowledge_base)

    def analyze_sentiment(self, text):
        """Analyze sentiment of the email text"""
        prompt = f"""
        Analyze the sentiment of the following text and classify it as Positive, Negative, or Neutral.
        Provide only the classification as a single word.

        Text: {text}
        """

        try:
            response = self._query_openai(prompt)
            sentiment = response.strip().lower()

            if 'positive' in sentiment:
                return 'Positive'
            elif 'negative' in sentiment:
                return 'Negative'
            else:
                return 'Neutral'
        except:
            return 'Neutral'

    def determine_urgency(self, text):
        """Determine urgency of the email"""
        prompt = f"""
        Analyze the following email text and determine if it's urgent or not urgent.
        Consider keywords like 'immediately', 'critical', 'cannot access', 'urgent', 'emergency', etc.
        Provide only the classification as either 'Urgent' or 'Not urgent'.

        Text: {text}
        """

        try:
            response = self._query_openai(prompt)
            urgency = response.strip().lower()

            if 'urgent' in urgency:
                return 'Urgent'
            else:
                return 'Not urgent'
        except:
            return 'Not urgent'

    def retrieve_knowledge(self, query, top_k=3):
        """Retrieve relevant knowledge from the knowledge base using TF-IDF similarity"""
        try:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.kb_vectors).flatten()
            top_indices = similarities.argsort()[-top_k:][::-1]

            relevant_knowledge = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    relevant_knowledge.append(self.knowledge_base[idx])

            return relevant_knowledge
        except Exception as e:
            print(f"Error retrieving knowledge: {e}")
            return []

    def generate_response(self, email_data):
        """Generate a response for the email using RAG"""
        # Retrieve relevant knowledge
        relevant_knowledge = self.retrieve_knowledge(email_data['body'])
        knowledge_str = "\n".join(relevant_knowledge) if relevant_knowledge else "No relevant knowledge found."

        prompt = f"""
        You are a customer support representative. Draft a professional and friendly response to the following email.
        Acknowledge the customer's sentiment and address their concerns appropriately.

        Use the following knowledge base information if relevant:
        {knowledge_str}

        Sender: {email_data['sender']}
        Subject: {email_data['subject']}
        Email Content: {email_data['body']}
        Sentiment: {email_data['sentiment']}
        Urgency: {email_data['urgency']}
        Key Requirements: {email_data.get('requirements', 'Not specified')}

        Provide only the response text without any additional formatting or explanations.
        """

        try:
            response = self._query_openai(prompt)
            return response.strip()
        except Exception as e:
            return f"Error generating response: {e}"

    def extract_requirements(self, text):
        """Extract key requirements from the email"""
        prompt = f"""
        Extract the key requirements, requests, or issues mentioned in the following email text.
        Provide a concise summary of what the customer needs.

        Text: {text}
        """

        try:
            response = self._query_openai(prompt)
            return response.strip()
        except:
            return "Unable to extract requirements"

    def _query_openai(self, prompt):
        """Query the OpenAI API"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides concise and accurate responses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": OPENAI_CONFIG['temperature'],
            "max_tokens": 1000
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")