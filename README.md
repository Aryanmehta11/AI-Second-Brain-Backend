# 🧠 AI Second Brain

An AI-powered document intelligence system that lets users upload PDF documents and have natural language conversations with them using production-grade RAG.

Built with FastAPI, PostgreSQL, and Google Gemini 2.5 Flash.


## 🎯 What This Is

Not a demo. Not a Jupyter notebook.
A deployed, measured, production-grade RAG system.

---

## 📊 Production Metrics

| Metric | Score |
|---|---|
| Faithfulness | 1.0 — zero hallucination |
| Answer Correctness | 0.97 — 97% accurate |
| Error Rate | 0% across production runs |
| P50 Latency | 2.94s |
| P99 Latency | 32.13s |
| Avg tokens/query | ~1,500 |
| Cost per query | <$0.001 |

Evaluated using RAGAs on real uploaded documents.
Monitored via LangSmith observability.

---

## ✨ Features

- **Hybrid Search** — vector + keyword search combined with Reciprocal Rank Fusion (RRF) for better retrieval accuracy
- **RAGAs Evaluation** — faithfulness + answer correctness scored on real documents
- **LangSmith Observability** — every Gemini call traced with latency, tokens, and cost
- **Token Tracking** — input/output tokens logged per query
- **Multi-Document Search** — query across all uploaded documents simultaneously
- **Conversation History** — contextual follow-up questions per document
- **JWT Authentication** — secure multi-user isolation with BCrypt password hashing
- **Deployed** — live backend on Render + frontend on Netlify

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Database | PostgreSQL + pgvector |
| Vector Search | Hybrid (cosine similarity + tsvector + RRF) |
| LLM | Google Gemini 2.5 Flash |
| Embeddings | Gemini Embedding-001 |
| Auth | JWT + BCrypt |
| Observability | LangSmith |
| Evaluation | RAGAs |
| PDF Processing | PyPDF |
| Deployment | Render (backend) + Netlify (frontend) |

---

## 🏗️ Architecture

### Data Flow

```
Upload:
PDF → Text Extraction → Chunking (800 chars)
→ Gemini Embeddings → pgvector Storage

Query (Hybrid Search):
Question → Embedding → Vector Search (cosine similarity)
                    + Keyword Search (tsvector)
                    → RRF Ranking → Top chunks
                    → Gemini 2.5 Flash → Answer

Evaluation:
Question + Answer + Chunks → RAGAs → Faithfulness + Correctness scores
```

### Database Schema

```
users           → accounts + auth
files           → document metadata
document_chunks → text chunks + vector embeddings + tsvector
messages        → conversation history per document
```

---

## ⚡ Quickstart

### 1. Clone

```bash
git clone https://github.com/Aryanmehta11/AI-Second-Brain-Backend.git
cd AI-Second-Brain-Backend
```

### 2. Virtual environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment variables

Create a `.env` file in the root:

```bash
DATABASE_URL=postgresql://username:password@localhost/dbname
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=your_google_api_key
SECRET_KEY=your_jwt_secret
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=AI-Second-Brain
```

### 5. Set up PostgreSQL

```sql
CREATE EXTENSION vector;

ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS content_tsv tsvector
GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

CREATE INDEX IF NOT EXISTS idx_content_tsv
ON document_chunks USING GIN(content_tsv);
```

### 6. Run

```bash
uvicorn app.main:app --reload
```

---

## 🔌 API Endpoints

### Auth

```
POST /auth/signup      → register new user
POST /auth/login       → get JWT token
```

### Documents

```
POST   /upload/            → upload PDF document
GET    /upload/files       → list your documents
DELETE /upload/{file_id}   → delete document
```

### AI

```
POST /ai/ask-doc           → ask question about specific document
POST /ai/ask-all           → search across all your documents
GET  /ai/history/{file_id} → get conversation history
POST /ai/evaluate          → run RAGAs evaluation scores
```

---

## 🔬 How Hybrid Search Works

Pure vector search has one blind spot — exact terms like IDs, codes, and numbers.

```
"certification number I460-4683"
Vector search → looks for MEANING → misses exact code ❌
Keyword search → finds exact match → returns it instantly ✅
```

Hybrid search runs both simultaneously and combines results using Reciprocal Rank Fusion (RRF):

```
Vector search  → ranked list 1 (semantic similarity)
Keyword search → ranked list 2 (exact matches)
RRF algorithm  → scores each chunk by rank in both lists
               → chunks appearing in both bubble to top
```

Result: better answers on both conceptual and specific queries.

---

## 📈 Observability

Every Gemini call is traced in LangSmith:

```
✅ Full prompt visible per request
✅ Token count — input + output
✅ Latency per call
✅ Cost per query
✅ 0% error rate in production
✅ 17+ production runs traced
```

---

## 💰 Cost Analysis

```
Simple question:    ~1,500 tokens → $0.0003/query
Complex summary:    ~2,700 tokens → $0.0005/query

At scale:
  1,000  users/day → ~$0.30/day  → ~$9/month
  10,000 users/day → ~$3.00/day  → ~$90/month
```

---

## 🔬 RAGAs Evaluation

Run evaluation locally:

```bash
python test_ragas.py
```

Or via API endpoint:

```bash
POST /ai/evaluate
{
  "question": "What is this document about?",
  "file_id": 1,
  "ground_truth": "optional — include for correctness score"
}
```

Response:

```json
{
  "question": "What is this document about?",
  "answer": "This document is about...",
  "chunks_used": 4,
  "scores": {
    "faithfulness": {
      "score": 1.0,
      "rating": "Excellent"
    },
    "answer_correctness": {
      "score": 0.97,
      "rating": "Excellent"
    }
  }
}
```

---

## 🔜 What's Next

- [ ] Streaming responses — word by word like ChatGPT
- [ ] Docker — containerise for one command deployment
- [ ] Semantic chunking — split at meaning boundaries not character count
- [ ] Async evaluation — RAGAs runs in background, zero latency impact
- [ ] Support Word + PPT files — beyond PDF only

---

## 📄 License

MIT — use it, build on it, ship it.

---

<p align="center">Built by <a href="https://github.com/Aryanmehta11">Aryan Mehta</a> | Building in public 🚀</p>
