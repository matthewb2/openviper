import json
from typing import Any
from agent.config import llm_call, llm_json_call


class Planner:
    def __init__(self):
        self.max_steps = 20

    def plan(self, goal: str, context: dict[str, Any]) -> dict[str, Any]:
        context_str = self._format_context(context)
        prompt = f"""
너는 코딩 에이전트의 플래너다. 사용자의 목표를 달성하기 위한 실행 가능한行动计划을 세워야 한다.

## 목표
{goal}

## 현재 맥락
{context_str}

## 출력 형식 (JSON)
{{
    "action": "search|edit|test|read_file|write_file|reflect|done",
    "reason": "행동을 선택한 이유",
    "details": {{
        "query": "검색어 또는 파일 경로",
        "instruction": "편집 지시사항",
        "content": "파일 작성 시 내용"
    }}
}}

실행 가능한行动计划만 제안하고, 반드시 JSON 형식으로만 출력한다.
"""
        return llm_json_call(prompt)

    def _format_context(self, context: dict[str, Any]) -> str:
        if not context:
            return "맥락 정보 없음"
        
        lines = []
        if "current_file" in context:
            lines.append(f"현재 파일: {context['current_file']}")
        if "recent_actions" in context:
            lines.append(f"최근 행동: {context['recent_actions'][-3:]}")
        if "errors" in context:
            lines.append(f"오류: {context['errors']}")
        if "task_history" in context:
            lines.append(f"작업 이력: {context['task_history'][-3:]}")
        
        return "\n".join(lines) if lines else "특별한 맥락 정보 없음"

    def create_subtask_plan(self, goal: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        context_str = self._format_context(context)
        prompt = f"""
너는 코딩 에이전트의 플래너다. 사용자의 목표를 여러 개의 작은 작업으로 분해해야 한다.

## 목표
{goal}

## 현재 맥락
{context_str}

## 출력 형식 (JSON 배열)
[
    {{"step": 1, "description": "작업 설명", "action": "search|edit|test|read_file|write_file"}}
]

목표를 달성하기 위해 필요한 최소한의 작업 단계로 분해하고, JSON 배열 형식으로만 출력한다.
"""
        result = llm_call(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return [{"step": 1, "description": goal, "action": "done"}]
