# BENCHMARK ONLY — IAC-002 storage without encryption-at-rest definition.
resource "aws_db_instance" "benchmark_unencrypted" {
  identifier              = "benchmark-unencrypted"
  engine                  = "mysql"
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  username                = "admin"
  password                = "must-rotate-in-real-use"
  skip_final_snapshot     = true
  publicly_accessible     = false
  storage_encrypted       = false
}
