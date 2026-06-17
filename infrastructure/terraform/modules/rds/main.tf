resource "aws_db_instance" "ipe" {
  identifier        = "ipe-${var.environment}"
  engine            = "postgres"
  engine_version    = "16.3"
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  db_name           = "ipe_${var.environment}"
  username          = "ipe"
  password          = var.db_password
  skip_final_snapshot = var.environment != "production"

  vpc_security_group_ids = [var.security_group_id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = { Name = "ipe-${var.environment}" }
}

resource "aws_db_subnet_group" "main" {
  name       = "ipe-${var.environment}"
  subnet_ids = var.subnet_ids
}

variable "environment" {}
variable "instance_class" { default = "db.t3.medium" }
variable "allocated_storage" { default = 100 }
variable "db_password" {}
variable "security_group_id" {}
variable "subnet_ids" { type = list(string) }
