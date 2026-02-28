import json
import os
from datetime import datetime

class Memory:
    def __init__(self, memory_file="agent_memory.json"):
        self.memory_file = memory_file
        self.data = {
            "current_project": None,
            "last_action": None,
            "last_file": None,
            "history": [],
            "errors": []
        }
        self._load()

    # -----------------------------
    # Persistence
    # -----------------------------
    def _load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def _save(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # -----------------------------
    # Project Tracking
    # -----------------------------
    def set_project(self, project_name):
        self.data["current_project"] = project_name
        self._save()

    def get_project(self):
        return self.data["current_project"]

    # -----------------------------
    # Action Tracking
    # -----------------------------
    def set_last_action(self, action):
        self.data["last_action"] = action
        self._save()

    def get_last_action(self):
        return self.data["last_action"]

    # -----------------------------
    # File Tracking
    # -----------------------------
    def set_last_file(self, file_path):
        self.data["last_file"] = file_path
        self._save()

    def get_last_file(self):
        return self.data["last_file"]

    # -----------------------------
    # History
    # -----------------------------
    def add_history(self, user_input, plan):
        self.data["history"].append({
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "plan": plan
        })
        self._save()

    def get_recent_history(self, limit=5):
        return self.data["history"][-limit:]

    # -----------------------------
    # Error Logging
    # -----------------------------
    def add_error(self, error_message):
        self.data["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        })
        self._save()

    def get_recent_errors(self, limit=3):
        return self.data["errors"][-limit:]