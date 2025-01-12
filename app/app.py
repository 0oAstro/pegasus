import json
import time
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from groq import Groq
from requests.exceptions import Timeout
from scipy.spatial.distance import cosine
import streamlit as st

# Configure Groq API
groq_client = Groq(api_key="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")

# Initialize SentenceTransformer model for embedding
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# Load course data
with open('all_courses_with_study_material.json') as f:
    courses_data = json.load(f)

course_names = list(courses_data.keys())
course_descriptions = [course['data'] for course in courses_data.values()]
course_materials = [course['study_material'] for course in courses_data.values()]

# Initialize Qdrant client
client = QdrantClient(
    url='https://03eaf461-d84a-41e3-8598-3fe6a2d8ad80.europe-west3-0.gcp.cloud.qdrant.io',
    api_key="FS7jZXzY3MUbQx07787x5EeJ7xQO60ox956det4fXdK6haFJ7mMQzQ"
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
            
            # Use Groq to generate course website link
            prompt = f"Give only the website link of course {course} IITD"
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",  # or your preferred Groq model
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            response = completion.choices[0].message.content

            full_description = (
                f"{description}, the course website: {response}, previous year paper links: "
                f"{', '.join(course_materials[idx])}"
            )
            results.append({"course_name": course, "description": full_description})
    else:
        try:
            search_result = client.search(
                collection_name="Shipathon",
                query_vector=query_embedding.tolist(),
                limit=10,
                timeout=timeout,
            )
            for hit in search_result:
                print(hit)
                idx = course_names.index(hit.payload['course'])
                time.sleep(1)  # Increased delay before generating response
                
                # Use Groq to generate course website link
                prompt = f"Give only the website link of course {hit.payload['course']} IITD"
                completion = groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",  # or your preferred Groq model
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=100
                )
                response = completion.choices[0].message.content

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

# Generate response using Groq
def generate_response_with_groq(user_query, courses_info):
    prompt = f"User query: '{user_query}'\nHere are the top 3 courses that match:\n{courses_info}\nSummarize and respond."
    try:
        time.sleep(2)  # Increased delay before sending the request
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",  # or your preferred Groq model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return completion.choices[0].message.content
    except Timeout as e:
        print(f"Timeout during response generation: {e}")
        return "Request timed out. Please try again."
    except Exception as e:
        print(f"Error during response generation: {e}")
        return None

# Streamlit UI code remains the same
def inject_custom_css():
    st.markdown("""
        <style>
        /* Global styling */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7fb;
            color: #333;
        }

        .stChatContainer {
            margin-top: 10px;
        }

        .user-message {
            background-color: #e1f5fe;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 5px;
            font-size: 14px;
        }

        .assistant-message {
            background-color: #f0f4c3;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 5px;
            font-size: 14px;
        }

        .stChatContainer .user-message {
            text-align: left;
        }

        .stChatContainer .assistant-message {
            text-align: right;
        }

        .stTextInput input {
            border-radius: 30px;
            padding: 15px;
            font-size: 16px;
            border: 1px solid #ddd;
            width: 100%;
        }

        .stButton button {
            background-color: #004ba0;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 30px;
            border: none;
            cursor: pointer;
        }

        .stButton button:hover {
            background-color: #003580;
        }

        .stChatInput {
            background-color: #ffffff;
            border-radius: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()
st.title("IIT D, D for DADDY")
st.markdown("""
    <h3 style="text-align:center;">Find Courses & Resources at IIT Delhi</h3>
    <p style="text-align:center;">Ask about courses, study materials, and more!</p>
""", unsafe_allow_html=True)

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
    response = generate_response_with_groq(user_input, courses_info_str)
    st.session_state.chat_history.append({"role": "assistant", "message": response})
    st.markdown(f'<div class="assistant-message">{response}</div>', unsafe_allow_html=True)