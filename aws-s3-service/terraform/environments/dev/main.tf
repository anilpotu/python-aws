module "vpc" {
  source       = "../../modules/vpc"
  project_name = var.project_name
  environment  = var.environment
}

module "ecr" {
  source       = "../../modules/ecr"
  project_name = var.project_name
  environment  = var.environment
}

module "messaging" {
  source       = "../../modules/messaging"
  project_name = var.project_name
  environment  = var.environment
}

module "iam" {
  source        = "../../modules/iam"
  project_name  = var.project_name
  environment   = var.environment
  s3_bucket_arn = module.messaging.s3_bucket_arn
  sns_topic_arn = module.messaging.sns_topic_arn
  sqs_queue_arn = module.messaging.sqs_queue_arn
}

module "alb" {
  source            = "../../modules/alb"
  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
}

module "ecs" {
  source                = "../../modules/ecs"
  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecr_repository_url    = module.ecr.repository_url
  image_tag             = var.image_tag
  execution_role_arn    = module.iam.execution_role_arn
  task_role_arn         = module.iam.task_role_arn
  target_group_arn      = module.alb.target_group_arn
  alb_security_group_id = module.alb.alb_security_group_id
  cpu                   = var.cpu
  memory                = var.memory
  desired_count         = var.desired_count
  log_retention_days    = var.log_retention_days
  aws_region            = var.aws_region
  s3_bucket_name        = module.messaging.s3_bucket_name
  sns_topic_arn         = module.messaging.sns_topic_arn
  sqs_queue_url         = module.messaging.sqs_queue_url
}

module "eks" {
  source              = "../../modules/eks"
  project_name        = var.project_name
  environment         = var.environment
  private_subnet_ids  = module.vpc.private_subnet_ids
  kubernetes_version  = var.eks_kubernetes_version
  node_instance_types = var.eks_node_instance_types
  node_desired_count  = var.eks_node_desired_count
  node_min_count      = var.eks_node_min_count
  node_max_count      = var.eks_node_max_count
}

module "irsa" {
  source               = "../../modules/irsa"
  project_name         = var.project_name
  environment          = var.environment
  oidc_provider_arn    = module.eks.oidc_provider_arn
  oidc_provider_url    = module.eks.oidc_provider_url
  namespace            = "default"
  service_account_name = "aws-s3-service"
  s3_bucket_arn        = module.messaging.s3_bucket_arn
  sns_topic_arn        = module.messaging.sns_topic_arn
  sqs_queue_arn        = module.messaging.sqs_queue_arn
}
