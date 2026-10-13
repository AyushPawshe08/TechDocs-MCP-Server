import os
import re

from dotenv import load_dotenv
from fastmcp import FastMCP

from .context7 import resolve_library as c7_resolve, get_library_docs as c7_get_docs
from .known_docs import KNOWN_DOCS

load_dotenv()

mcp = FastMCP("GetDoc")

DOCS_LOOKUP = {name.lower(): entry for name, entry in KNOWN_DOCS.items()}


def _extract_best_id(resolve_text: str) -> str | None:
    match = re.search(r"Context7-compatible library ID:\s*(/[\w./-]+)", resolve_text)
    return match.group(1).strip() if match else None


@mcp.tool()
def list_known_docs() -> dict:
    return {
        name: {"url": entry["url"], "context7_id": entry["context7_id"]}
        for name, entry in KNOWN_DOCS.items()
    }


@mcp.tool()
async def resolve_library(library_name: str) -> dict:
    entry = DOCS_LOOKUP.get(library_name.strip().lower())
    official_url = entry["url"] if entry else None
    cached_id = entry["context7_id"] if entry else None

    if cached_id:
        return {
            "library_name": library_name,
            "official_url": official_url,
            "context7_id": cached_id,
            "source": "cache",
        }

    try:
        raw = await c7_resolve(library_name)
        library_id = _extract_best_id(raw)
    except Exception as e:
        return {
            "library_name": library_name,
            "official_url": official_url,
            "context7_id": None,
            "error": str(e),
        }

    return {
        "library_name": library_name,
        "official_url": official_url,
        "context7_id": library_id,
        "source": "context7",
    }


@mcp.tool()
async def search_docs(library_name: str, query: str, language: str = "Python") -> dict:
    if not query.strip():
        return {"error": "query cannot be empty"}

    resolve_result = await resolve_library(library_name)

    if resolve_result.get("error"):
        return resolve_result

    library_id = resolve_result.get("context7_id")
    if not library_id:
        return {
            "library_name": library_name,
            "query": query,
            "error": "Could not resolve a Context7 library ID for this library.",
        }

    try:
        docs = await c7_get_docs(library_id, query, language)
    except Exception as e:
        return {
            "library_name": library_name,
            "context7_id": library_id,
            "query": query,
            "error": str(e),
        }

    return {
        "library_name": library_name,
        "official_url": resolve_result.get("official_url"),
        "context7_id": library_id,
        "query": query,
        "language": language,
        "docs": docs,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
