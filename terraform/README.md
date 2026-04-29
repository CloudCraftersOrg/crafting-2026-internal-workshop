# Terraform — Infrastructure

Provisions all AWS resources for **Build Together: El Workshop** (CloudCrafters × Business Analysis LATAM): Bedrock AgentCore runtime, AgentCore Memory, a Bedrock Knowledge Base backed by Amazon S3 Vectors and seeded with the HP corpus, ECR, IAM, and CloudWatch.

> **Back to root:** [../README.md](../README.md) | **Application:** [../app/README.md](../app/README.md)

## Table of Contents

1. [Resources provisioned](#resources-provisioned)
2. [File layout](#file-layout)
3. [Prerequisites](#prerequisites)
4. [Usage](#usage)
5. [Variables](#variables)
6. [Outputs](#outputs)
7. [Notes](#notes)

## Resources provisioned

| Resource | File | Description |
|---|---|---|
| `aws_bedrockagentcore_agent_runtime` | `agentcore.tf` | AgentCore runtime running the container |
| `aws_bedrockagentcore_agent_runtime_endpoint` | `agentcore.tf` | Invocable endpoint for the runtime |
| `aws_bedrockagentcore_memory` | `memory.tf` | Persistent cross-session memory store |
| `aws_bedrockagentcore_memory_strategy` | `memory.tf` | SUMMARIZATION strategy (optional) |
| `aws_bedrockagent_knowledge_base.harry_potter` | `knowledge_base.tf` | Vector KB over the HP corpus |
| `aws_bedrockagent_data_source.s3` | `knowledge_base.tf` | S3 data source bound to the KB |
| `aws_s3vectors_vector_bucket.kb` | `knowledge_base.tf` | S3 Vectors bucket holding the KB's vector index |
| `aws_s3vectors_index.kb` | `knowledge_base.tf` | 1024-dim cosine vector index Bedrock writes embeddings into |
| `aws_s3_bucket.kb_source` | `knowledge_base.tf` | Source bucket for KB documents |
| `aws_s3_object.book` (×7) | `knowledge_base.tf` | Auto-uploads `assets/books/*.pdf` on every apply |
| `null_resource.kb_ingest` | `knowledge_base.tf` | Triggers `start-ingestion-job` whenever any book changes |
| `aws_ecr_repository` | `ecr.tf` | Registry for the arm64 image |
| `aws_ecr_lifecycle_policy` | `ecr.tf` | Retains the last N images |
| `null_resource.docker_build_push` | `docker.tf` | Builds & pushes the arm64 image when source files change |
| `aws_iam_role.runtime` (+ inline policy) | `iam.tf` | Execution role for the AgentCore runtime |
| `aws_iam_role.kb_role` (+ inline policy) | `knowledge_base.tf` | Role assumed by Bedrock for KB ingestion + retrieval |
| `aws_cloudwatch_log_group.agent_execution` | `cloudwatch.tf` | Audit log group consumed by the agent's structured logger |

## File layout

```
terraform/
├── agentcore.tf      runtime + endpoint, env vars
├── memory.tf         AgentCore Memory + summarization strategy
├── knowledge_base.tf KB, S3 Vectors bucket + index, S3 source bucket + book objects, ingestion trigger, kb_role
├── iam.tf            runtime IAM role + inline policy
├── ecr.tf            ECR repo and lifecycle policy
├── docker.tf         content-addressable Docker build + ECR push
├── cloudwatch.tf     audit log group
├── locals.tf         derived identifiers and composed strings
├── variables.tf      input variables
├── outputs.tf        exported identifiers for downstream use
└── providers.tf      Terraform version constraint and AWS provider
```

## Prerequisites

| Tool | Minimum version | Notes |
|---|---|---|
| Terraform | 1.5.0 | `tfenv` or direct download |
| AWS provider | 6.17.0 | Fetched automatically by `terraform init` |
| AWS CLI | v2 | Credentials must allow Bedrock, S3 Vectors, ECR, IAM, S3, CloudWatch |
| Docker | 24+ with `buildx` | Required for the arm64 image build in `docker.tf` |

AWS credentials must have permission to create the resources listed above. The local-exec provisioner in `null_resource.kb_ingest` calls `aws bedrock-agent start-ingestion-job` with the calling principal — make sure that principal has `bedrock:StartIngestionJob` on the KB.

## Usage

```bash
cd terraform/
terraform init
terraform plan
terraform apply           # builds container, provisions infra, uploads books, kicks off ingestion
terraform output -json    # values needed by app/.env
terraform destroy         # tear everything down
```

Useful overrides:

```bash
# Different region / model
terraform apply \
  -var="region=us-east-1" \
  -var="model_id=us.amazon.nova-pro-v1:0"

# Force a Docker rebuild without source changes
terraform apply -var="image_tag=$(git rev-parse --short HEAD)"
```

## Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `region` | `string` | `us-east-1` | AWS region for all resources |
| `agent_name` | `string` | `workshop_agent` | Logical project name; drives resource naming |
| `team_id` | `string` | `shared` | Per-team suffix appended to every resource name (must be 2-16 chars, lowercase). Lets multiple teams deploy in the same account. |
| `model_id` | `string` | `us.anthropic.claude-sonnet-4-6` | Bedrock model or cross-region inference profile |
| `ecr_repo_name` | `string` | `workshop-agentcore` | ECR repository name |
| `image_tag` | `string` | `latest` | Docker image tag built and registered |
| `ecr_keep_last` | `number` | `30` | Max images retained in ECR before expiry |
| `max_result_chars` | `number` | `20000` | Hard cap on bytes per tool result (passed as env var) |
| `memory_actor_id` | `string` | `workshop-team` | Default actor namespace for memory isolation |
| `enable_memory_summarization` | `bool` | `true` | Attach a SUMMARIZATION strategy to the Memory resource |
| `memory_event_expiry_days` | `number` | `7` | Days before Memory events expire automatically |
| `agent_log_group_name` | `string` | `""` | Override log group name. Defaults to `/aws/bedrock-agentcore/<agent_name>` |
| `agent_log_retention_days` | `number` | `7` | Retention period for the agent's audit log group |

(Refer to `variables.tf` if any of the above drift; that file is the source of truth.)

## Outputs

| Output | Description |
|---|---|
| `agent_runtime_arn` | ARN consumed by `invoke_agent.py` to call the runtime |
| `agent_runtime_endpoint_arn` | Endpoint ARN for programmatic invocation |
| `image_uri` | Exact ECR image URI registered with the AgentCore runtime |
| `ecr_repository_url` | ECR repository for further image pushes |
| `runtime_role_arn` | IAM role ARN assumed by the AgentCore runtime |
| `memory_id` | AgentCore Memory resource ID — set as `MEMORY_ID` in `app/.env` |
| `knowledge_base_id` | Bedrock KB ID — set as `KNOWLEDGE_BASE_ID` in `app/.env` |
| `kb_s3_bucket` | S3 source bucket name (where the books live) |
| `agent_execution_log_group` | CloudWatch log group consumed by the agent's structured logger |

Retrieve outputs after apply:

```bash
terraform output agent_runtime_arn
terraform output -json
```

## Notes

### arm64 requirement
AgentCore runtimes run on arm64 only. `docker.tf` passes `--platform linux/arm64` to `buildx`. Cross-compilation from x86 hosts requires QEMU (installed automatically by Docker Desktop on macOS/Windows).

### Content-addressable builds
`docker.tf` hashes the Dockerfile, `pyproject.toml`, and key source files as Terraform `triggers`. The image is rebuilt and pushed **only when those files change**, keeping repeat applies fast.

### KB ingestion
`null_resource.kb_ingest` re-runs `start-ingestion-job` whenever any `aws_s3_object.book` etag changes. To force a re-ingest without a content change, taint it:

```bash
terraform taint null_resource.kb_ingest && terraform apply
```

Initial ingestion of all 7 books takes 1–3 minutes after the first apply; check status with:

```bash
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $(terraform output -raw knowledge_base_id) \
  --data-source-id $(aws bedrock-agent list-data-sources --knowledge-base-id $(terraform output -raw knowledge_base_id) --query 'dataSourceSummaries[0].dataSourceId' --output text) \
  --max-results 3
```

### State backend
Backend configuration is in `providers.tf`. If you're running this in a fresh account or fork, point the S3 backend at a bucket your team can write to, then `terraform init -reconfigure`.

### Provider version
`aws_bedrockagentcore_agent_runtime` and `aws_bedrockagentcore_memory` require AWS provider **≥ 6.17.0**. Earlier versions fail with an unknown resource type error.
