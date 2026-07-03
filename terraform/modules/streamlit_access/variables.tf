variable "project_name" {
  type = string
}
variable "table_arn" {
  type = string
}
variable "tags" {
  type    = map(string)
  default = {}
}
