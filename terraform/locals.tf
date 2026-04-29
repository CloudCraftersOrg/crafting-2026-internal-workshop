#######################################################################
# File: locals.tf
#
# Description:
#   Derived values composed from variables and resource attributes.
#   All string interpolation and computed identifiers live here so that
#   resource arguments reference only local.* or var.* directly.
#
# Notes:
#   - full_name_underscore / full_name_dash are the canonical name
#     prefixes; every resource that needs a unique-per-team name
#     should compose itself from one of these, never from var.agent_name
#     directly.
#######################################################################

# Per-team name prefixes. AgentCore / IAM / Memory accept underscores;
# ECR / S3 / S3 Vectors require dashes. Both incorporate the team_id so
# two teams in the same AWS account can apply without collision.
locals {
  full_name_underscore = "${var.agent_name}_${var.team_id}"
  full_name_dash       = "${replace(var.agent_name, "_", "-")}-${var.team_id}"
}

# Container image reference built before it is registered with AgentCore
locals {
  image_uri    = "${aws_ecr_repository.agent.repository_url}:${var.image_tag}"
  ecr_registry = aws_ecr_repository.agent.repository_url
}

# IAM identifiers composed from the full underscore name prefix
locals {
  runtime_role_name          = "${local.full_name_underscore}_runtime_role"
  runtime_inline_policy_name = "${local.full_name_underscore}_runtime_inline"
  # :* suffix is required for CloudWatch Logs resource ARNs in IAM policies
  agentcore_log_arn = "arn:aws:logs:${var.region}:*:log-group:/aws/bedrock-agentcore/*:*"
  runtime_role_arn  = aws_iam_role.runtime.arn
}

# Log group name: use the operator-supplied value or fall back to the
# conventional /aws/bedrock-agentcore/<full_name> path.
locals {
  resolved_agent_log_group_name = var.agent_log_group_name != "" ? var.agent_log_group_name : "/aws/bedrock-agentcore/${local.full_name_underscore}"
}

# ECR lifecycle policy human-readable description
locals {
  ecr_lifecycle_description = "Keep last ${var.ecr_keep_last} images"
}
