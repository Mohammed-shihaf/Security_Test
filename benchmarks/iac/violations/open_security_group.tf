# BENCHMARK ONLY — IAC-001 open ingress on non-web port (SSH from internet).
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_security_group" "benchmark_open_ssh" {
  name        = "benchmark-open-ssh"
  description = "Intentionally insecure fixture for Checkov/tfsec"

  ingress {
    description = "SSH open to world — benchmark violation"
    from_port   = 22
    to_port     = 22
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
