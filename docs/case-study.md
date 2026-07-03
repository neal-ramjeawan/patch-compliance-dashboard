<!--
  Case study writeup for the portfolio site (Next.js). Adapt the frontmatter
  to match your existing case study page schema — placeholders below.
-->

---
title: "Patch Compliance Dashboard"
summary: "An AWS-native platform for auditing Windows and Linux patch compliance, built with dependency injection and a cost-conscious, mock-first architecture."
tags: ["AWS", "Terraform", "Python", "DynamoDB", "Lambda", "Streamlit", "CI/CD"]
repoUrl: "#"
liveUrl: "#"
---

## The problem

Auditing patch compliance across a mixed fleet is deceptively fragile. Windows
tracks compliance through Cumulative Updates; Linux tracks it through
per-distro package managers (`apt`, `dnf`) with completely different
classification schemes for what counts as "security-critical." A naive
approach — SSH into every box and shell out to `apt list --upgradable` or
`Get-HotFix` — means maintaining brittle, OS-specific scripts and having no
single source of truth for compliance status.

I built this project to solve that properly: treat **AWS Systems Manager
Patch Manager** as the source of truth, since it already normalizes both
platforms into one compliance model, and build a dashboard on top of it.

## Approach: mock-first, AWS-native

One constraint shaped almost every decision: I didn't have a real AWS
environment with managed EC2 instances to test against yet. Rather than
block on that, I designed the whole system around an abstraction —
`PatchDataSource` — with two implementations: a `MockPatchSource` that
generates data shaped *identically* to SSM's real API responses, and an
`SSMPatchSource` that makes the real boto3 calls. The application code never
knows which one it's talking to.

That decision ended up shaping the whole architecture, not just the data
layer — because both the collection pipeline (Lambda) and the dashboard
(Streamlit) needed the same swap-without-rewrite property, dependency
injection became the organizing principle for the entire codebase, not
just a testing nicety.

## Architecture

- **Collection**: EventBridge Scheduler triggers a Lambda on a fixed
  interval. It calls SSM Patch Manager's `DescribeInstancePatchStates`/
  `DescribeInstancePatches` APIs and writes results to DynamoDB.
- **Storage**: DynamoDB, single-table design — `PK=INSTANCE#<id>, SK=LATEST`
  for the current fleet view, `SK=SCAN#<timestamp>` for history, with a GSI
  enabling an efficient "all instances' latest state" query.
- **Serving**: A Streamlit dashboard reads from DynamoDB and renders fleet-wide
  compliance metrics, filterable tables, and per-instance patch drill-down.

## Key decisions and tradeoffs

**Dependency injection via `typing.Protocol`, not a framework.** Python
doesn't have a dominant DI container the way Java or C# does, and for a
codebase this size, importing one would have been more machinery than the
problem needed. Instead, every service depends on an interface
(`PatchDataSource`, `PatchRepository`) and receives a concrete implementation
through its constructor — decided in exactly one place per deployable (the
"composition root"). The payoff: the entire test suite runs with **zero AWS
credentials**, because tests just construct `MockPatchSource` and
`InMemoryRepository` directly. That in turn means the CI pipeline can run
tests on every single pull request without ever touching a secret.

**DynamoDB over RDS, once App Runner ruled out RDS's networking cost.**
I originally planned to host the dashboard on ECS Fargate behind an ALB, then
switched to App Runner for lower ops overhead. That choice had a downstream
consequence I hadn't initially considered: connecting App Runner to RDS
would require a VPC Connector, which typically means paying for a NAT
Gateway (~$32/month) just for networking — on a project I wanted to run for
cents. DynamoDB needs no VPC at all; both Lambda and the dashboard reach it
over public AWS API endpoints. That one constraint made the storage decision
for me.

**Streamlit Community Cloud over any AWS compute service, for genuinely free
hosting.** App Runner, Fargate, and EC2 all looked attractive at different
points, but none of AWS's container-hosting options are free once idle — App
Runner and Fargate bill for provisioned compute continuously, and EC2's free
tier expires after 12 months. Streamlit Community Cloud is free indefinitely
and auto-deploys straight from this GitHub repo. The tradeoff: since it runs
outside AWS, it can't assume an IAM role the way App Runner could, so it
authenticates with a narrowly-scoped IAM user's access keys instead — a
deliberate, documented security tradeoff rather than an oversight.

## Testing and local development

Because the mock/real split runs all the way through the system, the project
supports three distinct local testing modes without touching a live AWS
account:

1. **Fully offline** — `MockPatchSource` + `InMemoryRepository`, used by the
   entire automated test suite and for local demos.
2. **LocalStack** — since `MockPatchSource` already stands in for SSM (which
   LocalStack can't meaningfully emulate anyway — there's no real fleet for
   it to report on), LocalStack's value here is testing the *real*
   `DynamoDBRepository` code path: actual boto3 calls, the single-table
   writes, the GSI query.
3. **Real AWS** — flipping one environment variable.

## What I'd do next

- Trend/history views using the scan history already being written to DynamoDB
- A CloudWatch alarm on Lambda scan failures, to round out the observability story
- Testing against a real EC2/SSM-managed fleet once available, to validate
  `SSMPatchSource` against live data rather than just its interface contract

## Tech stack

AWS (Lambda, DynamoDB, EventBridge Scheduler, SSM Patch Manager, IAM),
Terraform, Python 3.12, Streamlit, GitHub Actions (OIDC), LocalStack, pytest
