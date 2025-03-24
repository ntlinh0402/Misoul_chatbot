# MISOUL API

**MISOUL** (*My Soul*) là một chatbot tâm lý được phát triển để hỗ trợ người dùng với sức khỏe tinh thần. API này cung cấp khả năng tích hợp MISOUL vào các ứng dụng di động, web và các nền tảng khác.
Cài đặt
Yêu cầu

- `Python 3.8+`
- `Pip`
- `Git`
- Các thư viện khác trong requirements.txt

### Hướng dẫn các bước
**Bước 1**: Clone repository
bashCopygit clone <repository-url>
cd misoul-api


**Bước 2**: Cài đặt các gói phụ thuộc
bashCopypip install -r requirements.txt  


**Bước 3**: Cấu hình
Tạo file .env trong thư mục gốc với nội dung như trong file .env.example:

```
GOOGLE_API_KEY=<your-google-api-key>

MISOUL_API_KEY=<your-misoul-api-key>

DEBUG=True

VECTOR_DB_PATH=./data/misoul_vectordb

MODEL_NAME=models/gemini-1.5-flash
```
API Keys
Ứng dụng yêu cầu hai API key:

GOOGLE_API_KEY:

Cần đăng ký tại Google AI Studio (https://ai.google.dev/)

*Hoặc liên hệ team lead để nhận key*


**MISOUL_API_KEY:**

Đây là key tự tạo để bảo vệ API của MISOUL
Bạn có thể dùng key đã thống nhất trong team
Hoặc tạo key ngẫu nhiên của riêng bạn
Quan trọng: Dùng cùng một key trong cả server và client



Bước 4: Chạy API
bash
```python run.py```

API sẽ chạy tại địa chỉ http://127.0.0.1:5000 theo mặc định.
API Endpoints

Chat API

Endpoint: /api/chat

Method: POST

Headers:



Xem ví dụ trong file HTML đính kèm hoặc liên hệ team lead để được hướng dẫn chi tiết cách tích hợp vào ứng dụng di động.

### 🔒Bảo mật

Không được commit các API keys lên Git repository
Luôn sử dụng HTTPS trong môi trường production
Đảm bảo xác thực tất cả các yêu cầu API


