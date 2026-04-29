#######################################################################
# File: agentcore.tf
#
# Description:
#   Defines the Bedrock AgentCore runtime that runs the workshop agent
#   container. Wires the ECR image, IAM execution role, and
#   environment configuration into a single deployable runtime unit.
#
# Notes:
#   - network_mode PUBLIC is required for the runtime to reach Bedrock
#     and external APIs without a VPC NAT gateway.
#   - Environment variables are the contract between Terraform inputs
#     and the Python agent running inside the container.
#######################################################################

# Runs the workshop agent container on AgentCore with Bedrock access
resource "aws_bedrockagentcore_agent_runtime" "this" {
  agent_runtime_name = local.full_name_underscore
  role_arn           = local.runtime_role_arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = local.image_uri
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  environment_variables = {
    AWS_REGION        = var.region
    MODEL_ID          = var.model_id
    MAX_RESULT_CHARS  = tostring(var.max_result_chars)
    MEMORY_ID         = aws_bedrockagentcore_memory.this.id
    MEMORY_ACTOR_ID   = var.memory_actor_id
    AGENT_LOG_GROUP   = aws_cloudwatch_log_group.agent_execution.name
    KNOWLEDGE_BASE_ID = aws_bedrockagent_knowledge_base.harry_potter.id
  }

  depends_on = [
    aws_iam_role_policy.runtime_inline,
    null_resource.docker_build_push,
    aws_bedrockagentcore_memory.this,
    aws_cloudwatch_log_group.agent_execution,
    aws_bedrockagent_knowledge_base.harry_potter,
  ]
}

# Exposes the runtime as an invocable endpoint for external integrations
resource "aws_bedrockagentcore_agent_runtime_endpoint" "this" {
  name             = "${local.full_name_underscore}_endpoint"
  agent_runtime_id = aws_bedrockagentcore_agent_runtime.this.agent_runtime_id
  description      = "Endpoint for programmatic invocation of the workshop agent"

  depends_on = [aws_bedrockagentcore_agent_runtime.this]
}