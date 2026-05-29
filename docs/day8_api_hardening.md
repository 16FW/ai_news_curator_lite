# Day 8 - API Hardening

## Goal

- Standardized API success responses.
- Standardized API error responses.
- Added stricter keyword input validation.
- Added CORS headers in Lambda responses and SAM HTTP API configuration.
- Cleaned local API Gateway event files for news and keyword APIs.
- Kept real news API calls, crawling, AI summarization, and EventBridge scheduling out of scope.

## Response Format

Successful responses now use the shared envelope:

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

Examples:

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "ai_news_curator_lite"
  },
  "message": "ok"
}
```

```json
{
  "success": true,
  "data": {
    "item": {
      "user_id": "demo_user",
      "keyword": "aws",
      "created_at": "2026-05-29T00:00:00Z"
    }
  },
  "message": "keyword created"
}
```

## Error Format

Error responses now use a consistent shape:

```json
{
  "success": false,
  "data": null,
  "message": "keyword_required",
  "error": {
    "code": "keyword_required",
    "message": "keyword_required"
  }
}
```

Current error codes include:

- `invalid_json_body`
- `json_body_must_be_object`
- `keyword_required`
- `keyword_must_be_string`
- `keyword_too_long`
- `keyword_invalid_characters`
- `keyword_table_not_configured`
- `not_found`
- `internal_server_error`

## Input Validation

Keyword validation is shared by:

- `GET /news?keyword=...`
- `POST /keywords`
- `DELETE /keywords/{keyword}`

Rules:

- Keyword must be a string.
- Keyword is trimmed and normalized to lowercase.
- Keyword cannot be empty.
- Keyword length must be 40 characters or less.
- Keyword may contain letters, numbers, spaces, hyphens, and underscores.

## CORS

Lambda responses include:

```text
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type,Authorization
Access-Control-Allow-Methods: GET,POST,DELETE,OPTIONS
```

The SAM `AWS::Serverless::HttpApi` resource also includes matching `CorsConfiguration`.

## Local Events

The API Gateway v2 local event files are:

```text
backend/events/health_event.json
backend/events/get_news_event.json
backend/events/get_today_news_event.json
backend/events/create_keyword_event.json
backend/events/get_keywords_event.json
backend/events/list_keywords_event.json
backend/events/delete_keyword_event.json
```

`get_keywords_event.json` and `list_keywords_event.json` both target `GET /keywords`. The former is the preferred filename because it matches the route naming used by the app.

## Local Checks

Run from the repository root:

```powershell
python -m py_compile backend/app.py
```

Run from the `infra` directory:

```powershell
sam validate
sam build
sam local invoke AiNewsCuratorLiteFunction --event ../backend/events/health_event.json
sam local invoke AiNewsCuratorLiteFunction --event ../backend/events/get_news_event.json
sam local invoke AiNewsCuratorLiteFunction --event ../backend/events/get_today_news_event.json
```

The keyword and today-news endpoints query DynamoDB, so local invocation requires valid AWS credentials and deployed table names from the SAM template environment.

## Deployment

Run from the `infra` directory:

```powershell
sam build
sam deploy --stack-name ai-news-curator-lite
```

If `samconfig.toml` is configured:

```powershell
sam deploy
```

## Notes

- The MVP still uses `demo_user`.
- Day 8 does not add real news API integration.
- Day 8 does not add AI summarization.
- Day 8 does not add EventBridge scheduling.
