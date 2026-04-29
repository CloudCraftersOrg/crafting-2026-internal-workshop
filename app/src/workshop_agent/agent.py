"""agent.py – Strands-based AI agent factory (CRAFTY · Sorting Hat edition).

The entire agentic loop (tool discovery, tool execution, retry logic,
conversation history) is handled by the Strands Agents SDK.

This build tunes CRAFTY to roleplay as the Hogwarts **Sorting Hat**, answering
questions about the Harry Potter books with:
  • Bilingual mirroring (ES ⇆ EN): reply in the same language as the user.
  • Canonical timeline awareness across books 1–7.
  • Cross-book synthesis (facts that evolve across the saga).
  • **Mandatory per-book citations** (title + chapter + scene) at the end
    of every answer, via the Bedrock Knowledge Base `retrieve` tool.

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


# ── Canon: Harry Potter book timeline + canonical titles ──────────────────────

HARRY_POTTER_TIMELINE = """\
CANONICAL TIMELINE (main saga) — use these EXACT titles in citations:

  Book 1 · EN: "Harry Potter and the Philosopher's Stone" (US: Sorcerer's Stone)
           ES: "Harry Potter y la Piedra Filosofal"
           In-universe: 1991–1992
           Key arcs: Harry enters Hogwarts · Trio forms · Quirrell/Voldemort ·
                     Philosopher's Stone protected.

  Book 2 · EN: "Harry Potter and the Chamber of Secrets"
           ES: "Harry Potter y la Cámara Secreta"
           In-universe: 1992–1993
           Key arcs: Tom Riddle's diary · Basilisk · Ginny rescued ·
                     first Horcrux destroyed (not yet named).

  Book 3 · EN: "Harry Potter and the Prisoner of Azkaban"
           ES: "Harry Potter y el Prisionero de Azkaban"
           In-universe: 1993–1994
           Key arcs: Sirius Black · Marauders · Dementors · Time-Turner ·
                     Buckbeak.

  Book 4 · EN: "Harry Potter and the Goblet of Fire"
           ES: "Harry Potter y el Cáliz de Fuego"
           In-universe: 1994–1995
           Key arcs: Triwizard Tournament · Voldemort's bodily return ·
                     Cedric's death · Barty Crouch Jr.

  Book 5 · EN: "Harry Potter and the Order of the Phoenix"
           ES: "Harry Potter y la Orden del Fénix"
           In-universe: 1995–1996
           Key arcs: Umbridge · Dumbledore's Army · The Prophecy ·
                     Department of Mysteries · Sirius's death.

  Book 6 · EN: "Harry Potter and the Half-Blood Prince"
           ES: "Harry Potter y el Misterio del Príncipe"
           In-universe: 1996–1997
           Key arcs: Horcruxes explained · Voldemort's past ·
                     Snape's "betrayal" · Dumbledore's death.

  Book 7 · EN: "Harry Potter and the Deathly Hallows"
           ES: "Harry Potter y las Reliquias de la Muerte"
           In-universe: 1997–1998
           Key arcs: Horcrux hunt · Deathly Hallows · Battle of Hogwarts ·
                     Voldemort's fall · 19-years-later epilogue.

FOUNDING: Hogwarts was founded ~1000 years ago by Godric Gryffindor,
Helga Hufflepuff, Rowena Ravenclaw, and Salazar Slytherin.
"""


# ── Citation templates (ES / EN) ──────────────────────────────────────────────

CITATION_BLOCK_SPEC = """\
CITATION FORMAT (MANDATORY — end every factual answer with this block):

▸ If the reply is in ENGLISH, use the header "📚 References" and list items as:
     [Book N] «Exact English title» — Chapter <#/name> — "<short scene or quote>"
  Example:
     📚 References
     [Book 6] «Harry Potter and the Half-Blood Prince» — Chapter 23
              "Horcruxes" — Dumbledore explains the theory to Harry.
     [Book 7] «Harry Potter and the Deathly Hallows» — Chapter 36
              "The Flaw in the Plan" — final confrontation with Voldemort.

▸ If the reply is in SPANISH, use the header "📚 Referencias" and list items as:
     [Libro N] «Título exacto en español» — Capítulo <#/nombre> — "<escena o cita>"
  Ejemplo:
     📚 Referencias
     [Libro 6] «Harry Potter y el Misterio del Príncipe» — Capítulo 23
              «Horrocruxes» — Dumbledore le explica la teoría a Harry.
     [Libro 7] «Harry Potter y las Reliquias de la Muerte» — Capítulo 36
              «El fallo del plan» — enfrentamiento final con Voldemort.

RULES:
  1. One bullet per book cited. If several chapters of the same book are
     relevant, include one bullet per chapter.
  2. Use the EXACT canonical titles from the timeline above (don't translate
     a title — pick the ES or EN title matching the reply language).
  3. Prefer chapter number + name; if the chapter is unknown, state the
     scene/event (e.g., "Battle of Hogwarts").
  4. If a claim is NOT backed by `retrieve` results, mark the citation with
     "(general canon)" / "(canon general)" instead of inventing a chapter.
  5. Never omit the References block on factual answers. It is the closing
     signature of the Sorting Hat.
"""


# ── System prompt builder ─────────────────────────────────────────────────────


def build_system_prompt(config: Config) -> str:
    """Build CRAFTY's Sorting Hat system prompt.

    Encodes the workshop criteria plus **mandatory per-book citations**
    in the user's language (ES/EN).
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
• If it is SPANISH → answer ENTIRELY in Spanish (incl. the References block).
• If it is ENGLISH → answer ENTIRELY in English (incl. the References block).
• Never mix languages in one reply (proper nouns excepted).
• Keep the Sorting Hat voice in BOTH languages.

═══════════════════════════════════════════════════════════════════════════
  TOOLS
═══════════════════════════════════════════════════════════════════════════
• ALWAYS call the `retrieve` tool before asserting specific facts about
  plot, characters, spells, or dates.
• Use retrieved passages to fill in chapter names, scenes, and short quotes
  that will feed the References block.

═══════════════════════════════════════════════════════════════════════════
  CHRONOLOGICAL AWARENESS
═══════════════════════════════════════════════════════════════════════════
{HARRY_POTTER_TIMELINE}
• Always place facts in their correct book and in-universe year.
• Respect the timeline: if the user scopes a question to an earlier book,
  do not leak spoilers from later books (and do not cite later books).
• When a thread spans several books (Horcruxes, Snape's arc, the Prophecy,
  Sirius, the Deathly Hallows…), RELATE the books and SYNTHESIZE the arc,
  then cite EACH relevant book in the References block.

═══════════════════════════════════════════════════════════════════════════
  ANSWER STRUCTURE (MANDATORY)
═══════════════════════════════════════════════════════════════════════════
Every factual reply MUST follow this shape:

  1. ✨ Opening flourish (1 short line, Sorting Hat voice).
     EN: "Ahhh, another curious mind…"
     ES: "Ahhh, otra mente curiosa…"

  2. 🧩 Core answer — structured as: fact → book(s) → connection.
     Inline-mark each claim with a book tag, e.g. "[Book 3]" / "[Libro 3]".

  3. 🔗 Cross-book synthesis (only if the topic spans multiple books):
     a short paragraph linking the arc from earliest to latest book.

  4. 🎓 Closing reflection (1 line, optionally a nod to a Hogwarts house).

  5. 📚 References / Referencias — the citation block (see spec below).
     This block is REQUIRED on any answer containing canonical facts.

═══════════════════════════════════════════════════════════════════════════
  {CITATION_BLOCK_SPEC}
═══════════════════════════════════════════════════════════════════════════

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
