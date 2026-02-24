from typing import Any
from agent.config import llm_call, llm_json_call


class Reflector:
    def __init__(self):
        self.max_reflection_depth = 3

    def reflect(self, logs: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context_str = self._format_context(context) if context else ""
        prompt = f"""
너는 코딩 에이전트의 자기반성 모듈이다. 작업 결과를 분석하고 개선점을 파악해야 한다.

## 작업 로그
{logs}

## 현재 맥락
{context_str}

## 출력 형식 (JSON)
{{
    "success": true/false,
    "analysis": "결과 분석",
    "issues": ["발견된 문제점"],
    "suggestions": ["개선 제안"],
    "next_action": "reflect|retry|fix|done"
}}

분석 결과를 JSON으로만 출력한다.
"""
        return llm_json_call(prompt)

    def analyze_error(self, error: str, context: dict[str, Any]) -> dict[str, Any]:
        context_str = self._format_context(context)
        prompt = f"""
너는 디버깅 전문가다. 오류를 분석하고 해결책을 제시해야 한다.

## 오류 메시지
{error}

## 현재 맥락
{context_str}

## 출력 형식 (JSON)
{{
    "root_cause": "근본 원인",
    "solution": "해결 방법",
    "files_to_check": ["확인할 파일"],
    "fix_suggestion": "수정 제안"
}}

JSON으로만 출력한다.
"""
        return llm_json_call(prompt)

    def evaluate_result(self, result: Any, expected: str) -> dict[str, Any]:
        prompt = f"""
너는 결과 평가 전문가다. 작업 결과가 기대값과 일치하는지 평가하라.

## 기대 결과
{expected}

## 실제 결과
{result}

## 출력 형식 (JSON)
{{
    "passed": true/false,
    "score": 0-100,
    "feedback": "평가 피드백"
}}

JSON으로만 출력한다.
"""
        return llm_json_call(prompt)

    def _format_context(self, context: dict[str, Any]) -> str:
        if not context:
            return "맥락 정보 없음"
        
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
