import groq
from typing import List, Dict, Any
import re
import hashlib
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import numpy as np
from functools import lru_cache
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global clients
qdrant_client = QdrantClient(
    url = 'https://1b0c0fe7-c332-4414-9ce5-e6e4606d1980.us-east4-0.gcp.cloud.qdrant.io:6333',
    api_key = os.getenv('QDRANT'),
    grpc_port=6633
)
groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

@lru_cache(maxsize=100)
def generate_embedding(text: str) -> List[float]:
    """Generate and cache embeddings."""
    try:
        return embedding_model.encode(text).tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return [0] * 384

def normalize_course_code(text: str) -> List[str]:
    """Extract and normalize course codes."""
    try:
        matches = re.finditer(r'([A-Za-z]{3})(\d{3})', text, re.IGNORECASE)
        return [match.group(0).upper() for match in matches]
    except Exception as e:
        logger.error(f"Error normalizing course code: {e}")
        return []

def get_course_id(course_code: str) -> str:
    """Generate course ID from course code."""
    return hashlib.md5(course_code.encode()).hexdigest()

def format_context_with_materials(context: List[Dict]) -> Dict:
    """Process context and separate study materials."""
    formatted_context = []
    all_study_materials = []
    
    for item in context:
        if not hasattr(item, 'payload'):
            continue
            
        payload = item.payload
        if payload.get('course_code'):
            study_materials = payload.get('study_material', [])
            if study_materials:
                all_study_materials.extend([
                    {
                        'course_code': payload.get('course_code'),
                        'course_name': payload.get('course_name'),
                        'link': material
                    } for material in study_materials
                ])
            
            formatted_context.append({
                'type': 'course',
                'course_code': payload.get('course_code', ''),
                'course_name': payload.get('course_name', ''),
                'prerequisites': payload.get('prerequisites', []),
                'data': payload.get('data', ''),
            })
        elif payload.get('interviewee'):
            formatted_context.append({
                'type': 'interview',
                'content': payload.get('data', '')
            })
    
    return {
        'context': formatted_context,
        'study_materials': all_study_materials
    }

def chat(query: str) -> str:
    """
    Main chat function with emphasis on study materials.
    
    Args:
        query: User query
    Returns:
        str: Generated response
    """
    try:
        query_embedding = generate_embedding(query)
        context = []
        
        course_codes = normalize_course_code(query)
        
        if course_codes:
            try:
                course_ids = [get_course_id(code) for code in course_codes]
                course_results = qdrant_client.retrieve(
                    collection_name="courses",
                    ids=course_ids
                )
                
                if course_results:
                    context.extend(course_results)
                    
                    for code in course_codes:
                        interview_results = qdrant_client.search(
                            collection_name="interviews",
                            query_vector=query_embedding,
                            query_filter={
                                "must": [
                                    {"key": "data", "match": {"value": code}}
                                ]
                            },
                            limit=2
                        )
                        context.extend(interview_results)
            except Exception as e:
                logger.error(f"Error retrieving courses: {e}")
        
        if len(context) < 5:
            try:
                remaining = 5 - len(context)
                course_results = qdrant_client.search(
                    collection_name="courses",
                    query_vector=query_embedding,
                    limit=remaining // 2
                )
                interview_results = qdrant_client.search(
                    collection_name="interviews",
                    query_vector=query_embedding,
                    limit=remaining - (remaining // 2)
                )
                
                context.extend(course_results)
                context.extend(interview_results)
            except Exception as e:
                logger.error(f"Error in general search: {e}")
        
        processed_data = format_context_with_materials(context)
        
        if not processed_data['context']:
            return "I couldn't find relevant information. Could you please rephrase your question or provide more details?"
        
        try:
            # Customize system prompt based on study materials presence
            system_prompt = """You are a helpful academic assistant. Provide clear, concise responses focusing on course details or other university stuff. If study materials are provided in the context, explicitly mention them as resources for learning, including their links. Structure your response to clearly separate course information from available study materials."""
            
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"""Context: {processed_data['context']}
                    Study Materials: {processed_data['study_materials']}
                    
                    Query: {query}
                    
                    Note: If study materials are available, make sure to list them explicitly in your response as learning resources."""
                }
            ]
            
            response = groq_client.chat.completions.create(
                messages=messages,
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I encountered an error while generating the response. Please try again."
            
    except Exception as e:
        logger.error(f"Unexpected error in chat function: {e}")
        return "An unexpected error occurred. Please try again later."
    

# Example usage
import streamlit as st

# Inject custom CSS for styling
def inject_custom_css():
    st.markdown("""
        <style>
            /* Global background */
            .stApp {
                background-color: #121212;
                color: white;
                font-family: 'Arial', sans-serif;
            }

            /* Chat container styling */
            .stChatContainer {
                background-color: #1E1E2F;
                border-radius: 15px;
                padding: 20px;
                max-width: 700px;
                margin: auto;
                margin-top: 20px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                display: flex;
                flex-direction: column;
                gap: 10px;
            }

            /* User message style (rightmost aligned, adjusts to content) */
            .user-message {
                background-color: #0066cc;
                color: white;
                padding: 12px 16px;
                border-radius: 15px;
                margin-bottom: 10px;
                max-width: 70%;
                display: inline-block;
                text-align: left;
                word-wrap: break-word;
                float: right; /* Align to the right */
                position: relative; /* For positioning the user icon */
            }

            .user-message::before {
                content: "";
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                right: -30px; /* Adjust position as needed */
                width: 20px;
                height: 20px;
                background-color: #0066cc; 
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                color: white;
                font-size: 12px;
            }

            /* Assistant message style (leftmost aligned, adjusts to content) */
            .assistant-message {
                background-color: #4A4A5A;
                color: white;
                padding: 12px 16px;
                border-radius: 15px;
                margin-bottom: 10px;
                max-width: 70%;
                display: inline-block;
                text-align: left;
                word-wrap: break-word;
                float: left; /* Align to the left */
                position: relative; /* For positioning the assistant icon */
            }

            .assistant-message::before {
                content: "";
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                left: -30px; /* Adjust position as needed */
                width: 20px;
                height: 20px;
                background-color: #4A4A5A; 
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                color: white;
                font-size: 12px;
            }

            /* Input box styling */
            .stTextInput > div > input {
                background-color: #282c34;
                color: white;
                border: 1px solid #555;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 16px;
                margin-top: 15px;
            }

            /* Input focus */
            .stTextInput > div > input:focus {
                border-color: #0078FF;
                outline: none;
            }
        </style>
    """, unsafe_allow_html=True)

# Inject the CSS
inject_custom_css()

# App title
st.title("Virtual Companion Chat")

# Initialize chat history if not already done
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat display container
st.markdown('<div class="stChatContainer">', unsafe_allow_html=True)

# Display chat messages from the history
for chat in st.session_state.chat_history:
    role_class = "user-message" if chat["role"] == "user" else "assistant-message"
    st.markdown(f'<div class="{role_class}">{chat["message"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# User input box
user_input = st.chat_input("Type your message...")

# If user sends a message
if user_input:
    # Add user's message to chat history and display it
    st.session_state.chat_history.append({"role": "user", "message": user_input})
    st.markdown(f'<div class="user-message">{user_input}</div>', unsafe_allow_html=True)

    # Generate response using Gemini
    response = chat(user_input)

    # Generate assistant response
    assistant_response = response  # Replace with AI logic if needed
    st.session_state.chat_history.append({"role": "assistant", "message": assistant_response})
    st.markdown(f'<div class="assistant-message">{assistant_response}</div>', unsafe_allow_html=True)