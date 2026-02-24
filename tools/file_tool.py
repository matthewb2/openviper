import os


def _safe_path(workspace_root: str, file_path: str) -> str:
    """
    workspace 내부 경로로 강제 제한
    """
    full_path = os.path.abspath(os.path.join(workspace_root, file_path))

    if not full_path.startswith(workspace_root):
        raise ValueError("Invalid path: access outside workspace is not allowed")

    return full_path


def write_file(file_path: str, content: str, workspace_root: str):
    try:
        if not file_path:
            return {"error": "file_path is required", "success": False}

        full_path = _safe_path(workspace_root, file_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "success": True,
            "file_path": full_path
        }

    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


def read_file(file_path: str, workspace_root: str):
    try:
        full_path = _safe_path(workspace_root, file_path)

        if not os.path.exists(full_path):
            return {"error": "File not found", "success": False}

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "success": True,
            "content": content
        }

    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


def list_directory(path: str = "", workspace_root: str = ""):
    try:
        full_path = _safe_path(workspace_root, path)

        if not os.path.exists(full_path):
            return {"error": "Directory not found", "success": False}

        files = os.listdir(full_path)

        return {
            "success": True,
            "files": files
        }

    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }