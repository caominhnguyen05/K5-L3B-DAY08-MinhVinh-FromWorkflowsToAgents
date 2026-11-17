# Research card

## Phiếu của nhóm

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng | Cemri et al., “Why Do Multi-Agent LLM Systems Fail?”, NeurIPS 2025 Datasets and Benchmarks Track, https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html; nghiên cứu taxonomy trên 1,600+ trace từ 7 MAS framework |
| CLAIM | Một kết luận gốc của nguồn | MAST phân loại 14 failure mode thành ba nhóm: system design issues, inter-agent misalignment, và task verification. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Taxonomy được xây và đánh giá trên trace của các MAS/framework, model và task cụ thể trong paper; dùng làm lăng kính phân tích, không tự chứng minh nguyên nhân cho mọi lỗi của lab. |
| HYPOTHESIS | Nếu đổi shape A→B hoặc một thành phần, metric đổi theo hướng nào | C-002/seed 55 thuộc nhóm task verification vì hệ thống chấp nhận delay từ ticket trái với order. Bỏ `lookup_refund_history` khỏi orchestrator handoff sẽ giữ pass rate/pass^5, đồng thời giảm tool calls và cost/success. |
| METHOD | Biến giữ cố định; biến duy nhất được thay đổi | Phân loại trace swarm C-002/seed 55 theo MAST. Ablation riêng giữ MockLLM, world, 14 claim, 5 seed, giá, evaluator và các tool khác; chỉ bỏ `lookup_refund_history` khỏi orchestrator. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo | Đối chiếu status/quote với expected để đếm task-verification failure; đo pass rate, pass^5, variance, cost/success, mean và p95 steps, cùng số tool calls. |

## Kết quả ablation

- Lệnh benchmark chính đã chạy: `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Lệnh ablation đã chạy: `python -m lab8.benchmark --shapes orchestrator,orchestrator_no_history --extra-shape orchestrator_no_history=bonus.orchestrator_no_history:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_no_refund_history.json`
- Run id / file report: lỗi taxonomy `R-swarm-C-002-s55`; ablation đại diện `R-orchestrator_no_history-C-001-s11`, báo cáo đầy đủ `src/reports/ablation_no_refund_history.json` (70 trial mỗi biến thể).
- Kết quả so với hypothesis: đúng trong public set. C-002/seed 55 resolve sai; trace cho thấy DB delay 2, ticket delay 5, và quote 20,000 VND. Ablation giữ pass rate/pass^5 ở 1.000/1.000, variance 0; mean tool calls giảm 5.57→4.64 và cost/success giảm 57.11→47.82 VND. Mean steps giữ 3.71, p95 giữ 4.
- Giới hạn: đây là một tool ablation trên orchestrator, không chứng minh mọi lợi ích/chi phí của multi-agent. MockLLM không phải model sản xuất, latency là `unavailable`; 14 claim công khai không đại diện production.
