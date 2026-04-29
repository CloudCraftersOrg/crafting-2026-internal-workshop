#######################################################################
# File: knowledge_base.tf
#
# Description:
#   Amazon Bedrock Knowledge Base for Harry Potter content, backed by
#   an S3 source bucket (PDFs) and an Amazon S3 Vectors vector index.
#
# Usage:
#   1. terraform apply   — creates all resources below
#   2. Books in ../assets/books are auto-uploaded to the source bucket
#   3. null_resource.kb_ingest kicks off a Bedrock ingestion job which
#      embeds the chunks (Titan v2) and writes them to the S3 Vectors
#      index.
#
# Notes:
#   - S3 Vectors is the vector store (no idle floor, pay-per-use).
#     Replaces the previous OpenSearch Serverless collection.
#   - Bedrock KB manages the field mapping for S3 Vectors internally;
#     the integration only needs an index ARN with the right dimension
#     and distance metric.
#   - Runtime retrieve permissions are added in iam.tf.
#######################################################################

data "aws_caller_identity" "current" {}

locals {
  kb_name          = var.team_id
  kb_bucket_name   = "${local.full_name_dash}-kb-${data.aws_caller_identity.current.account_id}"
  kb_vector_bucket = "${local.full_name_dash}-vec-${data.aws_caller_identity.current.account_id}"
  kb_vector_index  = "harry-potter"
}

# ── S3 source bucket (PDFs) ──────────────────────────────────────────────────

resource "aws_s3_bucket" "kb_source" {
  bucket        = local.kb_bucket_name
  force_destroy = true

  tags = { Name = "${local.kb_name}-kb-source" }
}

resource "aws_s3_bucket_versioning" "kb_source" {
  bucket = aws_s3_bucket.kb_source.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ── S3 Vectors vector store ──────────────────────────────────────────────────

resource "aws_s3vectors_vector_bucket" "kb" {
  vector_bucket_name = local.kb_vector_bucket
  force_destroy      = true
}

# Vector index Bedrock KB writes embeddings into. Titan Embed Text v2 produces
# normalized 1024-dim vectors, so cosine distance is the conventional choice.
# AMAZON_BEDROCK_TEXT and AMAZON_BEDROCK_METADATA carry the chunk text and
# source metadata; marking them non-filterable keeps storage lean since we
# never filter by their contents.
resource "aws_s3vectors_index" "kb" {
  index_name         = local.kb_vector_index
  vector_bucket_name = aws_s3vectors_vector_bucket.kb.vector_bucket_name

  data_type       = "float32"
  dimension       = 1024
  distance_metric = "cosine"

  metadata_configuration {
    non_filterable_metadata_keys = [
      "AMAZON_BEDROCK_TEXT",
      "AMAZON_BEDROCK_METADATA",
    ]
  }
}

# ── IAM role for Knowledge Base ───────────────────────────────────────────────

resource "aws_iam_role" "kb_role" {
  name = "${local.full_name_underscore}_kb_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
      }
    }]
  })
}

resource "aws_iam_role_policy" "kb_inline" {
  name = "${local.full_name_underscore}_kb_inline"
  role = aws_iam_role.kb_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "S3Read"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = [aws_s3_bucket.kb_source.arn, "${aws_s3_bucket.kb_source.arn}/*"]
      },
      {
        Sid      = "BedrockEmbed"
        Effect   = "Allow"
        Action   = "bedrock:InvokeModel"
        Resource = "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v2:0"
      },
      {
        Sid    = "S3VectorsAccess"
        Effect = "Allow"
        Action = [
          "s3vectors:GetIndex",
          "s3vectors:ListIndexes",
          "s3vectors:PutVectors",
          "s3vectors:GetVectors",
          "s3vectors:QueryVectors",
          "s3vectors:DeleteVectors",
          "s3vectors:ListVectors",
        ]
        Resource = [
          aws_s3vectors_vector_bucket.kb.vector_bucket_arn,
          aws_s3vectors_index.kb.index_arn,
        ]
      },
    ]
  })
}

# ── Bedrock Knowledge Base ────────────────────────────────────────────────────

resource "aws_bedrockagent_knowledge_base" "harry_potter" {
  name     = "${local.full_name_underscore}_harry_potter_kb"
  role_arn = aws_iam_role.kb_role.arn

  knowledge_base_configuration {
    type = "VECTOR"

    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${var.region}::foundation-model/amazon.titan-embed-text-v2:0"
    }
  }

  storage_configuration {
    type = "S3_VECTORS"

    s3_vectors_configuration {
      index_arn = aws_s3vectors_index.kb.index_arn
    }
  }

  depends_on = [
    aws_iam_role_policy.kb_inline,
    aws_s3vectors_index.kb,
  ]
}

resource "aws_bedrockagent_data_source" "s3" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.harry_potter.id
  name              = "${local.full_name_underscore}_harry_potter_s3"

  data_source_configuration {
    type = "S3"

    s3_configuration {
      bucket_arn = aws_s3_bucket.kb_source.arn
    }
  }
}

# ── Source PDFs upload ───────────────────────────────────────────────────────
# Books live in ../assets/books and are uploaded on every apply. Re-uploads
# happen only when a file's hash changes, so steady-state applies are no-ops.

resource "aws_s3_object" "book" {
  for_each = fileset("${path.module}/../assets/books", "*.pdf")

  bucket      = aws_s3_bucket.kb_source.id
  key         = "books/${each.value}"
  source      = "${path.module}/../assets/books/${each.value}"
  source_hash = filemd5("${path.module}/../assets/books/${each.value}")
}

# ── Ingestion job ────────────────────────────────────────────────────────────
# Kick off a Bedrock KB ingestion every time the corpus changes.

resource "null_resource" "kb_ingest" {
  triggers = {
    book_hashes = jsonencode({ for k, v in aws_s3_object.book : k => v.source_hash })
    index_arn   = aws_s3vectors_index.kb.index_arn
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws bedrock-agent start-ingestion-job \
        --knowledge-base-id ${aws_bedrockagent_knowledge_base.harry_potter.id} \
        --data-source-id ${aws_bedrockagent_data_source.s3.data_source_id} \
        --region ${var.region} \
        --description "terraform-driven sync $(date -u +%Y%m%dT%H%M%SZ)"
    EOT
  }

  depends_on = [
    aws_s3_object.book,
    aws_bedrockagent_data_source.s3,
    aws_s3vectors_index.kb,
  ]
}
