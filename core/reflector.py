import json
from agent.config import llm_call


class Reflector:

    def reflect(self, result: str, context: dict) -> dict:
        prompt = f"""
You are a debugging reflector.

Result:
{result}

Context:
{context}

Return STRICT JSON:

{{
  "next_action": "retry|done"
}}
"""

        raw = llm_call(prompt)

        try:
            parsed = json.loads(raw)
            if "next_action" not in parsed:
                raise ValueError()
            return parsed
        except Exception:
            return {"next_action": "done"}