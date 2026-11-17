# Decision record

Điền sau dấu `:` trên cùng dòng, giữ nguyên nhãn. Số liệu lấy từ benchmark mới nhất: 4 shape × 14 claim × 5 seed.

- Shape chọn: workflow
- Commit hash: b4b1a0d
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (70/70)
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: không phát hiện trong trace đã quét; không có bypass trong test secret và approval

## Vì sao shape này

Chọn workflow, shape ít tự chủ nhất trong ba shape do nhóm triển khai. Nó pass 70/70 trial, pass^5 1.000, variance bằng 0 và cost/success thấp nhất trong ba shape làm được việc: 27.86 VND, so với 29.85 của single và 57.11 của orchestrator. Workflow có mean 4.43 steps, cao hơn orchestrator (3.71), nhưng giảm được chi phí đáng kể mà không giảm pass rate trên corpus này.

## Có đáng đổi lấy multi-agent không

Không trong bài toán và dữ liệu hiện tại. Orchestrator giữ pass rate ngang workflow nhưng tốn hơn khoảng 2.05 lần; swarm rẻ hơn orchestrator nhưng chỉ pass 69/70, pass^5 0.929, và có một lỗi C-002 ở seed 55. Các shape agent có ít trace steps hơn, nhưng không cải thiện độ đúng của workflow. Quyết định có thể đổi nếu corpus lớn hơn cho thấy phần việc song song giúp tăng pass rate đủ để bù cost và độ biến thiên.

## Trace và bằng chứng

Workflow trace ghi run id, trạng thái claim/order visibility, quote amount và quyết định; không ghi ticket, parent_secret, raw headers, toàn bộ claim row hay PII của đơn. Orchestrator handoff chỉ truyền claim id, task, scope, facts rỗng và danh sách tool đọc; trace của nó ghi handoff đã sanitize cùng kết quả investigator. Quét trace hiện có không thấy canary, số điện thoại, địa chỉ hoặc tên hàng. Đây là bằng chứng từ trace và test của public setup, không khẳng định ngoài đường chạy đã kiểm tra.

## Giới hạn

MockLLM là stand-in seeded, không phải model sản xuất; giá chỉ là mô phỏng và latency là `unavailable`. Benchmark gồm 14 claim công khai, 5 seed và không đại diện cho phân bố production. Swarm fail C-002/seed 55 vì nhánh seeded override thay delay 2 ngày từ order bằng 5 ngày từ ticket, dẫn đến quote 20,000 VND và refund sai một claim vốn phải denied. Workflow được chọn theo tiêu chí ít tự chủ nhất vẫn đạt toàn bộ pass trong bộ kiểm thử này; kết luận cần đánh giá lại trên hidden/production-like corpus.
