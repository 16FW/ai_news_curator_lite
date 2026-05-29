import json
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key


SERVICE_NAME = "ai_news_curator_lite"
# TODO: Replace the MVP demo user with a JWT/Cognito user id after auth is added.
USER_ID = "demo_user"
KEYWORD_TABLE_NAME = os.environ.get("KEYWORD_TABLE_NAME")
NEWS_TABLE_NAME = os.environ.get("NEWS_TABLE_NAME")

dynamodb = boto3.resource("dynamodb")
keyword_table = dynamodb.Table(KEYWORD_TABLE_NAME) if KEYWORD_TABLE_NAME else None
news_table = dynamodb.Table(NEWS_TABLE_NAME) if NEWS_TABLE_NAME else None
MAX_KEYWORD_LENGTH = 40
ALLOWED_KEYWORD_SYMBOLS = set(" -_")
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS"
}

SEED_NEWS_BY_KEYWORD = {
    "ai": [
        {
            "keyword": "ai",
            "published_at": "2026-05-26T00:00:00Z",
            "title": "AI infrastructure shifts toward smaller production models",
            "summary": "Teams are focusing on reliable smaller models, cost controls, and monitoring before expanding AI features.",
            "source": "seed",
            "url": "https://example.com/news/ai-infrastructure",
            "image_url": "https://example.com/images/ai-infrastructure.png"
        }
    ],
    "aws": [
        {
            "keyword": "aws",
            "published_at": "2026-05-26T00:00:00Z",
            "title": "Serverless teams refine Lambda and DynamoDB cost practices",
            "summary": "PAY_PER_REQUEST tables and lean Lambda handlers remain a practical baseline for early MVP backends.",
            "source": "seed",
            "url": "https://example.com/news/serverless-cost",
            "image_url": "https://example.com/images/serverless-cost.png"
        }
    ],
    "cloud": [
        {
            "keyword": "cloud",
            "published_at": "2026-05-26T00:00:00Z",
            "title": "Cloud backend MVPs favor managed services for faster delivery",
            "summary": "API Gateway, Lambda, and DynamoDB provide a small operational surface for portfolio-scale systems.",
            "source": "seed",
            "url": "https://example.com/news/cloud-mvp",
            "image_url": "https://example.com/images/cloud-mvp.png"
        }
    ]
}


def response(status_code, body, success=True, message="ok"):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            **CORS_HEADERS
        },
        "body": json.dumps({
            "success": success,
            "data": body if success else None,
            "message": message
        }, ensure_ascii=False)
    }


def error_response(status_code, code, message=None):
    error_message = message or code
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            **CORS_HEADERS
        },
        "body": json.dumps({
            "success": False,
            "data": None,
            "message": error_message,
            "error": {
                "code": code,
                "message": error_message
            }
        }, ensure_ascii=False)
    }


def cors_preflight_response():
    return {
        "statusCode": 204,
        "headers": CORS_HEADERS,
        "body": ""
    }


def parse_body(event):
    raw_body = event.get("body")
    if not raw_body:
        return None

    try:
        return json.loads(raw_body)
    except (TypeError, json.JSONDecodeError):
        return None


def validate_keyword(value, field_name="keyword"):
    if not isinstance(value, str):
        return None, f"{field_name}_must_be_string"

    keyword = value.strip().lower()
    if not keyword:
        return None, f"{field_name}_required"
    if len(keyword) > MAX_KEYWORD_LENGTH:
        return None, f"{field_name}_too_long"
    if any(not (char.isalnum() or char in ALLOWED_KEYWORD_SYMBOLS) for char in keyword):
        return None, f"{field_name}_invalid_characters"

    return keyword, None


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
    keyword_value = query_params.get("keyword") or "ai"
    keyword, validation_error = validate_keyword(keyword_value)
    if validation_error:
        return error_response(400, validation_error)

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
    if keyword_table is None:
        return error_response(500, "keyword_table_not_configured")

    body = parse_body(event)
    if body is None:
        return error_response(400, "invalid_json_body")
    if not isinstance(body, dict):
        return error_response(400, "json_body_must_be_object")

    keyword, validation_error = validate_keyword(body.get("keyword"))
    if validation_error:
        return error_response(400, validation_error)

    item = {
        "user_id": USER_ID,
        "keyword": keyword,
        "created_at": now_iso()
    }

    print(f"Creating keyword item: {item}")
    keyword_table.put_item(Item=item)

    return response(201, {
        "item": item
    }, message="keyword created")


def handle_get_keywords():
    if keyword_table is None:
        return error_response(500, "keyword_table_not_configured")

    print(f"Querying keywords for user_id={USER_ID}")

    result = keyword_table.query(
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
    if keyword_table is None:
        return error_response(500, "keyword_table_not_configured")

    path_parameters = event.get("pathParameters") or {}
    keyword_value = path_parameters.get("keyword", "")
    if not keyword_value:
        path = event.get("rawPath") or event.get("path", "")
        if path.startswith("/keywords/"):
            keyword_value = path.removeprefix("/keywords/")

    keyword, validation_error = validate_keyword(keyword_value)
    if validation_error:
        return error_response(400, validation_error)

    print(f"Deleting keyword={keyword} for user_id={USER_ID}")
    keyword_table.delete_item(
        Key={
            "user_id": USER_ID,
            "keyword": keyword
        }
    )

    return response(200, {
        "keyword": keyword
    }, message="keyword deleted")


def get_user_keywords():
    if keyword_table is None:
        raise RuntimeError("keyword_table_not_configured")

    result = keyword_table.query(
        KeyConditionExpression=Key("user_id").eq(USER_ID)
    )

    return [
        item.get("keyword")
        for item in result.get("Items", [])
        if item.get("keyword")
    ]


def normalize_news_item(item):
    return {
        "keyword": item.get("keyword"),
        "title": item.get("title"),
        "summary": item.get("summary"),
        "source": item.get("source"),
        "url": item.get("url"),
        "image_url": item.get("image_url"),
        "published_at": item.get("published_at")
    }


def query_news_for_keyword(keyword):
    if news_table is None:
        return []

    result = news_table.query(
        KeyConditionExpression=Key("keyword").eq(keyword),
        ScanIndexForward=False,
        Limit=5
    )

    return [
        normalize_news_item(item)
        for item in result.get("Items", [])
    ]


def seed_news_for_keyword(keyword):
    return [
        normalize_news_item(item)
        for item in SEED_NEWS_BY_KEYWORD.get(keyword, [])
    ]


def handle_get_today_news():
    if keyword_table is None:
        return error_response(500, "keyword_table_not_configured")

    keywords = get_user_keywords()
    items = []

    for keyword in keywords:
        keyword_news = query_news_for_keyword(keyword)
        if not keyword_news:
            keyword_news = seed_news_for_keyword(keyword)
        items.extend(keyword_news)

    items.sort(key=lambda item: item.get("published_at") or "", reverse=True)

    return response(200, {
        "user_id": USER_ID,
        "keywords": keywords,
        "items": items
    })


def lambda_handler(event, context):
    print("Received event:", json.dumps(event, ensure_ascii=False))

    try:
        route = get_route(event)
        print(f"Resolved route: {route}")

        if route.startswith("OPTIONS "):
            return cors_preflight_response()
        if route == "GET /health":
            return handle_health()
        if route == "GET /news/today":
            return handle_get_today_news()
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
