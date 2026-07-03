variable "function_name" {
  type = string
}
variable "table_name" {
  type = string
}
variable "table_arn" {
  type = string
}
variable "use_mock_data" {
  type    = string
  default = "false"
}
variable "placeholder_zip_path" {
  type        = string
  description = "Path to a minimal placeholder zip used only on first apply"
}
variable "tags" {
  type    = map(string)
  default = {}
}
