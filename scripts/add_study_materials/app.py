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

    # Generate assistant response
    assistant_response = f"Hi there! You said: {user_input}"  # Replace with AI logic if needed
    st.session_state.chat_history.append({"role": "assistant", "message": assistant_response})
    st.markdown(f'<div class="assistant-message">{assistant_response}</div>', unsafe_allow_html=True)