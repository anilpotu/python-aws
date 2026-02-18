variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "cpu" {
  description = "CPU units for the ECS task"
  type        = number
}

variable "memory" {
  description = "Memory (MiB) for the ECS task"
  type        = number
}

variable "desired_count" {
  description = "Number of ECS tasks to run"
  type        = number
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
}

variable "eks_kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.29"
}

variable "eks_node_instance_types" {
  description = "EC2 instance types for EKS node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "eks_node_desired_count" {
  description = "Desired number of EKS nodes"
  type        = number
  default     = 2
}

variable "eks_node_min_count" {
  description = "Minimum number of EKS nodes"
  type        = number
  default     = 1
}

variable "eks_node_max_count" {
  description = "Maximum number of EKS nodes"
  type        = number
  default     = 4
}
