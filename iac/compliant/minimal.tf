# Reference baseline — tighten further for your org (logging, versioning, KMS CMK, etc.).
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket" "private_logs" {
  bucket_prefix = "example-private-logs-"
}

resource "aws_s3_bucket_public_access_block" "private_logs" {
  bucket = aws_s3_bucket.private_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "private_logs" {
  bucket = aws_s3_bucket.private_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "private_logs" {
  bucket = aws_s3_bucket.private_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_security_group" "web_only" {
  name        = "example-web-only"
  description = "HTTP/HTTPS from internet only"

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
