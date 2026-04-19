# Deployment Information

## Public URL
Chưa có public URL thật trong môi trường hiện tại.

Lý do:
- Không có quyền truy cập Railway / Render / Cloud Run trong workspace này
- Không có cloud credentials hoặc dashboard session để tạo service thật

## Prepared Platform Config
- Railway: [06-lab-complete/railway.toml](/d:/AI_action/Day_12/day12_ha-tang-cloud_va_deployment/06-lab-complete/railway.toml)
- Render: [06-lab-complete/render.yaml](/d:/AI_action/Day_12/day12_ha-tang-cloud_va_deployment/06-lab-complete/render.yaml)

## Local Test Commands

### Health Check
```bash
curl http://localhost/health
```

### Readiness Check
```bash
curl http://localhost/ready
```

### API Test
```bash
curl -X POST http://localhost/ask \
  -H "X-API-Key: day12-local-prod-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user","question":"Hello"}'
```

## Environment Variables Required
- `PORT`
- `REDIS_URL`
- `AGENT_API_KEY`
- `LOG_LEVEL`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`

## Deployment Notes
- Ứng dụng production cần một Redis service dùng chung
- Khi deploy Railway/Render, phải set `REDIS_URL` sang Redis instance trên cloud
- Sau khi có credentials, có thể deploy ngay bằng các config đã chuẩn bị sẵn

## Local Verification Completed
- `GET /health` trả `200`
- `GET /ready` trả `200`
- `POST /ask` không có API key trả `401`
- `POST /ask` với API key hợp lệ trả `200`
- Vượt `10 req/min` cho cùng `user_id` trả `429`
- Khi đặt `MONTHLY_BUDGET_USD` rất thấp, `POST /ask` trả `402`
- Conversation history được lưu và đọc lại qua `GET /history/{user_id}`
- Docker stack thật đã chạy local với `3` agent replicas + `nginx` + `redis`
- Final Docker image quan sát thực tế: `279MB`

## Screenshots
Đã tạo screenshots local verification trong thư mục [screenshots](/d:/AI_action/Day_12/day12_ha-tang-cloud_va_deployment/screenshots):
- `stack-status.png`
- `service-running.png`
- `api-test.png`

Các ảnh này là bằng chứng chạy local thật. Chúng không phải ảnh cloud dashboard vì môi trường hiện tại chưa có credentials deploy.
