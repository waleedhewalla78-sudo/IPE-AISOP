# IPE Production EKS — Terraform Configuration
# Apply when AWS credentials are available
# terraform init && terraform plan && terraform apply

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "ipe-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "production"
}

variable "cluster_name" {
  default = "ipe-prod-eks"
}

# VPC
resource "aws_vpc" "ipe" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "ipe-prod-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.ipe.id
  cidr_block        = cidrsubnet(aws_vpc.ipe.cidr_block, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "ipe-prod-private-${count.index}"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# RDS PostgreSQL 16
resource "aws_db_subnet_group" "ipe" {
  name       = "ipe-prod-db-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_rds_cluster" "ipe" {
  cluster_identifier     = "ipe-prod-db"
  engine                 = "aurora-postgresql"
  engine_version         = "16"
  database_name          = "ipe_prod"
  master_username        = "ipe_admin"
  master_password        = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.ipe.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  storage_encrypted      = true
  backup_retention_period = 30
  preferred_backup_window = "03:00-04:00"

  tags = {
    Name = "ipe-prod-db"
  }
}

resource "aws_rds_cluster_instance" "ipe" {
  count              = 2
  identifier         = "ipe-prod-db-${count.index}"
  cluster_identifier = aws_rds_cluster.ipe.id
  instance_class     = "db.r6g.large"
  engine             = aws_rds_cluster.ipe.engine
  engine_version     = aws_rds_cluster.ipe.engine_version
}

variable "db_password" {
  sensitive = true
}

# MSK (Kafka 7.7)
resource "aws_msk_cluster" "ipe" {
  cluster_name           = "ipe-prod-kafka"
  kafka_version          = "3.7.0"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    storage_info {
      ebs_storage_info {
        volume_size = 500
      }
    }
    client_subnets = aws_subnet.private[*].id
    security_groups = [aws_security_group.kafka.id]
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
    encryption_at_rest_kms_key_arn = aws_kms_key.msk.arn
  }

  tags = {
    Name = "ipe-prod-kafka"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "ipe" {
  replication_group_id = "ipe-prod-redis"
  description          = "IPE Production Redis"
  node_type            = "cache.r6g.large"
  num_cache_clusters   = 2
  port                 = 6379
  security_group_ids   = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.ipe.name
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  tags = {
    Name = "ipe-prod-redis"
  }
}

resource "aws_elasticache_subnet_group" "ipe" {
  name       = "ipe-prod-redis-subnet"
  subnet_ids = aws_subnet.private[*].id
}

# KMS
resource "aws_kms_key" "msk" {
  description             = "IPE MSK encryption key"
  deletion_window_in_days = 30
}

resource "aws_kms_key" "rds" {
  description             = "IPE RDS encryption key"
  deletion_window_in_days = 30
}

# S3
resource "aws_s3_bucket" "artifacts" {
  bucket = "ipe-prod-artifacts"

  tags = {
    Name = "ipe-prod-artifacts"
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# Security Groups
resource "aws_security_group" "rds" {
  name_prefix = "ipe-prod-rds-"
  vpc_id      = aws_vpc.ipe.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_security_group" "kafka" {
  name_prefix = "ipe-prod-kafka-"
  vpc_id      = aws_vpc.ipe.id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "ipe-prod-redis-"
  vpc_id      = aws_vpc.ipe.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

# Outputs
output "rds_endpoint" {
  value = aws_rds_cluster.ipe.endpoint
}

output "kafka_bootstrap" {
  value = aws_msk_cluster.ipe.bootstrap_brokers_tls
}

output "redis_endpoint" {
  value = aws_elasticache_replication_group.ipe.primary_endpoint_address
}

output "artifacts_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}
