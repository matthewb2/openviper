import os
from typing import Any


def web_search(query: str, num_results: int = 5) -> dict[str, Any]:
    """
    웹 검색을 수행합니다.
    실제 환경에서는 Bing, Serper, DuckDuckGo 등의 API를 사용하세요.
    """
    api_key = os.getenv("SERPER_API_KEY") or os.getenv("BING_API_KEY")
    
    if not api_key:
        return {
            "query": query,
            "results": [
                {"title": f"Result for {query} - 1", "snippet": f"Search result snippet for {query}"},
                {"title": f"Result for {query} - 2", "snippet": f"Another result for {query}"},
            ],
            "error": "No API key configured - using mock results"
        }
    
    try:
        import requests
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        if os.getenv("SERPER_API_KEY"):
            response = requests.post(
                "https://google.serper.dev/search",
                headers=headers,
                json={"q": query, "num": num_results}
            )
            data = response.json()
            return {
                "query": query,
                "results": [
                    {"title": r.get("title"), "snippet": r.get("snippet"), "url": r.get("link")}
                    for r in data.get("organic", [])[:num_results]
                ]
            }
        
    except Exception as e:
        return {"query": query, "error": str(e), "results": []}
    
    return {"query": query, "results": []}


def code_search(query: str) -> dict[str, Any]:
    """
    코드 관련 검색을 수행합니다.
    """
    return web_search(f"code {query}")


def documentation_search(query: str) -> dict[str, Any]:
    """
    문서 검색을 수행합니다.
    """
    return web_search(f"documentation {query}")
