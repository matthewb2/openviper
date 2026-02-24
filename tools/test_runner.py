import subprocess
import os
from typing import Any


def run_test(command: str = "pytest", working_dir: str = ".") -> dict[str, Any]:
    """
    테스트를 실행합니다.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"command": command, "error": "Test timeout", "success": False}
    except Exception as e:
        return {"command": command, "error": str(e), "success": False}


def run_tests(test_path: str = "tests/", verbose: bool = True) -> dict[str, Any]:
    """
    테스트 디렉토리의 모든 테스트를 실행합니다.
    """
    verbose_flag = "-v" if verbose else ""
    command = f"pytest {test_path} {verbose_flag}"
    return run_test(command)


def run_specific_test(test_file: str, test_name: str | None = None) -> dict[str, Any]:
    """
    특정 테스트 파일 또는 테스트 메서드를 실행합니다.
    """
    if test_name:
        command = f"pytest {test_file}::{test_name} -v"
    else:
        command = f"pytest {test_file} -v"
    return run_test(command)


def check_test_coverage(test_path: str = "tests/") -> dict[str, Any]:
    """
    테스트 커버리지를 확인합니다.
    """
    command = f"pytest {test_path} --cov --cov-report=term-missing"
    return run_test(command)


def lint_code(file_path: str, linter: str = "ruff") -> dict[str, Any]:
    """
    코드 린트를 실행합니다.
    """
    command = f"{linter} {file_path}"
    return run_test(command)


def format_code(file_path: str, formatter: str = "black") -> dict[str, Any]:
    """
    코드 포맷을 지정합니다.
    """
    command = f"{formatter} {file_path}"
    return run_test(command)
