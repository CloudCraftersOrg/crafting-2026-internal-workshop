#######################################################################
# File: memory.tf
#
# Description:
#   Provisions the AgentCore Memory resource that the workshop agent uses to
#   persist and recall context across sessions. The memory ID is passed
#   to the runtime as an environment variable so the agent can scope
#   retrieval and storage to the correct resource.
#
# Notes:
#   - When enable_memory_summarization is true, the runtime role is
#     reused as the memory execution role; its trust policy must allow
#     bedrock-agentcore.amazonaws.com to assume it.
#   - Only one SUMMARIZATION strategy is allowed per Memory resource.
#######################################################################

# Names composed from the agent name for all memory-related resources
locals {
  memory_resource_name = "${local.full_name_underscore}_memory"
  # Bedrock AgentCore caps strategy name at 48 chars; "_summary" keeps us under
  # even with the longest allowed team_id.
  memory_strategy_name = "${local.full_name_underscore}_summary"
}

# Persistent cross-session memory store for the workshop agent
resource "aws_bedrockagentcore_memory" "this" {
  name                  = local.memory_resource_name
  event_expiry_duration = var.memory_event_expiry_days

  # Reuse the runtime role so the Memory service can invoke Bedrock models during consolidation
  memory_execution_role_arn = local.runtime_role_arn
}

# Condenses stored conversation turns into summaries scoped per session under the actor namespace.
# SUMMARIZATION strategies require {sessionId} as a mandatory namespace placeholder so the
# service can partition summaries by session at consolidation time.
resource "aws_bedrockagentcore_memory_strategy" "summarization" {
  count       = var.enable_memory_summarization ? 1 : 0
  name        = local.memory_strategy_name
  memory_id   = aws_bedrockagentcore_memory.this.id
  type        = "SUMMARIZATION"
  description = "Condenses workshop agent conversation turns into summaries for efficient recall across sessions."
  namespaces  = ["${var.memory_actor_id}/{sessionId}"]
}
