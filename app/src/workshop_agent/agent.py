"""agent.py – Strands-based AI agent factory.

The entire agentic loop (tool discovery, tool execution, retry logic,
conversation history) is handled by the Strands Agents SDK.

CUSTOMIZE: Update create_mcp_client() to use your own MCP servers if your
team needs tools beyond the Bedrock Knowledge Base retrieval.

Usage::

    agent, mcp_client = create_agent(config)
    response = agent("Who founded Hogwarts?")
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.tools.mcp import MCPClient
from strands_tools import retrieve

from workshop_agent.config import Config


# ── System prompt builder ─────────────────────────────────────────────────────


def build_system_prompt(config: Config) -> str:
    """Build the CRAFTY system prompt for the HORROCRUXES challenge."""
    now_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return f"""# Role
You are CRAFTY, an expert fan of Harry Potter. Your work is to answer — in either Spanish or English, matching the language of the question — the questions asked. Make sure to answer comprehensively, based strictly on the books.

# Context
You have access to the seven Harry Potter books. Look up related information in the books by using the `retrieve` tool. Do not answer from prior knowledge; if the retrieved passages do not support a claim, do not make it.

# Goal
Answer the question by providing the actual answer, and for every claim add:
- a book reference (verbatim quote or tight paraphrase, no more than 100 characters)
- the book title
- the chapter title and number
- the page of the passage

If any of these fields is not available from the retrieval result, state that explicitly instead of inventing it.

# Task
1. Analyze the question. If it is ambiguous or under-specified, ask the user a single clarifying question before searching.
2. Look for information in the books using the `retrieve` tool. Issue multiple targeted queries when the question spans characters, books, lists, or comparisons.
3. Answer the question, attaching the reference fields above to each claim, and end with a "Sources" list of the unique passages used.

Region: {config.aws_region}
Model: {config.effective_model_id}
Current UTC time: {now_utc}
"""


# ── MCP client factory ────────────────────────────────────────────────────────


def create_mcp_client(
    command: str,
    cross_account_env: Optional[dict[str, str]] = None,
) -> MCPClient:
    """Create an MCPClient for an extra tool the team wires in.

    Not called by default — the baseline ships with `retrieve` only. Append
    the result to the `tools` list in `create_agent()` (and the matching
    block in `server.py`) and remember to manage the client's lifecycle:

        mcp_client = create_mcp_client("your-mcp-server")
        mcp_client.start()
        ...
        mcp_client.stop()

    Args:
        command:           The MCP server entry-point command (the package
                           must be installed in this venv / image).
        cross_account_env: Optional AWS credential env vars to inject into
                           the subprocess for cross-account scenarios.

    Returns:
        An MCPClient ready to be passed to a Strands Agent.
    """
    env = dict(os.environ)
    if cross_account_env:
        env.update(cross_account_env)

    return MCPClient(
        lambda: stdio_client(StdioServerParameters(command=command, env=env))
    )


# ── Agent factory ─────────────────────────────────────────────────────────────


def create_agent(
    config: Config,
    cross_account_env: Optional[dict[str, str]] = None,
    message_history: Optional[list[dict[str, Any]]] = None,
) -> tuple[Agent, Optional[MCPClient]]:
    """Create a Strands Agent wired to the Knowledge Base retriever.

    The baseline only ships the Bedrock KB `retrieve` tool. Workshop teams
    can add MCP-based tools by appending the result of ``create_mcp_client()``
    to ``tools`` below (and managing its lifecycle in the caller).

    Args:
        config:            Application configuration.
        cross_account_env: Reserved for teams that add MCP servers needing
                           cross-account credentials (currently unused).
        message_history:   Optional existing conversation messages to resume.

    Returns:
        A (agent, mcp_client) tuple. The MCPClient is ``None`` until a team
        wires one in.
    """
    model = BedrockModel(
        model_id=config.effective_model_id,
        region_name=config.aws_region,
    )

    tools: list[Any] = []
    if config.knowledge_base_id:
        os.environ.setdefault("KNOWLEDGE_BASE_ID", config.knowledge_base_id)
        tools.append(retrieve)

    mcp_client: Optional[MCPClient] = None

    agent = Agent(
        model=model,
        tools=tools,
        system_prompt=build_system_prompt(config),
        messages=message_history or [],
    )

    return agent, mcp_client
