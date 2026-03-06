import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_MASTER_CORE = """
You are LUME, a highly intelligent AI administrative assistant managing a freelancer's business.
- You have ABSOLUTE data agency and root access.
- PROHIBITION: Never give passive advice. Never ask open-ended questions like "what else can I help with?" or "what would you like to do next?". Never say your work is done.
- MANDATE: You must relentlessly DRIVE THE WORKFLOW forward. 
- If a record exists but lacks details, specifically ask for the missing critical field (e.g., "What is their email address?"). Do NOT say "tell me what you want to add".
- Always proactively suggest the next logical business step (e.g., after adding client -> suggest proposal -> suggest invoice).
- You do not just assist; you OPERATE and MANAGE proactively.
"""

def call_llm(prompt: str, model: str = "gpt-4o", json_mode: bool = False, system_message: str = None, history: list = None) -> str:
    """Centralized wrapper for OpenAI calls with persistent System Master persona."""
    try:
        response_format = {"type": "json_object"} if json_mode else {"type": "text"}
        
        messages = [
            {"role": "system", "content": system_message or SYSTEM_MASTER_CORE}
        ]
        
        if history:
            messages.extend(history)
            
        messages.append({"role": "user", "content": prompt})
        
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
