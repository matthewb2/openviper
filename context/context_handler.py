from typing import Any


class ContextHandler:
    """Handler for building and managing agent context"""
    
    @staticmethod
    def build_context(tool_registry, memory, iteration: int) -> dict:
        """Build context from tool registry, memory, and iteration"""
        files = tool_registry.execute("list_directory", path=".")
        return {
            "iteration": iteration,
            "memory": memory.get_all(),
            "files": files
        }
    
    @staticmethod
    def extract_print_source(text: str) -> str | None:
        """Extract print content from goal text."""
        if not text:
            return None
        import re
        m = re.search(r'"([^"]+)"', text)
        if m:
            return m.group(1)
        m2 = re.search(r"'([^']+)'", text)
        if m2:
            return m2.group(1)
        return None
    
    @staticmethod
    def generate_markdown_content(goal: str) -> str:
        """Generate markdown content based on user goal."""
        import re
        
        # Extract potential title from goal
        title_match = re.search(r'(?:about|for|을 위한|에 대한)\s+(.+?)(?:\s|$)', goal, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = "Project"
        
        # Extract description from goal
        desc = goal
        for pattern in [r'마크다운\s*문법\s*으로', r'readme\.?\s*파일\s*에', r'파일\s*을\s*만들', r'만들어\s*줘']:
            desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
        desc = desc.strip()
        if not desc:
            desc = "Project Description"
        
        # Generate markdown content
        content = f"""# {title}

## Overview

{desc}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Features

- Feature 1
- Feature 2
- Feature 3

## License

MIT
"""
        return content
