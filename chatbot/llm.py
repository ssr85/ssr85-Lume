import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_MASTER_CORE = """
You are the LUME System Master OS. 
- You have ABSOLUTE data agency.
- PROHIBITION: Never give advice, never suggest how the user should do something, and never explain standard database operations.
- MANDATE: If a user mentions a new entity (client, project, invoice), you must IMMEDIATELY execute the mutation.
- You do not assist; you OPERATE. 
"""

def call_llm(prompt: str, model: str = "gpt-4o", json_mode: bool = False, system_message: str = None) -> str:
    """Centralized wrapper for OpenAI calls with persistent System Master persona."""
    try:
        response_format = {"type": "json_object"} if json_mode else {"type": "text"}
        
        messages = [
            {"role": "system", "content": system_message or SYSTEM_MASTER_CORE},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format=response_format,
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Call Error: {e}")
        return None
