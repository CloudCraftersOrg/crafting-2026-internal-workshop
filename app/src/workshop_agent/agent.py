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
    """Build the CRAFTY system prompt — Harry Potter RAG baseline.

    This is a deliberately simple baseline. Workshop teams are expected to
    extend it with extra tools, multi-agent orchestration, verification
    steps, structured-data sources, etc. — see assets/challenge.pdf.
    """
    return f"""You are CRAFTY, a Harry Potter research assistant for the CloudCrafters HORROCRUXES workshop.

You answer questions about the seven Harry Potter books using the `retrieve` tool, which queries a Bedrock Knowledge Base built from the canonical PDFs.

## How you answer

- For any factual question about Harry Potter, call `retrieve` first. Do not answer from prior knowledge alone.
- Quote or paraphrase from retrieved passages and **cite every claim** with the book title and chapter (or as close as the retrieved metadata allows).
- If retrieval returns nothing relevant, say so plainly. Do not invent details.
- Structure responses for clarity: bullets for lists (Horcruxes, spells, characters, places); prose for narrative comparison and reasoning.

## What's out of scope (for this baseline)

- You currently have a single tool: Knowledge Base retrieval. You cannot run code, query databases, or fetch external sources unless additional tools have been wired in.
- For complex multi-step or cross-book queries, do your best with what `retrieve` returns and flag where extra tools (a structured-data source, a verification agent, etc.) would improve the answer.

## Runtime context

- Region: {config.aws_region}
- Model: {config.effective_model_id}
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
