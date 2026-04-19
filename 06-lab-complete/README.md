# Lab 12 — Complete Production Agent

Project cuối cho Day 12, kết hợp đầy đủ các yêu cầu production:

- Multi-stage Docker build
- API key authentication
- Redis-backed rate limiting
- Redis-backed cost guard
- Redis-backed conversation history
- Health + readiness probes
- Graceful shutdown
- Structured JSON logging
- Docker Compose stack với Redis + Nginx
- Railway / Render deployment config

## Structure

```text
06-lab-complete/
├── app/
│   ├── auth.py
│   ├── config.py
│   ├── cost_guard.py
│   ├── main.py
│   └── rate_limiter.py
├── utils/
│   └── mock_llm.py
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── railway.toml
├── render.yaml
├── .env.example
└── check_production_ready.py
```

## Local Run

```bash
cd 06-lab-complete
cp .env.example .env
docker compose up --build --scale agent=3
```

Stack local:

- `nginx` lắng nghe ở `http://localhost`
- `agent` scale ngang bằng `docker compose up --scale agent=3`
- `redis` giữ state dùng chung cho history, rate limit, budget

## Test Commands

```bash
curl http://localhost/health
curl http://localhost/ready

curl -X POST http://localhost/ask \
  -H "X-API-Key: change-me-before-production" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"student1\",\"question\":\"What is deployment?\"}"

curl -X GET http://localhost/history/student1 \
  -H "X-API-Key: change-me-before-production"
```

## Rate Limit and Budget

- Rate limit mặc định: `10 req/minute per user_id`
- Monthly budget mặc định: `$10 per user_id`
- Hai cơ chế đều lưu trong Redis để không mất state khi scale nhiều instances

## Railway

`railway.toml` đã được chuẩn bị cho deploy bằng Dockerfile. Khi deploy thật cần set:

- `AGENT_API_KEY`
- `REDIS_URL`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`
- `LOG_LEVEL`

## Render

`render.yaml` dùng runtime Docker. Khi deploy thật cũng cần cung cấp `REDIS_URL` từ Redis service/add-on.

## Validation

```bash
python check_production_ready.py
```

Script trên kiểm tra file bắt buộc, security basics, endpoint definitions và Dockerfile.
