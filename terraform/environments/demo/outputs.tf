output "streamlit_access_key_id" {
  value = module.streamlit_access.access_key_id
}

output "streamlit_secret_access_key" {
  value     = module.streamlit_access.secret_access_key
  sensitive = true
  # Retrieve with: terraform output -raw streamlit_secret_access_key
  # Paste into Streamlit Cloud's app secrets — never commit this value.
}

output "lambda_function_name" {
  value = module.lambda.function_name
}

output "dynamodb_table_name" {
  value = module.dynamodb.table_name
}
