# AI News Curator Lite

AI News Curator Lite is a small serverless backend MVP for a portfolio project. It lets a user manage interest keywords and provides a simple API foundation for curated AI/IT news.

## Project Name

`ai_news_curator_lite`

The AWS CloudFormation stack name uses hyphens because stack names cannot contain underscores:

`ai-news-curator-lite`

## Goals

- Build a compact AWS serverless backend that can be deployed and tested quickly.
- Use API Gateway, Lambda, and DynamoDB as the core backend architecture.
- Keep the MVP small enough to complete while still showing backend/cloud fundamentals.
- Document architecture, cost policy, deployment, and operational tradeoffs.

## Core Features

- Health check API
- Keyword create/list/delete API backed by DynamoDB
- Mock news lookup API for early MVP testing
- SAM-based local build and AWS deployment flow
- CloudWatch-compatible Lambda logging

## Architecture

```text
Client
  -> API Gateway HTTP API
  -> AWS Lambda (Python)
  -> DynamoDB

Operations:
  -> CloudWatch Logs
  -> CloudWatch Metrics
```

The keyword table uses:

- Partition key: `user_id`
- Sort key: `keyword`
- Billing mode: `PAY_PER_REQUEST`

The current MVP uses a fixed `demo_user` value. A future authentication layer can replace it with a Cognito or JWT user id.

## Repository Structure

```text
ai_news_curator_lite
├─ backend
│  ├─ app.py
│  └─ events
├─ docs
├─ frontend
├─ infra
│  ├─ template.yaml
│  └─ samconfig.toml
├─ scripts
├─ tests
├─ README.md
└─ .gitignore
```

## Local Build

Run from the `infra` directory:

```bash
sam build
sam local invoke AiNewsCuratorLiteFunction --event ../backend/events/health_event.json
```

Keyword API local invoke calls DynamoDB, so it requires AWS credentials and a deployed/configured table environment.

## Deployment

Run from the `infra` directory:

```bash
sam build
sam deploy --stack-name ai-news-curator-lite
```

If `infra/samconfig.toml` is already configured:

```bash
sam deploy
```

## API Examples

```bash
curl https://{api_id}.execute-api.{region}.amazonaws.com/Prod/health
curl https://{api_id}.execute-api.{region}.amazonaws.com/Prod/keywords
```

See [docs/day6_dynamodb.md](docs/day6_dynamodb.md) for DynamoDB integration details and full test commands.
