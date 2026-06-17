resource "aws_eks_cluster" "ipe" {
  name     = "ipe-${var.environment}"
  role_arn = aws_iam_role.eks.arn
  vpc_config {
    subnet_ids = var.subnet_ids
  }
  enabled_cluster_log_types = ["api", "audit", "authenticator"]
}

resource "aws_iam_role" "eks" {
  name = "ipe-eks-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_eks_node_group" "ipe" {
  cluster_name    = aws_eks_cluster.ipe.name
  node_group_name = "ipe-${var.environment}-nodes"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.subnet_ids
  instance_types  = var.instance_types
  scaling_config {
    desired_size = var.desired_size
    min_size     = var.min_size
    max_size     = var.max_size
  }
}

resource "aws_iam_role" "node" {
  name = "ipe-eks-node-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

output "cluster_endpoint" { value = aws_eks_cluster.ipe.endpoint }
output "cluster_name" { value = aws_eks_cluster.ipe.name }
output "cluster_ca_cert" { value = aws_eks_cluster.ipe.certificate_authority[0].data }

variable "environment" {}
variable "subnet_ids" { type = list(string) }
variable "instance_types" { default = ["t3.medium"] }
variable "desired_size" { default = 3 }
variable "min_size" { default = 2 }
variable "max_size" { default = 6 }
