# Architecture

## Runtime flow

1. EventBridge Scheduler triggers the collector Lambda on a fixed interval (default: every 6 hours)
2. The Lambda's composition root (`handler.py`) wires either `SSMPatchSource` or `MockPatchSource`
   (based on `USE_MOCK_DATA`) into `PatchAuditService`, then runs a scan
3. Results are written to DynamoDB using a single-table design:
   - `PK=INSTANCE#<id>, SK=LATEST` — current state, overwritten each scan
   - `PK=INSTANCE#<id>, SK=SCAN#<timestamp>` — historical record
4. App Runner serves the Streamlit dashboard, whose composition root (`dashboard.py`)
   wires `DynamoDBRepository` into `ComplianceQueryService` to read the data back out
5. Both Lambda and App Runner reach DynamoDB over public AWS API endpoints —
   no VPC or NAT Gateway required, which was the deciding factor in choosing
   DynamoDB over RDS given App Runner as the hosting choice

## Why these specific AWS services

| Concern | Choice | Reasoning |
|---|---|---|
| Patch data source | SSM Patch Manager | AWS-native, already normalizes Windows CU and Linux package compliance into one model |
| Compute (collector) | Lambda | Scheduled, short-lived, well within free tier |
| Storage | DynamoDB (on-demand) | No VPC needed for App Runner connectivity; permanent free tier; matches SSM's key-value shape |
| Dashboard hosting | App Runner | Lowest ops overhead, built-in TLS/load balancing, no ALB cost; scales via CPU/mem-seconds |
| IaC | Terraform, spin-up/down | Matches actual usage pattern (demo-driven, not 24/7) |

## Dependency injection layering

See the main README's "Design principles" section and `common/patch_domain/` for
the full DI approach — interfaces, concrete implementations, services, and the
two composition roots (`lambda/patch_collector/handler.py`, `app/dashboard.py`).
