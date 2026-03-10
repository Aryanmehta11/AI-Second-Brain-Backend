# test_ragas.py
from dotenv import load_dotenv
load_dotenv()

from app.services.vector_service import search_chunks
from app.services.ai_service import ask_gemini
from app.services.eval_service import run_evaluation
from app.db.database import SessionLocal


def evaluate_real_question(
    question: str,
    file_id: int,
    ground_truth: str = None
):
    db = SessionLocal()

    # Step 1: Real chunks from YOUR pgvector
    chunks = search_chunks(db, question, file_id)
    db.close()

    print(f"📦 Retrieved {len(chunks)} chunks")

    if not chunks:
        print("❌ No chunks found — try a different file_id")
        return

    # Step 2: Real answer from YOUR Gemini
    context = "\n\n".join(chunks)
    prompt  = f"""You are a helpful document assistant.
Use ONLY the following document context to answer.
DOCUMENT CONTEXT: {context}
USER QUESTION: {question}"""

    answer = ask_gemini(prompt)
    print(f"💬 Answer: {answer[:150]}...")

    # Step 3: Score with RAGAs
    scores = run_evaluation(
        question     = question,
        answer       = answer,
        contexts     = chunks,
        ground_truth = ground_truth,
    )

    print("\n📊 RAGAs Scores on YOUR real system:")
    for metric, score in scores.items():
        emoji = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
        print(f"   {emoji} {metric}: {score}")

    return scores


# File 14 is your Azure cert document
evaluate_real_question(
    question     = "What is this document about?",
    file_id      = 14,
    ground_truth = "This document is about Aryan Mehta achieving the Microsoft Certified Azure Administrator Associate certification, including the date of achievement and certification details."
)