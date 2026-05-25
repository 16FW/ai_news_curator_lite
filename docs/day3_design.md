# Day 3 Design

## 프로젝트 개요

AI News Curator Lite는 사용자가 관심 키워드를 고르면 IT, AI, 백엔드, 클라우드 관련 뉴스를 짧은 카드 형태로 확인하고, 저장/좋아요/인기 키워드 통계를 볼 수 있는 서버리스 기반 MVP입니다.

## 기본 아키텍처

```text
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

## 운영 구성

- 모니터링: CloudWatch Logs, CloudWatch Metrics
- 사용자 지표 수집: GA4 또는 Custom Event API
- 관리자 입력: Admin API 또는 JSON bulk upload

## DynamoDB 테이블 설계

### users_keywords

사용자별 관심 키워드를 저장하는 테이블입니다. 복잡한 인증은 MVP 범위에서 제외하므로 `user_id`는 임시 사용자 식별자 또는 클라이언트에서 전달하는 식별자를 사용합니다.

- 목적: 사용자 관심 키워드 등록, 조회, 삭제
- Partition Key: `user_id`
- Sort Key: `keyword`
- 필요한 GSI: 없음
- 주요 Attribute: `user_id`, `keyword`, `created_at`

예시 JSON:

```json
{
  "user_id": "demo_user_001",
  "keyword": "AWS",
  "created_at": "2026-05-25T10:00:00+09:00"
}
```

### news_articles

관리자가 등록한 뉴스 카드 데이터를 저장하는 테이블입니다. 오늘의 뉴스 조회와 키워드별 뉴스 조회가 핵심 Access Pattern이므로 날짜와 키워드 기반 조회를 지원합니다.

- 목적: 뉴스 카드 저장 및 조회
- Partition Key: `article_id`
- Sort Key: 없음
- 필요한 GSI:
  - `published_date_index`: PK `published_date`, SK `created_at`
  - `keyword_index`: PK `keyword`, SK `published_date`
- 주요 Attribute: `article_id`, `title`, `summary`, `url`, `source`, `keyword`, `published_date`, `created_at`, `created_by`, `like_count`, `save_count`

예시 JSON:

```json
{
  "article_id": "article_20260525_001",
  "title": "AWS Lambda SnapStart improves cold start performance",
  "summary": "AWS Lambda의 콜드 스타트 최적화 기능과 서버리스 운영 비용 절감 효과를 소개합니다.",
  "url": "https://example.com/aws-lambda-snapstart",
  "source": "Example Tech",
  "keyword": "AWS",
  "published_date": "2026-05-25",
  "created_at": "2026-05-25T09:30:00+09:00",
  "created_by": "admin",
  "like_count": 0,
  "save_count": 0
}
```

### saved_articles

사용자가 저장한 뉴스 목록을 관리하는 테이블입니다. 사용자별 저장 목록 조회와 특정 기사 저장 여부 확인을 빠르게 처리합니다.

- 목적: 뉴스 저장, 저장 목록 조회, 저장 취소
- Partition Key: `user_id`
- Sort Key: `article_id`
- 필요한 GSI:
  - `article_saved_index`: PK `article_id`, SK `saved_at`
- 주요 Attribute: `user_id`, `article_id`, `saved_at`, `keyword`, `title`

예시 JSON:

```json
{
  "user_id": "demo_user_001",
  "article_id": "article_20260525_001",
  "saved_at": "2026-05-25T10:10:00+09:00",
  "keyword": "AWS",
  "title": "AWS Lambda SnapStart improves cold start performance"
}
```

### article_likes

사용자별 뉴스 좋아요 상태를 저장합니다. 같은 사용자가 같은 기사에 중복 좋아요를 누르지 않도록 `user_id`와 `article_id` 조합을 키로 사용합니다.

- 목적: 뉴스 좋아요 등록, 취소, 중복 방지
- Partition Key: `user_id`
- Sort Key: `article_id`
- 필요한 GSI:
  - `article_likes_index`: PK `article_id`, SK `liked_at`
- 주요 Attribute: `user_id`, `article_id`, `liked_at`, `keyword`

예시 JSON:

```json
{
  "user_id": "demo_user_001",
  "article_id": "article_20260525_001",
  "liked_at": "2026-05-25T10:15:00+09:00",
  "keyword": "AWS"
}
```

### user_events

실사용자 지표를 수집하기 위한 이벤트 테이블입니다. GA4를 우선 사용할 수 있지만, 포트폴리오에서는 Custom Event API를 함께 설계해 서비스 내부 지표 수집 역량을 보여줍니다.

- 목적: 사용자 행동 이벤트 수집
- Partition Key: `user_id`
- Sort Key: `event_time`
- 필요한 GSI:
  - `event_name_index`: PK `event_name`, SK `event_time`
  - `event_date_index`: PK `event_date`, SK `event_time`
- 주요 Attribute: `user_id`, `event_time`, `event_date`, `event_name`, `article_id`, `keyword`, `metadata`

예시 JSON:

```json
{
  "user_id": "demo_user_001",
  "event_time": "2026-05-25T10:20:00+09:00",
  "event_date": "2026-05-25",
  "event_name": "view_news_card",
  "article_id": "article_20260525_001",
  "keyword": "AWS",
  "metadata": {
    "page": "today",
    "device": "desktop"
  }
}
```

## Access Pattern 정리

| Access Pattern | 대상 테이블 | Key 또는 Index | 사용 API |
| --- | --- | --- | --- |
| 사용자 관심 키워드 등록 | `users_keywords` | PK `user_id`, SK `keyword` | `POST /keywords` |
| 사용자 관심 키워드 목록 조회 | `users_keywords` | PK `user_id` | `GET /keywords` |
| 사용자 관심 키워드 삭제 | `users_keywords` | PK `user_id`, SK `keyword` | `DELETE /keywords/{keyword}` |
| 오늘 등록된 뉴스 조회 | `news_articles` | GSI `published_date_index` | `GET /news/today` |
| 키워드별 뉴스 조회 | `news_articles` | GSI `keyword_index` | `GET /news?keyword=AWS` |
| 관리자 뉴스 등록 | `news_articles` | PK `article_id` | `POST /admin/news` |
| 사용자 뉴스 저장 | `saved_articles` | PK `user_id`, SK `article_id` | `POST /saved` |
| 사용자 저장 뉴스 목록 조회 | `saved_articles` | PK `user_id` | `GET /saved` |
| 사용자 저장 뉴스 삭제 | `saved_articles` | PK `user_id`, SK `article_id` | `DELETE /saved/{article_id}` |
| 뉴스 좋아요 등록 | `article_likes` | PK `user_id`, SK `article_id` | `POST /likes` |
| 뉴스 좋아요 취소 | `article_likes` | PK `user_id`, SK `article_id` | `DELETE /likes/{article_id}` |
| 기사별 좋아요 수 집계 보조 | `article_likes` | GSI `article_likes_index` | 내부 집계 또는 운영 확인 |
| 인기 키워드 통계 조회 | `news_articles`, `article_likes`, `saved_articles` | `keyword`, GSI 보조 | `GET /stats/popular-keywords` |
| 사용자 이벤트 수집 | `user_events` | PK `user_id`, SK `event_time` | `POST /events` |
| 이벤트 이름별 조회 | `user_events` | GSI `event_name_index` | 운영 분석 |
| 날짜별 이벤트 조회 | `user_events` | GSI `event_date_index` | 운영 분석 |

## API 명세

MVP에서는 복잡한 로그인과 JWT 인증을 제외하므로 `user_id`는 임시로 요청 헤더 `x_user_id` 또는 요청 본문에서 전달한다고 가정합니다. 운영 단계에서는 인증 계층을 추가해 `user_id`를 서버에서 확정해야 합니다.

### POST /keywords

- 설명: 사용자 관심 키워드 등록
- Request Body:

```json
{
  "keyword": "AWS"
}
```

- Response:

```json
{
  "message": "keyword_created",
  "keyword": "AWS"
}
```

### GET /keywords

- 설명: 사용자 관심 키워드 목록 조회
- Response:

```json
{
  "items": [
    {
      "keyword": "AWS",
      "created_at": "2026-05-25T10:00:00+09:00"
    }
  ]
}
```

### DELETE /keywords/{keyword}

- 설명: 사용자 관심 키워드 삭제
- Response:

```json
{
  "message": "keyword_deleted",
  "keyword": "AWS"
}
```

### GET /news/today

- 설명: 오늘 등록된 뉴스 카드 조회
- Response:

```json
{
  "items": [
    {
      "article_id": "article_20260525_001",
      "title": "AWS Lambda SnapStart improves cold start performance",
      "summary": "AWS Lambda의 콜드 스타트 최적화 기능과 서버리스 운영 비용 절감 효과를 소개합니다.",
      "keyword": "AWS",
      "source": "Example Tech",
      "url": "https://example.com/aws-lambda-snapstart",
      "published_date": "2026-05-25",
      "like_count": 0,
      "save_count": 0
    }
  ]
}
```

### GET /news?keyword=AWS

- 설명: 특정 키워드에 해당하는 뉴스 카드 조회
- Query String: `keyword`
- Response:

```json
{
  "keyword": "AWS",
  "items": [
    {
      "article_id": "article_20260525_001",
      "title": "AWS Lambda SnapStart improves cold start performance",
      "summary": "AWS Lambda의 콜드 스타트 최적화 기능과 서버리스 운영 비용 절감 효과를 소개합니다.",
      "source": "Example Tech",
      "url": "https://example.com/aws-lambda-snapstart",
      "published_date": "2026-05-25"
    }
  ]
}
```

### POST /admin/news

- 설명: 관리자 뉴스 등록
- Request Body:

```json
{
  "title": "AWS Lambda SnapStart improves cold start performance",
  "summary": "AWS Lambda의 콜드 스타트 최적화 기능과 서버리스 운영 비용 절감 효과를 소개합니다.",
  "url": "https://example.com/aws-lambda-snapstart",
  "source": "Example Tech",
  "keyword": "AWS",
  "published_date": "2026-05-25"
}
```

- Response:

```json
{
  "message": "news_created",
  "article_id": "article_20260525_001"
}
```

### POST /saved

- 설명: 뉴스 저장
- Request Body:

```json
{
  "article_id": "article_20260525_001"
}
```

- Response:

```json
{
  "message": "article_saved",
  "article_id": "article_20260525_001"
}
```

### GET /saved

- 설명: 사용자 저장 뉴스 목록 조회
- Response:

```json
{
  "items": [
    {
      "article_id": "article_20260525_001",
      "title": "AWS Lambda SnapStart improves cold start performance",
      "keyword": "AWS",
      "saved_at": "2026-05-25T10:10:00+09:00"
    }
  ]
}
```

### DELETE /saved/{article_id}

- 설명: 저장한 뉴스 삭제
- Response:

```json
{
  "message": "saved_article_deleted",
  "article_id": "article_20260525_001"
}
```

### POST /likes

- 설명: 뉴스 좋아요 등록
- Request Body:

```json
{
  "article_id": "article_20260525_001"
}
```

- Response:

```json
{
  "message": "article_liked",
  "article_id": "article_20260525_001"
}
```

### DELETE /likes/{article_id}

- 설명: 뉴스 좋아요 취소
- Response:

```json
{
  "message": "article_like_deleted",
  "article_id": "article_20260525_001"
}
```

### GET /stats/popular-keywords

- 설명: 저장 수, 좋아요 수, 조회 이벤트 등을 기반으로 인기 키워드 통계 조회
- Response:

```json
{
  "items": [
    {
      "keyword": "AWS",
      "score": 18,
      "like_count": 8,
      "save_count": 5,
      "view_count": 5
    }
  ]
}
```

### POST /events

- 설명: 사용자 행동 이벤트 수집
- Request Body:

```json
{
  "event_name": "view_news_card",
  "article_id": "article_20260525_001",
  "keyword": "AWS",
  "metadata": {
    "page": "today",
    "device": "desktop"
  }
}
```

- Response:

```json
{
  "message": "event_recorded"
}
```

## Lambda 함수 단위 설계

엔드포인트별로 Lambda 함수를 분리해 포트폴리오에서 책임 범위와 CloudWatch 모니터링 단위를 명확히 보여줍니다. 실제 운영에서는 트래픽 규모와 배포 단위를 고려해 일부 함수를 통합할 수 있습니다.

| Lambda 함수 | API | 주요 책임 | 사용 테이블 |
| --- | --- | --- | --- |
| `create_keyword_function` | `POST /keywords` | 관심 키워드 등록, 중복 등록 방지 | `users_keywords` |
| `list_keywords_function` | `GET /keywords` | 사용자별 관심 키워드 목록 조회 | `users_keywords` |
| `delete_keyword_function` | `DELETE /keywords/{keyword}` | 관심 키워드 삭제 | `users_keywords` |
| `list_today_news_function` | `GET /news/today` | 오늘 날짜 기준 뉴스 카드 조회 | `news_articles` |
| `list_news_by_keyword_function` | `GET /news?keyword=AWS` | 키워드별 뉴스 카드 조회 | `news_articles` |
| `create_admin_news_function` | `POST /admin/news` | 관리자 뉴스 등록, 기본 카운터 초기화 | `news_articles` |
| `save_article_function` | `POST /saved` | 뉴스 저장, 중복 저장 방지 | `saved_articles`, `news_articles` |
| `list_saved_articles_function` | `GET /saved` | 사용자 저장 뉴스 목록 조회 | `saved_articles` |
| `delete_saved_article_function` | `DELETE /saved/{article_id}` | 저장 뉴스 삭제 | `saved_articles`, `news_articles` |
| `like_article_function` | `POST /likes` | 뉴스 좋아요 등록, 중복 좋아요 방지 | `article_likes`, `news_articles` |
| `delete_article_like_function` | `DELETE /likes/{article_id}` | 뉴스 좋아요 취소 | `article_likes`, `news_articles` |
| `popular_keywords_function` | `GET /stats/popular-keywords` | 인기 키워드 통계 계산 및 반환 | `news_articles`, `saved_articles`, `article_likes`, `user_events` |
| `record_event_function` | `POST /events` | 사용자 행동 이벤트 저장 | `user_events` |

## AWS SAM 기반 infra 구조 초안

Day 4부터 AWS SAM을 기준으로 로컬 빌드와 로컬 API 실행이 가능하도록 구성합니다. Day 3에서는 실제 코드를 작성하지 않고, 다음 구조를 기준으로 구현 범위를 확정합니다.

```text
ai_news_curator_lite/
  backend/
    src/
      common/
      keywords/
      news/
      saved/
      likes/
      stats/
      events/
  infra/
    template.yaml
  docs/
    day3_design.md
  scripts/
    seed_news.py
  tests/
    k6/
      smoke_test.js
```

### SAM template 설계 방향

- Runtime: Python 또는 Node.js 중 하나로 통일
- API: API Gateway HTTP API
- Compute: Lambda 함수는 엔드포인트별 분리
- Database: DynamoDB 5개 테이블 정의
- Permissions: 함수별 최소 DynamoDB 권한 부여
- Logs: Lambda 기본 CloudWatch Logs 사용
- Environment Variables:
  - `USERS_KEYWORDS_TABLE`
  - `NEWS_ARTICLES_TABLE`
  - `SAVED_ARTICLES_TABLE`
  - `ARTICLE_LIKES_TABLE`
  - `USER_EVENTS_TABLE`

## Day 4 구현 작업 단위

Day 4는 설계된 전체 MVP 중 핵심 조회 흐름과 관리자 등록 흐름만 구현합니다. 저장, 좋아요, 통계, 이벤트 수집은 이후 단계에서 구현합니다.

1. 공통 유틸 작성
   - JSON 응답 포맷
   - 에러 응답 포맷
   - 현재 시간 생성
   - 요청 본문 파싱
   - `user_id` 추출

2. 키워드 API 구현
   - `POST /keywords`
   - `GET /keywords`
   - `DELETE /keywords/{keyword}`

3. 관리자 뉴스 등록 API 구현
   - `POST /admin/news`
   - 필수 필드 검증
   - `article_id` 생성
   - `like_count`, `save_count` 초기화

4. 오늘의 뉴스 조회 API 구현
   - `GET /news/today`
   - `published_date_index` 기반 조회

5. 키워드별 뉴스 조회 API 구현
   - `GET /news?keyword=AWS`
   - `keyword_index` 기반 조회

6. `infra/template.yaml` 초안 작성
   - DynamoDB 테이블 5개 정의
   - Day 4 대상 Lambda 함수 정의
   - API Gateway HTTP API 라우팅 정의
   - Lambda 환경 변수 정의
   - DynamoDB 접근 권한 정의

7. `sam build`
   - SAM 템플릿과 Lambda 패키징 검증

8. `sam local start-api`
   - 로컬 API Gateway 실행
   - DynamoDB Local 또는 실제 AWS DynamoDB 연결 방식 결정

9. curl 또는 Postman 테스트
   - 키워드 등록, 조회, 삭제
   - 관리자 뉴스 등록
   - 오늘의 뉴스 조회
   - 키워드별 뉴스 조회
