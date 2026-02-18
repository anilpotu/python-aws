output "role_arn" {
  description = "ARN of the IRSA IAM role"
  value       = aws_iam_role.irsa.arn
}
