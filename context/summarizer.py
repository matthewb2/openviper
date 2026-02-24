from typing import Any
from agent.config import llm_call, llm_json_call


class Summarizer:
    def __init__(self):
        self.max_length = 2000

    def summarize(self, text: str, max_tokens: int = 500) -> str:
        if len(text) <= self.max_length:
            return text
        
        prompt = f"""
다음 텍스트를 요약하라.

{text}

요약:
"""
        
        try:
            return llm_call(prompt)
        except:
            return text[:self.max_length] + "..."

    def summarize_context(self, context: dict[str, Any]) -> str:
        context_str = self._format_context(context)
        prompt = f"""
다음 에이전트 맥락을 간단히 요약하라.

{context_str}

핵심만 간결하게:
"""
        
        try:
            return llm_call(prompt)
        except:
            return context_str[:500]

    def summarize_history(self, history: list[dict[str, Any]]) -> str:
        if not history:
            return "No history"
        
        history_str = "\n".join([
            f"- {h.get('key', 'unknown')}: {str(h.get('value', ''))[:100]}"
            for h in history[-10:]
        ])
        
        prompt = f"""
다음 작업 이력을 요약하라.

{history_str}

요약:
"""
        
        try:
            return llm_call(prompt)
        except:
            return history_str

    def summarize_errors(self, errors: list[str]) -> str:
        if not errors:
            return "No errors"
        
        errors_str = "\n".join([f"- {e}" for e in errors[-5:]])
        
        prompt = f"""
다음 오류들을 분석하고 핵심 문제점을 요약하라.

{errors_str}

분석:
"""
        
        try:
            return llm_call(prompt)
        except:
            return errors_str

    def extract_key_info(self, text: str) -> dict[str, Any]:
        prompt = f"""
다음 텍스트에서 핵심 정보를 추출하라.

{text}

JSON 형식으로:
{{
    "files_mentioned": [],
    "functions_mentioned": [],
    "errors_mentioned": [],
    "goals": []
}}
"""
        
        try:
            result = llm_call(prompt)
            return llm_json_call(result)
        except:
            return {}

    def _format_context(self, context: dict[str, Any]) -> str:
        lines = []
        for key, value in context.items():
            if isinstance(value, str):
                value = value[:200]
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def create_summary_for_next_iteration(
        self,
        previous_result: Any,
        reflection: dict[str, Any]
    ) -> str:
        prompt = f"""
이전 작업 결과와 반성을 기반으로 다음 작업을 위한 간단한 컨텍스트를 생성하라.

이전 결과:
{previous_result}

반성:
{reflection}

핵심 컨텍스트:
"""
        
        try:
            return llm_call(prompt)
        except:
            return f"Previous: {str(previous_result)[:100]}"
