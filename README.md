<p align="center">
  <img src="assets/branding/cloudcrafters-logo.png" alt="CloudCrafters" width="220"/>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/branding/bal-logo.png" alt="Business Analysis LATAM Community" width="220"/>
</p>

# Build Together: El Workshop

> A collaboration between **CloudCrafters** and the **Business Analysis LATAM Community**.

A 2-hour build-and-pitch workshop. Each team gets the same Bedrock + AgentCore baseline (CRAFTY — a Harry Potter Q&A agent over a Bedrock Knowledge Base), extends it for the assigned challenge, and pitches the result.

## Table of Contents

1. [The challenge — HORROCRUXES](#the-challenge--horrocruxes)
2. [What you have on day one](#what-you-have-on-day-one)
3. [Difficulty tiers and sample queries](#difficulty-tiers-and-sample-queries)
4. [Validity criteria](#validity-criteria)
5. [Differentiators](#differentiators)
6. [Wow factor](#wow-factor)
7. [Bonus tracks](#bonus-tracks)
8. [What you pitch](#what-you-pitch)
9. [Persona — CRAFTY](#persona--crafty)
10. [Architecture](#architecture)
11. [Authentication](#authentication)
12. [Quick start](#quick-start)
13. [Multi-team deployments](#multi-team-deployments)
14. [Project structure](#project-structure)
15. [Where to extend](#where-to-extend)
16. [Commands reference](#commands-reference)
17. [Cost estimate](#cost-estimate)
18. [FAQ](#faq)
19. [Resources & contact](#resources--contact)

---

## The challenge — HORROCRUXES

**A multi-agent system for answering questions about the Harry Potter saga.**

Design and build **HORROCRUXES**: an intelligent multi-agent system capable of responding to complex queries in natural language about the seven Harry Potter books — from specific facts in a single chapter to cross-book analysis, character relationships, timelines, and thematic reasoning.

Every answer must be backed by real data from the knowledge corpus and include accurate citations to its sources.

You start from **CRAFTY**, a single-agent baseline that already answers basic Harry Potter questions over a Bedrock Knowledge Base. From there, you decide how to grow it.

## What you have on day one

| Provided | Where |
|---|---|
| Deployed Bedrock AgentCore runtime | `terraform/agentcore.tf` |
| Persistent agent memory (per-team isolation via `MEMORY_ACTOR_ID`) | `terraform/memory.tf` |
| Bedrock Knowledge Base seeded with the 7 HP PDFs | `terraform/knowledge_base.tf` + `assets/books/` |
| `CRAFTY` baseline agent — system prompt, retrieve tool, citations | `app/src/workshop_agent/agent.py` |
| Local CLI (`workshop-agent`) and remote invoker (`invoke_agent.py`) | `app/` |

## Difficulty tiers and sample queries

**Tier 1 — Basic (specific search):**

> *Q: What did Harry use to sneak around Hogwarts at night?*
>
> A: Harry used the Invisibility Cloak, an anonymous Christmas gift in his first year — later revealed as one of the Deathly Hallows, inherited from his father James Potter.
> *Reference: Philosopher's Stone, Ch. 12 "The Mirror of Erised."*

**Tier 2 — Intermediate (cross-book synthesis):**

> *Q: What are all of Voldemort's Horcruxes, in which book is each one discovered, and how was each destroyed?*
>
> A (excerpt): Tom Riddle's diary — *Chamber of Secrets*, Ch. 17, destroyed by Harry with a basilisk fang. Marvolo Gaunt's ring — *Half-Blood Prince*, Ch. 23, destroyed by Dumbledore with Gryffindor's sword. (…)
> *References: HBP Ch. 23 (Dumbledore's revelation), DH Ch. 6 (search plan).*

**Tier 3 — Complex (analysis & synthesis):**

> *Q: Compare the evolution of Snape and Draco Malfoy throughout the saga. At what key moments do their paths diverge from Voldemort's?*
>
> A (excerpt): Both characters operate under pressure from the dark side, but their arcs diverge significantly. Snape's loyalty to Dumbledore originates in *Deathly Hallows* Ch. 33 "The Prince's Tale". Draco's turning point is his inability to kill Dumbledore in *Half-Blood Prince* Ch. 27 "The Lightning-Struck Tower". (…)

**Tier 4 — Structured + narrative:**

> *Q: What spells does Hermione use in Prisoner of Azkaban? Which spell does she use most often across the whole series?*
>
> A (excerpt): In PoA — Riddikulus (Ch. 7, Lupin's boggart class), Lumos (Ch. 16), … . Across the series, the most-used spell is "Petrificus Totalus" / "Obliviate" (…)
> *References: PoA Ch. 7, 16; cross-analysis across all 7 books.*

## Validity criteria

To qualify for judging, the system must:

- Accept natural-language queries at all four tiers above.
- Return answers grounded in retrieved evidence (no fabrication).
- Cite sources for every factual claim (book + chapter, or as close as the retrieved metadata allows).
- Use the **7 HP books** as the unstructured corpus, plus **at least one structured source** (CSV, JSON, table, or similar) the team brings in.
- Be reachable via a runnable interface (local CLI, web UI, API — anything live the team can demo).

## Differentiators

Pick any combination — the more you ship, the higher the score:

- **Multi-agent orchestration** — a coordinator agent that dynamically delegates to specialists based on the query type.
- **Verification agent** — a second agent that cross-checks claims between retrieved passages and flags contradictions or stale information.
- **Conversational memory across sessions** — answers in turn 5 reference what was said in turn 1 of an earlier session. *Hint: `app/src/workshop_agent/memory.py` already has `save_turn` / `recall_session` / `summarize_session`. The baseline never calls `save_turn` from the REPL — wiring it in `cli.py` is most of this differentiator.*
- **RAG evaluation metrics** — implement faithfulness, relevance, and (where applicable) numerical correctness scoring on responses.
- **Structured-data reasoning** — beyond retrieval, the system can filter, sort, aggregate, and compare tabular data.

## Wow factor

- **Report generation** — produce a structured report (PDF/Markdown) summarizing a multi-step research session.
- **Data visualization** — generate charts/graphs from tabular data when it would help the answer.
- **Complex reasoning agent** — multi-step reasoning that combines data from multiple sources to reach a single conclusion (simulation, cross-comparison, informed recommendation).
- **Observability dashboard** — live view of agent latency, token usage, tool calls, traces.
- **Free creative feature** — anything else the team can justify as valuable.

## Bonus tracks

Smaller, well-scoped wins on top of the core build. Pick one or two:

| Track | What it is | Why judges care |
|---|---|---|
| **Eval harness** | A test set of 8–12 canonical Q&A pairs + a script that scores precision, recall, and citation accuracy on every model run. | Engineering rigor; quantifies improvement turn over turn. |
| **Chat UI** | A Streamlit / Gradio front-end wrapping the agent — non-technical viewers can play with it during the pitch. | Demo-friendly; raises the production polish of the pitch. |
| **Cost & latency dashboard** | Log token counts and turn duration; render as a CloudWatch dashboard or a simple Streamlit chart. | Shows production-thinking — tokens cost money. |
| **Bilingual EN ↔ ES** | Detect input language and answer in kind, while keeping citations in the original (English) source. | Genuine internationalization angle, easy win, looks great in a pitch. |
| **Caching layer** | In-memory or Redis cache for repeated queries / embeddings; show savings vs uncached. | Production thinking with a visible cost delta. |

## What you pitch

A 5-minute demo + 3-minute Q&A. Cover:

1. **What you built** — architecture in one slide; what's CRAFTY's role vs. what you added.
2. **Live answers** — at least one query per tier (basic, intermediate, complex, structured), preferably end-to-end with citations visible.
3. **Why your approach wins** — which differentiators / bonus tracks you implemented and why.
4. **Limitations and what's next** — honest. Judges respect "we know X is weak; here's how we'd fix it."

## Persona — CRAFTY

CRAFTY is deliberately minimal: it answers Harry Potter questions using the Bedrock Knowledge Base via the `retrieve` tool and cites the source book/chapter. The full system prompt lives in `app/src/workshop_agent/agent.py::build_system_prompt`. Teams are expected to extend it (extra tools, multi-agent orchestration, verification, etc.) per the differentiators above.

---

## Architecture

```
              ┌──────────────────────┐
              │   assets/books/*     │
              │   (7 HP PDFs)        │
              └──────────┬───────────┘
                         │ terraform apply
                         ▼
┌─────────────────────────────────────────────┐
│  S3 source bucket  ──►  Bedrock Knowledge   │
│                         Base (vector index  │
│                         on Amazon S3        │
│                         Vectors)            │
└─────────────────────────────────────────────┘
                         ▲
                         │ retrieve(text=…)
                         │
┌─────────────────────────────────────────────┐
│  CRAFTY Agent (Strands SDK)                 │
│  • Bedrock model (Claude / Nova)            │
│  • retrieve  — KB Q&A with citations        │
│  • AgentCore Memory (per-actor isolation)   │
└──────────┬──────────────────────────────────┘
           │
   ┌───────┴────────┐
   ▼                ▼
Local CLI       AgentCore container
(cli.py)        (server.py, arm64 in ECR)
```

## Authentication

Both Terraform and the Python agent use the standard AWS credential chain — env vars, then `AWS_PROFILE`, then `~/.aws/credentials`. Either of the paths below works for everything in this repo (`terraform apply`, `workshop-agent`, `invoke_agent.py`).

### Static IAM access keys (workshop attendees)

Drop your keys into `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
region = us-east-1
```

Or export them as env vars (per-shell):

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
```

Nothing else to do — Terraform and boto3 pick these up automatically.

### AWS SSO (alternative for organizations using IAM Identity Center)

```bash
aws configure sso              # one-time setup
aws sso login --profile yours  # refresh the session as needed
export AWS_PROFILE=yours
```

Same applies — every tool in this repo respects `AWS_PROFILE`.

## Quick start

### Prerequisites
- Terraform ≥ 1.5.0
- AWS CLI v2 with credentials configured (see [Authentication](#authentication) above)
- Docker ≥ 24 with `buildx` (for the arm64 image build)
- Python ≥ 3.12 and `uv`

### 1. Deploy infrastructure

Every team picks a short, lowercase **`team_id`** (e.g. `alpha`, `team-01`, `bal-1`). All AWS resources include the ID in their name and tags so multiple teams can share one AWS account without collisions.

```bash
cd terraform/
terraform init
terraform plan  -var="team_id=alpha"      # preview
terraform apply -var="team_id=alpha"      # builds + pushes the container, provisions everything,
                                          # uploads books to S3, kicks off ingestion job
```

`terraform apply` outputs the resource IDs you'll need next:

```bash
terraform output -json
```

> **Tip:** to avoid passing `-var` every time, drop a `terraform.tfvars` file (gitignored) into `terraform/` with `team_id = "alpha"`.

### 2. Configure local env

```bash
cd ../app
cp .env.example .env
```

Fill the values from `terraform output` — see the env-var table in [`app/README.md`](app/README.md#environment-variables).

### 3. Install + run

```bash
pip install uv
uv venv && source .venv/bin/activate
uv pip install -e .

# Local CLI (talks to Bedrock + KB directly)
workshop-agent

# Or hit the deployed AgentCore runtime
python invoke_agent.py --interactive
```

### 4. Verify

Try one query from each tier ([sample queries above](#difficulty-tiers-and-sample-queries)). On out-of-corpus questions (e.g. *"Who is the captain of the Holyhead Harpies in 2025?"*) CRAFTY should refuse cleanly rather than invent.

## Multi-team deployments

Multiple teams can share **one** AWS account by giving each one a different `team_id`. Every resource Terraform creates includes that ID in its name and in its AWS tags.

| Resource | Naming pattern (with `team_id = alpha`) |
|---|---|
| AgentCore runtime | `workshop_agent_alpha` |
| AgentCore Memory | `workshop_agent_alpha_memory` |
| Knowledge Base | `workshop_agent_alpha_harry_potter_kb` |
| S3 Vectors bucket | `workshop-agent-alpha-vec-<account_id>` |
| S3 Vectors index | `harry-potter` (scoped within the team's vector bucket) |
| S3 source bucket | `workshop-agent-alpha-kb-<account_id>` |
| ECR repo | `workshop-agentcore-alpha` |
| IAM roles | `workshop_agent_alpha_runtime_role`, `workshop_agent_alpha_kb_role` |
| CloudWatch log group | `/aws/bedrock-agentcore/workshop_agent_alpha` |

Every resource is also tagged with:

```
Project   = cloudcrafters-workshop
Workshop  = build-together-el-workshop
Team      = <team_id>
ManagedBy = terraform
```

**Cost tracking by team:** in AWS Cost Explorer, filter by tag `Team = <team_id>` to see per-team spend.

**Each team has their own terraform state.** Either:
- Each team forks the repo and configures their own state backend, or
- The facilitator runs `terraform apply -var="team_id=<id>"` per team from a single workstation, swapping state files between runs.

For the workshop where the facilitator drives all deploys, the latter is simpler: keep one state file per team in S3 (different keys like `workshop-2026/<team_id>/terraform.tfstate`).

**Cleanup after the workshop:** `cd terraform && terraform destroy -var="team_id=<id>"` per team. Teams that share an account can run `aws resourcegroupstaggingapi get-resources --tag-filters Key=Team,Values=<id>` to confirm everything's gone.

## Project structure

```
crafting-2026-internal-workshop/
├── README.md                         ◄ you are here
│
├── assets/                           workshop sources (committed, ~35 MB)
│   ├── branding/                     CloudCrafters + Business Analysis LATAM logos
│   └── books/                        the 7 HP PDFs (auto-uploaded to S3 on apply)
│
├── terraform/                        infrastructure as code
│   ├── agentcore.tf                  runtime + endpoint
│   ├── memory.tf                     AgentCore Memory + summarization strategy
│   ├── knowledge_base.tf             KB, S3 Vectors bucket + index, S3 + book objects, ingestion
│   ├── iam.tf                        runtime + KB roles
│   ├── ecr.tf                        container registry
│   ├── docker.tf                     content-addressed arm64 image build
│   ├── cloudwatch.tf                 audit log group
│   ├── locals.tf, variables.tf, outputs.tf, providers.tf
│   └── README.md
│
└── app/                              Python application
    ├── pyproject.toml
    ├── Dockerfile
    ├── invoke_agent.py               talk to the deployed runtime
    ├── scripts/
    │   └── run_local.sh
    ├── src/workshop_agent/
    │   ├── agent.py                  CRAFTY system prompt + agent factory  ◄ extend here
    │   ├── server.py                 FastAPI entry point for AgentCore container
    │   ├── cli.py                    interactive REPL
    │   ├── config.py                 env-var loading
    │   ├── memory.py                 AgentCore Memory wrapper
    │   ├── export.py                 session bundle export
    │   └── logging.py                JSON structured logs
    └── README.md
```

## Where to extend

CRAFTY is intentionally minimal — one tool (`retrieve`), one persona, one corpus. Teams extend it from there. The two files you'll touch most:

| File | What to change |
|---|---|
| `app/src/workshop_agent/agent.py` | `build_system_prompt()` (refine persona / response format) and `create_agent()` (add tools, multi-agent orchestration) |
| `app/src/workshop_agent/server.py` | Mirror tool-list changes here so the deployed runtime gets them too |

Each extension is a standard `terraform apply` away once you've edited the source files (the Docker image rebuild is content-addressed and only fires when source changes).

## Commands reference

### Local CLI

```bash
workshop-agent                                     # start the REPL
workshop-agent --model us.amazon.nova-pro-v1:0     # override model for the session
workshop-agent --export-dir ./out                  # change export bundle location
```

### Slash commands during a session

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/reset` | Clear conversation, start a new session |
| `/summarize` | Summarize the current session from AgentCore Memory * |
| `/recall <sessionId>` | Reload a previous session * |
| `/export` | Write a session bundle to `./exports/` |
| `/quit`, `/exit`, `/q` | Exit |

\* Requires persisting turns to AgentCore Memory — see the *Conversational memory across sessions* differentiator.

### Remote invoke (deployed runtime)

```bash
python invoke_agent.py --prompt "Who founded Hogwarts?"
python invoke_agent.py --interactive
python invoke_agent.py --interactive --export --export-dir ./out
```

### Terraform

```bash
terraform plan  -var="team_id=<id>"
terraform apply -var="team_id=<id>"
terraform output -json
terraform destroy -var="team_id=<id>"

# override variables on apply
terraform apply -var="team_id=<id>" -var="model_id=us.amazon.nova-pro-v1:0"

# force a rebuild without source changes
terraform apply -var="team_id=<id>" -var="image_tag=$(git rev-parse --short HEAD)"
```

## Cost estimate

Per workshop deployment, idle:

| Component | $/month | Notes |
|---|---|---|
| Bedrock model invocations | $1–10 | depends on usage; embedding + generation |
| AgentCore runtime | ~$50 | flat |
| AgentCore Memory | <$1 | low volume |
| S3 Vectors | <$1 | pay-per-use; ~7 PDFs ⇒ a few thousand vectors and a handful of queries during the workshop |
| ECR + S3 + CloudWatch | <$2 | storage + transfer |
| **Total** | **~$50–65** | per active deployment |

Run `terraform destroy -var="team_id=<id>"` when the workshop is done to stop AgentCore charges (S3 Vectors has no idle floor, but tearing it down keeps things tidy).

## FAQ

**Q: How do I change the model?**

```bash
terraform apply -var="team_id=<id>" -var="model_id=us.amazon.nova-pro-v1:0"
# or for one local session:
workshop-agent --model us.amazon.nova-pro-v1:0
```

**Q: Multiple teams sharing one AWS account?**

Each team uses a different `team_id`. AWS resources include the ID in their names; AWS tags include `Team=<id>` for cost attribution. See [Multi-team deployments](#multi-team-deployments).

**Q: Where do I see what the agent is thinking?**

Container logs:

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/<runtime-name>-DEFAULT --follow
```

Or set `DEBUG_MODE=true` for verbose local logging.

**Q: How do I add another data source to the KB?**

Add the file to `assets/books/` (or another folder under `assets/`) and run `terraform apply -var="team_id=<id>"`. The `aws_s3_object.book` resource picks up new files via `fileset()` and `null_resource.kb_ingest` re-triggers the Bedrock ingestion job.

**Q: The deployed agent fails with `RuntimeClientError` — where do I look?**

`/aws/bedrock-agentcore/runtimes/<runtime-name>-DEFAULT` and `…-<endpoint-name>` in CloudWatch. The container's Python tracebacks land there.

## Resources & contact

- **App development docs**: [`app/README.md`](app/README.md)
- **Infrastructure docs**: [`terraform/README.md`](terraform/README.md)
- **AWS Bedrock AgentCore**: <https://docs.aws.amazon.com/bedrock-agentcore/>
- **Strands Agents SDK**: <https://strandsagents.com/>
- **Owner**: CloudCrafters
- **Support during the workshop**: this is in-person — flag down anyone from CloudCrafters or the Business Analysis LATAM Community and they'll help.

---

<p align="center">
  <em>Build Together: El Workshop — CloudCrafters × Business Analysis LATAM</em>
</p>
