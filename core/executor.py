import subprocess
import os
import re
from config import llm_call


class Executor:
    """Execution handler for shell commands and file execution"""

    # ==============================
    # File Execution
    # ==============================

    @staticmethod
    def execute_file(path: str, cmd: str = "") -> dict:

        if not path:
            return {"status": "error", "error": "No file_path provided"}

        if not os.path.isabs(path):
            path = os.path.abspath(path)

        ext = os.path.splitext(path)[1].lower()

        try:

            # ==========================
            # JAVA
            # ==========================
            if ext == ".java":

                class_name = os.path.splitext(os.path.basename(path))[0]
                max_retries = 5

                for attempt in range(max_retries):

                    print(f"[COMPILE] Compiling {path} (attempt {attempt + 1})")

                    compile_result = subprocess.run(
                        ["javac", path],
                        capture_output=True,
                        text=True
                    )

                    if compile_result.returncode == 0:
                        print("[COMPILE] Success")
                        break

                    error_msg = compile_result.stderr
                    print("[COMPILE] Failed:")
                    print(error_msg)

                    print("[AUTO-FIX] Sending to LLM...")
                    fixed = Executor._auto_fix_with_llm(
                        language="java",
                        file_path=path,
                        error_msg=error_msg
                    )

                    if not fixed:
                        return {
                            "status": "error",
                            "error": f"Compilation failed after {attempt + 1} attempts:\n{error_msg}"
                        }

                    print("[AUTO-FIX] Code updated. Retrying...")

                else:
                    return {
                        "status": "error",
                        "error": f"Compilation failed after {max_retries} attempts"
                    }

                completed = subprocess.run(
                    ["java", "-cp", os.path.dirname(path), class_name],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(path)
                )

                print("\n=== 실행 결과 (Java) ===")
                print(completed.stdout)
                if completed.stderr:
                    print(completed.stderr)
                print("=" * 30)

                return {
                    "status": "ok" if completed.returncode == 0 else "error",
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr
                }

            # ==========================
            # PYTHON
            # ==========================
            elif ext == ".py":

                completed = subprocess.run(
                    ["python", path],
                    capture_output=True,
                    text=True
                )

                return {
                    "status": "ok" if completed.returncode == 0 else "error",
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr
                }

            else:
                return {"status": "error", "error": "Unsupported file type"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ==============================
    # LLM Auto Fix
    # ==============================

    @staticmethod
    def _auto_fix_with_llm(language: str, file_path: str, error_msg: str) -> bool:

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()

            prompt = f"""
You are a senior {language} developer.

The following file failed to compile.

=== Error Message ===
{error_msg}

=== Original Source Code ===
{original_code}

Return the FULL corrected source code.
Return ONLY valid {language} code.
Do not include explanations.
"""

            response = llm_call(
                prompt=prompt,
                temperature=0   # 코드 수정은 반드시 0
            )

            fixed_code = Executor._extract_code_block(response)

            if not fixed_code.strip():
                print("[AUTO-FIX] Empty response from LLM")
                return False

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_code)

            return True

        except Exception as e:
            print(f"[AUTO-FIX] LLM fix failed: {e}")
            return False

    # ==============================
    # Code Block Extractor
    # ==============================

    @staticmethod
    def _extract_code_block(text: str) -> str:
        pattern = r"```(?:\w+)?\s*(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()