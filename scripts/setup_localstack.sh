#!/usr/bin/env bash
# Starts LocalStack and creates the DynamoDB table with the same schema
# as terraform/modules/dynamodb/main.tf (PK/SK + GSI1 on SK). If that
# module's schema ever changes, update this to match.
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d localstack

echo "Waiting for LocalStack DynamoDB..."
until curl -s http://localhost:4566/_localstack/health | grep -q '"dynamodb": "available"'; do
  sleep 1
done

TABLE_NAME="${TABLE_NAME:-patch-dashboard-patch-data}"

aws dynamodb create-table \
  --endpoint-url http://localhost:4566 \
  --table-name "$TABLE_NAME" \
  --attribute-definitions \
      AttributeName=PK,AttributeType=S \
      AttributeName=SK,AttributeType=S \
  --key-schema \
      AttributeName=PK,KeyType=HASH \
      AttributeName=SK,KeyType=RANGE \
  --global-secondary-indexes \
      '[{"IndexName":"GSI1","KeySchema":[{"AttributeName":"SK","KeyType":"HASH"},{"AttributeName":"PK","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1 \
  --no-cli-pager \
  2>/dev/null || echo "Table already exists, continuing."

echo "LocalStack DynamoDB ready. Table: $TABLE_NAME"
echo "Next: python scripts/seed_localstack.py"
