# Báo cáo cá nhân — Nguyễn Cao Minh

## 1. Thông tin thành viên

- Họ tên: Nguyễn Cao Minh
- MSSV: 2A202604099
- Email: 26ai.minhnc@vinuni.edu.vn
- GitHub: https://github.com/caominhnguyen05

## 2. Phần việc phụ trách

Workflow, integration và single-agent shape.

## 3. Đóng góp cụ thể

- Commit `cc5e6da` triển khai workflow và thêm `src/tests/test_workflow.py`.
- Commit `3b5d86b` triển khai single-agent ReAct và thêm `src/tests/test_single.py`.
- Cả hai shape dùng dữ liệu có cấu trúc để tính quote; quyền ghi refund vẫn ở host và được kiểm soát bằng ledger/approval.

## 4. Bằng chứng

- `python -m pytest -q`: 77 passed, 248 deselected.
- Benchmark public: workflow 70/70, pass^5 1.000, cost/success 27.86 VND; single 70/70, pass^5 1.000, cost/success 29.85 VND.
- Các commit và test được đối chiếu trực tiếp với lịch sử Git.

## 5. Công cụ AI đã dùng

Thông tin sử dụng AI cá nhân không có trong lịch sử Git. Thành viên cần tự xác nhận và bổ sung công cụ/cách kiểm chứng nếu đã sử dụng.

## 6. Tự đánh giá

Hai shape hoàn thành đều qua public benchmark trên 14 claim và 5 seed. Workflow đạt cùng pass rate với single với cost/success thấp hơn trong bộ thử nghiệm này. Kết luận còn giới hạn bởi quy mô public corpus và MockLLM.
