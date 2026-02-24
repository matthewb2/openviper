from typing import Any, Callable
import os


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        from agent.tools.web_search import web_search
        from agent.tools.file_tool import read_file, write_file, list_directory
        from agent.tools.test_runner import run_test, run_tests
        
        self.register("web_search", web_search)
        self.register("read_file", read_file)
        self.register("write_file", write_file)
        self.register("list_directory", list_directory)
        self.register("run_test", run_test)
        self.register("run_tests", run_tests)

    def register(self, name: str, tool: Callable):
        self.tools[name] = tool

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}
        
        try:
            tool = self.tools[name]
            if name in ["read_file", "write_file", "list_directory"]:
                return tool(**kwargs)
            else:
                return tool(**kwargs)
        except Exception as e:
            return {"error": str(e)}

    def list_tools(self) -> list[str]:
        return list(self.tools.keys())

    def get_tool(self, name: str) -> Callable | None:
        return self.tools.get(name)
