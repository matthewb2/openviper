import uuid
import os
from typing import Any
from agent.core.state import AgentStateData, Task
from agent.core.planner import Planner
from agent.core.editor import Editor
from agent.core.reflector import Reflector
from agent.tools.registry import ToolRegistry
from agent.memory.working_memory import WorkingMemory
from agent.context.context_handler import ContextHandler
from agent.core.executor import Executor


class CodingAgent:

    def __init__(self, max_iterations: int = 10):
        self.state = AgentStateData(max_iterations=max_iterations)
        self.planner = Planner()
        self.editor = Editor()
        self.reflector = Reflector()
        self.tool_registry = ToolRegistry()
        self.memory = WorkingMemory()
        self.file_operation_success = False
        self.last_goal: str = ""

    # ==========================
    # PUBLIC RUN
    # ==========================

    def run(self, goal: str) -> dict[str, Any]:

        task = Task(id=str(uuid.uuid4()), description=goal)
        self.state.add_task(task)

        self.memory.add("goal", goal)
        self.last_goal = goal

        import re

        # ==========================
        # 🔥 파일 실행 요청 감지
        # ==========================
        if '실행' in goal or 'run' in goal.lower() or 'execute' in goal.lower():

            file_match = re.search(r'(\S+\.(py|java|js))', goal)

            if file_match:
                file_name = file_match.group(1)

                if not os.path.exists(file_name):
                    return {
                        "status": "error",
                        "error": f"파일이 존재하지 않습니다: {file_name}",
                        "iterations": 1
                    }

                print(f"[EXECUTE] {file_name}")
                exec_result = Executor.execute_file(file_name)

                return {
                    "status": exec_result.get("status", "ok"),
                    "result": exec_result,
                    "iterations": 1
                }

        # ==========================
        # 🔁 Planner Loop
        # ==========================

        self.file_operation_success = False

        while not self.state.is_max_iterations_reached():

            self.state.increment_iteration()

            context = ContextHandler.build_context(
                self.tool_registry,
                self.memory,
                self.state.iteration
            )

            plan = self.planner.plan(goal, context)

            print(f"\n[ITER {self.state.iteration}] PLAN:", plan)

            result = self._execute(plan)

            print(f"[ITER {self.state.iteration}] RESULT:", result)

            reflection = self.reflector.reflect(str(result), context)

            print(f"[ITER {self.state.iteration}] REFLECTION:", reflection)

            if reflection.get("next_action") == "done":

                if not self.file_operation_success:
                    print("🚫 DONE 차단: 파일 생성/수정 필요")
                    continue

                return {
                    "status": result.get("status", "ok"),
                    "result": result,
                    "iterations": self.state.iteration
                }

        return {
            "status": "error",
            "error": "Max iterations reached",
            "iterations": self.state.iteration
        }

    # ==========================
    # ACTION EXECUTION
    # ==========================

    def _execute(self, plan: dict) -> Any:

        action = plan.get("action")
        details = plan.get("details", {})

        if action == "read_file":
            return self.tool_registry.execute(
                "read_file",
                file_path=details.get("file_path", "")
            )

        elif action == "write_file":

            result = self.tool_registry.execute(
                "write_file",
                file_path=details.get("file_path", "output.py"),
                content=details.get("content", "")
            )

            if isinstance(result, dict) and not result.get("error"):
                self.file_operation_success = True

            return result

        elif action == "edit":

            file_path = details.get("file_path")

            original = self.tool_registry.execute(
                "read_file",
                file_path=file_path
            )

            if isinstance(original, dict) and "error" in original:
                return original

            updated = self.editor.edit(
                details.get("instruction", ""),
                original,
                details.get("web_info", "")
            )

            if not isinstance(updated, str):
                return {"error": "LLM edit failed"}

            write_result = self.tool_registry.execute(
                "write_file",
                file_path=file_path,
                content=updated
            )

            if isinstance(write_result, dict) and not write_result.get("error"):
                self.file_operation_success = True

            return write_result

        elif action == "execute":

            return Executor.execute_file(
                details.get("file_path", ""),
                details.get("command", "")
            )

        elif action == "done":

            if not self.file_operation_success:
                return {"error": "DONE blocked"}

            return {"status": "done"}

        return {"status": "unknown_action"}