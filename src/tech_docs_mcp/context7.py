import os
import json
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

CONTEXT7_URL = "https://mcp.context7.com/mcp"
CONTEXT7_API_KEY = os.getenv("CONTEXT7_API_KEY", "")
TIMEOUT = 30.0


def _parse_response(raw: str) -> dict:
    data_lines = [
        line[len("data:"):].strip()
        for line in raw.splitlines()
        if line.startswith("data:")
    ]
    if data_lines:
        return json.loads(data_lines[-1])
    return json.loads(raw)


async def _call_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if CONTEXT7_API_KEY:
        headers["Authorization"] = f"Bearer {CONTEXT7_API_KEY}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(CONTEXT7_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"Context7 HTTP {response.status_code}: {response.text[:300]}")

    data = _parse_response(response.text)

    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"Context7 error [{err.get('code')}]: {err.get('message')}")

    result = data.get("result", {})
    content = result.get("content", [])
    texts = [block.get("text", "") for block in content if block.get("type") == "text"]
    return "\n".join(texts).strip()


async def resolve_library(library_name: str) -> str:
    if not library_name.strip():
        raise ValueError("library_name cannot be empty")
    return await _call_tool(
        "resolve-library-id",
        {"libraryName": library_name, "query": library_name},
    )


async def get_library_docs(library_id: str, query: str, language: str = "Python") -> str:
    if not library_id.strip():
        raise ValueError("library_id cannot be empty")
    if not query.strip():
        raise ValueError("query cannot be empty")
    return await _call_tool(
        "query-docs",
        {"libraryId": library_id, "query": query, "language": language},
    )
