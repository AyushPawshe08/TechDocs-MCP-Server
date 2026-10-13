import asyncio
import os
import sys

from dotenv import load_dotenv
from fastmcp import Client
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from .server import mcp

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

SYSTEM_PROMPT = """You are an expert technical documentation assistant.
Answer questions accurately by consulting official documentation via the available tools.

Guidelines:
1. Always resolve technology names or search docs before answering.
2. Ground all answers in the retrieved documentation and cite canonical official source URLs.
3. Provide concrete, working code snippets conforming to modern library conventions.
4. If documentation does not support a specific claim or feature, state this explicitly rather than hallucinating syntax.
5. Note version or deprecation warnings where relevant."""


async def ask_question(question: str) -> None:
    async with Client(mcp) as client:
        @tool
        async def resolve_library(library_name: str) -> str:
            """Resolves library name to canonical URL and Context7 ID."""
            res = await client.call_tool("resolve_library", {"library_name": library_name})
            return res.content[0].text if res.content else str(res)

        @tool
        async def search_docs(library_name: str, query: str, language: str = "Python") -> str:
            """Fetches documentation and code examples from official sources."""
            res = await client.call_tool(
                "search_docs",
                {"library_name": library_name, "query": query, "language": language},
            )
            return res.content[0].text if res.content else str(res)

        @tool
        async def list_known_docs() -> str:
            """Lists all known libraries and their canonical documentation URLs."""
            res = await client.call_tool("list_known_docs", {})
            return res.content[0].text if res.content else str(res)

        tools = [resolve_library, search_docs, list_known_docs]
        llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
        agent = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)

        result = await agent.ainvoke({"messages": [("user", question)]})

        for msg in result["messages"]:
            if getattr(msg, "tool_calls", None):
                for call in msg.tool_calls:
                    print(f"Tool Call: {call['name']}({call['args']})")
            elif msg.type == "ai" and msg.content:
                print("\nAnswer:\n")
                print(msg.content)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How to connect MCP using Langchain"
    asyncio.run(ask_question(query))
