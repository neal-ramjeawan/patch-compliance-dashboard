terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  tags = {
    Project     = "patch-compliance-dashboard"
    Environment = "demo"
    ManagedBy   = "terraform"
  }
}

module "dynamodb" {
  source     = "../../modules/dynamodb"
  table_name = "${var.project_name}-patch-data"
  tags       = local.tags
}

module "lambda" {
  source                = "../../modules/lambda"
  function_name         = "${var.project_name}-collector"
  table_name            = module.dynamodb.table_name
  table_arn             = module.dynamodb.table_arn
  use_mock_data         = var.use_mock_data
  placeholder_zip_path  = "${path.module}/placeholder.zip"
  tags                  = local.tags
}

module "eventbridge" {
  source              = "../../modules/eventbridge"
  function_name       = module.lambda.function_name
  lambda_function_arn = module.lambda.function_arn
  schedule_expression = var.schedule_expression
}

module "streamlit_access" {
  source       = "../../modules/streamlit_access"
  project_name = var.project_name
  table_arn    = module.dynamodb.table_arn
  tags         = local.tags
}