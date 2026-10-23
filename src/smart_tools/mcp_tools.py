"""Load tools from the local MCP server (mcp_server/) for the agent.

The server runs over stdio. The adapter starts a fresh server subprocess for each
tool call, so the loaded tools stay valid across requests and can be cached.
"""

import logging
import sys
from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent

MCP_SERVERS = {
    "smart-rates": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "mcp_server.server"],
        "cwd": str(PROJECT_ROOT),  # mcp_server/ lives at the repo root, outside src/
        "env": {"PYTHONPATH": str(PROJECT_ROOT)},
    }
}

_tools_cache: list[BaseTool] | None = None


async def get_mcp_tools() -> list[BaseTool]:
    """Return the MCP server's tools, or [] if the server can't be reached.

    A failure is logged and not cached, so the next request retries.
    """
    global _tools_cache
    if _tools_cache is None:
        try:
            _tools_cache = await MultiServerMCPClient(MCP_SERVERS).get_tools()
        except Exception:
            logger.exception("Could not load MCP tools; continuing without them")
            return []
    return _tools_cache
