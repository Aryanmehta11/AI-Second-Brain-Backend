import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
genai.configure(api_key=os.getenv("GENAI_API_KEY"))
model=genai.GenerativeModel("gemini-2.0-flash")

def ask_gemini(question:str):
    response=model.generate_content(question)
    return response.text