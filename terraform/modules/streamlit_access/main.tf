# Streamlit Community Cloud runs outside AWS, so it can't assume an IAM
# role the way App Runner could. It needs long-lived access keys instead.
# We minimize the blast radius of that tradeoff by scoping this user to
# read-only actions on exactly one table.

resource "aws_iam_user" "streamlit_dashboard" {
  name = "${var.project_name}-streamlit-readonly"
  tags = var.tags
}

resource "aws_iam_user_policy" "dynamodb_read_only" {
  name = "dynamodb-read-only"
  user = aws_iam_user.streamlit_dashboard.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan"]
      Resource = [var.table_arn, "${var.table_arn}/index/*"]
    }]
  })
}

resource "aws_iam_access_key" "streamlit_dashboard" {
  user = aws_iam_user.streamlit_dashboard.name
}
