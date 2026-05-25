# AI News Curator Lite

서버리스 기반 AI/IT 뉴스 큐레이션 MVP 프로젝트입니다.

## Project Name

ai_news_curator_lite

## Goal

사용자가 관심 키워드를 등록하면 관련 뉴스 요약 카드를 조회하고, 저장/좋아요/인기 키워드 통계를 확인할 수 있는 서비스를 구현합니다.

이 프로젝트는 단순 CRUD가 아니라 AWS 서버리스 아키텍처 설계, 비용 최적화, 배포, 모니터링, 부하 테스트, 실사용자 지표 수집까지 포함하는 백엔드/클라우드 포트폴리오용 MVP입니다.

## Target Users

- 컴퓨터공학과 학생
- 개발자 취업 준비생
- 기술 트렌드를 빠르게 읽고 싶은 입문자
- AI/백엔드/클라우드 뉴스를 매일 간단히 확인하고 싶은 사람

## MVP Scope

### 필수 기능

- 관심 키워드 등록/조회/삭제
- 오늘의 뉴스 카드 조회
- 키워드별 뉴스 조회
- 뉴스 저장
- 뉴스 좋아요
- 인기 키워드 통계
- 관리자 뉴스 등록
- CloudWatch 로그/메트릭 확인
- k6 부하 테스트
- 실사용자 지표 수집

### 제외 기능

- 자동 뉴스 크롤링
- 복잡한 회원가입/로그인
- JWT 인증
- 실시간 AI 요약 호출
- 추천 알고리즘 고도화
- 관리자 전용 프론트 페이지
- EC2 상시 배포
- RDS/MySQL 사용

## Architecture

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

Monitoring:
CloudWatch Logs
CloudWatch Metrics

User Analytics:
GA4 or Custom Event API

Admin Input:
Admin API or JSON bulk upload
```
