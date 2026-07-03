resource "aws_iam_role" "collector" {
  name = "${var.function_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.collector.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Least-privilege: only the SSM read APIs the collector actually calls.
resource "aws_iam_role_policy" "ssm_read" {
  name = "ssm-patch-read"
  role = aws_iam_role.collector.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:DescribeInstancePatchStates",
        "ssm:DescribeInstancePatches",
        "ssm:DescribeInstancePatchStatesForPatchGroup",
      ]
      Resource = "*" # these Describe* APIs don't support resource-level scoping
    }]
  })
}

resource "aws_iam_role_policy" "dynamodb_write" {
  name = "dynamodb-write"
  role = aws_iam_role.collector.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:PutItem", "dynamodb:BatchWriteItem"]
      Resource = var.table_arn
    }]
  })
}

resource "aws_lambda_function" "collector" {
  function_name = var.function_name
  role          = aws_iam_role.collector.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 256

  # Placeholder on first apply — deploy-app.yml overwrites this via
  # `aws lambda update-function-code` once a real build exists.
  filename         = var.placeholder_zip_path
  source_code_hash = filebase64sha256(var.placeholder_zip_path)

  environment {
    variables = {
      TABLE_NAME    = var.table_name
      USE_MOCK_DATA = var.use_mock_data
    }
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [filename, source_code_hash] # code updates go through CI, not terraform apply
  }
}
