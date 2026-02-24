class Executor:
    def __init__(self, workspace):
        self.workspace = workspace

    def execute(self, plan: dict):
        action = plan.get("action")

        if action == "create_file":
            path = plan["details"]["path"]
            content = plan["details"]["content"]
            return self.workspace.write_file(path, content)

        if action == "done":
            return {"status": "done"}

        return {"status": "unknown_action"}