import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(prompt: str, model: str = "gpt-4o", json_mode: bool = False) -> str:
    """Centralized wrapper for OpenAI calls."""
    try:
        response_format = {"type": "json_object"} if json_mode else {"type": "text"}
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format,
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Call Error: {e}")
        return None
