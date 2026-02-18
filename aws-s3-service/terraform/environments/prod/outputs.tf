output "alb_url" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecr.repository_url
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.messaging.s3_bucket_name
}

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint of the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "irsa_role_arn" {
  description = "ARN of the IRSA role for Kubernetes service account"
  value       = module.irsa.role_arn
}
