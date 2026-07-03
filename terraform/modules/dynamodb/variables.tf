variable "table_name" {
  type        = string
  description = "Name of the DynamoDB table storing patch scan results"
}

variable "tags" {
  type    = map(string)
  default = {}
}
