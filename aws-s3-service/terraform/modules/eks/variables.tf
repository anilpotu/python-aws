variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs of the private subnets for EKS"
  type        = list(string)
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.29"
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_count" {
  description = "Desired number of nodes in the node group"
  type        = number
  default     = 2
}

variable "node_min_count" {
  description = "Minimum number of nodes in the node group"
  type        = number
  default     = 1
}

variable "node_max_count" {
  description = "Maximum number of nodes in the node group"
  type        = number
  default     = 4
}
