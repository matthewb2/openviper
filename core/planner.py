# core/planner.py

import json
import re
from agent.config import llm_call


class Planner:

    def _clean_json(self, text: str) -> str:
        text = re.sub(r"```json", "", text)
        text = re.sub(r"```", "", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text.strip()

    def plan(self, goal: str, context: dict) -> dict:

        prompt = f"""
You are a coding task planner.

Return STRICT JSON only.

Available actions:
- write_file
- create_folder

Rules:
- DO NOT include source code.
- DO NOT include explanations.
- Only return JSON.

GOAL:
{goal}

CONTEXT:
{context}
"""

        raw = llm_call(prompt, temperature=0)
        cleaned = self._clean_json(raw)

        try:
            parsed = json.loads(cleaned)
            return parsed
        except Exception:
            raise RuntimeError(f"Planner JSON invalid:\n{raw}")