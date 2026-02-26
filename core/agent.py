import uuid
import subprocess
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
        self.last_goal: str = ""

    # ==========================
    # PUBLIC RUN
    # ==========================

    def run(self, goal: str) -> dict[str, Any]:

        task = Task(id=str(uuid.uuid4()), description=goal)
        self.state.add_task(task)

        self.memory.add("goal", goal)
        self.last_goal = goal

        # 🔥 현재 작업 폴더 경로 변경 요청 감지
        import re
        import os
        
        # Check for directory change requests FIRST (more specific)
        chdir_patterns = [
            '경로를',  # "경로를 D:\project로 변경하세요"
            '폴더를',
            '디렉토리를',
            'current directory',
            'change directory',
            'chdir',
            'cd ',
        ]
        
        if any(kw in goal for kw in chdir_patterns) and ('변경' in goal or '변경하세요' in goal or 'change' in goal.lower() or '이동' in goal):
            print(f"[CHDIR] Directory change pattern detected in: {goal}")
            
            # Extract path - look for patterns like "D:\project", "C:\folder", etc.
            path_match = re.search(r'([A-Za-z]:\\[^\s]*)', goal)
            if not path_match:
                # Try to find folder name without drive letter
                path_match = re.search(r'(?:으로|로|에)\s+([a-zA-Z0-9_\\\-]+)', goal)
            
            if path_match:
                target_path = path_match.group(1)
                # If it's not a full path, assume it's relative to current or workspace
                if not re.match(r'[A-Za-z]:', target_path):
                    target_path = os.path.join("workspace", target_path)
                
                print(f"[CHDIR] Target path: {target_path}")
                
                # Create folder if it doesn't exist
                if '없으면' in goal or '새로' in goal or '새' in goal:
                    try:
                        os.makedirs(target_path, exist_ok=True)
                        print(f"[CHDIR] Created folder: {target_path}")
                    except Exception as e:
                        return {
                            "status": "error",
                            "error": f"폴더 생성 실패: {str(e)}",
                            "iterations": 1
                        }
                
                # Change directory
                try:
                    if os.path.exists(target_path):
                        os.chdir(target_path)
                        new_path = os.getcwd()
                        print(f"[CHDIR] Changed to: {new_path}")
                        return {
                            "status": "success",
                            "result": {
                                "status": "ok",
                                "path": new_path,
                                "message": f"작업 폴더가 변경되었습니다: {new_path}"
                            },
                            "iterations": 1
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"폴더가 존재하지 않습니다: {target_path}",
                            "iterations": 1
                        }
                except Exception as e:
                    return {
                        "status": "error",
                        "error": f"폴더 변경 실패: {str(e)}",
                        "iterations": 1
                    }

        # 🔥 현재 작업 폴더 경로 요청 감지
        import re
        import os
        
        # Check for current working directory queries
        cwd_patterns = [
            '지금 작업하고 있는 폴더',
            '현재 폴더',
            '현재 디렉토리',
            '작업 폴더',
            '현재 경로',
            '현재 디렉토리 경로',
            'current working directory',
            'cwd',
            '현재 디렉터리',
        ]
        
        if any(kw in goal for kw in cwd_patterns):
            current_path = os.getcwd()
            print(f"[CWD] Current working directory: {current_path}")
            return {
                "status": "success",
                "result": {
                    "status": "ok",
                    "path": current_path,
                    "message": f"현재 작업 폴더: {current_path}"
                },
                "iterations": 1
            }

        # 🔥 디렉토리 목록 요청 감지
        list_patterns = [
            '폴더 목록',
            '파일 목록',
            '디렉토리 목록',
            '현재 폴더 내용',
            '파일 보여줘',
            'list files',
            'list directory',
            '디렉터리 목록',
        ]
        
        if any(kw in goal for kw in list_patterns):
            current_path = os.getcwd()
            try:
                items = os.listdir(current_path)
                result_str = "\n".join([f"  📁 {item}/" if os.path.isdir(os.path.join(current_path, item)) else f"  📄 {item}" for item in items])
                print(f"[LIST] Files in {current_path}:\n{result_str}")
                return {
                    "status": "success",
                    "result": {
                        "status": "ok",
                        "path": current_path,
                        "items": items,
                        "message": f"현재 폴더 내용:\n{result_str}"
                    },
                    "iterations": 1
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "iterations": 1
                }

        # 🔥 폴더 생성 요청 감지
        import re
        import os
        
        # Check for folder/directory creation keywords
        if any(kw in goal for kw in ['폴더를 만드', '폴더를 생성', '디렉토리를 만드', '디렉토리를 생성', '새 폴더', 'create folder', 'create directory', 'mkdir']):
            print(f"[MKDIR] Folder creation pattern detected in: {goal}")
            
            # Try to extract folder name with multiple patterns
            folder_name = None
            
            # Pattern 1: "new_project 라는 새 폴더" or "new_project 라는 폴더"
            match = re.search(r'([a-zA-Z0-9_\-]+)\s*(?:라는\s*)?(?:새\s*)?폴더', goal)
            if match:
                folder_name = match.group(1)
            
            # Pattern 2: after "경로에 " 
            if not folder_name:
                match = re.search(r'경로에\s+([a-zA-Z0-9_\-]+)', goal)
                if match:
                    folder_name = match.group(1)
            
            # Pattern 3: after particles like "에" or "으로"
            if not folder_name:
                match = re.search(r'에\s+([a-zA-Z0-9_\-]+)', goal)
                if match:
                    folder_name = match.group(1)
            
            # Pattern 4: extract English word before "폴더" or "디렉토리"
            if not folder_name:
                match = re.search(r'([a-zA-Z0-9_\-]+)\s+(?:폴더|디렉토리)', goal)
                if match:
                    folder_name = match.group(1)
            
            if folder_name:
                print(f"[MKDIR] Extracted folder name: {folder_name}")
                
                # Look for path like D:\ or C:\
                path_match = re.search(r'([A-Za-z]:\\[^\\s]*)', goal)
                if path_match:
                    folder_path = os.path.join(path_match.group(1), folder_name)
                else:
                    # Use workspace by default
                    folder_path = os.path.join("workspace", folder_name)
                
                print(f"[MKDIR] Creating folder: {folder_path}")
                try:
                    os.makedirs(folder_path, exist_ok=True)
                    return {
                        "status": "success",
                        "result": {
                            "status": "ok",
                            "folder_path": folder_path,
                            "message": f"폴더가 생성되었습니다: {folder_path}"
                        },
                        "iterations": 1
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "error": str(e),
                        "iterations": 1
                    }

        # 🔥 Shell 명령어 실행 요청 감지
        import re
        import os
        import subprocess
        
        # Check for shell command patterns like "npm create vite", "python -m http.server", etc.
        command_patterns = [
            r'(?:명령을\s*)?실행\s*(?:하세요|해\s*줘|해라)',
            r'run\s+command',
            r'execute\s+command',
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, goal, re.IGNORECASE):
                # Look for known commands
                known_cmds = ['npm', 'npx', 'yarn', 'pnpm', 'pip', 'pip3', 'cargo', 'go', 'dotnet', 'make', 'gcc', 'g++', 'python', 'python3', 'node', 'bun', 'ruby', 'perl', 'php']
                for cmd in known_cmds:
                    if f'{cmd} ' in goal or goal.startswith(cmd):
                        # Find the full command starting from this keyword
                        idx = goal.find(cmd)
                        # Extract command - stop at Korean particles or common sentence endings
                        cmd_part = goal[idx:]
                        # Korean particles that end commands
                        korean_ends = ['을', '를', '는', '은', '에게', '한테', '에서', '으로', '로서', '처럼', '만큼', '같이', '마다', '마다', '라도', '든지', '든가']
                        # English endings
                        english_ends = [' please', ' to', ' and', ' then', '?', '\n']
                        # Combined
                        all_ends = korean_ends + english_ends
                        
                        for end in all_ends:
                            if end in cmd_part:
                                cmd_part = cmd_part.split(end)[0]
                        cmd_part = cmd_part.strip()
                        
                        if cmd_part:
                            
                            # Check if user wants to run in separate terminal with interaction
                            if any(kw in goal for kw in ['터미널', '별도', '새 창', '창에서', 'interactive', 'separate', 'new window']):
                                # Run in separate terminal with user interaction
                                print(f"[SHELL] Opening new terminal for interactive execution...")
                                # Use start cmd /k to keep window open after command
                                subprocess.Popen(
                                    f'start cmd /k "{cmd_part}"',
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL
                                )
                                return {
                                    "status": "success",
                                    "result": {
                                        "status": "ok",
                                        "message": "새 터미널에서 명령이 실행 중입니다. 별도 창을 확인하세요.",
                                        "command": cmd_part
                                    },
                                    "iterations": 1
                                }
                            
                            try:
                                # Handle interactive commands by adding appropriate flags
                                if 'npm create' in cmd_part:
                                    # For npm create vite, convert to npm init vite@latest
                                    if 'vite' in cmd_part:
                                        # Extract project name - find "vite" and get the next word
                                        parts = cmd_part.split()
                                        project_name = None
                                        for i, part in enumerate(parts):
                                            if part == 'vite' and i + 1 < len(parts):
                                                project_name = parts[i + 1]
                                                break
                                        
                                        if project_name and project_name not in ['명령을', '실행', '실행하세요', '명령', '을', '를']:
                                            cmd_part = f"npm create vite@latest {project_name} -- --template vanilla"
                                            print(f"[SHELL] Transformed command: {cmd_part}")
                                elif cmd_part.startswith('npm '):
                                    # Add -y flag for other npm commands
                                    if '-y ' not in cmd_part:
                                        cmd_part = cmd_part.replace('npm ', 'npm -y ', 1)
                                
                                # Run command and show output directly in console
                                print("-" * 40)
                                print(f"[실행] {cmd_part}")
                                print("-" * 40)
                                
                                process = subprocess.Popen(
                                    cmd_part,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True,
                                    cwd=os.getcwd(),
                                    encoding='utf-8',
                                    errors='replace'
                                )
                                
                                # Print output in real-time
                                output_lines = []
                                if process.stdout:
                                    for line in process.stdout:
                                        print(line, end='')
                                        output_lines.append(line)
                                
                                process.wait()
                                full_output = ''.join(output_lines)
                                
                                result = {
                                    "status": "ok" if process.returncode == 0 else "error",
                                    "returncode": process.returncode,
                                    "stdout": full_output,
                                    "stderr": ""
                                }
                                print("-" * 40)
                                return {
                                    "status": "success",
                                    "result": result,
                                    "iterations": 1
                                }
                            except subprocess.TimeoutExpired:
                                return {
                                    "status": "error",
                                    "error": "Command timed out after 2 minutes",
                                    "iterations": 1
                                }
                            except Exception as e:
                                return {
                                    "status": "error",
                                    "error": str(e),
                                    "iterations": 1
                                }
                break
        
        # Determine workspace directory for file operations
        workspace = "workspace"
        
        # Check for any file type execution request
        if '실행' in goal or 'run' in goal.lower() or 'execute' in goal.lower():
            # Find file in the goal
            py_file_match = re.search(r'(\S+\.py)', goal)
            java_file_match = re.search(r'(\S+\.java)', goal)
            js_file_match = re.search(r'(\S+\.js)', goal)
            
            file_to_run = None
            file_ext = None
            
            if py_file_match:
                file_name = py_file_match.group(1)
                file_to_run = os.path.join(workspace, file_name)
                file_ext = '.py'
            elif java_file_match:
                file_name = java_file_match.group(1)
                file_to_run = os.path.join(workspace, file_name)
                file_ext = '.java'
            elif js_file_match:
                file_name = js_file_match.group(1)
                file_to_run = os.path.join(workspace, file_name)
                file_ext = '.js'
            
            if file_to_run:
                print(f"[AUTO-EXECUTE] Detected execution request for: {file_to_run}")
                
                # Get the relative file name (without workspace prefix)
                file_name = os.path.basename(file_to_run)
                
                # Check if file exists first
                if os.path.exists(file_to_run):
                    exec_result = self._execute({"action": "execute", "details": {"file_path": file_to_run}})
                    print(f"[AUTO-EXECUTE] Result: {exec_result}")
                    return {
                        "status": "success",
                        "result": exec_result,
                        "iterations": 1
                    }
                else:
                    # File doesn't exist - create it based on file type
                    print(f"[AUTO-EXECUTE] File not found, creating: {file_to_run}")
                    
                    if file_ext == '.java':
                        # Extract class name from file name
                        class_name = os.path.splitext(os.path.basename(file_to_run))[0]
                        content = f"""public class {class_name} {{
    public static void main(String[] args) {{
        System.out.println("Hello World from Java");
    }}
}}
"""
                    elif file_ext == '.js':
                        content = "console.log('Hello World from JavaScript');\n"
                    else:
                        # Default to Python
                        content = "print('Hello World')\n"
                    
                    # Pass only file name to write_file (registry adds workspace automatically)
                    write_result = self.tool_registry.execute("write_file", file_path=file_name, content=content)
                    print(f"[AUTO-EXECUTE] File created: {write_result}")
                    
                    # Then execute - use the full path
                    exec_result = self._execute({"action": "execute", "details": {"file_path": file_to_run}})
                    print(f"[AUTO-EXECUTE] Result: {exec_result}")
                    return {
                        "status": "success",
                        "result": {"write": write_result, "execute": exec_result},
                        "iterations": 1
                    }

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

    def _extract_print_source(self, text: str) -> str | None:
        """Extract print content from goal text."""
        if not text:
            return None
        import re
        m = re.search(r'"([^"]+)"', text)
        if m:
            return m.group(1)
        m2 = re.search(r"'([^']+)'", text)
        if m2:
            return m2.group(1)
        return None

    def _generate_markdown_content(self, goal: str) -> str:
        """Generate markdown content based on user goal."""
        import re
        
        # Extract potential title from goal
        # Look for patterns like "about X", "for X", "X를 위한"
        title_match = re.search(r'(?:about|for|을 위한|에 대한)\s+(.+?)(?:\s|$)', goal, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Use first few words as title
            title = "Project"
        
        # Extract description from goal
        # Remove common patterns to get the core description
        desc = goal
        for pattern in [r'마크다운\s*문법\s*으로', r'readme\.?\s*파일\s*에', r'파일\s*을\s*만들', r'만들어\s*줘']:
            desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
        desc = desc.strip()
        if not desc:
            desc = "Project Description"
        
        # Generate markdown content
        content = f"""# {title}

## Overview

{desc}

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the project
python main.py
```

## Features

- Feature 1
- Feature 2
- Feature 3

## License

MIT
"""
        return content

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
            file_path = details.get("file_path", "output.py")
            content = details.get("content", "")
            
            # If content is empty, generate based on file type and goal
            if not content:
                # Check if it's a markdown file (README.md, etc.)
                if file_path.endswith('.md') or '마크다운' in self.last_goal or 'markdown' in self.last_goal.lower():
                    content = self._generate_markdown_content(self.last_goal)
                else:
                    # Try to extract print content for Python files
                    inferred = self._extract_print_source(self.last_goal)
                    if inferred:
                        content = f"print('{inferred}')\n"
            
            result = self.tool_registry.execute(
                "write_file",
                file_path=file_path,
                content=content
            )

            # Auto-execute if user requests run/execute and it's a Python file
            if file_path.endswith('.py') and ('실행' in self.last_goal or 'run' in self.last_goal.lower() or 'execute' in self.last_goal.lower()):
                print(f"[AUTO-EXECUTE] Running {file_path}...")
                exec_result = self._execute({"action": "execute", "details": {"file_path": file_path}})
                print(f"[AUTO-EXECUTE] Result: {exec_result}")
                result = {"write": result, "execute": exec_result}

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

        elif action == "execute":
            path = details.get("file_path", "")
            cmd = details.get("command", "")
            if not path:
                return {"status": "error", "error": "No file_path provided for execute"}
            
            import os
            # Convert to absolute path if relative
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            
            ext = os.path.splitext(path)[1].lower()
            
            try:
                if ext == '.java':
                    # Java: compile first, then run
                    class_name = os.path.splitext(os.path.basename(path))[0]
                    print(f"[COMPILE] Compiling {path}...")
                    compile_result = subprocess.run(
                        ["javac", path],
                        capture_output=True,
                        text=True
                    )
                    if compile_result.returncode != 0:
                        return {"status": "error", "error": f"Compilation failed: {compile_result.stderr}"}
                    print(f"[COMPILE] Compilation successful, running {class_name}...")
                    
                    # Run the compiled class
                    completed = subprocess.run(
                        ["java", "-cp", os.path.dirname(path), class_name],
                        capture_output=True,
                        text=True,
                        cwd=os.path.dirname(path)
                    )
                    return {"status": "ok", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
                
                elif ext == '.py':
                    # Python: run directly
                    if cmd:
                        cmd_args = cmd.split()
                        completed = subprocess.run(["python", path] + cmd_args, capture_output=True, text=True)
                    else:
                        completed = subprocess.run(["python", path], capture_output=True, text=True)
                    return {"status": "ok", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
                
                elif ext == '.js':
                    # JavaScript: run with node
                    completed = subprocess.run(["node", path], capture_output=True, text=True)
                    return {"status": "ok", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
                
                elif ext == '.sh':
                    # Shell script
                    completed = subprocess.run(["bash", path], capture_output=True, text=True)
                    return {"status": "ok", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
                
                else:
                    # Default: try with python
                    completed = subprocess.run(["python", path], capture_output=True, text=True)
                    return {"status": "ok", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
                    
            except FileNotFoundError as e:
                return {"status": "error", "error": f"Command not found: {str(e)}"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

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