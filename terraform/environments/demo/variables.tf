variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "patch-dashboard"
}

variable "use_mock_data" {
  type        = string
  default     = "true"
  description = "When true, Lambda/App Runner use MockPatchSource instead of real SSM/DynamoDB reads — useful before real EC2/SSM access exists"
}

variable "schedule_expression" {
  type    = string
  default = "rate(6 hours)"
}
