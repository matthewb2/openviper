import os
import sys
import argparse

# Ensure UTF-8 output on terminals that support reconfigure
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

agent_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(agent_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

def load_env_from_dotenv(dotenv_path: str):
    try:
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key:
                    os.environ[key] = val
    except FileNotFoundError:
        pass

from agent.core.agent import CodingAgent

def main():
    parser = argparse.ArgumentParser(description='Context-Aware Coding Agent')
    parser.add_argument('goal', nargs='?', help='Goal to achieve', default='')
    parser.add_argument('--max-iterations', type=int, default=10, help='Maximum iterations')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    # API key is read from .env GROQ_API_KEY, not via CLI flag
    
    args = parser.parse_args()
    # GROQ_API_KEY will be sourced from .env if present; CLI --api-key is deprecated
    # Load environment variables from .env located alongside this script
    dotenv_path = os.path.join(agent_dir, '.env')
    load_env_from_dotenv(dotenv_path)
    # Debug: verify .env loading
    key = os.environ.get('GROQ_API_KEY')
    if key:
        masked = key[:4] + '*' * max(0, len(key) - 4)
        print(f"[DEBUG] GROQ_API_KEY loaded from .env (len={len(key)}): {masked}")
    else:
        print("[DEBUG] GROQ_API_KEY not set in environment")
    
    # Normalize whitespace in provided goal to avoid garbled spacing in some terminals
    normalized_goal = ' '.join(args.goal.split()) if args.goal else ""

    # Initialize agent with parsed arguments
    agent = CodingAgent(max_iterations=args.max_iterations)
    
    if args.interactive:
        print("=== Context-Aware Coding Agent ===")
        print("대화형 모드입니다. 종료하려면 'quit' 또는 'exit'를 입력하세요.")
        print()
        
        while True:
            goal = input("목표 입력 > ").strip()
            
            if goal.lower() in ["quit", "exit", "종료"]:
                print("에이전트를 종료합니다.")
                break
            
            if not goal:
                continue
            
            print(f"\n작업 시작: {goal}")
            print("-" * 40)
            
            result = agent.run(goal)
            
            print(f"\n결과: {result}")
            print(f"반복 횟수: {result.get('iterations', 'N/A')}")
            print("-" * 40)
            print()
    
    elif args.goal:
        print(f"작업 시작: {normalized_goal}")
        result = agent.run(normalized_goal)
        print(f"결과: {result}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
