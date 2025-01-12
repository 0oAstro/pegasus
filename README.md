# IITD Campus Navigator: Vector Search System
Version 1.0 | January 2025

## Overview

IITD Campus Navigator is a chat-based system that helps users explore and understand life at IIT Delhi. Using vector search and language models, it provides information about:

- Academic programs and courses
- Campus facilities and navigation
- Student life and experiences
- Career guidance and opportunities

## System Architecture

### Core Components

```
[Streamlit Frontend] <-> [Chat Interface] <-> [Vector Search] <-> [Qdrant]
                                        |
                                  [Groq LLM API]
```

### Technology Stack

- Frontend: Streamlit
- Vector Database: Qdrant
- Embeddings: SentenceTransformer (all-MiniLM-L6-v2)
- LLM: Groq API
- Environment: Poetry, Nix

## Data Sources

### Academic Information

1. Course Catalog
   - Scraped course details
   - Course codes and names
   - Credit information
   - Prerequisites
   - Course descriptions

2. BSP Academic Resources
   - Course experiences
   - Study materials
   - Academic guidance
   - Student testimonials

### Inception Magazine Content

The freshers' magazine "Inception" provides:
- Campus facility descriptions
- Hostel information
- Navigation guides
- First-year experiences
- Essential campus knowledge

### Dalle United Magazine Content

BSP's "Dalle United" magazine contributes:
- Student interviews
- Campus life stories
- Cultural coverage
- Academic experiences
- Career guidance

## Vector Store Implementation

### Data Processing

1. Text Preprocessing
   - Cleaning and formatting
   - Context preservation
   - Campus terminology handling

2. Vector Generation
   - Text-to-vector conversion
   - Semantic embedding creation
   - Context maintenance

3. Collection Structure
   - Organized by source type
   - Optimized for retrieval
   - Contextual relationships preserved

## Development Setup

### Environment Configuration

```bash
# Initialize development environment
nix-shell
poetry install

# Start application
poetry run streamlit run app.py
```

### Project Structure

```
iitd-navigator/
├── pyproject.toml
├── poetry.lock
├── shell.nix
├── scripts/
│   ├── scraping/
│   ├── processing/
│   └── embedding/
├── docs/
└── notebooks/
```

## Query Processing

### Search Flow

1. Query Analysis
   - Intent recognition
   - Context identification
   - Source prioritization

2. Response Generation
   - Context-aware answers
   - Source combination
   - Natural language output

## Planned Enhancements

### Near-term

1. Content Updates
   - Regular magazine updates
   - New course information
   - Fresh student experiences

2. Search Features
   - Better context handling
   - Conversation memory
   - Multi-topic queries

### Long-term

1. User Experience
   - Mobile interface
   - Response speed
   - Better error handling

2. Data Coverage
   - More student resources
   - Additional magazines
   - Updated course content

## Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make changes with documentation
4. Submit a pull request

## License

MIT License. See LICENSE file.

---

*For detailed implementation information, refer to the scripts/ directory and development notebooks.*