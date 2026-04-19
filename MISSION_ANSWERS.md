# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. `01-localhost-vs-production/develop/app.py` hardcode API key trong code.
2. Port chạy bị cố định, không đọc từ environment variable.
3. Debug/reload phù hợp dev nhưng không an toàn cho production.
4. Không có `GET /health` để platform kiểm tra liveness.
5. Không có readiness check để biết lúc nào app thật sự sẵn sàng nhận traffic.
6. Không có graceful shutdown nên request đang xử lý có thể bị cắt ngang khi container dừng.
7. Logging dạng `print()`/plain text nên khó theo dõi trên cloud log aggregator.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcoded values | Environment variables | Tách config khỏi code, dễ đổi theo môi trường |
| Secrets | Gắn trực tiếp trong code | Inject từ env | Tránh lộ secrets trong repo |
| Health check | Không có | `/health` | Container orchestrator biết app còn sống |
| Readiness | Không có | `/ready` | Load balancer chỉ route khi app sẵn sàng |
| Logging | Plain text | Structured JSON | Dễ tìm kiếm và phân tích log |
| Shutdown | Đột ngột | Graceful shutdown | Giảm mất request khi deploy/restart |
| State | Dễ lưu in-memory | Tách khỏi process | Cần cho scale ngang |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11-slim`
2. Working directory: `/app` hoặc `/build` tùy stage
3. `COPY requirements.txt` trước để tận dụng Docker layer cache; khi code đổi mà dependencies chưa đổi thì không cần cài lại toàn bộ packages.
4. `CMD` đặt lệnh mặc định có thể override khi chạy container; `ENTRYPOINT` biến container thành executable cố định hơn.

### Exercise 2.3: Multi-stage build
- Stage 1 cài dependencies và build environment.
- Stage 2 chỉ copy phần runtime cần thiết nên image gọn hơn.
- Image nhỏ hơn vì không mang theo compiler/tooling build của stage đầu.
- Kết quả build thực tế của final image: `06-lab-complete-agent:latest 279MB`

### Exercise 2.4: Docker Compose stack
- Services start: `agent`, `redis`, `nginx`
- `nginx` nhận traffic ngoài và chuyển tiếp vào `agent`
- `agent` dùng `redis` cho history, rate limiting, cost guard
- Verify local bằng `docker compose up --build -d --scale agent=3`:
  - `3` agent containers healthy
  - `1` nginx container
  - `1` redis container

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- Repo đã có `06-lab-complete/railway.toml`
- Public URL chưa được tạo trong môi trường hiện tại vì không có quyền truy cập Railway và network/cloud credentials
- Biến môi trường bắt buộc khi deploy thật:
  - `AGENT_API_KEY`
  - `REDIS_URL`
  - `RATE_LIMIT_PER_MINUTE`
  - `MONTHLY_BUDGET_USD`
  - `LOG_LEVEL`

### Exercise 3.2: Render deployment
- `render.yaml` mô tả service theo kiểu declarative blueprint của Render
- `railway.toml` tập trung vào build/deploy behavior của Railway CLI
- Điểm khác chính: Render thường cấu hình env vars và service metadata trong `render.yaml`, còn Railway dùng `railway.toml` kết hợp dashboard/CLI variables

### Exercise 3.3: Cloud Run
- `cloudbuild.yaml` mô tả pipeline build và deploy
- `service.yaml` mô tả service configuration trên Cloud Run
- Đây là hướng phù hợp hơn cho CI/CD production

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- API key được verify qua header `X-API-Key`
- Sai key hoặc thiếu key trả về `401`
- Rate limiting dùng sliding window với Redis sorted set
- Limit mặc định trong final project: `10 req/min per user_id`
- Smoke test cục bộ với `fakeredis`:
  - `POST /ask` không có API key → `401`
  - `POST /ask` có API key hợp lệ → `200`
  - Request thứ 11 trong cùng 60 giây cho cùng `user_id` → `429`

### Exercise 4.4: Cost guard implementation
- Final project dùng Redis hash theo key tháng `budget:YYYY-MM:user_id`
- Mỗi request ghi `used_usd`, `request_count`, `input_tokens`, `output_tokens`
- Nếu `used_usd + estimated_cost > MONTHLY_BUDGET_USD` thì trả `402`
- Budget mặc định: `$10/tháng/user`
- Smoke test với `MONTHLY_BUDGET_USD=0.000001` trả về `402 Payment Required` ngay ở request đầu tiên

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- `GET /health` luôn phản ánh process còn sống
- `GET /ready` kiểm tra Redis và trạng thái shutdown trước khi nhận traffic
- Graceful shutdown dùng signal handler cho `SIGTERM` và `SIGINT`
- Conversation history lưu trong Redis list thay vì memory nên không mất khi scale ngang
- `nginx.conf` đóng vai trò load balancer phía trước các agent instances
- Verify thực tế qua Nginx:
  - 6 requests liên tiếp được phân phối qua 3 instance IDs khác nhau
  - Sau khi xóa 1 replica, request tiếp theo vẫn thành công và history vẫn tăng tiếp

## Part 6: Final Project

### Delivered features
- REST API trả lời câu hỏi: `POST /ask`
- Conversation history: lưu trong Redis, xem qua `GET /history/{user_id}`
- Dockerized multi-stage build
- Config từ environment variables
- API key authentication
- Redis-backed rate limiting `10 req/min`
- Redis-backed cost guard `$10/month`
- Health + readiness checks
- Graceful shutdown
- Stateless design
- Structured JSON logging
- Railway/Render deployment configs

### Local validation
- `python 06-lab-complete/check_production_ready.py`
- `python -m compileall 06-lab-complete/app`
- Smoke test với `fastapi.testclient + fakeredis`
  - `/health` → `200`
  - `/ready` → `200`
  - `/ask` với key hợp lệ → `200`
  - `/history/{user_id}` sau request đầu tiên → `history_length = 2`
  - rate limit vượt ngưỡng → `429`
  - budget quá thấp → `402`
- Smoke test với Docker stack thật qua `http://localhost`
  - `/health` → `200`
  - `/ready` → `200`
  - `/ask` thiếu key → `401`
  - `/ask` hợp lệ → `200`
  - load balancer quan sát được `3` instance IDs khác nhau
  - image size thực tế: `279MB`

### External blockers
- Chưa có public URL thật vì môi trường hiện tại không có quyền deploy Railway/Render và không có screenshots cloud dashboard.
