import os
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

LLM_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MAX_TOKENS = 4000


def llm_call(prompt: str, model: str = LLM_MODEL, temperature: float = 0.7) -> str:
    """Groq API 호출 함수"""
    if not LLM_API_KEY:
        return '{"action": "done", "reason": "No Groq API key configured"}'
    
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=GROQ_BASE_URL
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=MAX_TOKENS
        )
        content = response.choices[0].message.content
        return content if content is not None else '{"action": "done", "reason": "No response"}'
    except Exception as e:
        return f'{{"error": "{str(e)}"}}'


def llm_json_call(prompt: str) -> dict[str, Any]:
    """JSON 형식으로 응답하는 LLM 호출"""
    import json
    try:
        response = llm_call(prompt)
        return json.loads(response)
    except json.JSONDecodeError:
        return {"action": "error", "reason": "Failed to parse JSON"}


GROQ_MODELS = [
    "mixtral-8x7b-32768",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemma-7b-it"
]
