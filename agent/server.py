# server.py

import os
import subprocess
import shutil
from pathlib import Path
from fastapi import FastAPI
from fastapi import HTTPException
from typing import Optional
import sys

from pydantic import BaseModel

class MoveFileRequest(BaseModel):
    project_name: str
    source_path: str
    dest_path: str


# 작업 루트 디렉토리
app = FastAPI()

WORKSPACE = Path("D:/openviper/agent/workspace")  # 실제 작업 폴더



# ==============================
# 📌 Request Models
# ==============================


# -----------------------------
# Request 모델
# -----------------------------
class RunJavaRequest(BaseModel):
    project_name: str
    main_class: Optional[str] = None  # 지정 안 하면 자동 탐색


class CreateProjectRequest(BaseModel):
    project_name: str


class WriteFileRequest(BaseModel):
    project_name: str
    file_path: str
    content: str


class RunMavenRequest(BaseModel):
    project_name: str
    goal: str = "package"



# ==============================
# 📁 1. 프로젝트 생성
# ==============================

@app.post("/create_project")
def create_project(req: CreateProjectRequest):
    project_dir = WORKSPACE / req.project_name

    if project_dir.exists():
        return {"status": "error", "message": "Project already exists"}

    # Maven 기본 구조 생성
    (project_dir / "src/main/java").mkdir(parents=True)
    (project_dir / "src/test/java").mkdir(parents=True)

    pom_content = f"""
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>agent</groupId>
    <artifactId>{req.project_name}</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.10.1</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
"""

    with open(project_dir / "pom.xml", "w", encoding="utf-8") as f:
        f.write(pom_content.strip())

    return {"status": "success", "message": f"Project {req.project_name} created"}


# ==============================
# 📝 2. 파일 작성
# ==============================

@app.post("/write_file")
def write_file(req: WriteFileRequest):
    project_dir = WORKSPACE / req.project_name

    if not project_dir.exists():
        return {"status": "error", "message": "Project not found"}

    file_path = project_dir / req.file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(req.content)

    return {"status": "success", "message": f"{req.file_path} written"}


@app.post("/move_file")
def move_file(req: MoveFileRequest):
    try:
        project_dir = WORKSPACE / req.project_name
        src = project_dir / req.source_path
        dst = project_dir / req.dest_path

        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)

        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
# ==============================
# 🔨 3. Maven 빌드
# ==============================
@app.post("/run_maven")
def run_maven(req: RunMavenRequest):

    try:
        project_dir = WORKSPACE / req.project_name

        if not project_dir.exists():
            return {"status": "error", "message": "Project not found"}

        # 🔥 Windows에서는 mvn.cmd 사용
        mvn_executable = "mvn.cmd" if sys.platform.startswith("win") else "mvn"

        if shutil.which(mvn_executable) is None:
            return {
                "status": "error",
                "stderr": f"{mvn_executable} not found in PATH"
            }

        goal_parts = req.goal.split() if req.goal else ["package"]

        process = subprocess.Popen(
            [mvn_executable] + goal_parts,
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(timeout=120)

        return {
            "status": "success" if process.returncode == 0 else "error",
            "stdout": stdout,
            "stderr": stderr
        }

    except subprocess.TimeoutExpired:
        process.kill()
        return {
            "status": "error",
            "stderr": "Maven execution timeout"
        }

    except Exception as e:
        return {
            "status": "error",
            "stderr": str(e)
        }
# ==============================
# ▶ 4. Java 실행
# ==============================

# -----------------------------
# 유틸: main 클래스 자동 탐색
# -----------------------------
def find_main_class(classes_dir: Path) -> Optional[str]:
    for root, dirs, files in os.walk(classes_dir):
        for file in files:
            if file.endswith(".class"):
                class_path = Path(root) / file
                rel_path = class_path.relative_to(classes_dir)
                class_name = ".".join(rel_path.with_suffix("").parts)
                # 단순히 main 클래스 있는지 확인 없이 첫 클래스 반환
                return class_name
    return None

# -----------------------------
# 안정화된 run_java
# -----------------------------
@app.post("/run_java")
def run_java(req: RunJavaRequest):
    try:
        project_dir = WORKSPACE / req.project_name
        classes_dir = project_dir / "target" / "classes"

        if not classes_dir.exists():
            return {"status": "error", "message": "Project not compiled"}

        # main_class가 없으면 자동 탐색
        main_class = req.main_class or find_main_class(classes_dir)
        if not main_class:
            return {"status": "error", "message": "No class found to run"}

        # Windows 경로 문제 해결
        classes_dir_str = str(classes_dir.resolve())
        project_dir_str = str(project_dir.resolve())

        # Java 실행
        process = subprocess.Popen(
            ["java", "-cp", classes_dir_str, main_class],
            cwd=project_dir_str,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(timeout=60)

        return {
            "status": "success" if process.returncode == 0 else "error",
            "stdout": stdout,
            "stderr": stderr
        }

    except subprocess.TimeoutExpired:
        return {"status": "error", "stderr": "Execution timed out"}
    except Exception as e:
        return {"status": "error", "stderr": str(e)}
# ==============================
# 🚀 서버 실행 안내
# ==============================

# 실행 명령:
# uvicorn server:app --reload --port 8000