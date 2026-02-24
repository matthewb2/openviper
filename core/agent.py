import uuid
import os
from typing import Any
from agent.core.state import AgentStateData, Task
from agent.core.planner import Planner
from agent.core.editor import Editor
from agent.core.reflector import Reflector
from agent.tools.registry import ToolRegistry
from agent.memory.working_memory import WorkingMemory
from agent.context.context_builder import ContextBuilder


class CodingAgent:

    def __init__(self, max_iterations: int = 10):
        self.state = AgentStateData(max_iterations=max_iterations)
        self.planner = Planner()
        self.editor = Editor()
        self.reflector = Reflector()
        self.tool_registry = ToolRegistry()
        self.memory = WorkingMemory()
        self.context_builder = ContextBuilder()
        self.history = []

        # 🔥 최소 1파일 생성 보장 플래그
        self.file_operation_success = False

    # ==========================
    # PUBLIC RUN
    # ==========================

    def run(self, goal: str) -> dict[str, Any]:

        task = Task(id=str(uuid.uuid4()), description=goal)
        self.state.add_task(task)

        self.memory.add("goal", goal)

        # 🔥 매 실행마다 초기화
        self.file_operation_success = False

        while not self.state.is_max_iterations_reached():

            self.state.increment_iteration()

            context = self._build_context()

            plan = self.planner.plan(goal, context)

            print(f"\n[ITER {self.state.iteration}] PLAN:", plan)
            
            if plan.get("action") == "done" and "코드" in goal:
                print("⚠ Planner 수정: 코딩 요청이므로 write_file 강제 전환")
                plan = {
                    "action": "write_file",
                    "details": {
                        "file_path": "output.py",
                        "content": "print('Hello World')"
                    }
                }

            result = self._execute(plan)

            print(f"[ITER {self.state.iteration}] RESULT:", result)

            reflection = self.reflector.reflect(str(result), context)

            print(f"[ITER {self.state.iteration}] REFLECTION:", reflection)

            # 🔒 DONE 강제 차단
            if reflection.get("next_action") == "done":

                if not self.file_operation_success:
                    print("🚫 DONE 차단: 최소 1개 파일 생성/수정이 필요합니다.")
                    continue

                print("✅ DONE 허용: 파일 변경 확인됨")

                return {
                    "status": "success",
                    "result": result,
                    "iterations": self.state.iteration
                }

        return {
            "status": "error",
            "error": "Max iterations reached",
            "iterations": self.state.iteration
        }

    # ==========================
    # CONTEXT
    # ==========================

    def _build_context(self) -> dict:
        files = self.tool_registry.execute("list_directory", path=".")
        return {
            "iteration": self.state.iteration,
            "memory": self.memory.get_all(),
            "files": files
        }

    # ==========================
    # ACTION EXECUTION
    # ==========================

    def _execute(self, plan: dict) -> Any:

        action = plan.get("action")
        details = plan.get("details", {})

        if action == "search":
            return self.tool_registry.execute(
                "web_search",
                query=details.get("query", "")
            )

        elif action == "read_file":
            return self.tool_registry.execute(
                "read_file",
                file_path=details.get("file_path", "")
            )

        elif action == "edit":
            return self._handle_edit(details)

        elif action == "write_file":
            result = self.tool_registry.execute(
                "write_file",
                file_path=details.get("file_path", ""),
                content=details.get("content", "")
            )

            # 🔥 성공 판정 조건 강화
            if isinstance(result, dict) and not result.get("error"):
                self.file_operation_success = True

            return result

        elif action == "test":
            return self.tool_registry.execute("run_tests")

        elif action == "done":
            # 🔥 직접 done 호출도 차단
            if not self.file_operation_success:
                return {"error": "DONE blocked: no file created"}
            return {"status": "done"}

        return {"status": "unknown_action"}

    # ==========================
    # EDIT HANDLER (안정화)
    # ==========================

    def _handle_edit(self, details: dict):

        file_path = details.get("file_path")

        if not file_path:
            return {"error": "file_path missing"}

        # 1️⃣ read
        original = self.tool_registry.execute(
            "read_file",
            file_path=file_path
        )

        if isinstance(original, dict) and "error" in original:
            return original

        # 2️⃣ LLM edit
        updated = self.editor.edit(
            details.get("instruction", ""),
            original,
            details.get("web_info", "")
        )

        if not isinstance(updated, str):
            return {"error": "LLM edit failed"}

        # 3️⃣ write
        write_result = self.tool_registry.execute(
            "write_file",
            file_path=file_path,
            content=updated
        )

        # 🔥 성공 시만 인정
        if isinstance(write_result, dict) and not write_result.get("error"):
            self.file_operation_success = True

        return write_result