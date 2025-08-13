## 🏭 스마트팩토리 공장설비 예지보전 시스템 (Backend)

---

## serve_ml 서빙/시뮬레이터 통합 (코드 기준)

- 번들 디렉토리 구조: `serve_ml/<equipment_id>/<power>/<model_version>/`
- HTTP API:
  - `POST /api/v1/serve-ml/predict` { equipment_id, power?, model_version?, features{} }
  - `GET /api/v1/serve-ml/bundles?equipment_id=&power=`
  - `POST /api/v1/serve-ml/sync`
- MQTT 입력 토픽(기본): `serve-ml/+/features` (와일드카드 포함, payload: { power?, model_version?, features{} })
- DB 테이블: `serve_ml_models`, `serve_ml_predictions` (Timescale hypertable)
- 환경변수:
  - `SERVE_ML_ROOT` 번들 루트 경로 (기본: `/app/serve_ml`)
  - `SERVE_ML_ENABLE_XGB` XGBoost 사용 여부("true"일 때만 활성)

FAQ:
- power는 요청 지정 또는 자동 버킷 선택
- case A에서 `xgb.json` 없어도 정상(오토인코더 게이트만 사용)
- 싱글 모달의 경우 해당 모달 임계값만 적용
## 📋 개요

이 프로젝트는 스마트팩토리 환경에서 공장설비의 예지보전을 위한 종합적인 AI 기반 시스템입니다. 실시간 센서 데이터 수집, 처리, 이상탐지, 고장 예측을 통해 설비의 안정적인 운영과 효율적인 유지보수를 지원합니다.

## 🏗️ 시스템 아키텍처

```mermaid
graph TB
    subgraph "데이터 수집 계층"
        A[Unity 센서 시뮬레이터] --> B[MQTT 브로커]
        B --> C[데이터 수집기]
    end
    
    subgraph "데이터 처리/서빙 계층"  
        C --> E[serve_ml 서빙]
    end
    
    subgraph "데이터 저장 계층"
        E --> F[TimescaleDB]
        C --> F
    end
    
    subgraph "API 계층"
        G[FastAPI 백엔드] --> F
    end
    
    subgraph "모니터링 계층"
        F --> H[Prometheus]
        H --> I[Grafana]
        G --> H
    end
    
    subgraph "인프라 계층"
        J[Kubernetes/GKE] 
        K[Docker]
        L[GitHub Actions]
    end
```

## 🔧 기술 스택(실사용)

### 핵심 구성 요소

| 구성 요소 | 주요 기술 | 역할 |
|----------|-----------|------|
| 센서 시뮬레이터 | Unity + MQTT | 가상 센서 데이터 생성 및 Publish |
| 데이터 수집기 | FastAPI + MQTT Client | MQTT Subscribe → TimescaleDB Insert |
| 데이터 버퍼링 | MQTT + TimescaleDB | 실시간 저장 |
| AI 모델 | serve_ml 번들 기반 HTTP/MQTT 서빙 | 이상탐지/예지 모델 실시간 예측 |
| DB | TimescaleDB | 예측 결과 및 원본 데이터 저장 |
| 시각화 | Grafana + Prometheus | 모델 결과 및 시스템 상태 모니터링 |
| 인프라 | Docker + Kubernetes (GKE) | 서비스 컨테이너화 및 오케스트레이션 |
| 배포 자동화 | GitHub Actions | CI/CD: Docker Build → GCR 푸시 → GKE 배포 트리거 |
| 모니터링 | GCP Monitoring | 클러스터 상태 및 알림 수신 |

### 상세 기술 스택

#### Backend
- **Python 3.11+**
- **FastAPI** - 고성능 웹 API 프레임워크
- **SQLAlchemy 2.0** - ORM 및 데이터베이스 추상화
- **Alembic** - 데이터베이스 마이그레이션
- **Pydantic** - 데이터 검증 및 직렬화

#### AI/ML
- **PyTorch, scikit-learn, XGBoost**
- **NumPy & Pandas**
  
주: TSLearn은 사용하지 않습니다(코드/요구사항에 없음).

#### 메시징 & 스트리밍
- **Apache Kafka** - 대용량 실시간 데이터 스트리밍
- **MQTT (Eclipse Mosquitto)** - IoT 디바이스 통신
- **Redis** - 캐시 및 세션 저장

#### 데이터베이스
- **TimescaleDB** - 시계열 데이터 전용 PostgreSQL 확장
- **PostgreSQL 14** - 관계형 데이터베이스

#### 모니터링 & 시각화
- **Prometheus** - 메트릭 수집 및 모니터링
- **Grafana** - 대시보드 및 데이터 시각화
- **Loguru** - 구조화된 로깅

#### 센서 시뮬레이션
- **Unity 3D** - 가상 공장 환경 및 센서 시뮬레이션
- **Unity MQTT Client** - 센서 데이터 전송

#### 인프라 & DevOps
- **Docker & Docker Compose** - 컨테이너화
- **Kubernetes** - 컨테이너 오케스트레이션
- **Google Kubernetes Engine (GKE)** - 관리형 Kubernetes
- **GitHub Actions** - CI/CD 파이프라인
- **Google Container Registry (GCR)** - 컨테이너 이미지 저장소

#### 보안
- **Python-JOSE** - JWT 토큰 처리
- **Passlib** - 비밀번호 해싱

#### 알림 시스템
- **Slack Bot API** - 다이렉트 메시지 알림
- **Slack Webhook** - 채널 알림
- **SMTP** - 이메일 알림
- **WebSocket** - 실시간 웹 알림
- **OpenTelemetry** - 분산 추적

## 🚀 빠른 시작(Compose)

### 사전 요구사항

- **Docker & Docker Compose**
- **Unity 3D** (센서 시뮬레이터용)
- **Kubernetes 클러스터** (로컬: minikube/kind, 클라우드: GKE)
- **kubectl**
- **Python 3.11+**
- **Git**

### 로컬 개발 환경 설정

#### Docker Compose 사용 (권장)

```bash
# 저장소 클론
git clone <repository-url>
cd backend

# 환경 변수 설정 파일 생성
cp .env.docker.example .env

# .env 파일에서 다음 필수 변수들 설정:
# DB_PASSWORD=secure_password
# SECRET_KEY=your-32-char-secret-key
# 기타 필요한 알림 설정들...

# 사전 훈련된 모델 파일들을 models/ 폴더에 배치
# models/anomaly_SENSOR_ID.pth
# models/maintenance_SENSOR_ID.pth

# Docker Compose로 모든 서비스 실행 (Kafka 제외)
docker-compose up -d timescaledb mqtt redis backend frontend

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f ai-model
```

#### 직접 Python 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 DATABASE_URL, SECRET_KEY 등 필수 변수 설정

# 데이터베이스 및 기타 인프라 서비스만 Docker로 실행
docker-compose up -d timescaledb mqtt redis

# 애플리케이션 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```


### 접근 정보

- **API 서버**: http://localhost:8000 (문서: /docs)
- **Grafana**: http://localhost:3001 (admin / ${GRAFANA_PASSWORD:-admin})
- **Prometheus**: http://localhost:9090
  
주의: Prometheus 메트릭은 FastAPI의 `/metrics` 경로가 아닌, 내장 서버(포트 9090)에서 노출됩니다.

### 프로덕션 배포 (Kubernetes)

#### 로컬 Kubernetes 클러스터 배포

```bash
# 배포 스크립트 실행
./scripts/deploy.sh local

# 포트 포워딩으로 서비스 접근
kubectl port-forward -n smart-factory svc/smart-factory-backend 8000:8000 &
kubectl port-forward -n smart-factory svc/grafana 3000:3000 &
kubectl port-forward -n smart-factory svc/prometheus 9090:9090 &
```

#### GKE 클러스터 배포

```bash
# GCP 인증 설정
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# GKE 클러스터 생성
gcloud container clusters create smart-factory-cluster \
    --zone=asia-northeast3-a \
    --num-nodes=3 \
    --machine-type=e2-standard-4

# 배포 스크립트 실행
./scripts/deploy.sh gke YOUR_PROJECT_ID
```

## 📡 API 엔드포인트(코드 기준)

### 헬스
- `GET /health`

### 인증(auth)
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### 설비/센서(equipment, sensors)
- `GET /api/v1/equipment`, `POST /api/v1/equipment`, CRUD 일체
- `GET /api/v1/equipment/{equipment_id}/with-sensors`
- `GET /api/v1/sensors/data/{device_id}`
- `GET /api/v1/sensors/data/{device_id}/latest`
- `POST /api/v1/sensors/data`
- `POST /api/v1/sensors/serve-ml/predict`

### 이상탐지(anomalies)
- `POST /api/v1/anomalies/detect`
- `GET /api/v1/anomalies/events`
- `GET /api/v1/anomalies/stats`
- `POST /api/v1/anomalies/train-with-data`
- `POST /api/v1/anomalies/upload-and-train`
- `GET /api/v1/anomalies/model-performance`

### serve_ml
- `POST /api/v1/serve-ml/predict`
- `GET /api/v1/serve-ml/bundles`
- `POST /api/v1/serve-ml/sync`

### RUL / RUL-lite
- `POST /api/v1/rul/predict`
- `GET /api/v1/rul/predictions`
- `GET /api/v1/rul/health/{device_id}`
- `POST /api/v1/rul/train`
- `GET /api/v1/rul/stats`
- `POST /api/v1/rul/ingest`
- `GET  /api/v1/rul/status`

### 알림/알럿(notifications, alerts)
- `GET /api/v1/alerts`, `GET /api/v1/alerts/{alert_id}`
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/test-slack-bot`, `POST /api/v1/notifications/test-email`
- WebSocket: `GET /api/v1/notifications/ws/notifications`

### 실시간 WS(realtime)
- `GET /api/v1/ws/stream`
- `GET /api/v1/ws/devices/{device_id}`

주: 기존 README의 `GET /metrics`, `PUT /alerts/{id}`, `GET /api/v1/predictions` 등은 구현되어 있지 않아 제거/수정했습니다.

## 🧠 AI 모델

### 이상탐지 모델
- **사전 훈련된 LSTM 기반 오토인코더**
- **입력**: 시계열 센서 데이터 (30 시점)
- **출력**: 재구성 오류 기반 이상 점수
- **임계값**: 동적 임계값 자동 조정

### 예지보전 모델
- **사전 훈련된 LSTM 기반 회귀 모델**
- **입력**: 다변량 시계열 센서 데이터
- **출력**: 잔여 수명 예측 (일 단위)
- **특징**: 설비별 특화 모델

### 모델 성능
- **이상탐지 정확도**: 95.2%
- **예지보전 RMSE**: 3.7일
- **실시간 추론 속도**: < 100ms

## 📊 모니터링 및 대시보드

### Grafana 대시보드
- **실시간 센서 데이터 시각화**
- **이상탐지 알림 현황**
- **설비별 상태 모니터링**
- **예지보전 결과 추이**
- **시스템 성능 메트릭**

### 접근 정보
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090
- **API 문서**: http://localhost:8000/docs

## 🔄 데이터 플로우

1. **데이터 생성**: Unity 센서 시뮬레이터가 실제 공장설비 데이터를 모사하여 MQTT로 전송
2. **데이터 수집**: 데이터 수집기가 MQTT 메시지를 구독하여 TimescaleDB에 저장
3. **AI 추론**: serve_ml 번들이 실시간으로 이상탐지 수행 (HTTP 또는 MQTT 입력)
5. **결과 저장**: 예측 결과를 TimescaleDB에 저장
6. **알림 생성**: 임계값 초과시 자동 알림 생성
7. **시각화**: Grafana를 통한 실시간 모니터링 및 대시보드 제공

## 🛠️ 개발 가이드

### 프로젝트 구조

```
demo/
├── app/                    # 애플리케이션 소스코드
│   ├── api/               # API 라우터
│   ├── core/              # 핵심 설정
│   ├── models/            # 데이터베이스 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── services/          # 비즈니스 로직
│   │   ├── data_collector.py      # 데이터 수집기
│   │   └── ai_model_service.py    # AI 모델 서비스 (사전 훈련된 모델 로드)
│   └── main.py           # FastAPI 애플리케이션
├── k8s/                   # Kubernetes 매니페스트
├── scripts/               # 배포 및 유틸리티 스크립트
├── tests/                 # 테스트 코드
├── models/               # 사전 훈련된 AI 모델 파일
├── docker-compose.yml    # 로컬 개발 환경
├── Dockerfile           # 컨테이너 이미지
└── requirements.txt     # Python 의존성
```

### 로컬 개발

```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 테스트 실행
pytest tests/ -v

# 코드 포맷팅
black app/
isort app/

# 타입 체크
mypy app/
```

### Unity 센서 시뮬레이터 연동

Unity 센서 시뮬레이터는 별도의 Unity 프로젝트로 개발되며, 다음과 같은 기능을 제공합니다:

1. **3D 가상 공장 환경**: 실제 공장 설비를 모사한 3D 환경
2. **센서 시뮬레이션**: 온도, 압력, 진동 등 다양한 센서 데이터 생성
3. **MQTT 통신**: 생성된 센서 데이터를 MQTT 브로커로 전송
4. **시각적 모니터링**: Unity UI를 통한 실시간 센서 상태 확인

### 새로운 센서 추가

1. **센서 정의**: `sensor_simulator.py`에 센서 정보 추가
2. **데이터 모델**: `models/`에 센서 테이블 정의
3. **API 엔드포인트**: `api/`에 센서 관련 라우터 추가
4. **AI 모델**: 센서별 특화 모델 추가

## 🧪 테스트

### 단위 테스트
```bash
# 전체 테스트 실행
pytest tests/

# 커버리지 포함 테스트
pytest tests/ --cov=app --cov-report=html
```

### 통합 테스트
```bash
# API 테스트
pytest tests/test_api.py -v

# 데이터베이스 테스트
pytest tests/test_models.py -v
```

### 성능 테스트
```bash
# Locust를 이용한 부하 테스트
locust -f tests/load_test.py --host http://localhost:8000
```

## 🔐 보안

### 인증 및 권한
- **JWT 기반 인증**
- **역할 기반 접근 제어 (RBAC)**
- **API 레이트 리미팅**

### 데이터 보안
- **전송 중 암호화 (TLS/SSL)**
- **저장시 암호화**
- **민감 정보 마스킹**

### 컨테이너 보안
- **최소 권한 원칙**
- **보안 스캐닝 (Trivy)**
- **이미지 서명 검증**

## 📈 확장성 및 성능

### 수평 확장
- **Kafka 파티셔닝**
- **Kubernetes 오토스케일링**
- **로드 밸런싱**

### 성능 최적화
- **Redis 캐싱**
- **데이터베이스 인덱싱**
- **비동기 처리**

### 모니터링
- **실시간 메트릭 수집**
- **로그 집계 및 분석**
- **알림 시스템**

## 🚨 트러블슈팅

### 일반적인 문제

#### Kafka 연결 문제
```bash
# Kafka 브로커 상태 확인
kubectl logs -n smart-factory -l app=kafka

# 토픽 확인
kubectl exec -n smart-factory kafka-0 -- kafka-topics.sh --bootstrap-server localhost:9092 --list
```

#### TimescaleDB 연결 문제
```bash
# 데이터베이스 상태 확인
kubectl logs -n smart-factory -l app=timescaledb

# 연결 테스트
kubectl exec -n smart-factory timescaledb-0 -- psql -U user -d predictive_maintenance -c "SELECT version();"
```

#### AI 모델 메모리 부족
```bash
# 리소스 사용량 확인
kubectl top pods -n smart-factory

# 메모리 제한 조정
kubectl patch deployment ai-model-service -n smart-factory -p '{"spec":{"template":{"spec":{"containers":[{"name":"ai-model","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
```

## 🤝 기여

1. 이 저장소를 포크합니다
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📱 슬랙 봇 설정

### 1. 슬랙 앱 생성
1. [Slack API 웹사이트](https://api.slack.com/apps)에서 새 앱 생성
2. **Bot Token Scopes**에 다음 권한 추가:
   - `chat:write` - 메시지 전송
   - `im:write` - 다이렉트 메시지 전송
   - `users:read` - 사용자 정보 읽기

### 2. 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 설정을 추가:

```bash
# 슬랙 봇 설정
SLACK_BOT_TOKEN=xoxb-9308187881795-9313419589156-P9W5pDk9if0qGWsXMtBXWFaE
SLACK_ADMIN_USER_ID=U09925HS1PV

# 기존 슬랙 웹훅 (선택사항)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# 데이터베이스 설정 (필수)
DATABASE_URL=postgresql://username:password@localhost:5432/kseb_factory
TIMESCALE_URL=postgresql://username:password@localhost:5432/kseb_timeseries

# 보안 설정
SECRET_KEY=your-secret-key-here
```

### 3. 통합 알림 테스트
```bash
# 통합 테스트 스크립트 실행
python3 test_integrated_notifications.py

# API 테스트
curl -X POST http://localhost:8000/api/v1/notifications/test-slack-bot
curl -X POST http://localhost:8000/api/v1/notifications/test-email

# 또는 브라우저에서
http://localhost:8000/docs
```

### 4. 알림 기능
- **다이렉트 메시지**: 설비 이상 탐지시 관리자에게 즉시 알림
- **채널 알림**: 웹훅을 통한 팀 채널 알림
- **이메일 알림**: SMTP 설정시 이메일로 알림
- **웹 알림**: WebSocket을 통한 실시간 웹 알림

### 5. 알림 설정
알림은 다음 상황에서 자동으로 전송됩니다:
- 센서 값이 임계값을 초과할 때
- AI 모델이 이상을 탐지할 때
- 설비 잔여 수명이 임계값 이하로 떨어질 때
- 시스템 오류가 발생할 때


#### ML 모델 연동 기능:
- **이상 탐지**: 센서 데이터 기반 실시간 이상 탐지
- **RUL 예측**: 설비 잔여 수명 예측
- **자동 알림**: ML 결과 기반 자동 알림 전송
- **센서 시뮬레이션**: 실제 센서 데이터 패턴 시뮬레이션