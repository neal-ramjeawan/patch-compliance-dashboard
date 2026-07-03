resource "aws_dynamodb_table" "patch_data" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST" # on-demand — no idle cost, fits spin-up/down usage

  hash_key  = "PK"
  range_key = "SK"

  attribute {
    name = "PK"
    type = "S"
  }
  attribute {
    name = "SK"
    type = "S"
  }

  # Lets the repository query "all items where SK = LATEST" across every
  # instance, without scanning the whole table.
  global_secondary_index {
    name            = "GSI1"
    hash_key        = "SK"
    range_key       = "PK"
    projection_type = "ALL"
  }

  tags = var.tags
}
