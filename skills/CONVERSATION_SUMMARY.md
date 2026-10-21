# Tóm Tắt Toàn Bộ Phiên Làm Việc (Conversation Summary)

**Ngày thực hiện:** 18/10/2026  
**Thư mục làm việc:** `/home/tringuyen/xstk`

---

## 1. Yêu cầu 1: Cài đặt 3 MCP Servers cho Oh My Pi (omp)
- **3 MCP đã cài đặt:**
  1. `codeprimate/math-mcp`: Cài qua `uv tool install git+https://github.com/codeprimate/math-mcp` $\rightarrow$ binary tại `/home/tringuyen/.local/bin/math-mcp`.
  2. `SHSharkar/MCP-Mathematics`: Cài qua `uv tool install mcp-mathematics` $\rightarrow$ binary tại `/home/tringuyen/.local/bin/mcp-mathematics`.
  3. `akalaric/mcp-wolframalpha`: Clone và tạo venv tại `/home/tringuyen/.local/share/mcp-servers/mcp-wolframalpha/.venv`. Đã tối ưu mã nguồn để khởi động mượt mà ngay cả khi chưa có API key.
- **Cấu hình:** Đã tạo file cấu hình `.mcp.json` và `.omp/mcp.json` tương thích chuẩn với Oh My Pi.

---

## 2. Yêu cầu 2: Cào (Crawl) Dữ liệu Vietlott Lotto 5/35
- **Địa chỉ cào:** `https://vietlott.vn/vi/trung-thuong/ket-qua-trung-thuong/535` và `winning-number-535`.
- **Kết quả:** Cào toàn bộ **954 kỳ quay** (từ kỳ đầu tiên `#00001` ngày 29/06/2025 đến kỳ mới nhất `#00954` ngày 18/10/2026).
- **Lưu trữ:** Đã lưu dưới các dạng:
  - `vietlott_535.db` (SQLite)
  - `vietlott_535.csv`
  - `vietlott_535.json`
- **Script cào:** `scrape_vietlott_535.py`.

---

## 3. Yêu cầu 3: Chuẩn hóa Dữ liệu (Z-Score) và Xuất Biểu Đồ qua `math-mcp`
- **Công cụ:** Gọi `describe_data`, `plot_bar`, `plot_histogram` của `math-mcp` qua stdio protocol.
- **Kết quả sinh ra:**
  - `vietlott_535_standardized.csv`: Bảng dữ liệu chuẩn hóa có tổng số, Z-score tổng, chẵn/lẻ, tài/xỉu.
  - `vietlott_535_frequency_stats.csv`: Tần suất và Z-score của 35 số chính.
  - 4 biểu đồ PNG trong thư mục `charts/`:
    - `01_frequency_distribution.png`
    - `02_zscore_standardized_balls.png`
    - `03_sum_histogram.png`
    - `04_special_numbers.png`

---

## 4. Yêu cầu 4: Tự Động Cập Nhật Sau Mỗi Ngày / Mỗi Kỳ
- **Script:** `auto_update.py`
- **Cơ chế:** Kiểm tra gia tăng (incremental update) dựa vào `MAX(draw_id)`. Khi có kỳ mới, tự động nạp vào DB, xuất lại CSV/JSON, chạy lại chuẩn hóa và làm mới 4 biểu đồ.
- **Tự động hóa:** Tích hợp Linux Cron job tự động chạy mỗi 30 phút.

---

## 5. Yêu cầu 5: Bash Script Tiện Ích Kèm Comment Hướng Dẫn
- **Script:** `xstk.sh` (đã `chmod +x`).
- Chứa comment hướng dẫn đầy đủ cách chạy và ý nghĩa của các file Python, kèm các lệnh quản lý tắt:
  - `./xstk.sh status`
  - `./xstk.sh update`
  - `./xstk.sh plot`
  - `./xstk.sh scrape-all`
  - `./xstk.sh cron-on` / `cron-off`
  - `./xstk.sh watch`
  - `./xstk.sh qr`

---

## 6. Yêu cầu 6: Mô Hình Dung Sai QR (Typical Set) Dự Đoán Cấu Trúc Chung
- **Ý tưởng:** Tương tự như mã QR bị che 20-25% vẫn quét được nhờ các điểm neo định vị.
- **5 Điểm neo vĩ mô trích xuất từ 954 kỳ:**
  1. Tổng 5 số: $75.2\%$ rơi vào $[65, 115]$ ($Z \in [-1.2\sigma, +1.2\sigma]$).
  2. Tỷ lệ Chẵn / Lẻ: $66.5\%$ là $3:2$ hoặc $2:3$.
  3. Tỷ lệ Tài / Xỉu (ngưỡng 18): $64.7\%$ là $3:2$ hoặc $2:3$.
  4. Độ rộng bộ số (Span): $79.5\%$ rơi vào $[18, 32]$.
  5. Cặp số liền kề: $89.9\%$ có đúng $0$ hoặc $1$ cặp liên tiếp.
- **Bao hàm Số Đặc Biệt ($1 - 12$):** Phân phối đồng đều, $87.8\%$ không trùng với 5 số chính.
- **Hàm khoảng cách QR ($D_{\text{total}}$):**
  - $D \le 3.85$: Top 50% Typical Core (Tối ưu nhất).
  - $D \le 7.08$: Vùng dung sai 80% của lịch sử.
  - $D > 7.08$: Vùng rủi ro lệch chuẩn.
- **So sánh Tổng vs D-Score:** Nên chú trọng vào D-Score vì D-Score là chỉ số đa chiều bao hàm cả Tổng, trong khi chỉ nhìn vào Tổng có thể bỏ sót tới $40.8\%$ các bộ số bị dị tật (dồn cục, lệch chẵn lẻ).
- **Công cụ kiểm tra & sinh số chuẩn:** `qr_filter.py` (tích hợp trong `./xstk.sh qr`).
