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

There are **two identities** in this workshop and you only deal with one of them:

### 1. Your team's identity — IAM Identity Center (you)

Your team representative gives the facilitator one email address. Each team gets a single user in **AWS IAM Identity Center**. Sign-in flow:

1. Check your inbox for an *"Invitation to join AWS"* email from `no-reply@signin.aws`.
2. Click the link, set your password, complete MFA setup.
3. You'll land on a personal **AWS access portal** (`https://d-xxxxxxxxxx.awsapps.com/start`).
4. Click the workshop account → choose the **`WorkshopOnlyAccess`** role → AWS Console opens.

That's it. You're in. **No CLI setup, no access keys, no terminal authentication.** The Identity Center session lasts 8 hours by default; renew by going back to the access portal.

### 2. The pipeline's identity (managed by the facilitator)

GitHub Actions assumes an IAM role (`cloudcrafters-workshop-pipeline`) via **GitHub OIDC** — no static keys, no secrets to rotate, just short-lived federated tokens minted on each workflow run. The role's trust policy is scoped to this repo, so workflows in other repos can't borrow it. You never see or use this — it exists so the pipeline can apply your branch's changes without you needing AWS credentials of your own.

## Quick start

> **No local setup required.** You can do the entire workshop from your browser: edit code on GitHub, watch the pipeline deploy, and test the agent in the AWS Console. Skip to **Optional: local development** at the bottom if you'd rather use a real editor + CLI.

### Prerequisites
- A modern browser
- The IAM Identity Center invite from the facilitator (see [Authentication](#authentication))
- Your GitHub account added as a collaborator to the repo

### Your 7 team branches

Each team has a branch named after them. There are 7 teams (4 Hogwarts houses + 3 wizarding locations):

```
gryffindor   slytherin   ravenclaw   hufflepuff
hogsmeade    diagon      gringotts
```

The branch name **is** your `team_id` — every AWS resource the pipeline creates will be named after it.

### 1. Find your team's branch on GitHub

Open <https://github.com/CloudCraftersOrg/crafting-2026-internal-workshop> and use the branch dropdown to switch to your team (e.g. `gryffindor`).

### 2. Edit a file in the GitHub web UI

Click any file (`app/src/workshop_agent/agent.py` is the most useful starting point), then click the ✏️ pencil icon, top-right. Make your change. At the bottom of the page, **commit directly to your team's branch**.

### 3. Watch the pipeline deploy

Open the **Actions** tab — you'll see a "Deploy team infra" run kick off automatically.
- First deploy on a fresh branch: ~5–8 minutes (Docker build + KB ingestion)
- Subsequent deploys: usually ~2–3 minutes

When it finishes, the workflow posts a commit comment with your team's deployment IDs (runtime ARN, KB ID, memory ID).

### 4. Test the agent in the AWS Console

Sign in via the Identity Center portal and go to:

> **Bedrock AgentCore → Runtimes** → click `workshop_agent_<your-team>` → **Sessions / Test**

Type a prompt (e.g. *"What did Harry use to sneak around Hogwarts at night?"*) and hit enter. The agent answers from the Knowledge Base, with citations.

You can also browse logs at **CloudWatch → Log groups → `/aws/bedrock-agentcore/runtimes/workshop_agent_<your-team>-DEFAULT`** to see what tool the agent called and why.

### Iterate

1. Change `agent.py` in the GitHub web UI → commit
2. Wait for the pipeline (Actions tab)
3. Re-test in the AWS Console
4. Repeat

That's the full loop. No clone, no Python venv, no `terraform apply`, no Docker.

---

### Optional: local development

If you'd rather use your own editor and a CLI, you can also clone the repo and use `invoke_agent.py` to talk to the deployed runtime. You'll need:

- Python ≥ 3.12 and `uv`
- AWS CLI v2 with SSO configured against the workshop account

```bash
# One-time setup
git clone https://github.com/CloudCraftersOrg/crafting-2026-internal-workshop.git
cd crafting-2026-internal-workshop
git checkout <your-team-branch>

cd app
pip install uv
uv venv && source .venv/bin/activate
uv pip install -e .

# Configure AWS SSO (one-time)
aws configure sso          # use the start URL the facilitator provides

# Refresh creds when needed
aws sso login --profile <your-profile>
export AWS_PROFILE=<your-profile>

# Populate app/.env (see below), then:
python invoke_agent.py --interactive
```

#### Populating `app/.env`

`cp .env.example .env` first, then fill in the per-team values.

**Easiest:** the deploy pipeline posts a ready-to-paste env block as a commit comment after each successful run. Open the **Actions** tab, click your team's most recent green run, follow the link to the triggering commit, and copy the env block from the bottom comment.

**Alternative — pull each value from the AWS Console** (handy when you can't find the commit comment, or after a destroy + redeploy):

| Variable | Where to find it in the console |
|---|---|
| `AWS_REGION` | Always `us-east-1` for this workshop |
| `MODEL_ID` | Use the default already in `.env.example` (`us.anthropic.claude-sonnet-4-6`) unless you've changed it on your branch |
| `MEMORY_ID` | **Bedrock → AgentCore → Memory** → click `workshop_agent_<your-team>_memory` → copy the *Memory ID* (looks like `workshop_agent_<team>_memory-xxxxxxxxxx`) |
| `MEMORY_ACTOR_ID` | Your team name (e.g. `gryffindor`). This is just a string namespace — you choose it. |
| `KNOWLEDGE_BASE_ID` | **Bedrock → Knowledge Bases** → click `workshop_agent_<your-team>_harry_potter_kb` → copy the *Knowledge base ID* (10-char alphanumeric) |
| `AGENT_RUNTIME_ARN` | **Bedrock → AgentCore → Runtimes** → click `workshop_agent_<your-team>` → copy the *Runtime ARN* from the Details panel |

Edit code locally, commit + push, the pipeline still does the deploy.

## Multi-team deployments

The 7 teams share **one** AWS account. Each team's branch has its own GitHub Environment with its own AWS access keys, its own Terraform state file, and its own set of named resources.

### Naming and tagging per team

Every resource Terraform creates includes the team name in its identifier and its AWS tags.

| Resource | Naming pattern (with branch / team `gryffindor`) |
|---|---|
| AgentCore runtime | `workshop_agent_gryffindor` |
| AgentCore Memory | `workshop_agent_gryffindor_memory` |
| Knowledge Base | `workshop_agent_gryffindor_harry_potter_kb` |
| S3 Vectors bucket | `workshop-agent-gryffindor-vec-<account_id>` |
| S3 Vectors index | `harry-potter` (scoped within the team's vector bucket) |
| S3 source bucket | `workshop-agent-gryffindor-kb-<account_id>` |
| ECR repo | `workshop-agentcore-gryffindor` |
| IAM roles | `workshop_agent_gryffindor_runtime_role`, `workshop_agent_gryffindor_kb_role` |
| CloudWatch log group | `/aws/bedrock-agentcore/workshop_agent_gryffindor` |

Every resource is also tagged:

```
Project   = cloudcrafters-workshop
Workshop  = build-together-el-workshop
Team      = <team_id>
ManagedBy = terraform
```

### Pipeline architecture

| | |
|---|---|
| **Push to a team branch** | Triggers `.github/workflows/deploy.yml` → `terraform apply -var="team_id=<branch>"` with state at `s3://cloudcrafters-workshop-2026-tfstate/workshop-2026/<branch>/terraform.tfstate` |
| **Push to `main`** | Triggers `.github/workflows/validate.yml` only (`terraform validate`, `terraform fmt -check`, Python compile) — no deploy |
| **Manual destroy** | `.github/workflows/destroy.yml` via the **Actions** tab, takes a `team_id` input + a confirmation string |

### Cost tracking and cleanup

- **Per-team spend:** AWS Cost Explorer → filter by tag `Team = <team_id>`
- **Cleanup after the workshop:** facilitator triggers the **Destroy team infra** workflow once per team
- **Orphan check:** `aws resourcegroupstaggingapi get-resources --tag-filters Key=Project,Values=cloudcrafters-workshop` should return empty post-cleanup

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
