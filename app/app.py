import json
import time
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance
import google.generativeai as genai
from requests.exceptions import Timeout
from scipy.spatial.distance import cosine
import streamlit as st

# Configure Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp", generation_config={
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
})

# Initialize SentenceTransformer model for embedding
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# Load course data


# Streamlit UI
def inject_custom_css():
    st.markdown("""
        <style>
        /* Styling omitted for brevity */
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()
st.title("Virtual Companion Chat")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown('<div class="stChatContainer">', unsafe_allow_html=True)
for chat in st.session_state.chat_history:
    role_class = "user-message" if chat["role"] == "user" else "assistant-message"
    st.markdown(f'<div class="{role_class}">{chat["message"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

user_input = st.chat_input("Type your message...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "message": user_input})
    st.markdown(f'<div class="user-message">{user_input}</div>', unsafe_allow_html=True)

    response = chat(user_input)
    st.session_state.chat_history.append({"role": "assistant", "message": response})
    st.markdown(f'<div class="assistant-message">{response}</div>', unsafe_allow_html=True)