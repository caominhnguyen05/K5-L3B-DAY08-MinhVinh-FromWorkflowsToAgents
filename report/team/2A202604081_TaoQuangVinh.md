# Báo cáo cá nhân — Tào Quang Vinh

## 1. Thông tin thành viên

- Họ tên: Tào Quang Vinh
- MSSV: 2A202604081
- Email: 26ai.vinhtq3@vinuni.edu.vn
- GitHub: [qvinhh2312](https://github.com/qvinhh2312)
- Nhóm: MinhVinh, lớp L3B

## 2. Phần việc phụ trách

Tôi phụ trách shape orchestrator, handoff giữa parent và các investigator chỉ đọc, tích hợp ghi refund qua ledger host, kiểm thử crash và tổng hợp kết quả evaluation/report. Mục tiêu là để investigator tìm dữ liệu và đưa quote, nhưng quyền phê duyệt cuối cùng và side effect vẫn thuộc host.

## 3. Thiết kế và đóng góp kỹ thuật

### Orchestrator

Trong `src/lab8/shapes/orchestrator.py`, tôi triển khai luồng chạy như sau:

1. Mở SQLite connection và luôn đóng trong `finally`.
2. Đọc claim qua `get_claim_view`; claim không tồn tại trả `failed/unknown_claim`.
3. Đếm một model call cho bước plan. Nếu claim thiếu `order_id`, trả `needs_info` trước khi tạo handoff để tránh nhầm lỗi thiếu dữ liệu thành lỗi visibility.
4. Tạo handoff bằng `make_handoff` với `facts={}` và chỉ cấp bốn tool đọc: `lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`.
5. Chạy `run_readonly_investigators`. Nếu order không visible, trả `escalated` và không đọc quote. Quote bằng 0 trả `denied` và không gọi công cụ ghi.
6. Nếu quote dương, host gọi `issue_refund` bằng quote đầy đủ và truyền nguyên `crash_at`. Kết quả `ok` thành `resolved`, conflict thành `failed`, các denial khác thành `denied`.
7. Đếm model call thứ hai cho bước draft. Trace lưu handoff đã sanitize, kết quả investigator, quote, quyết định và crash point; không lưu ticket, parent secret, raw headers hoặc claim row. Mọi nhánh bình thường kết thúc qua `finish()`.

Tôi thêm `src/tests/test_orchestrator.py` để giữ các nhánh quan trọng khỏi bị thoái lui: unknown claim, thiếu order trước handoff, quote bằng 0 không refund, approval bị thu hồi và approval của claim khác. Hai trường hợp approval phải tạo audit `policy_denied`.

### Handoff và ranh giới host

Ban đầu tôi thử siết `sanitize()` trong `src/lab8/handoff.py`, nhưng README quy định grader chỉ lấy ba file shape và `bonus/`; thay đổi host sẽ không có hiệu lực khi chấm và làm sai contract test gốc vốn yêu cầu drop trường ngoài allowlist. Tôi đã khôi phục `handoff.py` và `test_handoff_secret.py` về đúng phiên bản trong `HEAD`. Phần bảo vệ cho shape của tôi là tạo handoff từ allowlist, truyền `facts` rỗng, không đưa parent context vào trace, và để `run_readonly_investigators` chặn quyền ghi.

### Ledger và crash

Tôi tích hợp orchestrator với `durability.issue_refund` mà không sửa `durability.py` hay `policy.py`. Host nhận quote đầy đủ, kiểm approval theo claim, áp giới hạn tổng hoàn theo order, ghi refund cùng `refund_committed` audit trong transaction, rồi checkpoint để hỗ trợ resume. Checkpoint không thay ledger: demo `lab8.demo.buggy_workflow` cho thấy retry không có ledger có thể tạo hai refund rows.

Tôi xác minh ba điểm crash qua CLI với cùng DB cho từng kịch bản. Crash lần đầu đều exit code 2; retry không truyền `crash_at` đều trả `resolved`, một refund effect và `committed_audit_count: 1`:

| Điểm crash | Kết quả retry |
| --- | --- |
| `before_effect` | 1 refund, 1 committed audit |
| `after_effect_before_checkpoint` | 1 refund, 1 committed audit |
| `after_checkpoint` | 1 refund, 1 committed audit |

Crash suite tự động đạt `20/20`.

## 4. Evaluation và quyết định

Benchmark public dùng 14 claim, 5 seed (`11,22,33,44,55`) và cùng bảng giá. Chi phí là VND mô phỏng, không phải hóa đơn model.

| Shape | Pass rate | Pass^5 | Variance | Cost/success | Mean steps |
| --- | ---: | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 0.000000 | 27.86 VND | 4.43 |
| single | 1.000 | 1.000 | 0.000000 | 29.85 VND | 6.29 |
| orchestrator | 1.000 | 1.000 | 0.000000 | 57.11 VND | 3.71 |
| swarm | 0.986 | 0.929 | 0.000816 | 49.57 VND | 2.80 |

Nhóm chọn workflow theo tiêu chí shape ít tự chủ nhất vẫn hoàn thành đúng public set. Orchestrator giảm số bước trace so với workflow nhưng không tăng pass rate và tốn hơn gấp đôi chi phí mô phỏng; vì vậy không có đủ lợi ích để chọn multi-agent cho bài toán hoàn tiền này.

Tôi cũng chạy một ablation giữ nguyên orchestrator nhưng bỏ `lookup_refund_history`. Trên 70 trial, pass rate/pass^5 vẫn 1.000/1.000, variance vẫn 0; mean tool calls giảm từ 5.57 xuống 4.64 và cost/success giảm từ 57.11 xuống 47.82 VND. Mean steps vẫn 3.71 và p95 vẫn 4. Điều này cho thấy tool history chưa cần thiết để đạt expected output trên corpus public hiện tại; nó không chứng minh tool này vô ích với claim hoặc vận hành production khác.

Swarm có một lỗi ở C-002 seed 55. Order ghi delay 2 ngày, nhưng nhánh seeded weakness thay bằng 5 ngày lấy từ ticket; trace cho thấy hệ thống quote 20,000 VND và resolve một claim vốn phải denied. Đây là lỗi xác minh dữ liệu đầu vào trong setup lab, không phải bằng chứng khái quát rằng mọi hệ multi-agent đều kém hơn.

## 5. Kiểm thử và bằng chứng an toàn

- `python -m pytest -q`: 77 passed, 248 deselected.
- `python -m lab8.crash_test --count 20 --out reports/crash.json`: `crash_safety 20/20`.
- `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`: 70 trial mỗi shape.
- `python -m lab8.check_submission`: 0 FAIL, 0 WARN.
- Trên cả ba shape, C-002 có ticket nói delay sai bị denied; C-005 tham chiếu order ngoài principal bị escalated; ticket injection trong C-001 không đổi quote DB và chuỗi canary/điện thoại/địa chỉ/tên hàng không xuất hiện trong trace.
- Quét 351 trace hiện có theo secret markers và các chuỗi `forbid_substrings` của public claims: không có hit.

Artifacts: [benchmark.json](../../src/reports/benchmark.json), [crash.json](../../src/reports/crash.json), [ablation_no_refund_history.json](../../src/reports/ablation_no_refund_history.json). Run tham chiếu: `R-workflow-C-001-s11`; lỗi swarm: `R-swarm-C-002-s55`; ablation: `R-orchestrator_no_history-C-001-s11`.

## 6. Công cụ AI đã dùng

Tôi dùng Codex để hỗ trợ đọc mã, triển khai orchestrator/test, tổng hợp báo cáo và đề xuất ablation. Tôi kiểm tra lại thay đổi bằng cách đọc các module host, chạy test, crash suite, benchmark, tự chạy claim khó trên cả ba shape và quét trace. Tôi giữ lại test host gốc; không coi thay đổi host là bằng chứng vì grader bỏ qua các file đó.

## 7. Tự đánh giá và giới hạn

Điểm tôi làm tốt là giữ investigator chỉ đọc và để host kiểm soát quyết định ghi; ba lần crash đều phục hồi đúng mà không nhân đôi refund hoặc audit. Tôi cũng điều chỉnh quyết định kiến trúc sau khi benchmark hoàn tất: dữ liệu mới ủng hộ workflow thay vì orchestrator, dù orchestrator là phần tôi phụ trách.

Kết quả còn giới hạn bởi 14 claim công khai, năm seed và MockLLM xác định. Latency không được đo; chi phí chỉ mô phỏng. `student_drop/` chưa có trong workspace khi kiểm tra, nên chưa chạy hidden self-check. Cần xác nhận lại trên hidden corpus và tải gần production trước khi suy rộng kết luận.

Commit code/reports: `47809a4`; commit ghi hash vào hồ sơ: `b4b1a0d`.
