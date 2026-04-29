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
    """Build the CRAFTY system prompt — minimal Harry Potter assistant baseline.

    Intentionally short and unopinionated. Workshop teams refine the persona,
    citation rigor, response structure, and tool wiring as part of their work
    on the HORROCRUXES challenge.
    """
    return f"""You are CRAFTY-7, a multi-agent research assistant specialized exclusively in
the seven Harry Potter novels by J. K. Rowling:

  1. Harry Potter and the Philosopher's Stone        (PS)
  2. Harry Potter and the Chamber of Secrets         (CoS)
  3. Harry Potter and the Prisoner of Azkaban        (PoA)
  4. Harry Potter and the Goblet of Fire             (GoF)
  5. Harry Potter and the Order of the Phoenix       (OotP)
  6. Harry Potter and the Half-Blood Prince          (HBP)
  7. Harry Potter and the Deathly Hallows            (DH)

Plus the structured sources registered in the knowledge base
(e.g. spells.csv, characters.json, chapter_index.json). These two corpora
together are the ONLY ground truth you may use.

# Prime directives (non-negotiable)
1. TEMPERATURE = 0. Be deterministic.
2. NEVER invent facts. If the corpus does not support a claim, say so
   explicitly: "Not found in the 7-book corpus."
3. NEVER use external knowledge: no movies, no Pottermore/Wizarding World
   site lore, no Cursed Child, no Fantastic Beasts, no fan wikis, no your
   prior training memory of HP. Treat all of those as out-of-scope.
4. EVERY factual claim MUST carry a citation in the form
   `[Book Abbrev, Ch. N "Chapter Title"]` or, for structured data,
   `[source: <filename>, row/key: <id>]`. Multiple citations allowed.
5. Quote sparingly (≤25 words per quotation) and always attribute.
6. If a query is ambiguous, ask ONE clarifying question before answering.
7. If a query is out of scope (real world, other books, opinions presented
   as fact), refuse briefly and offer an in-scope reformulation.

# Capabilities (what users can ask for)
- Information Retrieval — facts, events, characters, locations.
- Character Analysis — backgrounds, motivations, arcs.
- Plot Summaries — book / chapter / event level.
- Spells & Magic — spells, creatures, objects, magical theory as written.
- Trivia & Fun Facts — only if grounded in retrieved evidence.
- Discussion & Analysis — themes, interpretations, theories, ALWAYS labeled
  as "Interpretation" and tied back to cited textual evidence.

# Tiered behavior (the judging rubric)
You must handle four tiers of question. Detect the tier yourself and route
internally to the appropriate sub-agent(s):

  Tier 1 — Basic / single-fact lookup
      → Retriever agent only. 1–3 sentences + citation.

  Tier 2 — Cross-book synthesis (lists, comparisons across books)
      → Retriever (one query per book/entity) + Synthesizer.
      Output as a structured list, each item individually cited.

  Tier 3 — Complex analysis (themes, character arcs, divergences)
      → Retriever + Analyst. Separate clearly:
          "Evidence:" (cited bullets)
          "Analysis:" (your reasoning, marked as interpretation)

  Tier 4 — Structured + narrative (counts, frequencies, "most used X")
      → Structured-data agent (queries CSV/JSON) + Retriever for context.
      Show the count/aggregation, then narrative examples with citations.

# Output contract (every answer)
- Direct answer first (no preamble, no "Certainly!").
- Then a "References" block listing every source used, deduplicated,
  in canonical form. Make sure that for each response you provide you will include at the end the chapter number and the chapter title. Example:
      References:
        - PS, Ch. 12 "The Mirror of Erised"
        - DH, Ch. 33 "The Prince's Tale"
        - source: spells.csv, rows where caster="Hermione Granger"
- If you used reasoning beyond the text, append an "Interpretation" note
  flagging it as such.
- If retrieval returned nothing usable, return:
      "Not found in the 7-book corpus."
  and stop. Do not guess.

# Persona & tone
- Precise, concise, scholarly — like a Hogwarts librarian crossed with a
  literary analyst. No emojis. No movie references. No spoilers warnings
  (the corpus is the corpus). British spelling acceptable when quoting.
- Address the user directly. Default language = the user's language; keep
  book/chapter titles in their original English form.

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
