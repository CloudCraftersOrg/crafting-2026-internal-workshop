#!/usr/bin/env bash
# run_local.sh – Run the workshop agent CLI locally with required env vars
#
# Usage:
#   ./scripts/run_local.sh                     # interactive REPL
#   ./scripts/run_local.sh --model <model_id>  # one-off model override
#
# Reads variables from app/.env (auto-loaded) or from the current shell env.
#
# Required:
#   AWS_REGION         – e.g. us-east-1
#   MODEL_ID           – e.g. us.anthropic.claude-sonnet-4-6
#   MEMORY_ID          – AgentCore Memory resource ID (terraform output memory_id)
#   MEMORY_ACTOR_ID    – Actor namespace (e.g. your team_id)
#   KNOWLEDGE_BASE_ID  – Bedrock KB ID (terraform output knowledge_base_id)
#
# Optional:
#   MAX_RESULT_CHARS   – default 20000
#   DEBUG_MODE         – true/false

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── Load .env if it exists ──────────────────────────────────────────────────
ENV_FILE="${APP_DIR}/.env"
if [[ -f "${ENV_FILE}" ]]; then
  echo "📄  Loading environment from ${ENV_FILE}"
  # shellcheck disable=SC1090
  set -a; source "${ENV_FILE}"; set +a
fi

# ── Validate required vars ──────────────────────────────────────────────────
REQUIRED=(AWS_REGION MODEL_ID MEMORY_ID MEMORY_ACTOR_ID KNOWLEDGE_BASE_ID)
MISSING=()
for var in "${REQUIRED[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    MISSING+=("$var")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "❌  Missing required env vars:" >&2
  for v in "${MISSING[@]}"; do echo "    $v" >&2; done
  echo "" >&2
  echo "  Either:" >&2
  echo "    • Copy ${APP_DIR}/.env.example → .env and fill in values from 'terraform output'" >&2
  echo "    • Or export them in your shell: export AWS_REGION=us-east-1 etc." >&2
  exit 1
fi

# ── Activate the project venv if present ────────────────────────────────────
VENV_ACTIVATE="${APP_DIR}/.venv/bin/activate"
if [[ -f "${VENV_ACTIVATE}" ]]; then
  # shellcheck disable=SC1090
  source "${VENV_ACTIVATE}"
else
  echo "❌  Virtualenv not found at ${APP_DIR}/.venv" >&2
  echo "    First-time setup:" >&2
  echo "      pip install uv" >&2
  echo "      cd ${APP_DIR}" >&2
  echo "      uv venv && source .venv/bin/activate" >&2
  echo "      uv pip install -e ." >&2
  exit 1
fi

# ── Launch the CLI ──────────────────────────────────────────────────────────
echo "🚀  Starting Workshop Agent…"
echo "    Region   : ${AWS_REGION}"
echo "    Model    : ${MODEL_ID}"
echo "    KB       : ${KNOWLEDGE_BASE_ID}"
echo "    Actor    : ${MEMORY_ACTOR_ID}"
echo ""

cd "${APP_DIR}"
exec python -m workshop_agent "$@"
