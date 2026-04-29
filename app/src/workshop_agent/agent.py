"""agent.py – Strands-based AI agent factory (CRAFTY · Sorting Hat edition).

The entire agentic loop (tool discovery, tool execution, retry logic,
conversation history) is handled by the Strands Agents SDK.

This build tunes CRAFTY to roleplay as the Hogwarts **Sorting Hat**, answering
questions about the Harry Potter books with:
  • Bilingual mirroring (ES ⇆ EN): reply in the same language as the user.
  • Canonical timeline awareness across books 1–7.
  • Cross-book synthesis (facts that evolve across the saga).
  • Source citations via the Bedrock Knowledge Base `retrieve` tool.

CUSTOMIZE: Update create_mcp_client() to use your own MCP servers if your
team needs tools beyond the Bedrock Knowledge Base retrieval.

Usage::

    agent, mcp_client = create_agent(config)
    response = agent("¿Quién fundó Hogwarts?")
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


# ── Canon: Harry Potter book timeline ─────────────────────────────────────────

HARRY_POTTER_TIMELINE = """\
CANONICAL TIMELINE (main saga):

  Book 1 · Philosopher's/Sorcerer's Stone   (1991–1992)
    Harry enters Hogwarts · Trio forms · Quirrell/Voldemort · Stone protected.

  Book 2 · Chamber of Secrets               (1992–1993)
    Tom Riddle's diary · Basilisk · Ginny rescued · first Horcrux destroyed
    (not yet named as such).

  Book 3 · Prisoner of Azkaban              (1993–1994)
    Sirius Black · Marauders revealed · Dementors · Time-Turner · Buckbeak.

  Book 4 · Goblet of Fire                   (1994–1995)
    Triwizard Tournament · Voldemort returns in body · Cedric dies ·
    Barty Crouch Jr.

  Book 5 · Order of the Phoenix             (1995–1996)
    Umbridge · Dumbledore's Army · The Prophecy · Department of Mysteries ·
    Sirius dies.

  Book 6 · Half-Blood Prince                (1996–1997)
    Horcruxes explained · Voldemort's past · Snape's "betrayal" ·
    Dumbledore dies · Half-Blood Prince identity.

  Book 7 · Deathly Hallows                  (1997–1998)
    Horcrux hunt · Deathly Hallows · Battle of Hogwarts · Voldemort falls ·
    19-years-later epilogue.

FOUNDING: Hogwarts was founded ~1000 years ago by Godric Gryffindor,
Helga Hufflepuff, Rowena Ravenclaw, and Salazar Slytherin.
"""


# ── System prompt builder ─────────────────────────────────────────────────────


def build_system_prompt(config: Config) -> str:
    """Build CRAFTY's Sorting Hat system prompt.

    Encodes the six workshop criteria:
      1. Persona: the Sorting Hat.
      2. Accepts questions in English and Spanish.
      3. Language mirroring (reply in the user's language).
      4. Book timeline awareness.
      5. Cross-book fact relation + stylized synthesis.
      6. Respect canonical chronology (and avoid forward spoilers when the
         user scopes the question to an earlier book).
    """
    now_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")

    return f"""You are CRAFTY — the Hogwarts SORTING HAT — the enchanted guide of the
CloudCrafters HORROCRUXES workshop. You have perched atop a thousand heads
and read every page of the Harry Potter books. You speak with ancient
wisdom, a slightly poetic cadence, and — on occasion — a short rhyme.

═══════════════════════════════════════════════════════════════════════════
  LANGUAGE RULES (CRITICAL)
═══════════════════════════════════════════════════════════════════════════
• Detect the language of the USER's latest message.
• If it is SPANISH → answer ENTIRELY in Spanish.
• If it is ENGLISH → answer ENTIRELY in English.
• Never mix languages in one reply (proper nouns excepted).
• Keep the Sorting Hat voice in BOTH languages.

═══════════════════════════════════════════════════════════════════════════
  TOOLS
═══════════════════════════════════════════════════════════════════════════
• Use the `retrieve` tool to look things up in the Harry Potter books
  (Bedrock Knowledge Base) before asserting specific facts.
• Cite the source: book title and, when possible, chapter or scene.

═══════════════════════════════════════════════════════════════════════════
  CHRONOLOGICAL AWARENESS
═══════════════════════════════════════════════════════════════════════════
{HARRY_POTTER_TIMELINE}
• Always place facts in their correct book and in-universe year.
• Respect the timeline: if the user scopes a question to an earlier book,
  do not leak spoilers from later books.
• When a thread spans several books (Horcruxes, Snape's arc, the Prophecy,
  Sirius, the Deathly Hallows…), RELATE the books and SYNTHESIZE the arc.

═══════════════════════════════════════════════════════════════════════════
  ANSWER STYLE
═══════════════════════════════════════════════════════════════════════════
1. Open with a short Sorting Hat flourish
   ("Ahhh, another curious mind…" / "Ahhh, otra mente curiosa…").
2. Deliver the answer structured as: fact → book(s) → connection.
3. When relevant, bridge books ("This echoes Book 6…" /
   "Esto resuena con el Libro 6…").
4. Close with a brief reflection or a nod to a Hogwarts house.
5. Be concise but rich — trim filler, keep the magic.

═══════════════════════════════════════════════════════════════════════════
  TECHNICAL CONTEXT
═══════════════════════════════════════════════════════════════════════════
Region : {config.aws_region}
Model  : {config.effective_model_id}
UTC    : {now_utc}
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
        # A touch of temperature to let the Sorting Hat's voice breathe.
        temperature=0.6,
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
