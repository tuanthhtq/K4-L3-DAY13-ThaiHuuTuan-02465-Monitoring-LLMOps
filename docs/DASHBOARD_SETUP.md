# Dựng và kiểm tra dashboard

[`../config/dashboard.yaml`](../config/dashboard.yaml) là contract chấm điểm, không phụ thuộc việc bạn dựng dashboard trong Langfuse hay một công cụ local. File này quy định đúng nguồn dữ liệu, phép tổng hợp, đơn vị và threshold cho sáu panel.

Trường `query` trong YAML là pseudocode mô tả phép tính, không phải câu lệnh để copy nguyên vào mọi công cụ. Bạn chuyển cùng logic đó sang cú pháp của công cụ đã chọn.

## Mapping dữ liệu

| Panel | Event/field | Phép tổng hợp |
|---|---|---|
| Latency | `response_sent.latency_ms/ttft_ms` | latency P50/P95/P99 và TTFT P95 |
| Traffic | `request_received` | count, request/phút |
| Errors | `request_received`, `request_failed`, `error_type`, `tool_success` | error rate, breakdown và retrieval success |
| Cost | `response_sent.cost_usd` | tổng theo phút và toàn cửa sổ |
| Tokens | `response_sent.tokens_in/tokens_out` | tổng theo từng field |
| Quality | `response_sent.quality_score` | mean |

Giữ time range mặc định 60 phút, refresh 30 giây và hiển thị threshold/SLO line. Giá trị chính xác nằm trong `config/dashboard.yaml`; không tự đổi contract chỉ để ảnh dashboard đẹp hơn.

## Cách dựng

1. Hoàn thiện logging/PII và chạy API.
2. Chạy `python scripts/load_test.py --concurrency 5` để tạo baseline.
3. Dùng `data/logs.jsonl` làm nguồn chuẩn để tạo đúng sáu panel bằng Streamlit, notebook, Grafana hoặc công cụ tương đương. Langfuse vẫn là nơi mở trace/prompt version để điều tra sâu.
4. Đặt tên panel, đơn vị và threshold giống contract.
5. Chạy validator:

```bash
python scripts/validate_dashboard.py
```

Validator kiểm tra cấu trúc contract; nó không thể chứng minh biểu đồ trong ảnh dùng đúng dữ liệu. Evidence runtime vẫn bắt buộc.

## Chạy dashboard Streamlit local

Dashboard đã triển khai tại [`../scripts/dashboard.py`](../scripts/dashboard.py). Từ thư mục repository, chạy:

```powershell
.\.venv\Scripts\python.exe -m streamlit run scripts/dashboard.py --server.headless true --server.port 8501
```

Mở `http://localhost:8501`. Dashboard đọc trực tiếp `data/logs.jsonl`, mặc định hiển thị 60 phút gần nhất và tự refresh mỗi 30 giây. Mốc thời gian được lấy từ các event request/response, không bị lệch bởi log `app_started`. Sidebar cho phép đổi time range hoặc bấm `Reload now` để đọc lại file log.

Sáu panel tương ứng với contract là latency/TTFT, request traffic, error rate/retrieval success, cost, input/output tokens và quality score. Mỗi panel hiển thị đơn vị và threshold; sau khi có workload trong log, chụp toàn bộ dashboard lưu thành `submission/evidence/11-dashboard-overview.png`.

Ở màn hình desktop, dashboard dùng bố cục 3 cột x 2 hàng và biểu đồ thấp để sáu panel vừa trong một viewport. Trên màn hình hẹp, các cột tự động xếp lại để nội dung vẫn đọc được.

Tiêu đề dashboard dùng component heading chuẩn của Streamlit với chiều cao dòng cố định để vẫn hiển thị đầy đủ khi dùng chế độ compact.

## Cách kiểm tra runtime

1. Lưu ảnh baseline và giá trị P95/error/cost hiện tại.
2. Bật một incident practice, ví dụ `python scripts/inject_incident.py --scenario rag_slow`.
3. Chạy lại load test với cùng input và concurrency.
4. Xác nhận panel liên quan thay đổi theo đúng hướng; với `rag_slow`, P95 phải tăng rõ ràng.
5. Lọc log chậm, lấy correlation ID rồi mở trace có cùng ID.
6. Tắt incident bằng `python scripts/inject_incident.py --scenario rag_slow --disable`.

Ảnh dashboard phải nhìn được tên panel, time range, đơn vị và threshold. Báo cáo phải dẫn lại trace ID hoặc log line dùng để giải thích thay đổi.
