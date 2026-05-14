# BENCHMARK ONLY — IAC-003 public-read bucket (legacy pattern; scanners flag variants).
resource "aws_s3_bucket" "benchmark_public" {
  bucket = "benchmark-public-bucket-terraform-metrics"
  acl    = "public-read"
}

resource "aws_s3_bucket_public_access_block" "benchmark_disabled" {
  bucket = aws_s3_bucket.benchmark_public.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}
