variable "function_name" {
  type = string
}
variable "lambda_function_arn" {
  type = string
}
variable "schedule_expression" {
  type    = string
  default = "rate(6 hours)"
}
