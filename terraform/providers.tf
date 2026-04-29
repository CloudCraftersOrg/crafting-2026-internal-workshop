#######################################################################
# File: providers.tf
#
# Description:
#   Declares the Terraform version constraint and configures the AWS
#   provider with the deployment region. No backend is configured;
#   state is stored locally for this proof-of-concept.
#
# Notes:
#   - AWS provider >= 6.17.0 is required for the
#     aws_bedrockagentcore_agent_runtime resource type.
#   - S3 Vectors resources (aws_s3vectors_*) require AWS provider >= 6.x.
#######################################################################

# Pins Terraform and provider versions to ensure reproducible applies
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.1"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.4"
    }
  }

  # Store Terraform state remotely with encryption and native file locking
  backend "s3" {
    bucket  = "cloudcrafters-workshop-2026-tfstate"
    key     = "workshop-2026/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

# Targets all resources to the region defined by the region variable.
# default_tags applies to every taggable AWS resource — used for cost
# attribution per team and quick teardown queries.
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "cloudcrafters-workshop"
      Workshop  = "build-together-el-workshop"
      Team      = var.team_id
      ManagedBy = "terraform"
    }
  }
}
