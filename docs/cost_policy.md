# Cost Policy

AI News Curator Lite는 10일 MVP 프로젝트이므로 비용이 낮고 관리가 쉬운 AWS 서버리스 구성을 우선합니다.

## Principles

- EC2 상시 배포는 사용하지 않습니다.
- RDS/MySQL은 사용하지 않습니다.
- Lambda, API Gateway, DynamoDB, S3, CloudFront 중심으로 구성합니다.
- CloudWatch 로그 보관 기간은 짧게 설정합니다.
- 테스트 데이터와 임시 리소스는 실습 후 정리합니다.

## Initial Cost Control

- 프론트엔드는 S3 정적 호스팅과 CloudFront를 사용합니다.
- 백엔드는 Lambda 온디맨드 실행을 사용합니다.
- 데이터 저장소는 DynamoDB 온디맨드 또는 낮은 트래픽 기준 설정을 사용합니다.
- 부하 테스트는 짧은 시간 동안 제한된 요청량으로 실행합니다.
