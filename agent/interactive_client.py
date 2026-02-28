# interactive_client.py (Groq version)
import sys
import re
import os
import requests
from dotenv import load_dotenv
from groq import Groq
import json

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.core import Memory

memory = Memory()




def safe_json_loads(text):
    decoder = json.JSONDecoder()
    obj, index = decoder.raw_decode(text)
    return obj

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
You must respond with ONLY valid JSON.
Do not include explanations.
Do not use markdown.
Do not add any text before or after JSON.
Do not explain.
"""


conversation_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response")
    return match.group(0)


def build_context(user_input):
    context = {
        "current_project": memory.get_project(),
        "last_action": memory.get_last_action(),
        "last_file": memory.get_last_file(),
        "recent_history": memory.get_recent_history(),
        "recent_errors": memory.get_recent_errors()
    }
    return context
    
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
    json_str = extract_json(content)

    return safe_json_loads(content)
    
    
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

def read_multiline_input(prompt=">>> "):
    print(prompt + "(여러 줄 입력 가능, 빈 줄 두 번 입력 시 종료)")
    
    lines = []
    empty_count = 0
    
    while True:
        try:
            line = input()
        except EOFError:
            break
        
        if line.strip() == "":
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
        
        lines.append(line)
    
    return "\n".join(lines)
    
def interactive_loop():
    print("=== Groq Coding Agent Interactive Mode ===")

    while True:
        user_input = read_multiline_input(">>> ")

        if not user_input:
            continue

        # 1️⃣ LLM 계획 생성
        plan = call_llm(user_input)
        
        context = build_context(user_input)

        messages = [
            {"role": "system", "content": "You are a coding agent. Respond ONLY in JSON."},
            {"role": "system", "content": f"Memory Context: {json.dumps(context)}"},
            {"role": "user", "content": user_input}
        ]

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
        
        memory.set_last_action(plan.get("action"))

        if "project_name" in plan.get("details", {}):
            memory.set_project(plan["details"]["project_name"])

        if "file_path" in plan.get("details", {}):
            memory.set_last_file(plan["details"]["file_path"])

        memory.add_history(user_input, plan)


# ==============================
# 🚀 실행
# ==============================

if __name__ == "__main__":
    interactive_loop()