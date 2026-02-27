import uuid
import os
import json
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

    def __init__(self, max_iterations: int = 5):
        self.state = AgentStateData(max_iterations=max_iterations)
        self.planner = Planner()
        self.executor = Executor()
        self.context = {}
        self.editor = Editor()
        self.reflector = Reflector()
        self.tool_registry = ToolRegistry()
        self.memory = WorkingMemory()
        self.file_operation_success = False
        self.last_goal: str = ""

    # ==========================
    # PUBLIC RUN
    # ==========================
    def run(self, goal: str):
        
        # Set default working directory to workspace
        workspace_path = os.path.join(os.getcwd(), "workspace")
        if os.path.exists(workspace_path):
            os.chdir(workspace_path)
        
        # Check for directory change request FIRST (more specific)
        if any(kw in goal for kw in ['폴더를', '디렉토리를', '경로를']) and any(kw in goal for kw in ['변경', '전환', '이동', 'change', 'move', '해주세요', '해줘', '하세요']):
            import re
            # Extract target path
            path_match = re.search(r'([A-Za-z]:\\[^\s]*)', goal)
            if not path_match:
                path_match = re.search(r'으로\s+(\S+)', goal)
            if not path_match:
                path_match = re.search(r'폴더\s+(\S+)', goal)
            
            if path_match:
                target_path = path_match.group(1) if path_match.lastindex else path_match.group(0)
                # Clean up the path
                target_path = target_path.rstrip('으로로.')
                
                try:
                    if os.path.exists(target_path):
                        os.chdir(target_path)
                        new_path = os.getcwd()
                        print(f"\n=== 폴더 변경 ===")
                        print(f"변경 후 경로: {new_path}")
                        print("=" * 30)
                        return {
                            "status": "success",
                            "result": {
                                "status": "ok",
                                "path": new_path,
                                "message": f"작업 폴더가 변경되었습니다: {new_path}"
                            }
                        }
                    else:
                        # Try workspace path
                        workspace_path = os.path.join("workspace", target_path)
                        if os.path.exists(workspace_path):
                            os.chdir(workspace_path)
                            new_path = os.getcwd()
                            print(f"\n=== 폴더 변경 ===")
                            print(f"변경 후 경로: {new_path}")
                            print("=" * 30)
                            return {
                                "status": "success",
                                "result": {
                                    "status": "ok",
                                    "path": new_path,
                                    "message": f"작업 폴더가 변경되었습니다: {new_path}"
                                }
                            }
                        return {
                            "status": "error",
                            "error": f"폴더가 존재하지 않습니다: {target_path}"
                        }
                except Exception as e:
                    return {
                        "status": "error",
                        "error": f"폴더 변경 실패: {str(e)}"
                    }
        
        # Check for current directory query (show only)
        if any(kw in goal for kw in ['현재 작업 폴더', '현재 폴더', '현재 경로', 'current directory', 'cwd', '현재 디렉토리', '폴더 경로']) and '변경' not in goal and '이동' not in goal:
            current_path = ContextHandler.get_current_directory()
            print(f"\n=== 현재 작업 폴더 ===")
            print(f"경로: {current_path}")
            print("=" * 30)
            return {
                "status": "success",
                "result": {
                    "status": "ok",
                    "path": current_path,
                    "message": f"현재 작업 폴더: {current_path}"
                }
            }
        
        # Check for directory listing query
        if any(kw in goal for kw in ['폴더 목록', '파일 목록', '디렉토리 목록', '현재 폴더 내용', '파일 보여줘', 'list files', 'list directory']):
            result = ContextHandler.list_directory(".")
            if result.get("success"):
                items = result.get("items", [])
                print(f"\n=== 현재 폴더 내용 ===")
                for item in items:
                    icon = "📁" if item["type"] == "directory" else "📄"
                    print(f"  {icon} {item['name']}")
                print("=" * 30)
                return {
                    "status": "success",
                    "result": result
                }
        
        print("Planning...")
        plan = self.planner.plan(goal, self.context)

        print("Plan:", plan)

        print("Executing...")
        result = self.executor.execute(plan)

        return result
    # ==========================
    # ACTION EXECUTION
    # ==========================

    def _execute(self, plan: dict) -> Any:

        # Handle multiple actions from planner
        if "actions" in plan:
            results = []
            for action_item in plan["actions"]:
                action = action_item.get("action")
                params = action_item.get("params", {})
                
                if action == "create_folder":
                    folder_name = params.get("folder_name", "")
                    if folder_name:
                        try:
                            os.makedirs(os.path.join("workspace", folder_name), exist_ok=True)
                            print(f"[FOLDER] Created folder: {folder_name}")
                            results.append({"action": "create_folder", "status": "ok", "folder": folder_name})
                        except Exception as e:
                            results.append({"action": "create_folder", "status": "error", "error": str(e)})
                
                elif action == "write_file":
                    folder_name = params.get("folder_name", "")
                    file_name = params.get("file_name", "")
                    content = params.get("content", "")
                    
                    # Extract actual code from JSON if needed
                    try:
                        import json
                        if content.startswith('{'):
                            content_obj = json.loads(content)
                            content = content_obj.get("code", content)
                    except:
                        pass
                    
                    if folder_name:
                        file_path = os.path.join("workspace", folder_name, file_name)
                    else:
                        file_path = os.path.join("workspace", file_name)
                    
                    result = self.tool_registry.execute(
                        "write_file",
                        file_path=file_path,
                        content=content
                    )
                    
                    if isinstance(result, dict) and not result.get("error"):
                        self.file_operation_success = True
                        print(f"[FILE] Written: {file_path}")
                    
                    results.append({"action": "write_file", "result": result})
            
            return {"status": "ok", "results": results}
        
        # Original single action handling
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