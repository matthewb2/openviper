# core/executor.py

import os
import json
from agent.config import llm_call


class Executor:

    def execute(self, plan: dict):

        results = []

        actions = plan.get("actions")

        if not actions:
            raise ValueError("No actions found in plan")

        for step in actions:

            action = step.get("action")
            params = step.get("params", {})

            if action == "create_folder":
                results.append(self._create_folder(params))

            elif action == "write_file":
                results.append(self._write_file(params))

            else:
                raise ValueError(f"Unknown action: {action}")

        return "\n".join(results)

    def _create_folder(self, params):

        folder = params.get("folder_name")

        if not folder:
            raise ValueError("Missing folder_name")

        os.makedirs(folder, exist_ok=True)

        return f"Folder created: {folder}"

    def _write_file(self, params):

        folder_name = params.get("folder_name")
        file_name = params.get("file_name")

        if not file_name:
            raise ValueError("Missing file_name")

        # 🔥 경로 조합
        if folder_name:
            full_path = os.path.join(folder_name, file_name)
        else:
            full_path = file_name

        # 코드 추출
        content = params.get("content")

        if not content:
            raise ValueError("Missing content")

        try:
            parsed = json.loads(content)
            code = parsed.get("code", "")
        except:
            code = content

        # 🔥 디렉토리 생성 (빈 문자열 방지)
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code.strip())

        return f"File written: {full_path}"