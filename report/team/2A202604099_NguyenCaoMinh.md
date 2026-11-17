# Báo cáo cá nhân — Nguyễn Cao Minh

## 1. Thông tin thành viên

- Họ tên: Nguyễn Cao Minh
- MSSV: 2A202604099
- Email: 26ai.minhnc@vinuni.edu.vn
- GitHub: https://github.com/caominhnguyen05

## 2. Phần việc phụ trách

- Triển khai hai shape `workflow` và single-agent ReAct, bao gồm viết test cho từng phần, chạy kiểm thử và đối chiếu cách xử lý với `docs/business_rules.md` và `docs/contracts.md`.

## 3. Đóng góp cụ thể

- Implement `run_claim()` trong `src/lab8/shapes/workflow.py` theo các bước cố định: đọc claim, kiểm tra mã đơn và quyền sở hữu, tính quote từ order có cấu trúc, gọi host và trả `RunResult` qua `finish()` (commit `cc5e6da`).
- Viết `src/tests/test_workflow.py` với 8 test cho claim không tồn tại, approval thuộc claim khác, approval thấp hơn quote, xung đột số tiền khi retry, ba điểm crash và ticket chứa chỉ dẫn không đáng tin.
- Triển khai `run_claim()` trong `src/lab8/shapes/single.py`, sử dụng `run_react()` với giới hạn 8 bước, chỉ cho phép tool đọc và gọi host ghi refund sau khi vòng lặp kết thúc (commit `3b5d86b`). MockLLM hiện chưa trả lệnh gọi tool có cấu trúc, nên `decide()` chọn hành động bằng code dựa trên observation; các lời gọi MockLLM vẫn được tính vào budget.
- Viết `src/tests/test_single.py` với 10 test cho claim không tồn tại, ranh giới chỉ đọc của ReAct và thống kê model call, giới hạn bước, approval sai claim, approval thấp hơn quote, retry xung đột, ba điểm crash và ticket injection.
- Đối chiếu code với business rules: tiền do `compute_compensation` tính từ dữ liệu có cấu trúc và policy hiện hành; không lấy số ngày trễ từ ticket; truyền quote đầy đủ để host kiểm approval, trừ refund trước đó và chống ghi trùng.
- Đối chiếu code với contract: trả đúng `status` và `proposal_amount`, lấy refund/audit từ ledger qua `finish()`, ghi trace hợp lệ và tránh ghi dữ liệu nhạy cảm. Cả hai shape chuyển `crash_at` vào `issue_refund()` và để `InjectedCrash` truyền ra cho harness kiểm tra.
- Chạy lại test cho từng shape và bộ test mặc định để xác nhận không có test fail trong các bộ đã chạy.

## 4. Bằng chứng

### Commit đóng góp

Ba commit trong ảnh bằng chứng đã được đối chiếu với lịch sử Git của repo:

| Hash | Nội dung commit | Phần đóng góp |
| --- | --- | --- |
| [`16a5647`](https://github.com/caominhnguyen05/K5-L3B-DAY08-MinhVinh-FromWorkflowsToAgents/commit/16a5647) | Add member roles | Ghi thông tin và vai trò các thành viên |
| [`cc5e6da`](https://github.com/caominhnguyen05/K5-L3B-DAY08-MinhVinh-FromWorkflowsToAgents/commit/cc5e6da) | Add workflow logic and tests | Triển khai workflow và test |
| [`3b5d86b`](https://github.com/caominhnguyen05/K5-L3B-DAY08-MinhVinh-FromWorkflowsToAgents/commit/3b5d86b) | Add single agent and tests | Triển khai single-agent ReAct và test |

## 5. Công cụ AI đã dùng

- Sử dụng Codex (model GPT-6.1 Sol) để hỗ trợ implement code cho hai phần workflow và single-agent ReAct, bao gồm hỗ trợ viết test và giải thích luồng xử lý.

- Tôi tự kiểm tra kết quả bằng cách đọc và so sánh code với `docs/business_rules.md` và `docs/contracts.md`, đặc biệt ở các điểm: nguồn dữ liệu tính tiền, trạng thái trả về, quote đầy đủ, approval, idempotency, crash và trace an toàn. Sau đó tôi chạy lại test của workflow, single và bộ test mặc định để bảo đảm không có test fail trong các bộ đã chạy. Tôi dùng kết quả kiểm thử thực tế làm bằng chứng, không chỉ dựa vào phần giải thích hoặc khẳng định của công cụ AI.

## 6. Tự đánh giá

Tôi đã hoàn thành phần workflow và single-agent ReAct cùng các test bổ sung. Qua việc đối chiếu tài liệu và chạy test, tôi hiểu rõ hơn sự khác nhau giữa điều phối theo các bước cố định và điều phối qua vòng ReAct, cũng như ranh giới giữa model, tool tính tiền và host ghi refund.

Hai shape đều qua 62 test public tương ứng, và bộ test mặc định không có test fail. 
