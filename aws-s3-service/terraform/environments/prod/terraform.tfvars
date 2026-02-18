project_name       = "aws-s3-service"
environment        = "prod"
aws_region         = "us-east-1"
cpu                = 512
memory             = 1024
desired_count      = 2
log_retention_days = 30

eks_kubernetes_version  = "1.29"
eks_node_instance_types = ["t3.large"]
eks_node_desired_count  = 3
eks_node_min_count      = 2
eks_node_max_count      = 6
