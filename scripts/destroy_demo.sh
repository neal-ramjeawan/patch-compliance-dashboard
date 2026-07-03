#!/usr/bin/env bash
# Tears down the demo environment's billable resources. Terraform state
# bucket and ECR repo are left in place intentionally.
set -euo pipefail

cd "$(dirname "$0")/../terraform/environments/demo"
terraform init
terraform destroy -auto-approve

echo "Demo environment destroyed. Remote state bucket and ECR repo were left intact."
