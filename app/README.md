# Workshop Agent — Application

`workshop-agent` is the Python package that powers CRAFTY, the Harry Potter Q&A agent for the HORROCRUXES challenge. It runs in two places:

- **Local CLI** (`cli.py`) — interactive REPL on your laptop, talks to Bedrock + KB directly.
- **AgentCore container** (`server.py`) — FastAPI server packaged into an arm64 image and deployed by Terraform.

Both share the same agent factory in `agent.py`. Built on the **Strands Agents SDK**, with **Bedrock** as the LLM and a **Bedrock Knowledge Base** for retrieval.

> **Back to root:** [../README.md](../README.md) | **Infrastructure:** [../terraform/README.md](../terraform/README.md)

## Table of Contents

1. [Local quick start](#local-quick-start)
2. [Environment variables](#environment-variables)
3. [Interactive commands](#interactive-commands)
4. [Where to extend](#where-to-extend)
5. [Invoke remote runtime](#invoke-remote-runtime)
6. [Build & push to ECR](#build--push-to-ecr)
7. [Source layout](#source-layout)
8. [Logging](#logging)
9. [Exported bundles](#exported-bundles)

## Local quick start

```bash
cd app/
pip install uv
uv venv && source .venv/bin/activate
uv pip install -e .

cp .env.example .env       # then fill in real values from `terraform output`
workshop-agent             # interactive CLI
```

Other run modes:

```bash
python -m workshop_agent                            # equivalent to `workshop-agent`
./scripts/run_local.sh                              # auto-sources .env
workshop-agent --model us.amazon.nova-pro-v1:0      # one-off model override
```

## Environment variables

### Required

| Variable | Source / value |
|---|---|
| `AWS_REGION` | `us-east-1` (matches the AgentCore runtime region) |
| `MODEL_ID` | Bedrock model ID, e.g. `us.amazon.nova-lite-v1:0` |
| `MEMORY_ID` | `terraform output memory_id` |
| `MEMORY_ACTOR_ID` | A short string per team (e.g. `team-alpha`); namespaces Memory |
| `KNOWLEDGE_BASE_ID` | `terraform output knowledge_base_id` |

### Required only for the remote-invoker

| Variable | Source / value |
|---|---|
| `AGENT_RUNTIME_ARN` | `terraform output agent_runtime_arn` |

### Optional

| Variable | Default | Description |
|---|---|---|
| `MAX_RESULT_CHARS` | `20000` | Soft cap on bytes returned per tool call |
| `DEBUG_MODE` | `false` | Set `true` for verbose structured logs |
| `AGENT_LOG_GROUP` | — | Override the CloudWatch log group used for audit logs |

### Example `.env`

```dotenv
AWS_REGION=us-east-1
MODEL_ID=us.amazon.nova-lite-v1:0
MEMORY_ID=workshop_agent_memory-xxxxxxxxxxxx
MEMORY_ACTOR_ID=workshop-team
MAX_RESULT_CHARS=20000
DEBUG_MODE=false
KNOWLEDGE_BASE_ID=XXXXXXXXXX

# For invoke_agent.py
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-1:111111111111:runtime/workshop_agent-xxxxxxxxxx
```

## Interactive commands

| Command | Description |
|---|---|
| `/help` | Show command reference |
| `/reset` | Clear conversation, start a new session |
| `/summarize` | Summarize the current session from AgentCore Memory |
| `/recall <sessionId>` | Reload a previous session by ID |
| `/export` | Write a session bundle to `./exports/` |
| `/quit`, `/exit`, `/q` | Exit |

## Where to extend

CRAFTY ships with a single tool (`retrieve` against the HP KB) and a focused system prompt. The HORROCRUXES challenge expects more. Common extensions:

### 1. Refine the system prompt

[`src/workshop_agent/agent.py`](src/workshop_agent/agent.py) → `build_system_prompt()`.

Tighten how CRAFTY structures answers (citation style, JSON-mode for downstream parsing, multi-step reasoning prompts, etc.).

### 2. Add a structured-data tool

The brief requires at least one structured source. Pick one:

- **Strands function tool** — write a `@tool`-decorated function that loads a CSV/JSON of characters, spells, horcruxes, etc. and exposes filter/sort/aggregate. Append it to `tools` in `create_agent()` (and the matching block in `server.py`).
- **MCP server** — uncomment the `create_mcp_client()` call in `create_agent()` and point the command at your server. Useful for SQL-backed sources or external APIs.

### 3. Multi-agent orchestration

Build a router agent that delegates to specialists (per book, per query type, per data source). Strands supports nested agents and tool-as-agent patterns.

### 4. Verification step

Add a second pass that cross-checks claims in the response against retrieved passages (or against a separate retrieval) and flags contradictions.

Make the same edit in `server.py` so the deployed runtime gets the change. After editing, `terraform apply` rebuilds and pushes the image (content-addressed, only fires when sources change).

## Invoke remote runtime

`invoke_agent.py` calls a deployed AgentCore runtime without running the container locally:

```bash
python invoke_agent.py --prompt "Who founded Hogwarts?"
python invoke_agent.py --interactive
python invoke_agent.py --interactive --export --export-dir ./out
```

`AGENT_RUNTIME_ARN` is resolved in this order:

1. `AGENT_RUNTIME_ARN` env var
2. `.env` in the current directory
3. `terraform output -json` (key: `agent_runtime_arn`)

## Build & push to ECR

`docker.tf` does this on every `terraform apply` when source files change. To force a rebuild without touching source, bump the `image_tag` variable: `terraform apply -var="image_tag=$(git rev-parse --short HEAD)"`.

Prerequisites: Docker ≥ 24 with `buildx`, AWS CLI v2 with ECR push permissions. AgentCore requires `linux/arm64` images.

## Source layout

```
src/workshop_agent/
├── __init__.py        package version
├── __main__.py        `python -m workshop_agent` entry point
├── cli.py             interactive REPL (Click + Rich)
├── agent.py           Strands Agent factory + CRAFTY system prompt
├── server.py          FastAPI HTTP server (AgentCore container entry point)
├── config.py          env-var loading and validation
├── memory.py          AgentCore Memory: save_turn, recall_session, summarize_session
├── export.py          session bundle export to JSON
└── logging.py         JSON structured logging → stdout (picked up by AgentCore)
```

## Logging

Every turn is logged as a JSON object to **stdout**, which AgentCore forwards to the runtime log group. Fields include `correlation_id`, `session_id`, `user_prompt`, `tool_calls`, `tool_outputs`, `final_answer`, `exceptions`.

To tail live:

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/<runtime-name>-DEFAULT --follow
```

## Exported bundles

`/export` (interactive) or `--export` (`invoke_agent.py`) writes a JSON bundle:

```json
{
  "session_id": "abc-123…",
  "timestamp": "2026-04-28T18:00:00Z",
  "memory_actor_id": "team-alpha",
  "model_id": "us.amazon.nova-lite-v1:0",
  "conversation_turns": [
    {"role": "user", "content": "…"},
    {"role": "assistant", "content": "…"}
  ],
  "tool_calls": [...]
}
```

Saved as `workshop-bundle-<session_id[:8]>-<timestamp>.json` under the export directory.
