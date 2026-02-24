from typing import Any
from datetime import datetime
from collections import deque


class WorkingMemory:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.history: deque[dict[str, Any]] = deque(maxlen=max_size)
        self.web_info = ""
        self.current_file = None
        self.last_result = None

    def add(self, key: str, value: Any):
        entry = {
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(entry)

    def add_step(self, step: dict[str, Any]):
        step["timestamp"] = datetime.now().isoformat()
        self.history.append(step)

    def set_web_info(self, info: str):
        self.web_info = info

    def set_current_file(self, file_path: str):
        self.current_file = file_path

    def set_last_result(self, result: Any):
        self.last_result = result

    def get_context(self) -> dict[str, Any]:
        recent = list(self.history)[-5:]
        return {
            "recent_history": recent,
            "web_info": self.web_info,
            "current_file": self.current_file,
            "last_result": self.last_result
        }

    def get_all(self) -> list[dict[str, Any]]:
        return list(self.history)

    def get_by_key(self, key: str) -> list[Any]:
        return [entry["value"] for entry in self.history if entry.get("key") == key]

    def clear(self):
        self.history.clear()
        self.web_info = ""
        self.current_file = None
        self.last_result = None

    def get_recent(self, n: int = 5) -> list[dict[str, Any]]:
        return list(self.history)[-n:]
