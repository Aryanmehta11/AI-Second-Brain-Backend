"""
RAGAs evaluation: vector-only vs hybrid (vector + keyword + RRF) retrieval.

Usage:
    docker run -d --name ai_brain_eval_db -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=ai_second_brain -p 5433:5432 pgvector/pgvector:pg16
    python -m eval.run_eval --docs path/to/pdf/folder

Runs against a throwaway local pgvector DB (EVAL_DATABASE_URL), never the
production DATABASE_URL. Answers use the same prompt as /ai/ask-doc.
"""
import argparse
import json
import os
import statistics
import time
from datetime import date
from pathlib import Path

EVAL_DB = os.getenv(
    "EVAL_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/ai_second_brain"
)
os.environ["DATABASE_URL"] = EVAL_DB  # must be set before app imports load .env

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.db.database import SessionLocal
from app.services.ai_service import ask_gemini
from app.services.chunk_service import chunk_text
from app.services.embedding_service import embed_texts
from app.services.pdf_service import extract_text_from_pdf
from app.services.vector_service import search_chunks, hybrid_search_chunks

from google import genai
from ragas import evaluate, EvaluationDataset, SingleTurnSample, RunConfig
from ragas.embeddings import embedding_factory
from ragas.llms import llm_factory
from ragas.metrics import Faithfulness, AnswerCorrectness, LLMContextRecall

EVAL_DIR = Path(__file__).parent
FILE_IDS = {"azure": 9001, "roadmap": 9002}
METRICS = ["faithfulness", "answer_correctness", "context_recall"]


def with_retry(fn, *args, tries=6):
    for i in range(tries):
        try:
            return fn(*args)
        except Exception as e:
            if i == tries - 1:
                raise
            wait = 10 * (i + 1)
            print(f"  retry in {wait}s: {str(e)[:120]}")
            time.sleep(wait)


def setup_schema(db):
    db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id TEXT PRIMARY KEY,
            file_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector,
            content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
        )
    """))
    db.commit()


def ingest(db, docs_dir: Path, documents: dict):
    for key, meta in documents.items():
        file_id = FILE_IDS[key]
        n = db.execute(text("SELECT count(*) FROM document_chunks WHERE file_id=:f"), {"f": file_id}).scalar()
        if n:
            print(f"{key}: {n} chunks already ingested")
            continue
        chunks = chunk_text(extract_text_from_pdf(str(docs_dir / meta["pdf"])))
        for start in range(0, len(chunks), 50):
            batch = chunks[start:start + 50]
            for i, (chunk, emb) in enumerate(zip(batch, with_retry(embed_texts, batch))):
                db.execute(
                    text("INSERT INTO document_chunks (id, file_id, content, embedding) "
                         "VALUES (:id, :f, :c, CAST(:e AS vector))"),
                    {"id": f"{file_id}_{start + i}", "f": file_id, "c": chunk, "e": str(emb)},
                )
        db.commit()
        print(f"{key}: ingested {len(chunks)} chunks")


def answer(question: str, chunks: list[str]) -> str:
    # Same prompt as /ai/ask-doc, with no prior conversation
    context = "\n\n".join(chunks)
    prompt = f"""
You are a helpful document assistant.

Conversation so far:


Use ONLY the following document context to answer.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}
"""
    return with_retry(ask_gemini, prompt)


def score(samples: list[SingleTurnSample]) -> list[dict]:
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    llm = llm_factory("gemini-2.5-flash", provider="google", client=client)
    emb = embedding_factory(provider="google", client=client)
    result = evaluate(
        dataset=EvaluationDataset(samples=samples),
        metrics=[Faithfulness(llm=llm), AnswerCorrectness(llm=llm), LLMContextRecall(llm=llm)],
        llm=llm,
        embeddings=emb,
        run_config=RunConfig(max_workers=4, max_retries=10, max_wait=60, timeout=180),
    )
    df = result.to_pandas()
    return [
        {m: (None if df[m].iloc[i] != df[m].iloc[i] else round(float(df[m].iloc[i]), 4))
         for m in METRICS if m in df.columns}
        for i in range(len(df))
    ]


def push_dataset_to_langsmith(spec: dict):
    try:
        from langsmith import Client
        c = Client()
        if c.has_dataset(dataset_name=spec["name"]):
            return
        ds = c.create_dataset(spec["name"], description=spec["description"])
        c.create_examples(
            inputs=[{"question": q["question"], "doc": q["doc"]} for q in spec["questions"]],
            outputs=[{"ground_truth": q["ground_truth"]} for q in spec["questions"]],
            dataset_id=ds.id,
        )
        print(f"LangSmith dataset created: {spec['name']}")
    except Exception as e:
        print(f"LangSmith upload skipped: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", required=True, help="folder containing the PDFs listed in dataset.json")
    args = ap.parse_args()

    spec = json.loads((EVAL_DIR / "dataset.json").read_text(encoding="utf8"))
    db = SessionLocal()
    setup_schema(db)
    ingest(db, Path(args.docs), spec["documents"])
    push_dataset_to_langsmith(spec)

    retrievers = {"vector": search_chunks, "hybrid": hybrid_search_chunks}
    rows = []
    for mode, retrieve in retrievers.items():
        samples = []
        for n, q in enumerate(spec["questions"], 1):
            chunks = retrieve(db, q["question"], FILE_IDS[q["doc"]])
            ans = answer(q["question"], chunks)
            print(f"[{mode} {n}/{len(spec['questions'])}] {q['question'][:60]}")
            samples.append(SingleTurnSample(
                user_input=q["question"], response=ans,
                retrieved_contexts=chunks, reference=q["ground_truth"],
            ))
            rows.append({"mode": mode, "doc": q["doc"], "question": q["question"],
                         "ground_truth": q["ground_truth"], "answer": ans, "chunks": len(chunks)})
        scores = score(samples)
        for row, s in zip([r for r in rows if r["mode"] == mode], scores):
            row["scores"] = s
    db.close()

    summary = {}
    for mode in retrievers:
        summary[mode] = {}
        for m in METRICS:
            vals = [r["scores"].get(m) for r in rows if r["mode"] == mode and r["scores"].get(m) is not None]
            summary[mode][m] = {"mean": round(statistics.mean(vals), 3) if vals else None, "n": len(vals)}

    out = EVAL_DIR / "results" / f"{date.today()}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"dataset": spec["name"], "judge": "gemini-2.5-flash",
                               "summary": summary, "rows": rows}, indent=2), encoding="utf8")

    print(f"\n| Retrieval | {' | '.join(METRICS)} |\n|---|{'---|' * len(METRICS)}")
    for mode, s in summary.items():
        print(f"| {mode} | " + " | ".join(f"{s[m]['mean']} (n={s[m]['n']})" for m in METRICS) + " |")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
