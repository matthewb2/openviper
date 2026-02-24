class Orchestrator:
    def __init__(self, planner, executor, workspace, max_iters=10):
        self.planner = planner
        self.executor = executor
        self.workspace = workspace
        self.max_iters = max_iters
        print("🔥 HARDENED ORCHESTRATOR LOADED")

    def run(self, goal: str):
        self.workspace.reset_tracking()
        file_operation_executed = False

        for iteration in range(1, self.max_iters + 1):

            plan = self.planner.plan(goal)
            print(f"[ITER {iteration}] PLAN:", plan)

            action = plan.get("action")

            # 🔥 DONE 강제 차단
            if action == "done":
                if not file_operation_executed:
                    print("🚫 DONE 차단됨: 최소 1개 파일 생성/수정이 필요합니다.")
                    continue
                print("✅ DONE 허용: 파일 변경 확인됨")
                return {
                    "status": "success",
                    "iterations": iteration
                }

            # 파일 작업 실행
            result = self.executor.execute(plan)
            print(f"[ITER {iteration}] RESULT:", result)

            if action in ("create_file", "write_file", "edit_file"):
                if result.get("status") in ("created", "modified"):
                    file_operation_executed = True

        return {
            "status": "failed",
            "reason": "max iterations exceeded"
        }