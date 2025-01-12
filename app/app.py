import streamlit as st
from groq import Groq
import os
import re
import json
import hashlib
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import time


model = "llama-3.2-70b-versatile"

# Initialize clients
groq = Groq(api_key=st.secrets["GROQ_API_KEY"])
client = QdrantClient(
    url=st.secrets["QDRANT_ENDPOINT"],
    api_key=st.secrets["QDRANT_API_KEY"],
)

# Initialize encoder
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# Streamlit page config
st.set_page_config(
    page_title="IITD Campus Navigator",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "course_cache" not in st.session_state:
    st.session_state.course_cache = {}

def generate_course_id(course_code: str) -> str:
    """Generate MD5 hash for course code after normalizing format."""
    normalized = re.sub(r'[\s-]', '', course_code.upper())
    return hashlib.md5(normalized.encode()).hexdigest()

def extract_course_codes(query: str) -> List[str]:
    """Extract course codes handling various formats (COL100, COL 100, COL-100)."""
    pattern = r'[A-Za-z]{2,3}[\s-]?\d{3}'
    matches = re.findall(pattern, query, re.IGNORECASE)
    return [re.sub(r'[\s-]', '', match.upper()) for match in matches]

def validate_and_get_course_info(code: str) -> Optional[Dict[str, Any]]:
    """Validate and fetch course information from database."""
    course_id = generate_course_id(code)
    result = client.retrieve(
        collection_name='courses',
        ids=[course_id]
    )
    return result[0].payload if result and result[0].payload else None

def get_course_level_info(course_code: str) -> Optional[Dict[str, str]]:
    """Get course level information with IIT-D specific context."""
    if not course_code:
        return None

    match = re.search(r'[A-Z]{2,3}\d{3}', course_code)
    if not match:
        return None

    level_num = int(course_code[-3])
    
    levels = {
        1: {
            "level": "100-level",
            "description": "First year courses, mostly fundae",
            "difficulty": "Chill scene for most part",
            "advice": "Good for freshies, basic concepts"
        },
        2: {
            "level": "200-level",
            "description": "Second year core stuff",
            "difficulty": "Moderate BT",
            "advice": "Start building your fundae"
        },
        3: {
            "level": "300-level",
            "description": "Third year depth courses",
            "difficulty": "Decent BT level",
            "advice": "Major concepts, stay on your toes"
        },
        4: {
            "level": "400-level",
            "description": "Final year specialized courses",
            "difficulty": "Solid BT potential",
            "advice": "Advanced stuff, needs dedication"
        },
        5: {
            "level": "500-level",
            "description": "Dual/Masters level",
            "difficulty": "Heavy scene",
            "advice": "Research oriented, proper grind required"
        },
        6: {
            "level": "600-level",
            "description": "Masters specialized",
            "difficulty": "Peak BT hours",
            "advice": "Research focus, publication worthy"
        },
        7: {
            "level": "700-level",
            "description": "Advanced graduate",
            "difficulty": "Maximum BT",
            "advice": "Deep research and innovation"
        },
        8: {
            "level": "800-level",
            "description": "Doctoral specialized",
            "difficulty": "Beyond BT",
            "advice": "Novel research contributions"
        }
    }
    
    return levels.get(level_num, {
        "level": "unknown",
        "description": "Specialized course",
        "difficulty": "Depends on prof",
        "advice": "Check with seniors"
    })

def analyze_query_intent(query: str) -> Dict[str, float]:
    """Analyze query intent and assign collection relevance scores."""
    intent_prompt = f"""Analyze this query and assign relevance scores from 0 to 1 for each collection.
Return only a JSON object with the scores in this exact format:
{{
    "courses": 0.0,
    "interviews": 0.0,
    "inception": 0.0,
    "united": 0.0
}}

Query: {query}

Consider:
- courses: academic courses, study materials, academic questions
- interviews: internship/placement preparation, career advice
- inception: campus life, IITD culture, facilities
- united: social life, relationships, campus social scene"""

    try:
        response = groq.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": intent_prompt}],
            temperature=0.1,
            max_tokens=100,
            response_format={ "type": "json_object" }
        )
        
        scores = json.loads(response.choices[0].message.content)
        
        validated_scores = {}
        for collection in ['courses', 'interviews', 'inception', 'united']:
            try:
                score = float(scores.get(collection, 0.0))
                validated_scores[collection] = max(0.0, min(1.0, score))
            except (TypeError, ValueError):
                validated_scores[collection] = 0.25
        
        return validated_scores

    except Exception as e:
        print(f"Error in analyze_query_intent: {e}")
        return {
            'courses': 0.25,
            'interviews': 0.25,
            'inception': 0.25,
            'united': 0.25
        }

def determine_query_type(query: str) -> Set[str]:
    """Determine which collections to search using pattern matching and AI intent."""
    collections = set()
    
    patterns = {
        'courses': r'(course|prereq|credit|professor|prof|class|semester|slot|timing|study|material|book)',
        'interviews': r'(interview|intern|placement|resume|company|job|preparation|study)',
        'inception': r'(hostel|mess|canteen|lhs|sac|oat|iitd|dassi|satti|fakka|bt)',
        'united': r'(relationship|dating|crush|love|randi|rizz|breakup|gossip)'
    }
    
    query_lower = query.lower()
    pattern_matches = set()
    for collection, pattern in patterns.items():
        if re.search(pattern, query_lower):
            pattern_matches.add(collection)
    
    intent_scores = analyze_query_intent(query)
    
    AI_SCORE_THRESHOLD = 0.3
    
    collections.update(pattern_matches)
    
    for collection, score in intent_scores.items():
        if score > AI_SCORE_THRESHOLD or collection in pattern_matches:
            collections.add(collection)
    
    if not collections:
        collections = set(patterns.keys())
    
    return collections

def fetch_from_collections(query: str, collections: Set[str], limit: int = 5) -> Dict[str, List[Dict]]:
    """Fetch relevant results from specified collections."""
    results = {}
    
    try:
        query_vector = encoder.encode(query).tolist()
        
        for collection in collections:
            try:
                search_results = client.search(
                    collection_name=collection,
                    query_vector=query_vector,
                    limit=limit
                )
                
                if search_results:
                    results[collection] = [
                        {
                            'id': result.id,
                            'score': result.score,
                            'payload': result.payload
                        }
                        for result in search_results
                        if result.score > 0.3
                    ]
                else:
                    results[collection] = []
                    
            except Exception as e:
                print(f"Error searching collection {collection}: {e}")
                results[collection] = []
                
    except Exception as e:
        print(f"Error in vector search: {e}")
        results = {collection: [] for collection in collections}
    
    return results

def process_course_info(course_data: Dict) -> Dict:
    """Process course information treating all fields as optional."""
    if not course_data:
        return {
            "error": "Course information not available",
            "message": "Please verify the course code or check the department website"
        }

    processed_info = {}
    
    # Define all possible fields
    fields_mapping = {
        "course_code": "code",
        "course_name": "name",
        "instructor": "prof",
        "instructor_mail": "email",
        "credits": "credits",
        "credit_structure": "structure",
        "prerequisites": "prereqs",
        "slot": "slot",
        "lec_time": "schedule",
        "data": "description",
        "overlaps": "overlaps",
        "study_materials": "study_materials"
    }
    
    # Process schedule if it exists
    if 'lec_time' in course_data and course_data['lec_time']:
        schedule = course_data['lec_time']
        days_map = {
            'M': 'Monday', 'T': 'Tuesday', 'W': 'Wednesday',
            'Th': 'Thursday', 'F': 'Friday'
        }
        for abbr, full in days_map.items():
            schedule = schedule.replace(abbr, full)
        course_data['lec_time'] = schedule

    # Only include fields that exist and have values
    for db_field, output_field in fields_mapping.items():
        if db_field in course_data and course_data[db_field]:
            processed_info[output_field] = course_data[db_field]

    # Add level info only if course code exists
    if 'code' in processed_info:
        level_info = get_course_level_info(processed_info['code'])
        if level_info:
            processed_info['level_info'] = level_info

    return processed_info

def chat(query: str) -> str:
    """Main chat function for IIT-D campus navigator."""
    # Extract and validate course codes with accurate information
    course_codes = extract_course_codes(query)
    course_info = {}
    invalid_courses = []
    
    for code in course_codes:
        info = validate_and_get_course_info(code)
        if info:
            course_info[code] = process_course_info(info)
        else:
            invalid_courses.append(code)
    
    # Determine collections to search
    relevant_collections = determine_query_type(query)
    
    # Fetch results from all relevant collections
    collection_results = fetch_from_collections(query, relevant_collections)
    
    # Prepare context for the response
    context = {
        'query': query,
        'course_info': course_info,
        'collection_results': collection_results,
        'relevant_collections': relevant_collections,
        'invalid_courses': invalid_courses
    }
    
    prompt = f"""IITD Campus Navigator 🎓

Query: {query}

Intent Analysis:
- Main focus areas detected across campus life
- Relevant information from {', '.join(relevant_collections)}
- Using only verified course information

Guidelines:
1. Only provide course details that are explicitly available in the data
2. If a course field isn't available, don't mention it or assume its value
3. For invalid course codes, suggest checking the department website
4. Use IITD lingo naturally (dassi, satti, fakka, bt)
5. Keep responses factual and data-driven

Courses found: {list(course_info.keys()) if course_info else "None"}
Invalid courses: {invalid_courses if invalid_courses else "None"}

CONTEXT: {context}"""

    try:
        response = groq.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in chat completion: {e}")
        return "I'm having trouble processing your query. Please try again or be more specific."

def stream_response(response: str):
    """Stream the response word by word."""
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def chat_with_history(query: str) -> str:
    """Enhanced chat function that considers conversation history."""
    # Extract and validate course codes with caching
    course_codes = extract_course_codes(query)
    course_info = {}
    invalid_courses = []
    
    for code in course_codes:
        # Check cache first
        if code in st.session_state.course_cache:
            course_info[code] = st.session_state.course_cache[code]
        else:
            info = validate_and_get_course_info(code)
            if info:
                processed_info = process_course_info(info)
                course_info[code] = processed_info
                st.session_state.course_cache[code] = processed_info
            else:
                invalid_courses.append(code)
    
    # Build conversation history context
    history_context = ""
    if len(st.session_state.messages) > 0:
        last_messages = st.session_state.messages[-3:]  # Consider last 3 messages
        history_context = "\nRecent conversation:\n" + "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in last_messages
        ])
    
    # Determine collections to search
    relevant_collections = determine_query_type(query)
    collection_results = fetch_from_collections(query, relevant_collections)
    
    context = {
        'query': query,
        'course_info': course_info,
        'collection_results': collection_results,
        'relevant_collections': relevant_collections,
        'invalid_courses': invalid_courses
    }
    
    prompt = f"""IITD Campus Navigator 🎓

Query: {query}

Intent Analysis:
- Main focus areas detected across campus life
- Relevant information from {', '.join(relevant_collections)}
- Using only verified course information
- 
Guidelines:
1. Only provide course details that are explicitly available in the data
2. If a course field isn't available, don't mention it
3. For invalid course codes, suggest checking the department website
4. Use IITD lingo naturally (bhai, atthi (8 cg), nahli (9 cg), devdass (broke up person), machao (a cracked dude who is so successful everyone's jealous), super senior (5th year senior), faccha/facchi (first year), rdv (rendevezous, cult fest of iitd), litwits (meme channel of iitd), dassi (10 cg), satti (7 cg), fakka (fail course), bt (bad time/bad trip))
5. Keep responses factual and data-driven
6. Consider conversation history for context
7. You are not meant to use words like atthi nahli dassi as replacement for bhai
8. Integrate Gen-Z Lingo
9. A brief rundown of clubs at IIT Delhi
- QC: Quizzing club of iit delhi
- DevClub: Developer student club
- DebSoc: Debating Society
- PFC: Photography and Film Club
- Dance Club: Dance Club
- Vdefyn: Related to dance
- Music Club: Music Club
- FACC: Fine Arts and Crafts Club
- Lit Club: Literary Society, the literature cookers
- EDC: Entrepreneurship Development Cell
- Drama Club: Drama Club
- Hindi Samiti and Spic Macay: The maestros of ghazal
- Aries: AI/ML Club
- Axl8r is the formula 1 club, Hyperloop is building hyperloop, robotics club is known for robotics

Courses found: {list(course_info.keys()) if course_info else "None"}
Invalid courses: {invalid_courses if invalid_courses else "None"}

{history_context}

CONTEXT: {context}"""

    try:
        response = groq.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in chat completion: {e}")
        return "I'm having trouble processing your query. Please try again or be more specific."

def main():
    st.title("IITD Campus Navigator 🎓")
    
    # Add a sidebar with additional information
    with st.sidebar:
        st.markdown("""
        ### About
        Welcome to IITD Campus Navigator! Ask me anything about:
        - Courses and academics 📚
        - Campus life and facilities 🏫
        - Interview prep and placements 💼
        - Social scene and activities 🎮
        
        Use natural language and don't hesitate to use IITD lingo!
        """)
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Accept user input
    if prompt := st.chat_input("Ask about courses, campus life, or anything IITD!"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response = chat_with_history(prompt)
            st.write_stream(stream_response(response))
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()