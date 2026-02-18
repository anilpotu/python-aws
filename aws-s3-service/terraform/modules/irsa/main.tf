data "aws_iam_policy_document" "irsa_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:sub"
      values   = ["system:serviceaccount:${var.namespace}:${var.service_account_name}"]
    }

    condition {
      test     = "StringEquals"
      variable = "${var.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "irsa" {
  name               = "${var.project_name}-${var.environment}-irsa"
  assume_role_policy = data.aws_iam_policy_document.irsa_assume_role.json

  tags = {
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "irsa_permissions" {
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

resource "aws_iam_role_policy" "irsa_permissions" {
  name   = "${var.project_name}-${var.environment}-irsa-permissions"
  role   = aws_iam_role.irsa.id
  policy = data.aws_iam_policy_document.irsa_permissions.json
}
