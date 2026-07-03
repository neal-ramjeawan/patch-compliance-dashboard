output "access_key_id" {
  value = aws_iam_access_key.streamlit_dashboard.id
}

output "secret_access_key" {
  value     = aws_iam_access_key.streamlit_dashboard.secret
  sensitive = true # still shows in terraform state — see README security note
}
