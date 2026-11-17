# Báo cáo cá nhân — Tào Quang Vinh

## 1. Thông tin thành viên

- Họ tên: Tào Quang Vinh
- MSSV: 2A202604081
- Email: 26ai.vinhtq3@vinuni.edu.vn
- GitHub: https://github.com/qvinhh2312

## 2. Phần việc phụ trách

Orchestrator + handoff; ledger/crash integration; tổng hợp benchmark và báo cáo nhóm.

## 3. Đóng góp cụ thể

- Hoàn thiện `src/lab8/shapes/orchestrator.py`: đọc claim qua `get_claim_view`, dừng `needs_info` trước handoff, handoff chỉ cấp read tools, dùng quote investigator và để host gọi `issue_refund` với quote đầy đủ cùng `crash_at`.
- Bổ sung `src/tests/test_orchestrator.py` cho unknown claim, thiếu order, quote bằng 0, approval bị thu hồi và approval thuộc claim khác.
- Giữ nguyên host handoff implementation và test host starter; grader cuối chỉ nhận shape files và bonus nên thay đổi host không phải cách sửa phù hợp.
- Tạo ablation bonus loại `lookup_refund_history`, cùng báo cáo benchmark/crash và tài liệu ADR, research card, group report.

## 4. Bằng chứng

- Commit code/reports: `47809a4`; commit hash trong ADR/TEAM được ghi ở commit tài liệu tiếp theo.
- `python -m pytest -q`: 77 passed, 248 deselected.
- `python -m lab8.crash_test --count 20 --out reports/crash.json`: `crash_safety 20/20`.
- Benchmark 4 shape: workflow 70/70, run `R-workflow-C-001-s11`; cost/success 27.86 VND, pass^5 1.000.
- Ablation: bỏ `lookup_refund_history` giữ pass rate/pass^5 1.000, giảm cost/success 57.11→47.82 VND trong public set; xem `src/reports/ablation_no_refund_history.json`.
- Quét trace public hiện có không thấy canary, số điện thoại, địa chỉ hoặc tên hàng.
- Chạy claim nói dối (C-002), ownership khác (C-005) và ticket injection trên cả ba shape; kết quả lần lượt denied, escalated, resolved theo dữ liệu đơn, trace không có canary/PII injection.

## 5. Công cụ AI đã dùng

Codex hỗ trợ triển khai và rà soát. Tôi kiểm tra kết quả bằng pytest, crash suite, benchmark cùng việc đọc trace và mã nguồn.

## 6. Tự đánh giá

Tôi đã tách side effect khỏi investigator, giữ quyết định refund ở host và xác minh khả năng phục hồi ledger qua ba điểm crash. Kết luận kiến trúc dựa trên số liệu mới cho thấy workflow đơn giản hơn đáp ứng đầy đủ public set với chi phí thấp nhất. Giới hạn chính là public set nhỏ và MockLLM không đại diện cho model production.
