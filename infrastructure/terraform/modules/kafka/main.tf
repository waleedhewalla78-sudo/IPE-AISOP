resource "aws_msk_cluster" "ipe" {
  cluster_name           = "ipe-${var.environment}"
  kafka_version          = "3.7.0"
  number_of_broker_nodes = var.broker_count

  broker_node_group_info {
    instance_type   = var.instance_type
    client_subnets  = var.subnet_ids
    security_groups = [var.security_group_id]
    storage_info {
      ebs_storage_info {
        volume_size = var.volume_size
      }
    }
  }

  tags = { Name = "ipe-${var.environment}" }
}

output "bootstrap_brokers" { value = aws_msk_cluster.ipe.bootstrap_brokers }

variable "environment" {}
variable "subnet_ids" { type = list(string) }
variable "security_group_id" {}
variable "instance_type" { default = "kafka.t3.small" }
variable "broker_count" { default = 3 }
variable "volume_size" { default = 100 }
