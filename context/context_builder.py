from typing import Any
from agent.core.state import AgentState


class ContextBuilder:
    def __init__(self):
        self.max_history_length = 10

    def build(
        self,
        current_state: AgentState,
        task_history: list[Any],
        working_memory: list[dict[str, Any]],
        action_history: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        context = {
            "current_state": current_state.value if isinstance(current_state, AgentState) else str(current_state),
            "task_summary": self._summarize_tasks(task_history),
            "recent_actions": self._summarize_actions(action_history or []),
            "memory": self._format_memory(working_memory),
            "errors": self._extract_errors(task_history)
        }
        
        return context

    def _summarize_tasks(self, task_history: list[Any]) -> list[dict[str, Any]]:
        summaries = []
        for task in task_history[-self.max_history_length:]:
            if hasattr(task, 'description') and hasattr(task, 'status'):
                summaries.append({
                    "description": task.description,
                    "status": task.status,
                    "error": getattr(task, 'error', None)
                })
        return summaries

    def _summarize_actions(self, action_history: list[dict[str, Any]]) -> list[str]:
        summaries = []
        for action in action_history[-5:]:
            if "plan" in action and isinstance(action["plan"], dict):
                action_type = action["plan"].get("action", "unknown")
                summaries.append(f"Iteration {action.get('iteration')}: {action_type}")
        return summaries

    def _format_memory(self, working_memory: list[dict[str, Any]]) -> str:
        if not working_memory:
            return "Empty memory"
        
        lines = []
        for entry in working_memory[-5:]:
            key = entry.get("key", "unknown")
            value = entry.get("value", "")
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines) if lines else "No recent memory"

    def _extract_errors(self, task_history: list[Any]) -> list[str]:
        errors = []
        for task in task_history:
            if hasattr(task, 'error') and task.error:
                errors.append(task.error)
        return errors[-5:]

    def add_file_context(self, context: dict[str, Any], file_path: str, content: str) -> dict[str, Any]:
        context["current_file"] = file_path
        context["file_content"] = content[:1000]
        return context

    def add_web_context(self, context: dict[str, Any], search_results: list[dict[str, Any]]) -> dict[str, Any]:
        context["web_results"] = search_results[:3]
        return context
