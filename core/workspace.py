from pathlib import Path

class Workspace:
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.modified_files = set()

    def write_file(self, path: str, content: str):
        full_path = self.root / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        full_path.write_text(content, encoding="utf-8")

        # 실제 디스크 존재 확인
        if not full_path.exists():
            raise RuntimeError(f"파일 생성 실패: {path}")

        self.modified_files.add(str(full_path))
        return {"status": "created", "path": str(full_path)}

    def has_modifications(self) -> bool:
        return len(self.modified_files) > 0

    def reset_tracking(self):
        self.modified_files.clear()