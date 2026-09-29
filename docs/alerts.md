# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: High latency P95
- Severity: warning
- Duration: 10 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: `fast_successful_requests`, latency P95 <= 3000 ms
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` trong 10 phút
- Ảnh hưởng tới người dùng: câu trả lời chậm hoặc request hết thời gian chờ
- Ba bước kiểm tra đầu tiên: xem dashboard latency/TTFT; lọc log theo thời gian; mở trace và so sánh retrieval với generation
- Mitigation tạm thời: giảm concurrency, tắt scenario/feature gây chậm, chuyển traffic sang cấu hình ổn định
- Owner: `llm-platform`

## Alert 2

- Tên: High error rate
- Severity: critical
- Duration: 5 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: error rate guardrail <= 2%
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` trong 5 phút
- Ảnh hưởng tới người dùng: request thất bại hoặc không nhận được câu trả lời
- Ba bước kiểm tra đầu tiên: xem error breakdown; lọc `request_failed`; mở trace lỗi và kiểm tra retrieval/LLM span
- Mitigation tạm thời: rollback prompt/config mới, tắt incident đang bật, giảm tải hoặc chuyển sang fallback
- Owner: `api-oncall`

## Alert 3

- Tên: Low retrieval success
- Severity: warning
- Duration: 10 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: retrieval success rate >= 90%
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90` trong 10 phút
- Ảnh hưởng tới người dùng: câu trả lời thiếu tài liệu hoặc chất lượng giảm
- Ba bước kiểm tra đầu tiên: xem panel errors/retrieval; kiểm tra `tool_success`; mở trace retrieval để tìm timeout hoặc lỗi dữ liệu
- Mitigation tạm thời: bật fallback knowledge, giảm phạm vi truy vấn, khôi phục cấu hình retriever ổn định
- Owner: `search-oncall`
