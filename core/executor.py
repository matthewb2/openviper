import subprocess
import os
import re
import tempfile
import difflib
from typing import Optional, Dict, Any
from config import llm_call


class Executor:

    # ==============================
    # PUBLIC FILE EXECUTION
    # ==============================

    @staticmethod
    def execute_file(
        path: str,
        cmd: str = "",
        context: Optional[dict] = None
    ) -> Dict[str, Any]:

        if not os.path.exists(path):
            return {"status": "error", "error": f"File not found: {path}"}

        ext = os.path.splitext(path)[1].lower()

        if ext == ".java":
            return Executor._execute_java(path, context)

        elif ext == ".py":
            completed = subprocess.run(
                ["python", path],
                capture_output=True,
                text=True
            )
            return {
                "status": "ok" if completed.returncode == 0 else "error",
                "stdout": completed.stdout,
                "stderr": completed.stderr
            }

        return {"status": "error", "error": "Unsupported file type"}

    # ==============================
    # JAVA EXECUTION LOOP
    # ==============================

    @staticmethod
    def _execute_java(path: str, context: Optional[dict]):

        workspace_root = os.path.dirname(path)
        class_name = os.path.splitext(os.path.basename(path))[0]
        max_retries = 5

        if context is None:
            context = {}

        context["workspace"] = workspace_root
        context["target_file"] = path

        for attempt in range(max_retries):

            context["iteration"] = attempt + 1

            print(f"[COMPILE] Attempt {attempt + 1}")

            workspace_root = os.path.dirname(path) or "."

            java_files = [
                f for f in os.listdir(workspace_root)
                if f.endswith(".java")
            ]

            compile_cmd = ["javac"] + java_files

            compile_result = subprocess.run(
                compile_cmd,
                cwd=workspace_root,
                capture_output=True,
                text=True
            )

            if compile_result.returncode == 0:
                print("[COMPILE] Success")
                break

            error_msg = compile_result.stderr
            context["last_error"] = error_msg

            print("[COMPILE] Failed:")
            print(error_msg)

            print("[AUTO-FIX] Requesting full file rewrite from LLM...")

            updated_files = Executor._request_full_rewrite_from_llm(
                language="java",
                workspace_root=workspace_root,
                error_msg=error_msg,
                context=context
            )

            if not updated_files:
                return {"status": "error", "error": "LLM did not return valid files"}

            diff_text = Executor._generate_combined_diff(
                workspace_root,
                updated_files
            )

            Executor._apply_updated_files(workspace_root, updated_files)

        else:
            return {"status": "error", "error": "Max compile retries reached"}

        run_result = subprocess.run(
            ["java", "-cp", workspace_root or ".", class_name],
            capture_output=True,
            text=True
        )

        return {
            "status": "ok" if run_result.returncode == 0 else "error",
            "stdout": run_result.stdout,
            "stderr": run_result.stderr
        }

    # ==============================
    # LLM FULL FILE REQUEST
    # ==============================

    @staticmethod
    def _request_full_rewrite_from_llm(
        language: str,
        workspace_root: str,
        error_msg: str,
        context: Optional[dict]
    ) -> Optional[Dict[str, str]]:

        source_files = {}

        for file in os.listdir(workspace_root):
            if file.endswith(".java"):
                full_path = os.path.join(workspace_root, file)
                with open(full_path, "r", encoding="utf-8") as f:
                    source_files[file] = f.read()

        context_block = Executor._build_context_block(context)

        files_block = ""
        for name, content in source_files.items():
            files_block += f"\n=== FILE: {name} ===\n{content}\n"

        prompt = f"""
You are a senior {language} developer inside an autonomous coding agent.

{context_block}

Compilation failed.

=== ERROR MESSAGE ===
{error_msg}

Here are all source files:

{files_block}

Fix the issue.

IMPORTANT:
- Return ONLY corrected files.
- If multiple files need modification, return all modified files.
- Use EXACT format:

=== FILE: FileName.java ===
<full corrected content>

- Do NOT include explanations.
- Do NOT use markdown.
"""

        response = llm_call(prompt, temperature=0)
        response = Executor._ensure_str(response)

        return Executor._parse_multi_file_response(response)

    # ==============================
    # PARSE MULTI FILE RESPONSE
    # ==============================

    @staticmethod
    def _parse_multi_file_response(text: str) -> Optional[Dict[str, str]]:

        if not text:
            return None

        text = re.sub(r"```.*?\n", "", text)
        text = text.replace("```", "")

        pattern = r"=== FILE: (.*?) ===\n(.*?)(?=\n=== FILE:|\Z)"
        matches = re.findall(pattern, text, re.DOTALL)

        if not matches:
            return None

        files = {}
        for filename, content in matches:
            files[filename.strip()] = content.rstrip() + "\n"

        return files

    # ==============================
    # GENERATE LOCAL DIFF
    # ==============================

    @staticmethod
    def _generate_combined_diff(
        workspace_root: str,
        updated_files: Dict[str, str]
    ) -> str:

        combined_diff = ""

        for filename, new_content in updated_files.items():

            full_path = os.path.join(workspace_root, filename)

            if not os.path.exists(full_path):
                original_content = ""
            else:
                with open(full_path, "r", encoding="utf-8") as f:
                    original_content = f.read()

            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{filename}",
                tofile=f"b/{filename}",
            )

            combined_diff += "".join(diff)

        return combined_diff

    # ==============================
    # APPLY DIFF USING GIT
    # ==============================

    @staticmethod
    def _apply_updated_files(workspace_root: str, updated_files: Dict[str, str]):

        for filename, new_content in updated_files.items():
            full_path = os.path.join(workspace_root, filename)

            print(f"[APPLY] Overwriting {filename}")

            with open(full_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new_content)
    # ==============================
    # CONTEXT BUILDER
    # ==============================

    @staticmethod
    def _build_context_block(context: Optional[dict]) -> str:
        if not context:
            return ""

        lines = ["=== AGENT CONTEXT ==="]
        for k, v in context.items():
            if v is None:
                continue
            if isinstance(v, str) and len(v) > 2000:
                v = v[-2000:]
            lines.append(f"{k}: {v}")

        return "\n".join(lines)

    # ==============================
    # UTIL
    # ==============================

    @staticmethod
    def _ensure_str(data):
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return data