import os 
from google import genai
from dotenv import load_dotenv
from ragas import evaluate,EvaluationDataset,SingleTurnSample
from ragas.embeddings import embedding_factory
from ragas.llms import llm_factory
from ragas.metrics import (
    ContextPrecision,
    Faithfulness,
    AnswerCorrectness,
)
load_dotenv()

#RAGas own Gemini
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
llm    = llm_factory("gemini-2.5-flash", provider="google", client=client)
embeddings=embedding_factory(provider="google",client=client)

def run_evaluation(question:str,answer:str,contexts:str,ground_truth:str=None)->dict:
    if isinstance(contexts,str):
        contexts=[contexts]

    sample=SingleTurnSample(
        user_input=question,
        response=answer,
        retrieved_contexts=contexts,
        reference=ground_truth
    )
    dataset=EvaluationDataset(samples=[sample])

    metrics=[Faithfulness(llm=llm)]

    if ground_truth:
        metrics.append(AnswerCorrectness(llm=llm))

    result=evaluate(dataset=dataset,metrics=metrics,llm=llm,embeddings=embeddings)

    df=result.to_pandas()
    scores={}
    for col in ["faithfulness","answer_correctness"]:
        if col in df.columns:
            val=df[col].iloc[0]
            if val is not None:
                scores[col]=round(float(val),4)
    return scores            

