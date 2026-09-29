# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Thái Hữu Tuấn
- **MSSV:** 2a202602465
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/tuanthhtq/K4-L3-DAY13-ThaiHuuTuan-02465-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2a202602465`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log | `evidence/04-structured-log.txt` |
| PII redaction | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/06-trace-list.txt` |
| Trace waterfall | `evidence/07-trace-waterfall.txt` |
| Trace metadata | `evidence/08-trace-metadata.txt` |
| Prompt versions | `evidence/09-prompt-versions.txt` |
| Prompt rollback | `evidence/10-prompt-rollback.txt` |
| Dashboard runtime | `evidence/11-dashboard-overview.txt` |
| Incident metric | `evidence/12-incident-metric.txt` |
| Incident log | `evidence/13-incident-log.txt` |
| Incident trace | `evidence/14-incident-trace.txt` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | 22 log records, 10 correlation IDs, không thiếu required/enrichment fields |
| `validate_dashboard.py` | Chưa chạy | 6/6 panel | Dashboard contract hợp lệ |
| `pytest` | Chưa chạy | 22 passed | Toàn bộ test hiện tại đạt |
| Số traces hợp lệ | Chưa kiểm tra | 35 root traces trong 24 giờ | Đã xác nhận qua Langfuse observations API; cần ảnh trace list |
| Số PII leak | 0 | 0 | Workload CP1 không phát hiện PII nguyên văn |
| Latency P95 / TTFT P95 | Chưa tính | 4035 ms / 50 ms | Current challenge window; P95 latency exceeded the 3000 ms SLO |
| Retrieval success rate | Chưa tính | 100% | All current responses reported `tool_success=true` |

### Baseline CP1

Đã chạy:

```text
python scripts/load_test.py
python scripts/validate_logs.py
```

Kết quả baseline:

- Tổng số log được phân tích: 22
- Log thiếu required fields: 20
- Log thiếu enrichment context: 20
- Số correlation ID duy nhất: 0
- Số PII leak: 0
- Điểm ước tính: 30/100
- Các request trả về HTTP 200 nhưng correlation ID là `MISSING`

Nguyên nhân baseline chưa đạt là các TODO trong `app/middleware.py` và `app/main.py` chưa được hoàn thiện. Middleware chưa tạo/truyền correlation ID và log chưa được enrich với `user_id_hash`, `session_id`, `feature`, `model`, `env`.

### Kết quả CP1 sau khi triển khai

Đã xóa log cũ, chạy lại workload và kiểm tra bằng `python scripts/validate_logs.py`:

- Tổng số log được phân tích: 21
- Log thiếu required fields: 0
- Log thiếu enrichment context: 0
- Số correlation ID duy nhất: 10
- Số PII leak: 0
- Điểm ước tính: 100/100
- 10 request đều trả HTTP 200 và có correlation ID dạng `req-<8-hex>`

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** `app/middleware.py` nhận `x-request-id` hoặc sinh ID dạng `req-<8-hex>`, bind vào structlog context và trả lại qua `x-request-id`; kết quả CP1 có 10 correlation IDs duy nhất.
- **Các metadata được ghi vào structured log:** Đã bổ sung bind `user_id_hash`, `session_id`, `feature`, `model` và `env` trong `app/main.py`; validator ghi nhận 0 log thiếu enrichment.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` được đăng ký trước `JsonlFileProcessor` trong `app/logging_config.py`; scrubber xử lý cả string, dict và list lồng nhau.
- **Cách kiểm chứng kết quả:** Dùng `python scripts/validate_logs.py`; baseline đạt 30/100 và kết quả CP1 hiện tại đạt 100/100. Evidence runtime nằm tại `evidence/05-pii-redaction.txt`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Chạy workload bằng key của project `day13-k4-l3a-2a202602465`; đã xác nhận 35 root traces trong 24 giờ qua qua Langfuse observations API.
- **Cấu trúc root/retrieval/generation observations:** `lab-agent-run` là root; `retrieval` là child loại `retriever`; `fake-llm-generate` là child loại `generation`. Child observations đã được thêm trong `app/agent.py`.
- **Cách nối trace với log:** Dùng cùng `correlation_id` trong metadata của root/child observation và structured log.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1, labels `baseline`, `production`.
- **Version/label candidate:** Version 2, label `candidate`.
- **Trace ID của mỗi version:** v1 `cbd3feece73e667bbd3457aeb5c2fd3e`; v2 `22ad7fe48f1fbc74cefc26e2b5438353`; promoted v2 `6d668fa40dd38c3b3dca7c3c2a84bf16`; rollback v1 `20249ddb95c44be546b5ae0d91d9ee45`.
- **Cách promote và rollback `production`:** Đã promote `production` sang version 2, chạy trace `6d668fa40dd38c3b3dca7c3c2a84bf16`, sau đó rollback về version 1 và chạy trace `20249ddb95c44be546b5ae0d91d9ee45`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Contract `config/dashboard.yaml` đã hợp lệ 6/6; runtime data summary nằm tại `evidence/11-dashboard-overview.txt` và cần được dùng để chụp dashboard có 6 panel.
- **SLO và lý do chọn:** SLO `fast_successful_requests` yêu cầu 99.5% request thành công với latency không quá 3000 ms trong cửa sổ 28 ngày.
- **Cách tính error budget:** `100% - 99.5% = 0.5%` request được phép không đạt SLO trong mỗi cửa sổ 28 ngày.
- **Ba alert và runbook tương ứng:** Đã cấu hình latency P95, error rate và retrieval success trong `config/alert_rules.yaml`; runbook nằm tại `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`; cohort `K4`; seed `1311`.
- **Khoảng thời gian điều tra:** 2026-09-29 09:35:06–09:35:16 UTC.
- **Triệu chứng từ metrics:** Incident `rag_slow` trên feature `monitoring`; 5/5 request vượt ngưỡng 2000 ms, latency 2652–4035 ms, mean 2929.4 ms; TTFT giữ ở 50 ms.
- **Log line và correlation ID liên quan:** `response_sent` có correlation ID `req-db9bd7ff` và latency 4035 ms; các ID còn lại là `req-6a1b9bf1`, `req-d42f2dfa`, `req-1802b940`, `req-2b776c21`.
- **Trace ID và span gây ảnh hưởng:** Trace `663cc910f399a440184fb797d22ddb53` nối với `req-db9bd7ff`; span `retrieval` mất khoảng 2.502 s trong khi `fake-llm-generate` khoảng 0.153 s. Các trace còn lại cũng có retrieval khoảng 2.501–2.502 s.
- **Root cause:** Incident `rag_slow` chèn độ trễ 2.5 s vào bước retrieval; retrieval là span chiếm phần lớn latency, không phải LLM generation.
- **Fix action:** Đã tắt incident `rag_slow`, xác nhận request sau đó không còn bị chèn độ trễ; tiếp tục theo dõi P95 retrieval/overall latency.
- **Preventive measure:** Alert latency P95 > 3000 ms trong 10 phút, alert retrieval success/latency, giữ child spans retrieval và generation để khoanh vùng nhanh hơn.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Dùng correlation ID do client truyền vào khi hợp lệ, nếu không có thì sinh ID mới dạng `req-<8-hex>` để nối request giữa log và trace.
- **Một lỗi/blocker đã gặp:** Lần cài đặt đầu tiên dùng Python 3.14 khiến `pydantic-core` phải build từ source và thất bại do PyO3 chưa hỗ trợ Python 3.14.
- **Cách tìm nguyên nhân và xử lý:** Đọc lỗi build chỉ ra Python 3.14 vượt phiên bản tối đa PyO3 hỗ trợ; hướng xử lý là tạo virtual environment bằng Python 3.11.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics cho thấy 5/5 request vượt 2000 ms; log lấy `req-db9bd7ff`; trace `663cc910f399a440184fb797d22ddb53` cho thấy retrieval chậm 2.502 s và generation chỉ 0.153 s.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version giúp truy xuất v1/v2 và rollback production; token/cost nằm trên generation observation; SLO/alert biến latency và error budget thành tín hiệu vận hành.
- **Điều quan trọng nhất đã học:** Baseline validator giúp xác định các thiếu sót của starter trước khi triển khai logging và observability.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Đã hoàn tất source/config và incident analysis; còn thiếu ảnh runtime dashboard, trace/prompt/rollback và commit SHA cuối.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
