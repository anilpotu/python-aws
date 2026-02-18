data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution_role" {
  name               = "${var.project_name}-${var.environment}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name               = "${var.project_name}-${var.environment}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "task_permissions" {
  statement {
    sid = "S3Access"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      var.s3_bucket_arn,
      "${var.s3_bucket_arn}/*",
    ]
  }

  statement {
    sid       = "SNSPublish"
    actions   = ["sns:Publish"]
    resources = [var.sns_topic_arn]
  }

  statement {
    sid = "SQSAccess"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
    ]
    resources = [var.sqs_queue_arn]
  }
}

resource "aws_iam_role_policy" "task_permissions" {
  name   = "${var.project_name}-${var.environment}-task-permissions"
  role   = aws_iam_role.ecs_task_role.id
  policy = data.aws_iam_policy_document.task_permissions.json
}
