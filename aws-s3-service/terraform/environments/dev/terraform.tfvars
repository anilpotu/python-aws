project_name       = "aws-s3-service"
environment        = "dev"
aws_region         = "us-east-1"
cpu                = 256
memory             = 512
desired_count      = 1
log_retention_days = 14

eks_kubernetes_version  = "1.29"
eks_node_instance_types = ["t3.medium"]
eks_node_desired_count  = 2
eks_node_min_count      = 1
eks_node_max_count      = 3
