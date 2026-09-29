# Evidence cá nhân

Đặt ảnh hoặc output text dùng để chấm vào thư mục này. Danh sách đầy đủ xem tại [docs/SUBMISSION.md](../../docs/SUBMISSION.md).

Tên file gợi ý:

```text
01-pytest.txt
02-log-validator.txt
03-dashboard-validator.txt
04-structured-log.txt
05-pii-redaction.txt
06-trace-list.txt
07-trace-waterfall.txt
08-trace-metadata.txt
09-prompt-versions.txt
10-prompt-rollback.txt
11-dashboard-overview.txt
12-incident-metric.txt
13-incident-log.txt
14-incident-trace.txt
```

Có thể dùng `.txt` cho output của tests/validators. Có thể tách dashboard thành nhiều ảnh nếu một ảnh không đọc rõ.

Để tạo ảnh dashboard runtime, chạy Streamlit theo [DASHBOARD_SETUP.md](../../docs/DASHBOARD_SETUP.md), mở `http://localhost:8501`, rồi chụp toàn bộ sáu panel và lưu thành `11-dashboard-overview.png`.

Ảnh `04`, `05`, `13` lấy từ terminal hoặc `data/logs.jsonl`. Ảnh `06`–`10`, `14` lấy từ project Langfuse cá nhân `day13-k4-l3a-<MSSV>` và nên nhìn thấy tên project. Không mở/chụp trang API Keys.

Từ `submission/REPORT.md`, dẫn ảnh bằng đường dẫn tương đối:

```markdown
![Trace waterfall](evidence/07-trace-waterfall.png)
```

Không commit secret, API key, PII thô hoặc evidence của học viên/lớp khác.
