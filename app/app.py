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
with open('final_courses.json') as f:
    courses_data = json.load(f)

course_names = list(courses_data.keys())
course_descriptions = [course['data'] for course in courses_data.values()]
course_materials = [course['study_material'] for course in courses_data.values()]

# Initialize Qdrant client
client = QdrantClient(
    url=st.secrets["QDRANT_URL"],
    api_key=st.secrets["QDRANT_API_KEY"],
)

# Function to calculate cosine similarity
def calculate_cosine_similarity(embedding1, embedding2):
    return 1 - cosine(embedding1, embedding2)

# Function to perform search
def search_courses(user_query, timeout=30):
    query_normalized = user_query.lower()
    queries = query_normalized.split()
    exact_matches = []

    for query in queries:
        exact_matches += [course for course in course_names if query in course.lower()]

    query_embedding = encoder.encode([user_query])[0]
    results = []

    if exact_matches:
        for course in exact_matches:
            idx = course_names.index(course)
            description = course_descriptions[idx]
            time.sleep(2)  # Increased delay before generating response
            response = gemini_model.generate_content(
                f"Give only the website link of course {course} IITD"
            )
            full_description = (
                f"{description}, the course website: {response}, previous year paper links: "
                f"{', '.join(course_materials[idx])}"
            )
            results.append({"course_name": course, "description": full_description})
    else:
        try:
            search_result = client.search(
                collection_name="courses",
                query_vector=query_embedding.tolist(),
                limit=10,
                timeout=timeout,
            )
            for hit in search_result:
                print(hit)
                idx = course_names.index(hit.payload['course'])
                time.sleep(1)  # Increased delay before generating response
                response = gemini_model.generate_content(
                    f"Give only the website link of course {hit.payload['course']} IITD"
                )
                full_description = (
                    f"{hit.payload['description']}, the course website: {response}, "
                    f"previous year paper links: {', '.join(course_materials[idx])}"
                )
                results.append({"course_name": hit.payload['course'], "description": full_description})
        except Timeout as e:
            print(f"Timeout during search: {e}")

    if not results:
        return [{"course_name": "No relevant course found", "description": "Please refine your query."}]
    return results

# Generate response using Gemini
def generate_response_with_gemini(user_query, courses_info):
    prompt = f"User query: '{user_query}'\nHere are the top 3 courses that match:\n{courses_info}\nSummarize and respond."
    try:
        time.sleep(2)  # Increased delay before sending the request
        response = gemini_model.generate_content(prompt)
        return response.text
    except Timeout as e:
        print(f"Timeout during response generation: {e}")
        return "Request timed out. Please try again."
    except Exception as e:
        print(f"Error during response generation: {e}")
        return None

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

    courses_info = search_courses(user_input)
    courses_info_str = "\n".join(
        [f"Course: {course['course_name']}\nDescription: {course['description']}" for course in courses_info]
    )
    response = generate_response_with_gemini(user_input, courses_info_str)
    st.session_state.chat_history.append({"role": "assistant", "message": response})
    st.markdown(f'<div class="assistant-message">{response}</div>', unsafe_allow_html=True)