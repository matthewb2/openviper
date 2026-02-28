import subprocess
import sys
import os

def main():
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "agent.server:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("Starting server on port 8000...")

    client_process = subprocess.Popen(
        [sys.executable, "agent/interactive_client.py"]
    )

    server_process.wait()
    client_process.wait()

if __name__ == "__main__":
    main()
