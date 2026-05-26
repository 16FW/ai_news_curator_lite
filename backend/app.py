import json
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key


SERVICE_NAME = "ai_news_curator_lite"
# TODO: Replace the MVP demo user with a JWT/Cognito user id after auth is added.
USER_ID = "demo_user"
TABLE_NAME = os.environ.get("KEYWORD_TABLE_NAME")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }


def error_response(status_code, message):
    return response(status_code, {"message": message})


def parse_body(event):
    raw_body = event.get("body")
    if not raw_body:
        return None

    try:
        return json.loads(raw_body)
    except (TypeError, json.JSONDecodeError):
        return None


def get_route(event):
    route_key = event.get("routeKey")
    if route_key and route_key != "$default":
        return route_key

    request_context = event.get("requestContext", {})
    http_context = request_context.get("http", {})
    method = http_context.get("method") or event.get("httpMethod", "")
    path = http_context.get("path") or event.get("path", "")
    return f"{method.upper()} {path}"


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def handle_health():
    return response(200, {
        "status": "ok",
        "service": SERVICE_NAME
    })


def handle_get_news(event):
    query_params = event.get("queryStringParameters") or {}
    keyword = (query_params.get("keyword") or "ai").strip().lower()

    print(f"Returning mock news for keyword={keyword}")
    return response(200, {
        "keyword": keyword,
        "items": [
            {
                "title": f"Mock {keyword.upper()} serverless news",
                "summary": "This is a mock summary for Day 4 implementation.",
                "source": "mock",
                "url": "https://example.com",
                "publishedAt": "2026-05-25"
            }
        ]
    })


def handle_create_keyword(event):
    if table is None:
        return error_response(500, "keyword_table_not_configured")

    body = parse_body(event)
    if body is None:
        return error_response(400, "invalid_json_body")

    keyword = str(body.get("keyword", "")).strip().lower()
    if not keyword:
        return error_response(400, "keyword_required")

    item = {
        "user_id": USER_ID,
        "keyword": keyword,
        "created_at": now_iso()
    }

    print(f"Creating keyword item: {item}")
    table.put_item(Item=item)

    return response(201, {
        "message": "keyword created",
        "item": item
    })


def handle_get_keywords():
    if table is None:
        return error_response(500, "keyword_table_not_configured")

    print(f"Querying keywords for user_id={USER_ID}")

    result = table.query(
        KeyConditionExpression=Key("user_id").eq(USER_ID)
    )

    items = [
        {
            "user_id": item.get("user_id"),
            "keyword": item.get("keyword"),
            "created_at": item.get("created_at")
        }
        for item in result.get("Items", [])
    ]

    return response(200, {"items": items})


def handle_delete_keyword(event):
    if table is None:
        return error_response(500, "keyword_table_not_configured")

    path_parameters = event.get("pathParameters") or {}
    keyword = str(path_parameters.get("keyword", "")).strip().lower()
    if not keyword:
        path = event.get("rawPath") or event.get("path", "")
        if path.startswith("/keywords/"):
            keyword = path.removeprefix("/keywords/").strip().lower()

    if not keyword:
        return error_response(400, "keyword_required")

    print(f"Deleting keyword={keyword} for user_id={USER_ID}")
    table.delete_item(
        Key={
            "user_id": USER_ID,
            "keyword": keyword
        }
    )

    return response(200, {
        "message": "keyword deleted",
        "keyword": keyword
    })


def lambda_handler(event, context):
    print("Received event:", json.dumps(event, ensure_ascii=False))

    try:
        route = get_route(event)
        print(f"Resolved route: {route}")

        if route == "GET /health":
            return handle_health()
        if route == "GET /news":
            return handle_get_news(event)
        if route == "POST /keywords":
            return handle_create_keyword(event)
        if route == "GET /keywords":
            return handle_get_keywords()
        if route == "DELETE /keywords/{keyword}" or route.startswith("DELETE /keywords/"):
            return handle_delete_keyword(event)

        return error_response(404, "not_found")
    except Exception as exc:
        print(f"Unhandled error: {exc}")
        return error_response(500, "internal_server_error")
