import os
from typing import Any


def read_file(file_path: str) -> dict[str, Any]:
    """파일을 읽어 내용을 반환합니다."""
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}", "content": None}
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"file_path": file_path, "content": content, "success": True}
    except Exception as e:
        return {"error": str(e), "file_path": file_path, "success": False}


def write_file(file_path: str, content: str) -> dict[str, Any]:
    """파일을 작성합니다."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {"file_path": file_path, "success": True}
    except Exception as e:
        return {"error": str(e), "file_path": file_path, "success": False}


def list_directory(directory_path: str = ".") -> dict[str, Any]:
    """디렉토리 목록을 반환합니다."""
    try:
        items = os.listdir(directory_path)
        result = []
        
        for item in items:
            full_path = os.path.join(directory_path, item)
            is_dir = os.path.isdir(full_path)
            result.append({
                "name": item,
                "type": "directory" if is_dir else "file",
                "path": full_path
            })
        
        return {"directory": directory_path, "items": result, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


def get_file_info(file_path: str) -> dict[str, Any]:
    """파일 정보를 반환합니다."""
    try:
        stat = os.stat(file_path)
        return {
            "file_path": file_path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "exists": True
        }
    except Exception as e:
        return {"error": str(e), "exists": False}


def search_in_file(file_path: str, pattern: str) -> dict[str, Any]:
    """파일에서 패턴을 검색합니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        matches = []
        for i, line in enumerate(lines, 1):
            if pattern in line:
                matches.append({"line": i, "content": line.strip()})
        
        return {"file_path": file_path, "pattern": pattern, "matches": matches}
    except Exception as e:
        return {"error": str(e)}
