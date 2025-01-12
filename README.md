# Campus Navigator Chatbot Project Report

## Introduction
The Campus Navigator chatbot is designed to provide users with information about courses offered at IIT Delhi, as well as insights from interviews conducted by the Business Standard Premium (BSP). The project involves several key components, including web scraping, data processing, vector database integration, OCR, and UI development.

## Project Components

### 1. Course Information Scraping
- **Objective**: To gather detailed information about courses of study and courses offered at IIT Delhi.
- **Method**: Web scraping techniques were employed to extract course data from IIT Delhi's official website.
- **Outcome**: A comprehensive dataset of courses, including course titles, descriptions, and other relevant details.

### 2. Vector Database Integration
- **Objective**: To store and retrieve course information efficiently.
- **Method**: Qdrant, a vector similarity search engine, was used to add the scraped course data to a vector database.
- **Outcome**: Each course was assigned a unique `course_id` based on an MD5 hash, facilitating quick and accurate data retrieval.

### 3. Interview Data Processing
- **Objective**: To analyze and chunk interview data for better understanding and retrieval.
- **Method**: Interviews were scraped from BSP and then chunked using NLTK's Punkt tokenizer. Gemini was used for further processing.
- **Outcome**: Structured and chunked interview data, ready for integration and analysis.

### 4. Data Normalization
- **Objective**: To ensure consistency and uniformity in the data.
- **Method**: All scraped and processed data were normalized to maintain a standard format.
- **Outcome**: Normalized data that is easy to query and retrieve.

### 5. OCR on Inception PDF
- **Objective**: To extract textual information from PDF documents related to IIT Delhi.
- **Method**: Optical Character Recognition (OCR) was performed on the Inception PDF to extract IITD lingo and general information.
- **Outcome**: Extracted text data that provides insights into IIT Delhi's terminology and general information.

### 6. User Interface Development
- **Objective**: To create an intuitive and user-friendly interface for interacting with the chatbot.
- **Method**: Streamlit was used to develop the UI, allowing users to query the chatbot and receive information.
- **Outcome**: A functional and aesthetically pleasing UI that enhances user experience.

## Conclusion
The Campus Navigator chatbot project successfully integrates various technologies to provide a comprehensive solution for accessing course information and interview insights related to IIT Delhi. The use of web scraping, vector databases, data processing, OCR, and UI development ensures that the chatbot is both efficient and user-friendly.

## Future Work
- **Enhancements**: Continuous improvement of the chatbot's capabilities, including more advanced NLP techniques and expanded data sources.
- **Maintenance**: Regular updates to the course and interview data to ensure accuracy and relevance.
- **User Feedback**: Incorporating user feedback to refine the chatbot's functionality and UI.