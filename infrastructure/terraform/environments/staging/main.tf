module "vpc" {
  source      = "../../modules/vpc"
  environment = "staging"
  vpc_cidr    = "10.0.0.0/16"
}

module "rds" {
  source            = "../../modules/rds"
  environment       = "staging"
  db_password       = var.db_password
  security_group_id = aws_security_group.rds.id
  subnet_ids        = module.vpc.private_subnet_ids
}

module "eks" {
  source      = "../../modules/eks"
  environment = "staging"
  subnet_ids  = module.vpc.private_subnet_ids
}

resource "aws_security_group" "rds" {
  vpc_id = module.vpc.vpc_id
}
