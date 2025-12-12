# README – Gateway Registration Guide


# Celery task
celery -A app.celery_task.c_app worker -l info

celery -A app.celery_task.c_app worker -l info -P solo -c 1
# hoặc
celery -A app.celery_task.c_app worker -l info --pool=threads -c 4


# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8055


Hướng dẫn nhanh để đăng ký service vào gateway khi dùng bộ toolkit `folder-gateway-skill/` hoặc FastAPI chính.

## Biến môi trường cần thiết
- `GATEWAY_URL`: URL gateway, ví dụ `http://127.0.0.1:30090`.
- `SERVICE_BASE_URL`: URL service mà gateway sẽ gọi, ví dụ `http://127.0.0.1:8000`.
- `SERVICE_NAME`: tên hiển thị, mặc định `rag-fastapi-chatbot`.
- `GATEWAY_PREFIX`: prefix để tránh trùng path, ví dụ `/rag-bot` (tùy chọn).
- `REGISTER_RETRIES` / `REGISTER_DELAY`: số lần retry và thời gian chờ giữa các lần (mặc định 5 và 1.0s).

## Auto đăng ký (FastAPI chính)
1) Đặt các biến trên (trong `.env` hoặc env runtime).
2) Khởi động service: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (hoặc docker/compose).
3) Xem log: phải có `Gateway registered (...) routes=N`. Nếu lỗi, nó sẽ retry theo `REGISTER_RETRIES`.
4) Mở Swagger gateway và gọi thử 1–2 route để chắc không 404/401.

## Đăng ký thủ công (cURL)
Nếu không dùng auto, gửi payload đăng ký:
```bash
curl -X POST "$GATEWAY_URL/gateway/register" \
  -H "Content-Type: application/json" \
  -d @payload.json
```
Ví dụ `payload.json`:
```json
{
  "name": "rag-fastapi-chatbot",
  "base_url": "http://127.0.0.1:8000",
  "routes": [
    {
      "name": "rag-search",
      "method": "POST",
      "gateway_path": "/v1/rag/search",
      "upstream_path": "/v1/rag/search",
      "summary": "RAG search",
      "description": "Search RAG pipeline"
    }
  ]
}
```

## Lưu ý kiểm tra
- `SERVICE_BASE_URL` phải là địa chỉ thực tế gateway gọi tới (không phải gateway).
- `GATEWAY_URL` phải trỏ gateway thật (port đúng).
- Nếu dùng `GATEWAY_PREFIX`, đảm bảo Swagger gateway hiển thị route với prefix đó.
- Khi copy sang repo khác, giữ nguyên thư mục `folder-gateway-skill/` và chỉnh lại env/port cho khớp hạ tầng mới.
