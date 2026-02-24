import uuid
from typing import Any
from agent.core.state import AgentState, AgentStateData, Task
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
        self.working_memory = WorkingMemory()
        self.context_builder = ContextBuilder()
        self.action_history = []

    def run(self, goal: str) -> dict[str, Any]:
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description=goal)
        self.state.add_task(task)
        
        self._add_to_memory("user_goal", goal)
        
        while not self.state.is_max_iterations_reached():
            self.state.increment_iteration()
            
            context = self._build_context()
            
            self.state.update_state(AgentState.PLANNING)
            plan = self.planner.plan(goal, context)
            
            self.action_history.append({"iteration": self.state.iteration, "plan": plan})
            
            self.state.update_state(AgentState.EXECUTING)
            result = self._execute_action(plan, context)
            
            self._add_to_memory(f"action_{self.state.iteration}", result)
            
            self.state.update_state(AgentState.REFLECTING)
            reflection = self.reflector.reflect(str(result), context)
            
            if reflection.get("next_action") == "done":
                task.status = "completed"
                task.completed_at = __import__("datetime").datetime.now()
                task.result = result
                self.state.update_state(AgentState.IDLE)
                return {"status": "success", "result": result, "iterations": self.state.iteration}
            
            if reflection.get("next_action") == "retry":
                continue
                
        task.status = "max_iterations"
        task.error = "Maximum iterations reached"
        self.state.update_state(AgentState.ERROR)
        return {"status": "error", "error": "Max iterations reached", "iterations": self.state.iteration}

    def _build_context(self) -> dict[str, Any]:
        context = self.context_builder.build(
            current_state=self.state.current_state,
            task_history=self.state.task_history,
            working_memory=self.working_memory.get_all(),
            action_history=self.action_history
        )
        self.state.context = context
        return context

    def _execute_action(self, plan: dict[str, Any], context: dict[str, Any]) -> Any:
        action = plan.get("action", "done")
        details = plan.get("details", {})
        
        if action == "search":
            query = details.get("query", "")
            return self.tool_registry.execute("web_search", query=query)
        
        elif action == "edit":
            instruction = details.get("instruction", "")
            file_content = details.get("file_content", "")
            web_info = details.get("web_info", "")
            return self.editor.edit(instruction, file_content, web_info)
        
        elif action == "read_file":
            file_path = details.get("query", "")
            return self.tool_registry.execute("read_file", file_path=file_path)
        
        elif action == "write_file":
            file_path = details.get("query", "")
            content = details.get("content", "")
            return self.tool_registry.execute("write_file", file_path=file_path, content=content)
        
        elif action == "test":
            test_command = details.get("query", "")
            return self.tool_registry.execute("run_test", command=test_command)
        
        elif action == "reflect":
            return self.reflector.reflect(str(context), context)
        
        else:
            return {"status": "done", "message": "No action needed"}

    def _add_to_memory(self, key: str, value: Any):
        self.working_memory.add(key, value)

    def get_state(self) -> AgentStateData:
        return self.state

    def get_history(self) -> list[dict[str, Any]]:
        return self.action_history
