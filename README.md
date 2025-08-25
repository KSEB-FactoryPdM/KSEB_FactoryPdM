# 🏭 스마트팩토리 공장 회전 설비 이상탐지 및 예지보전  
**Smart Factory Predictive Maintenance Monorepo**  
공장 회전체 장비(HVAC, 펌프, 팬 등)의 **이상탐지 및 예지보전**을 위해,  
**Unity 기반 가상 센서 시뮬레이션 → 실시간 데이터 수집·스트리밍 → AI 분석 → 시각화**  
까지 전 과정을 구현한 **백엔드 API + 프론트엔드 대시보드 + AI 모델 서빙** 통합 레포지토리입니다.  

---

## 📌 프로젝트 개요
본 시스템은 Unity 가상 센서 시뮬레이터를 통해 생성한 데이터를 MQTT로 송신하고,  
FastAPI 기반 데이터 수집기가 Kafka·TimescaleDB에 적재합니다.  
PyTorch + XGBoost 기반 **이상탐지 모델**과 LSTM 기반 **RUL(Remaining Useful Life) 예측 모델**을 실시간 서빙하며,  
Next.js 기반 대시보드에서 모니터링·알림·장비 관리를 수행합니다.  
전체 환경은 **Docker Compose(로컬)** 또는 **Kubernetes(GKE)** 에서 구동됩니다.

---

## 🏗 아키텍처

![시스템 아키텍처](docs/FactoryPdM%20(1).png)

*Unity 센서 시뮬레이터 → MQTT → 데이터 수집기 → Kafka/TimescaleDB → AI 모델 서빙 → 대시보드*

**주요 구성 요소:**
- **Unity 센서 시뮬레이터**: 가상 공장 환경에서 센서 데이터 생성
- **MQTT 브로커**: 실시간 센서 데이터 전송
- **데이터 수집기**: MQTT 구독 → Kafka/TimescaleDB 적재
- **AI 모델 서빙**: serve_ml 번들 기반 실시간 추론
- **대시보드**: Next.js 기반 모니터링 UI

---

## 🚀 빠른 시작 (Docker Compose)

사전 요구사항: Docker, Docker Compose

```bash
git clone <repository-url>
cd backend

# 환경 변수 템플릿 복사 (필요시 변수 수정)
cp .env.docker.example .env

# 핵심 서비스 기동 (DB, MQTT, Redis, Backend, Frontend)
docker compose up -d timescaledb mqtt redis backend frontend

# 선택: 모니터링/메시징 도구 포함 기동
# docker compose up -d grafana prometheus kafka zookeeper kafka-ui

# 상태 확인
docker compose ps
```

접속 주소(기본값):

- API: `http://localhost:8000` (문서: `/docs`)
- Frontend: `http://localhost:3002` (core 구성 사용 시 `http://localhost:3000`)
- Grafana: `http://localhost:3001`
- Prometheus: `http://localhost:9090`
- Kafka UI: `http://localhost:8080`
- MQTT: `tcp://localhost:1883` (WebSocket `ws://localhost:9001`)
- TimescaleDB: `localhost:5432`
- Redis: `localhost:6379`

중지/정리:

```bash
docker compose down    # 컨테이너 종료
docker compose down -v # 종료 + 볼륨 제거
```

---


## 📦 서비스 구성 요약

- 데이터 수집: MQTT → (옵션) Kafka → TimescaleDB
- 모델/서빙: serve_ml 번들 기반 실시간 추론(HTTP/MQTT)
- API: FastAPI로 장비/센서/이상탐지/RUL 기능 제공
- 대시보드: Next.js 기반 실시간 모니터링, 알림/설비 관리 UI
- 모니터링: Prometheus + Grafana

간단한 데이터 흐름:
1) 센서/시뮬레이터 → MQTT publish
2) 수집기 subscribe → DB 적재 (또는 Kafka 경유)
3) 모델 추론 → 결과 저장/알림
4) 대시보드/API 조회 및 시각화

---

## 📁 레포 구조

```
.
├── backend/
│   ├── docker-compose.yml
│   ├── docker/
│   └── README.md
├── frontend/
│   ├── package.json
│   └── README.md
└── ai/
```
