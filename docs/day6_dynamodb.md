# Day 6 - DynamoDB Integration

## Goal

- Connected the Lambda backend to DynamoDB.
- Replaced the mock keyword API behavior with real create, list, and delete operations.
- Injected the DynamoDB table name through the Lambda environment variable `KEYWORD_TABLE_NAME`.
- Added least-privilege DynamoDB permissions for the keyword table.

## DynamoDB Table Design

The keyword table stores user-selected keywords for the news curator API.

- Table logical name: `KeywordTable`
- Partition key: `user_id`
- Sort key: `keyword`
- Billing mode: `PAY_PER_REQUEST`
- MVP user id: `demo_user`

The MVP does not include authentication yet, so the Lambda uses a fixed `demo_user` value. After Cognito or JWT authentication is added, `user_id` should be replaced with the authenticated user's subject or user id.

Example item:

```json
{
  "user_id": "demo_user",
  "keyword": "aws",
  "created_at": "2026-05-26T00:00:00Z"
}
```

## API Changes

### GET /health

Returns service health.

Response:

```json
{
  "status": "ok",
  "service": "ai_news_curator_lite"
}
```

### POST /keywords

Creates or overwrites a keyword for `demo_user`.

Request:

```json
{
  "keyword": "aws"
}
```

Response:

```json
{
  "message": "keyword created",
  "item": {
    "user_id": "demo_user",
    "keyword": "aws",
    "created_at": "2026-05-26T00:00:00Z"
  }
}
```

Validation:

- Missing body or invalid JSON returns `400`.
- Missing or empty `keyword` returns `400`.
- The keyword is trimmed and converted to lowercase.

### GET /keywords

Lists keywords for `demo_user`.

Response:

```json
{
  "items": [
    {
      "user_id": "demo_user",
      "keyword": "aws",
      "created_at": "2026-05-26T00:00:00Z"
    }
  ]
}
```

### DELETE /keywords/{keyword}

Deletes a keyword for `demo_user`. Deleting a missing keyword still returns success for this MVP.

Response:

```json
{
  "message": "keyword deleted",
  "keyword": "aws"
}
```

## Deployment

Run from the `infra` directory:

```bash
sam build
sam deploy --stack-name ai-news-curator-lite
```

If `samconfig.toml` is configured, this is also valid:

```bash
sam deploy
```

The CloudFormation stack name must use hyphens, not underscores: `ai-news-curator-lite`.

## Test Commands

Replace `{api_id}` and `{region}` with the deployed API Gateway values.

### curl

```bash
curl https://{api_id}.execute-api.{region}.amazonaws.com/Prod/health

curl -X POST https://{api_id}.execute-api.{region}.amazonaws.com/Prod/keywords \
  -H "Content-Type: application/json" \
  -d "{\"keyword\":\"aws\"}"

curl https://{api_id}.execute-api.{region}.amazonaws.com/Prod/keywords

curl -X DELETE https://{api_id}.execute-api.{region}.amazonaws.com/Prod/keywords/aws
```

### PowerShell

PowerShell aliases `curl` to `Invoke-WebRequest`, so `Invoke-RestMethod` is clearer on Windows.

```powershell
Invoke-RestMethod -Method Get -Uri "https://{api_id}.execute-api.{region}.amazonaws.com/Prod/health"

Invoke-RestMethod -Method Post `
  -Uri "https://{api_id}.execute-api.{region}.amazonaws.com/Prod/keywords" `
  -ContentType "application/json" `
  -Body '{"keyword":"aws"}'

Invoke-RestMethod -Method Get -Uri "https://{api_id}.execute-api.{region}.amazonaws.com/Prod/keywords"

Invoke-RestMethod -Method Delete -Uri "https://{api_id}.execute-api.{region}.amazonaws.com/Prod/keywords/aws"
```

### SAM Local

Run from the `infra` directory:

```bash
sam build
sam local invoke AiNewsCuratorLiteFunction --event ../backend/events/health_event.json
sam local invoke AiNewsCuratorLiteFunction --event ../backend/events/create_keyword_event.json
sam local invoke AiNewsCuratorLiteFunction --event ../backend/events/list_keywords_event.json
sam local invoke AiNewsCuratorLiteFunction --event ../backend/events/delete_keyword_event.json
```

`GET /health` can run locally without AWS credentials. Keyword operations call DynamoDB, so local invoke requires valid AWS credentials and a deployed table name supplied through the SAM template environment.

## Notes

- README should stay focused on the portfolio project overview, architecture, features, and run/deploy instructions.
- Day-by-day implementation details are kept in `docs/day6_dynamodb.md`.
- DynamoDB uses `PAY_PER_REQUEST` for MVP cost optimization.
- The current MVP uses `demo_user` because authentication is not implemented.
- The `user_id` key can later be replaced with a Cognito/JWT user identifier.
