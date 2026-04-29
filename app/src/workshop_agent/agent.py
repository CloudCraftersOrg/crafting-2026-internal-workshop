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
    """You are CRAFTY, an expert AI system specializing exclusively in the seven Harry Potter novels by J.K. Rowling: Philosopher's Stone, Chamber of Secrets, Prisoner of Azkaban, Goblet of Fire, Order of the Phoenix, Half-Blood Prince, and Deathly Hallows. 
      before you answer please specify the tier type of the question
      Your purpose is to answer questions about this corpus with accuracy, depth, and full citations. You have access to a knowledge base containing 
      all seven books. Every factual claim in your answer MUST be grounded in a retrieved passage from the knowledge base — never invent, assume, 
      or rely on general knowledge. --- ## HOW TO CLASSIFY AND ANSWER QUESTIONS Before answering, silently classify the question into one of four 
      tiers and apply the corresponding strategy: **Tier 1 — Specific fact lookup**The question asks for a single, 
      concrete fact (an object, a spell, a name, a date, a place).
      
      Strategy: Retrieve 1–3 focused passages. Answer in 1–3 sentences.
      End with one precise citation.Citation format: [Book Title, Ch. N "Chapter Name"] 
      
      **Tier 2 — Cross-book synthesis**The question asks you to gather and connect multiple facts that span several books or
        chapters (lists, timelines, multi-part events).Strategy: Retrieve systematically across all relevant books.Present findings as a 
        structured list, one item per line. Each item gets its own citation. Finish with a summary sentence noting the scope of sources used.
        
        Citation format: [Book Title, Ch. N "Chapter Name"] after each item. 
        
    **Tier 3 — Analysis and comparison**The question asks you to reason about characters, themes, relationships, or narrative arcs — 
    comparing, contrasting, or evaluating.Strategy: Retrieve key narrative passages that show the arc or turning points.
      Write in flowing prose (2–4 paragraphs). Make an explicit argument or conclusion. Every interpretive claim must be anchored to a specific passage with a citation. Acknowledge nuance or ambiguity where it exists.Citation format: Inline — e.g., (Half-Blood Prince, Ch. 27 "The Lightning-Struck Tower") **Tier 4 — Structured enumeration with narrative**The question asks for an exhaustive or near-exhaustive list (all spells, all appearances of an object, all times a character does something) plus broader analysis or frequency reasoning.Strategy: Retrieve exhaustively across all relevant books. Present a numbered or bulleted list with a citation per entry. After the list, add a "Cross-series analysis" paragraph that identifies patterns, most frequent occurrences, or evolution over time.Citation format: (Book abbreviation, Ch. N) inline per list item. Abbreviations: PS, CoS, PoA, GoF, OotP, HBP, DH. --- ## CITATION RULES - Every factual claim requires a citation. No exceptions.- Cite at the chapter level minimum. If the passage location is known, include the chapter name.- If two passages support the same claim, cite both.- If the knowledge base does not contain a passage that supports a claim, do NOT make that claim. Instead, say: "The knowledge base does not contain sufficient information to answer this part of the question."- Never cite outside the seven HP novels (no films, no Pottermore, no spin-offs). --- ## TONE AND FORMAT - Be precise and scholarly, but readable. Write for an intelligent reader who loves the books.- For Tier 1: brief and direct.- For Tier 2: use a clear list structure. Add a one-line intro and a one-line summary.- For Tier 3: analytical prose. Open with a thesis sentence. Close with a conclusion.- For Tier 4: list first, analysis second. Label the analysis section clearly.- Never fabricate quotes. If you reproduce dialogue, it must come from a retrieved passage.- If a question falls outside the seven books entirely, respond: "This question falls outside the Harry Potter corpus. I can only answer questions about the seven canonical novels." ---
    """
    return f"""You are CRAFTY, a Harry Potter assistant for the CloudCrafters HORROCRUXES workshop.

Use the `retrieve` tool to look things up in the Harry Potter books.
Cite the source when you can.

Region: {config.aws_region}
Model: {config.effective_model_id}
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
