module "vpc" {
  source      = "../../modules/vpc"
  environment = "production"
  vpc_cidr    = "10.0.0.0/16"
}

module "rds" {
  source            = "../../modules/rds"
  environment       = "production"
  db_password       = var.db_password
  instance_class    = "db.r6g.large"
  allocated_storage = 500
  security_group_id = aws_security_group.rds.id
  subnet_ids        = module.vpc.private_subnet_ids
}

module "eks" {
  source         = "../../modules/eks"
  environment    = "production"
  subnet_ids     = module.vpc.private_subnet_ids
  instance_types = ["t3.large"]
  desired_size   = 5
  min_size       = 3
  max_size       = 10
}

module "kafka" {
  source            = "../../modules/kafka"
  environment       = "production"
  subnet_ids        = module.vpc.private_subnet_ids
  security_group_id = aws_security_group.kafka.id
}

resource "aws_security_group" "rds" {
  vpc_id = module.vpc.vpc_id
}

resource "aws_security_group" "kafka" {
  vpc_id = module.vpc.vpc_id
}
