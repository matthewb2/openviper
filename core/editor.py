from typing import Any
from agent.config import llm_call


class Editor:
    def __init__(self):
        self.max_file_size = 100000

    def edit(self, goal: str, file_content: str = "", web_info: str = "", instruction: str = "") -> str:
        prompt = f"""
너는 코드 편집기다. 주어진 목표에 따라 코드를 작성하거나 수정해야 한다.

## 목표
{goal}

## 웹 검색 결과
{web_info if web_info else "관련 웹 정보 없음"}

## 현재 파일 내용
{file_content if file_content else "새 파일 작성"}

## 편집 지시사항
{instruction if instruction else "목표에 맞게 코드 작성"}

## 요구사항
1. 현재 파일 내용을 기반으로 목표를 달성하도록 수정
2. 웹 검색 결과를 참고하여 정확한 정보 반영
3. 전체 파일 내용을 반환
4. 코드는 반드시 실행 가능한 형태로 작성
5. 주석은 한국어로 작성

코드만 출력한다.
"""
        return llm_call(prompt, temperature=0.3)

    def read_file_for_edit(self, goal: str, file_path: str) -> str:
        prompt = f"""
너는 코드 편집기다. 파일을 읽고 목표에 맞게 수정할 준비를 해야 한다.

## 목표
{goal}

## 파일 경로
{file_path}

## 작업
이 파일을 편집할 준비가 되었다. "준비 완료"만 출력한다.
"""
        return llm_call(prompt, temperature=0.3)

    def validate_syntax(self, code: str, language: str = "python") -> dict[str, Any]:
        prompt = f"""
다음 코드의 문법 오류를 확인하고 JSON으로 결과를 반환하라.

```python
{code}
```

## 출력 형식
{{
    "valid": true/false,
    "errors": ["오류 목록"]
}}
"""
        import json
        try:
            result = llm_call(prompt, temperature=0.1)
            return json.loads(result)
        except:
            return {"valid": False, "errors": ["Syntax validation failed"]}
