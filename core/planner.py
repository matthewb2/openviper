import json
from agent.config import llm_call


class Planner:

    def plan(self, goal: str, context: dict) -> dict:
        prompt = f"""
You are a coding agent planner.
If the user asks to create code, write code, generate a script, or build a program,
you MUST use action="write_file".

You are NOT allowed to respond with action="done"
unless at least one file operation has already occurred.

Never finish immediately when the goal involves coding.
GOAL:
{goal}

CONTEXT:
{context}

Return STRICT JSON only:

{{
  "action": "search|edit|read_file|write_file|test|done",
  "details": {{
    "file_path": "",
    "query": "",
    "instruction": ""
  }}
}}
"""

        raw = llm_call(prompt)

        try:
            parsed = json.loads(raw)
            if "action" not in parsed:
                raise ValueError("Invalid schema")
            return parsed
        except Exception:
            # fallback 안전 처리
            return {
                "action": "done",
                "details": {}
            }