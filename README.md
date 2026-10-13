# tech-docs-mcp

An MCP (Model Context Protocol) server that provides AI coding assistants with official, live library documentation and verified code snippets.

## Installation

```bash
pip install tech-docs-mcp
```

Or run directly without installation using `uvx`:

```bash
uvx tech-docs-mcp
```

## Configuration for Claude Desktop / Cursor

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tech-docs": {
      "command": "uvx",
      "args": ["tech-docs-mcp"],
      "env": {
        "CONTEXT7_API_KEY": "<your-context7-api-key>"
      }
    }
  }
}
```