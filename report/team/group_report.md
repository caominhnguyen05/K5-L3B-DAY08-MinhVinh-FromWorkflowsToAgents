# Báo cáo nhóm — MinhVinh, Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: MinhVinh
- Thành viên: Nguyễn Cao Minh và Tào Quang Vinh; thông tin chi tiết ở [TEAM.md](../../TEAM.md).
- Repo: https://github.com/caominhnguyen05/K5-L3B-DAY08-MinhVinh-FromWorkflowsToAgents, nhánh `main`.
- Commit chốt: điền sau commit cuối.

## 2. Mục tiêu và cách tiếp cận

Nhóm so sánh bốn cách tổ chức xử lý claim trên cùng bộ dữ liệu, cùng giá và cùng năm seed. Workflow dùng quy tắc xác định; single dùng một agent ReAct chỉ đọc; orchestrator chuyển handoff cho investigator chỉ đọc và giữ quyền ghi ở host; swarm reference thêm peer/parse calls. Nhóm chia workflow và single cho Nguyễn Cao Minh; orchestrator, handoff, ledger/crash và tổng hợp kết quả cho Tào Quang Vinh.

## 3. Giải pháp

Ba shape của nhóm không để model tự quyết định số tiền hoặc ghi refund. Workflow đọc claim và order qua tool, tính quote bằng code rồi gọi host. Single dùng vòng ReAct có giới hạn tám bước; các tool trong loop chỉ đọc, còn host xác thực quote và ghi. Orchestrator kiểm tra claim, dừng sớm khi thiếu order id, tạo handoff theo allowlist rồi nhận order/policy/refund-history/quote từ investigator. Host gọi `issue_refund` bằng quote đầy đủ. `durability.issue_refund` ràng approval với claim, áp trần theo order, và ghi ledger cùng audit trong một transaction. Checkpoint hỗ trợ resume nhưng ledger là nguồn bảo đảm idempotency.

Handoff chỉ chứa trường hợp đồng, claim id, scope, task, facts allowlist và tool được cấp. Trace ghi sự kiện cần để giải thích quyết định, không ghi ticket, parent secret, headers hay claim row. Trace được quét trên các run public đã tạo; các kiểm thử riêng xác nhận denial khi approval sai hoặc bị thu hồi.

## 4. Kết quả

Benchmark được tạo bằng `lab8.benchmark` trên 14 claim × 5 seed. Số liệu là VND mô phỏng; latency không đo được.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean / p95 steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 27.86 | 4.43 / 5 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 29.85 | 6.29 / 7 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 57.11 | 3.71 / 4 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Nhóm chọn workflow: đây là shape ít tự chủ nhất trong ba shape đã triển khai, có 70/70 pass và cost/success thấp nhất. Orchestrator ít trace steps hơn nhưng không tăng độ đúng và có cost cao hơn. Swarm có một fail: C-002, seed 55. Code reference cố ý thay delay 2 ngày ở order bằng 5 ngày trong ticket ở seed chia hết cho 5; trace `R-swarm-C-002-s55` cho thấy quote 20,000 VND và kết quả resolve sai claim lẽ ra denied.

Crash suite đạt 20/20. Kiểm tra thủ công orchestrator tại `before_effect`, `after_effect_before_checkpoint` và `after_checkpoint` đều crash exit 2; retry cùng DB cho một refund, một committed audit và status resolved. Bộ test hiện tại: 77 passed, 248 deselected. Thư mục `student_drop/` chưa có trong workspace tại lần kiểm tra này.

Nhóm chạy thêm ba trường hợp khó trên cả workflow, single và orchestrator: C-002 có ticket nói delay 5 ngày trong khi order ghi 2 ngày (cả ba denied); C-005 tham chiếu order ngoài principal (cả ba escalated); và C-001 có ticket injection yêu cầu gọi write tool, kèm canary/PII (cả ba resolved theo quote DB, chuỗi injection/canary/PII không xuất hiện trong trace).

## 5. Ablation và khó khăn

Để đo giá của một investigator, nhóm chạy thêm `orchestrator_no_history`, chỉ bỏ `lookup_refund_history` khỏi handoff và giữ nguyên model, dữ liệu, seeds, giá, evaluator cùng các tool khác. Trên 70 trial, cả hai biến thể đều pass 70/70, pass^5 1.000, variance 0. Bỏ tool làm mean tool calls giảm 5.57 xuống 4.64 và cost/success giảm 57.11 xuống 47.82 VND; trace steps giữ 3.71 mean và 4 p95. Đây là ablation một thành phần trên public set, không chứng minh tool này vô ích trên claim khác hoặc production.

`lab8.demo.buggy_workflow` minh họa rằng checkpoint đơn lẻ không ngăn side effect lặp lại: demo báo hai refund rows trong khi ledger host phải giữ một. Vì vậy refund row và `refund_committed` audit được ghi nguyên tử; retry đọc ledger để trả idempotent replay.

## 6. Đóng góp

Nguyễn Cao Minh hoàn thiện workflow và single, kèm `test_workflow.py` và `test_single.py`. Tào Quang Vinh hoàn thiện orchestrator, thêm `test_orchestrator.py`, crash/handoff coverage và báo cáo. Commit cụ thể được liệt kê trong [TEAM.md](../../TEAM.md) và sẽ bổ sung hash cuối sau commit.

## 7. Hạn chế và hướng cải thiện

MockLLM là stand-in xác định, không đại diện model sản xuất; chi phí là giá mô phỏng và latency `unavailable`. Corpus chỉ gồm 14 claim, năm seed nên không thể kết luận về phân bố hoặc tải production. Hidden self-check chưa chạy vì coach chưa phát `student_drop/`. Nên bổ sung claim injection, lời khai sai, ownership chéo và đánh giá hidden trước khi khái quát hóa kết quả.

## 8. Tài liệu tham khảo

- Cemri et al. (2025), [Why Do Multi-Agent LLM Systems Fail?](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html), NeurIPS 2025 Datasets and Benchmarks Track.
- Số liệu benchmark/crash/ablation trong `src/reports/benchmark.json`, `src/reports/crash.json` và `src/reports/ablation_no_refund_history.json`.
