# AI Second Brain

An AI-powered document intelligence system that allows users to upload PDF documents and ask intelligent questions about their content using Retrieval-Augmented Generation (RAG). Built with FastAPI, PostgreSQL, and Google Gemini.

## Features

- **Document Upload & Processing**: Upload PDF files and automatically extract, chunk, and embed text content
- **Intelligent Q&A**: Ask questions about specific documents or search across all your documents
- **Conversation History**: Maintain chat history for each document with contextual follow-ups
- **Vector Search**: Fast semantic search using PostgreSQL with pgvector extension
- **User Authentication**: Secure JWT-based authentication with user isolation
- **Multi-Document Search**: Query across all your uploaded documents simultaneously
- **RESTful API**: Clean, documented API endpoints for all operations

## Tech Stack

- **Backend**: FastAPI (Python web framework)
- **Database**: PostgreSQL with pgvector extension for vector similarity search
- **AI Models**: Google Gemini 2.0-Flash for text generation, Gemini Embedding-001 for embeddings
- **Authentication**: JWT tokens with BCrypt password hashing
- **PDF Processing**: PyPDF library for text extraction
- **ORM**: SQLAlchemy for database operations
- **Deployment**: Uvicorn ASGI server

## Prerequisites

- Python 3.8+
- PostgreSQL database with pgvector extension installed
- Google Gemini API key

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-second-brain
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://username:password@localhost/dbname
   GEMINI_API_KEY=your_gemini_api_key_here
   JWT_SECRET_KEY=your_jwt_secret_key_here
   ```

5. **Set up PostgreSQL database**:
   - Create a PostgreSQL database
   - Install pgvector extension:
     ```sql
     CREATE EXTENSION vector;
     ```

6. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

   Or using the provided scripts:
   ```bash
   ./start.sh  # For Unix-like systems
   ```

## Usage

### API Endpoints

#### Authentication
- `POST /auth/signup` - Register a new user
- `POST /auth/login` - Login and get JWT token

#### File Management
- `POST /upload/` - Upload a PDF document (requires authentication)
- `GET /upload/files` - List all your uploaded documents
- `DELETE /upload/{file_id}` - Delete a document and its associated data

#### AI Queries
- `POST /ai/ask-doc` - Ask a question about a specific document
- `POST /ai/ask-all` - Ask a question across all your documents
- `GET /ai/history/{file_id}` - Get conversation history for a document

### Example Usage

1. **Register/Login** to get a JWT token
2. **Upload a PDF** using the upload endpoint
3. **Ask questions** using the AI endpoints with your token

#### Sample API Call (Ask about a document):
```bash
curl -X POST "http://localhost:8000/ai/ask-doc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main topics covered in this document?",
    "file_id": 1
  }'
```

## Architecture Overview

### Data Flow
1. **Upload**: PDF → Text Extraction → Chunking (800 chars) → Embedding Generation → Vector Storage
2. **Query**: Question → Embedding → Vector Similarity Search → Context Retrieval → AI Generation → Response

### Database Schema
- `users`: User accounts
- `files`: Uploaded document metadata
- `document_chunks`: Text chunks with vector embeddings
- `messages`: Chat history per document

### Key Components
- **Vector Service**: Handles embedding generation and similarity search
- **AI Service**: Interfaces with Google Gemini for question answering
- **Auth Service**: Manages user registration, login, and JWT validation
- **PDF Service**: Processes uploaded PDF files
- **Chat Service**: Manages conversation history

## Configuration

- **Chunk Size**: Default 800 characters (configurable in `pdf_service.py`)
- **Search Results**: Top 4 chunks for single doc, top 6 for all docs
- **Conversation History**: Last 5 messages included in context
- **JWT Expiry**: 24 hours

## Deployment

### Using Procfile (Heroku-style)
The `Procfile` is configured for deployment:
```
web: uvicorn app.main:app --host=0.0.0.0 --port=$PORT
```

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `JWT_SECRET_KEY`: Secret key for JWT signing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive Swagger UI documentation.