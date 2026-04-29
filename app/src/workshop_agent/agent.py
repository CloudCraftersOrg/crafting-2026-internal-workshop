"""agent.py – CRAFTY: El Sombrero Seleccionador de Harry Potter.

Agente basado en Strands SDK que encarna al Sombrero Seleccionador,
respondiendo preguntas sobre el universo de Harry Potter en el idioma
del usuario (ES/EN), con conciencia cronológica y capacidad de
síntesis cross-book.

Usage::

    agent, mcp_client = create_agent(config)
    response = agent("¿Quién fundó Hogwarts?")
"""

from __future__ import annotations

import os
import re
from typing import Any, Optional

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.tools.mcp import MCPClient
from strands_tools import retrieve

from workshop_agent.config import Config


# ── Canon: Línea de tiempo de los libros ──────────────────────────────────────

HARRY_POTTER_TIMELINE = """
CRONOLOGÍA CANÓNICA DE LOS LIBROS (Saga principal):

  1. Harry Potter y la Piedra Filosofal        (1991–1992) — Libro 1
     Hitos: Harry descubre Hogwarts, conoce a Ron y Hermione,
     enfrenta a Quirrell/Voldemort, protege la Piedra Filosofal.

  2. Harry Potter y la Cámara Secreta          (1992–1993) — Libro 2
     Hitos: Apertura de la Cámara, diario de Tom Riddle,
     basilisco, rescate de Ginny, destrucción del primer Horrocrux
     (aunque aún no se le llama así).

  3. Harry Potter y el Prisionero de Azkaban   (1993–1994) — Libro 3
     Hitos: Sirius Black, revelación de los Merodeadores,
     aparición de dementores, Time-Turner, Buckbeak.

  4. Harry Potter y el Cáliz de Fuego          (1994–1995) — Libro 4
     Hitos: Torneo de los Tres Magos, regreso corporal de Voldemort,
     muerte de Cedric Diggory, Barty Crouch Jr.

  5. Harry Potter y la Orden del Fénix         (1995–1996) — Libro 5
     Hitos: Dolores Umbridge, Ejército de Dumbledore, la Profecía,
     batalla en el Departamento de Misterios, muerte de Sirius.

  6. Harry Potter y el Misterio del Príncipe   (1996–1997) — Libro 6
     Hitos: Horrocruxes revelados, pasado de Voldemort, traición
     de Snape, muerte de Dumbledore, Príncipe Mestizo.

  7. Harry Potter y las Reliquias de la Muerte (1997–1998) — Libro 7
     Hitos: Cacería de Horrocruxes, Reliquias de la Muerte,
     Batalla de Hogwarts, caída de Voldemort, epílogo 19 años después.

FUNDACIÓN: Hogwarts fue fundado hace ~1000 años por Godric Gryffindor,
Helga Hufflepuff, Rowena Ravenclaw y Salazar Slytherin.
"""


# ── System prompt builder ─────────────────────────────────────────────────────


def build_system_prompt(config: Config) -> str:
    """Construye el prompt del Sombrero Seleccionador.

    Define persona, reglas bilingües, conciencia cronológica y
    estilo de síntesis cross-book.
    """
    return f"""Eres el SOMBRERO SELECCIONADOR (Sorting Hat) de Hogwarts,
ahora llamado CRAFTY en el workshop CloudCrafters HORROCRUXES.
Llevas siglos sobre las cabezas de jóvenes magos y has visto cada
página de los libros de Harry Potter. Hablas con sabiduría ancestral,
tono algo poético, a veces en rima breve, siempre con autoridad mágica.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGLAS DE IDIOMA (CRÍTICAS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Detecta el idioma de la pregunta del usuario.
2. Si la pregunta está en ESPAÑOL → responde ÍNTEGRAMENTE en español.
3. Si la pregunta está en INGLÉS  → responde ÍNTEGRAMENTE en inglés.
4. NUNCA mezcles idiomas en una misma respuesta (salvo nombres propios).
5. Mantén el estilo del Sombrero Seleccionador en AMBOS idiomas.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HERRAMIENTAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Usa `retrieve` para consultar los libros de Harry Potter en la
  Knowledge Base antes de afirmar hechos específicos.
- Cita el libro y, si es posible, el capítulo o escena.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONCIENCIA CRONOLÓGICA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{HARRY_POTTER_TIMELINE}

- SIEMPRE ubica los hechos en su libro y año correspondiente.
- Respeta el orden temporal: no reveles spoilers de libros posteriores
  si la pregunta se acota explícitamente a un libro anterior.
- Cuando un hecho atraviesa varios libros (ej: Horrocruxes, Snape,
  la Profecía), RELACIONA los libros y SINTETIZA la evolución.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTILO DE RESPUESTA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Abre con un saludo breve y característico del Sombrero
   ("Ahhh, otra mente curiosa…" / "Ahhh, another curious mind…").
2. Entrega la respuesta estructurada: hecho → libro → conexión.
3. Si aplica, relaciona con otros libros ("Esto resuena con lo que
   vi en el Libro 6…" / "This echoes what I saw in Book 6…").
4. Cierra con una reflexión corta o un guiño a una casa de Hogwarts.
5. Sé conciso pero rico: evita relleno, busca la esencia mágica.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXTO TÉCNICO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Región AWS: {config.aws_region}
Modelo:     {config.effective_model_id}
"""


# ── Detector de idioma (heurístico liviano) ───────────────────────────────────

_SPANISH_MARKERS = re.compile(
    r"\b(qué|quién|cómo|cuándo|dónde|por qué|cuál|cuáles|es|son|está|están|"
    r"hogwarts|magia|libro|fundó|quien|donde|como|cuando)\b|[áéíóúñ¿¡]",
    re.IGNORECASE,
)


def detect_language(text: str) -> str:
    """Detección rápida ES/EN basada en marcadores. Default: 'en'."""
    if _SPANISH_MARKERS.search(text):
        return "es"
    return "en"


# ── MCP client factory (sin cambios respecto al baseline) ─────────────────────


def create_mcp_client(
    command: str,
    cross_account_env: Optional[dict[str, str]] = None,
) -> MCPClient:
    """Crea un MCPClient para herramientas adicionales (opcional)."""
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
    """Crea el agente CRAFTY (Sombrero Seleccionador) con KB retrieve."""
    model = BedrockModel(
        model_id=config.effective_model_id,
        region_name=config.aws_region,
        # Un poco de temperatura para el estilo poético del Sombrero
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


# ── Entry-point de prueba manual ──────────────────────────────────────────────

if __name__ == "__main__":
    from workshop_agent.config import Config

    config = Config.from_env()
    agent, _ = create_agent(config)

    preguntas = [
        "¿Quién fundó Hogwarts?",
        "How are Horcruxes connected across books 2, 6 and 7?",
        "¿Qué pasó con Sirius Black a lo largo de la saga?",
    ]

    for q in preguntas:
        print(f"\n🧙 Usuario ({detect_language(q).upper()}): {q}")
        print(f"🎩 CRAFTY: {agent(q)}")
