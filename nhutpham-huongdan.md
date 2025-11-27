# Hướng dẫn chạy RAG FastAPI Chatbot
Cài Python 3.11 > 
conda deactivate
py -0p
set "PATH=C:\Users\Admin\AppData\Local\Programs\Python\Python311;C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts;%SystemRoot%\system32;%SystemRoot%"
where python
python -V

rmdir /s /q .venv
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -V  # kiểm tra ra 3.14.x
python.exe -m pip install --upgrade pip

xóa biến môi trường gây nhiễu 
set PYTHONHOME=
set PYTHONPATH=
set "PATH=C:\Users\Admin\AppData\Local\Programs\Python\Python311;C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts;%SystemRoot%\system32;%SystemRoot%"

pip install -r requirements.txt


pip install -r requirements-py310.txt

ollama list
curl http://localhost:11434/api/tags

## 1) Chuẩn bị môi trường
- Copy env: `cp .env.example .env` rồi điền các biến bắt buộc (DB, MinIO, Redis, JWT). Nếu dùng Ollama local:
  - `EMBEDDING_MODEL=embeddinggemma`
  - `OLLAMA_HOST=http://ollama:11434`
- Đảm bảo Docker và Docker Compose đã cài.

## 2) Khởi động bằng Docker
```bash
docker compose up -d --build
```

python -m venv .venv && .venv\\Scripts\\activate && pip install -r requirements.txt


Lỗi “relation user does not exist” vì DB chưa có bảng. Bạn cần chạy migration để tạo schema:

Đảm bảo .env trỏ đúng DB (ví dụ postgresql+asyncpg://postgres:123456@localhost:5432/aiservices).

Chạy migration trong venv:

alembic upgrade head
(nếu dùng docker compose, có thể docker compose exec backend alembic upgrade head)

Sau khi migration thành công, bảng user sẽ được tạo và bạn signup lại sẽ không còn lỗi.

rồi uvicorn app.main:app --reload --host 0.0.0.0 --port 8008



Kiểm tra:
- Backend: `curl http://localhost:8000/v1/health`
- Ollama tags: `curl http://localhost:11435/api/tags`
- MinIO console: http://localhost:9001 (đăng nhập MINIO_ACCESS_KEY/SECRET_KEY)

## 3) Luồng Postman/API demo
Base URL: `http://localhost:8000/v1` (đổi nếu VERSION khác).

1. Signup: `POST /v1/oauth/signup` body `{email, password, full_name}`.
2. Login: `POST /v1/oauth/login` lấy `access_token`.
3. Tạo KB: `POST /v1/kb` body `{name, description}` (Bearer token).
4. Upload file: `POST /v1/document?kb_id=<kb_id>` body form-data `files` (Bearer token) → lấy `document_id`.
5. Chunk: `POST /v1/chunking?document_id=<document_id>` (Bearer token).
6. Embedding: `POST /v1/embedding?document_id=<document_id>` (Bearer token) → gọi model `embeddinggemma` qua Ollama.
7. Tạo chat: `POST /v1/chat` (Bearer token) → lấy `chat_id`.
8. Hỏi đáp RAG: `POST /v1/c/<chat_id>?question=...` (Bearer token) → stream text.

## 4) Test nhanh embedding (host)
```bash
curl -s -X POST http://localhost:11434/api/embed \
  -H "Content-Type: application/json" \
  -d '{"model":"embeddinggemma","input":"hello world"}'
```

## 5) Lưu ý cấu hình
- Dùng hostname service trong Docker: DB `db:5432`, Redis `redis:6379`, MinIO `minio:9000`, Ollama `ollama:11434`.
- JWT: đặt `SECRET_KEY`, `SALT`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `JTI_EXPIRY_SECOND` với giá trị thật.
- Nếu đổi VERSION trong `.env`, cập nhật URL tương ứng.

Luồng Postman demo RAG
Base URL: http://localhost:8000/v1 (thay v1 bằng VERSION trong .env). Tất cả trừ signup/login cần Bearer Access Token.

Signup: POST /v1/oauth/signup
Body JSON: {"email":"you@example.com","password":"StrongPass123","full_name":"You"}
(hoặc dùng tài khoản đã có).

Login: POST /v1/oauth/login
Body JSON: {"email":"you@example.com","password":"StrongPass123"}
Lấy access_token (và refresh_token nếu cần).
postman request POST 'http://localhost:8008/v1/oauth/login' \
  --header 'Content-Type: application/json' \
  --body '{"email":"nhutpm7777@gmail.com","password":"Abcd1234!"}'

Tạo Knowledge Base: POST /v1/kb
Header: Authorization: Bearer <access_token>
Body JSON: {"name":"project-a","description":"Chat logs & docs"}
Lấy kb_id.
=>>  "id": "b6e196f1-0a30-4940-92a4-de008a082d47",

postman request POST 'http://localhost:8008/v1/kb' \
  --header 'Content-Type: application/json' \
  --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoibmh1dHBtNzc3N0BnbWFpbC5jb20iLCJ1c2VyX2lkIjoiMDU3NWQ1YzQtOTRkNS00MGMyLWE4MmYtNjY4MDdlM2NiMDk1Iiwicm9sZSI6InVzZXIifSwiZXhwIjoxNzY0MjMzNzQ4LCJqdGkiOiJhMDlkNWYyYi0wYTlkLTRkYmEtOTViMS0zYzliNDEwY2I1YjAiLCJyZWZyZXNoIjpmYWxzZX0.N832Ntp6Wd_XjsuYD4HGKoHyDPiCLZdNeRsuUeH-8cg' \
  --body '{"name":"friendify ai","description":"Chat logs & docs"}' \
  --auth-bearer-token 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoibmh1dHBtNzc3N0BnbWFpbC5jb20iLCJ1c2VyX2lkIjoiMDU3NWQ1YzQtOTRkNS00MGMyLWE4MmYtNjY4MDdlM2NiMDk1Iiwicm9sZSI6InVzZXIifSwiZXhwIjoxNzY0MjMzNzQ4LCJqdGkiOiJhMDlkNWYyYi0wYTlkLTRkYmEtOTViMS0zYzliNDEwY2I1YjAiLCJyZWZyZXNoIjpmYWxzZX0.N832Ntp6Wd_XjsuYD4HGKoHyDPiCLZdNeRsuUeH-8cg'

Upload tài liệu: POST /v1/document?kb_id=<kb_id>
Header: Bearer token.
Body: form-data files = file cần upload (có thể chọn nhiều). Trả về document_id.

Chunk: POST /v1/chunking?document_id=<document_id>
Header: Bearer token.
Nếu OK, trạng thái doc sẽ thành “chunked”.

Embedding: POST /v1/embedding?document_id=<document_id>
Header: Bearer token.
Hệ thống gọi Ollama embeddinggemma và ghi vector vào DB.

Tạo chat session: POST /v1/chat
Header: Bearer token. Trả về chat_id.

curl -X POST http://localhost:8008/v1/c \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"<chat_id>","question":"Tóm tắt cuộc họp với Hong-gil tuần trước"}'

Header: Bearer token.
Query param question (VD: question=Tóm tắt cuộc họp với Hong-gil tuần trước). Phản hồi stream text/plain.

Ghi chú

File upload dùng form-data, không phải JSON.
Nếu cần xem/kiểm tra chunk/embedding: GET /v1/chunking/<document_id> hoặc GET /v1/embedding (tùy use-case, endpoint chính là embed POST ở trên).
Nếu chạy từ host gọi trực tiếp Ollama để test model: curl -s -X POST http://localhost:11434/api/embed -H "Content-Type: application/json" -d "{\"model\":\"embeddinggemma\",\"input\":\"hello world\"}".
Khi đổi VERSION trong .env, cập nhật tất cả URL tương ứng.


#

postman request POST 'http://localhost:8008/v1/oauth/signup' \
  --header 'Content-Type: application/json' \
  --body '{
  "email": "nhutpm7777@gmail.com",
  "username": "nhutpham",
  "first_name": "Nhut",
  "last_name": "Pham",
  "password": "Abcd1234!",
  "confirm_password": "Abcd1234!"
}
'{
    "message": "Account created! Check email to verify your email",
    "user": {
        "email": "nhutpm7777@gmail.com",
        "username": "nhutpham",
        "last_name": "Pham",
        "first_name": "Nhut",
        "id": "0575d5c4-94d5-40c2-a82f-66807e3cb095",
        "is_verified": false,
        "role": "user",
        "created_at": "2025-11-27T08:22:07.079462Z",
        "updated_at": "2025-11-27T08:22:07.079462Z"
    }
}
postman request POST 'http://localhost:8008/v1/document?kb_id=b6e196f1-0a30-4940-92a4-de008a082d47' \
  --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoibmh1dHBtNzc3N0BnbWFpbC5jb20iLCJ1c2VyX2lkIjoiMDU3NWQ1YzQtOTRkNS00MGMyLWE4MmYtNjY4MDdlM2NiMDk1Iiwicm9sZSI6InVzZXIifSwiZXhwIjoxNzY0MjMzNzQ4LCJqdGkiOiJhMDlkNWYyYi0wYTlkLTRkYmEtOTViMS0zYzliNDEwY2I1YjAiLCJyZWZyZXNoIjpmYWxzZX0.N832Ntp6Wd_XjsuYD4HGKoHyDPiCLZdNeRsuUeH-8cg' 'files=@"/D:/NHUTPHAM-GIT-D/rag-fastapi-chatbot/dataset/chatbot.csv"' \
  --auth-bearer-token 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjp7ImVtYWlsIjoibmh1dHBtNzc3N0BnbWFpbC5jb20iLCJ1c2VyX2lkIjoiMDU3NWQ1YzQtOTRkNS00MGMyLWE4MmYtNjY4MDdlM2NiMDk1Iiwicm9sZSI6InVzZXIifSwiZXhwIjoxNzY0MjMzNzQ4LCJqdGkiOiJhMDlkNWYyYi0wYTlkLTRkYmEtOTViMS0zYzliNDEwY2I1YjAiLCJyZWZyZXNoIjpmYWxzZX0.N832Ntp6Wd_XjsuYD4HGKoHyDPiCLZdNeRsuUeH-8cg'

[
    {
        "object_path": "tmp/chatbot_ee29a8f7e4134471e179154d4c580e62dd916a6358a56d55bec0b506d89f8b61.csv",
        "file_name": "chatbot.csv",
        "file_size": 1279,
        "content_type": "application/octet-stream",
        "file_hash": "ee29a8f7e4134471e179154d4c580e62dd916a6358a56d55bec0b506d89f8b61",
        "username": "nhutpham",
        "knowledge_base_id": "b6e196f1-0a30-4940-92a4-de008a082d47",
        "id": "b7bfb042-075e-420b-9b6d-3966d394a781",
        "status": "pending",
        "created_at": "2025-11-27T08:55:25.367352Z",
        "updated_at": "2025-11-27T08:55:25.367352Z"
    }
]


# BỔ SUNG Công Nghệ
Reranking 
Caching - Caching embedding
Bọc lớp route semantic cho question vespa 
Lớp các ngữ cảnh => thêm routes
Lớp input và output => bọc searching và gợi ý 
- lớp embedding input - index => chia nhỏ ra để thinking => cũng là tiêu chuẩn sẵn rồi => kiểm tra code xem 
- cơ chế loading models như nào 


=>> phân tích logic output và bộ lọc promt :
độ dài token tối đa có thể hỗ trợ là gì 

=>> trong 1 phiên chat nó có lưu lại lịch sử history và có tài sử dụng => trong phiên chat hay không ?

- chunking và embedding định kỳ => bọc riêng cho từng lịch sử chatbot 

# Phân tích : lịch sử 
Logic output & prompt: app/llm_model/services.py có 2 prompt (contextualize và answer). Lịch sử lấy tối đa 3 message gần nhất từ Redis (SimpleRedisHistory), rồi gọi contextualize_chain và answer_chain.
Độ dài token: không có giới hạn cứng trong code; ChatOllama đang set num_predict=1024 (số token sinh). Context tối đa phụ thuộc model Ollama bạn dùng (ví dụ gpt-oss 20B có context riêng).
Lịch sử phiên chat: có lưu vào Redis (SimpleRedisHistory) và cả DB (bảng message). Mỗi lần hỏi, nó nạp lại tối đa 3 messages trước.
Chunking & embedding: hiện làm thủ công qua endpoint /v1/chunking và /v1/embedding cho từng document. Không có job định kỳ theo lịch sử chat; nếu muốn định kỳ hoặc mỗi phiên, cần tự bọc thêm Celery/cron.

- nếu lấy từ redis thì chưa đủ => nó tự xóa mà ta => nó phải lấy từ timeline đã lưu trong postgre chứ 

