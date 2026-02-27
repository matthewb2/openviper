# interactive_client.py (Groq version)

import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq

# ==============================
# 🔧 환경 설정
# ==============================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MCP_SERVER_URL = "http://localhost:8000"

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)

# ==============================
# 🧠 시스템 프롬프트
# ==============================

SYSTEM_PROMPT = """
You are a coding agent planner.

Available MCP tools:

1. create_project
   parameters: { "project_name": string }

2. write_file
   parameters: {
       "project_name": string,
       "file_path": string,
       "content": string
   }

3. run_maven
   parameters: {
       "project_name": string,
       "goal": string
   }

4. run_java
   parameters: {
       "project_name": string,
       "main_class": string
   }

You MUST respond ONLY in valid JSON.
The current project name must be reused unless user specifies otherwise.
All Java source files must be placed inside:
src/main/java/
If a tool is needed:

{
  "action": "tool_name",
  "parameters": { ... }
}

If no tool is needed:

{
  "action": "none",
  "message": "text"
}

Do not explain.
Return JSON only.
"""


conversation_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


# ==============================
# 🤖 LLM 호출
# ==============================

def call_llm(user_input):

    conversation_history.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history,
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    # LLM 응답도 저장
    conversation_history.append({"role": "assistant", "content": content})

    return json.loads(content)
    
# ==============================
# 🔌 MCP 서버 호출
# ==============================

def call_mcp(action, params):
    try:
        url = f"{MCP_SERVER_URL}/{action}"
        response = requests.post(url, json=params, timeout=60)

        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}",
                "detail": response.text
            }

        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": "MCP server connection failed",
            "detail": str(e)
        }


# ==============================
# 🔁 대화형 루프
# ==============================

def interactive_loop():
    print("=== Groq Coding Agent Interactive Mode ===")
    print("종료하려면 'exit' 입력\n")

    while True:
        user_input = input(">>> ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("종료합니다.")
            break

        if not user_input:
            continue

        # 1️⃣ LLM 계획 생성
        plan = call_llm(user_input)

        action = plan.get("action")

        if action == "none":
            print(plan.get("message", "No action"))
            continue

        print(f"\n[PLAN] → {action}")
        print("[PARAMS]")
        print(json.dumps(plan.get("parameters", {}), indent=2, ensure_ascii=False))

        # 2️⃣ MCP 실행
        result = call_mcp(action, plan.get("parameters", {}))

        print("\n[RESULT]")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n----------------------------------------\n")


# ==============================
# 🚀 실행
# ==============================

if __name__ == "__main__":
    interactive_loop()