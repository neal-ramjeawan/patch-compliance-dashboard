terraform {
  backend "s3" {
    # Filled in via `terraform init -backend-config=` in deploy-infra.yml,
    # so the bucket/table names aren't hardcoded into version control.
    key = "patch-dashboard/demo/terraform.tfstate"
  }
}
