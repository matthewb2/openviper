from typing import Any, Callable
import os


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Callable] = {}

        # ✅ 안정화: 작업 루트 강제 지정
        self.workspace_root = os.path.abspath("workspace")
        os.makedirs(self.workspace_root, exist_ok=True)

        self._register_default_tools()

    def _register_default_tools(self):
        from agent.tools.web_search import web_search
        from agent.tools.file_tool import read_file, write_file, list_directory
        from agent.tools.test_runner import run_test, run_tests

        # 🔥 파일 툴에 workspace 강제 바인딩
        def read_file_safe(**kwargs):
            kwargs["workspace_root"] = self.workspace_root
            return read_file(**kwargs)

        def write_file_safe(**kwargs):
            kwargs["workspace_root"] = self.workspace_root
            return write_file(**kwargs)

        def list_directory_safe(**kwargs):
            kwargs["workspace_root"] = self.workspace_root
            return list_directory(**kwargs)

        self.register("web_search", web_search)
        self.register("read_file", read_file_safe)
        self.register("write_file", write_file_safe)
        self.register("list_directory", list_directory_safe)
        self.register("run_test", run_test)
        self.register("run_tests", run_tests)

    def register(self, name: str, tool: Callable):
        self.tools[name] = tool

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}

        try:
            tool = self.tools[name]
            return tool(**kwargs)
        except Exception as e:
            return {"error": str(e)}

    def list_tools(self) -> list[str]:
        return list(self.tools.keys())

    def get_tool(self, name: str) -> Callable | None:
        return self.tools.get(name)