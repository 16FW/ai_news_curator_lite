# Architecture

AI News Curator Lite는 서버리스 기반 MVP로 설계합니다.

## High Level Flow

```text
User
  ↓
React Static Frontend
  ↓
S3 + CloudFront
  ↓
API Gateway HTTP API
  ↓
Lambda
  ↓
DynamoDB
```

## Monitoring

- CloudWatch Logs
- CloudWatch Metrics

## User Analytics

- GA4
- Custom Event API

## Admin Input

- Admin API
- JSON bulk upload
