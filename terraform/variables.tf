#######################################################################
# File: variables.tf
#
# Description:
#   Input variables for custom AI agents deployed on
#   AWS Bedrock AgentCore. Controls runtime identity, model selection,
#   container image lifecycle, and agent behaviour.
#
# Notes:
#   - AgentCore and ECR must reside in the same AWS region.
#   - The Memory resource is provisioned by memory.tf; its ID is passed
#     to the container automatically via agentcore.tf.
#######################################################################

# Controls which AWS region all resources are created in
variable "region" {
  type        = string
  description = "AWS region where AgentCore runtime and ECR repository are deployed."
  default     = "us-east-1"
}

# Drives resource naming and the AgentCore runtime identifier
variable "agent_name" {
  type        = string
  description = "Logical name for the AgentCore runtime, used to compose resource names."
  default     = "workshop_agent"
}

# Per-team suffix so multiple teams can deploy in the same AWS account
# without resource-name collisions. Must be short and lowercase to fit
# S3 / S3 Vectors naming rules (3-63 chars, lowercase alphanumeric or hyphens).
variable "team_id" {
  type        = string
  description = "Per-team suffix appended to all resource names. Use a short lowercase identifier like 'alpha', 'team-01', 'bal-1'."
  default     = "shared"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,15}$", var.team_id))
    error_message = "team_id must be 2-16 chars, lowercase alphanumeric or hyphens, starting with a letter."
  }
}

# Determines which Bedrock model the agent calls during the agentic loop
variable "model_id" {
  type        = string
  description = "Bedrock model or cross-region inference profile ID invoked by the container."
  default     = "us.anthropic.claude-sonnet-4-6"
}

# Identifies the ECR repository that stores the agent container image
variable "ecr_repo_name" {
  type        = string
  description = "Name of the ECR repository created to host the agent Docker image."
  default     = "workshop-agentcore"
}

# Pinning the image tag triggers a rebuild and runtime update on apply
variable "image_tag" {
  type        = string
  description = "Docker image tag built, pushed to ECR, and registered with AgentCore."
  default     = "latest"
}

# Prevents unbounded ECR storage growth by expiring old images automatically
variable "ecr_keep_last" {
  type        = number
  description = "Maximum number of images to retain in ECR before the lifecycle policy expires older ones."
  default     = 30
}

# Hard cap on serialised JSON bytes returned per tool result; keeps prompts
# within the model's context limit.
variable "max_result_chars" {
  type        = number
  description = "Hard cap (bytes) on the JSON returned per tool result. Matches the MAX_RESULT_CHARS env var read by the container."
  default     = 20000
}

# Scopes memories to a logical user or team to keep different users' histories isolated
variable "memory_actor_id" {
  type        = string
  description = "Actor ID that owns memories in the AgentCore Memory resource."
  default     = "workshop-team"
}

# Enables automatic summarisation of conversation turns so past sessions can be recalled concisely
variable "enable_memory_summarization" {
  type        = bool
  description = "When true, a SUMMARIZATION strategy is attached to the Memory resource using the runtime execution role."
  default     = true
}

# Balances recency with storage cost; 7 days is a reasonable retention window
variable "memory_event_expiry_days" {
  type        = number
  description = "Number of days before individual Memory events are automatically expired."
  default     = 7
}

# When set, the agent writes structured JSON audit logs to this existing CloudWatch
# Log Group in addition to stdout.  Leave empty to log to stdout only.
# The log group must already exist — Terraform does not create it.
variable "agent_log_group_name" {
  type        = string
  description = "Override for the CloudWatch Log Group name. Defaults to /aws/bedrock-agentcore/<agent_name> when empty."
  default     = ""
}

# 7 days covers the full workshop window plus a debug buffer afterwards.
variable "agent_log_retention_days" {
  type        = number
  description = "Retention period in days for the agent execution log group."
  default     = 7
}

