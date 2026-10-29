---
name: vietlott-535-analysis
description: "Kiến thức, dữ liệu, công thức toán học và công cụ phân tích xác suất thống kê Vietlott Lotto 5/35 với mô hình dung sai QR"
---

# Kỹ Năng: Phân Tích Xác Suất Thống Kê Vietlott Lotto 5/35 (Mô Hình Mahalanobis & Shannon Gap Entropy)

Tài liệu này lưu lại toàn bộ tri thức, công thức toán học tối ưu, dữ liệu và công cụ đã xây dựng cho dự án `xstk`.

---

## 1. Hệ thống MCP Servers đã cài đặt

1. **`math-mcp`** (`codeprimate/math-mcp`):
   - Đường dẫn thực thi: `/home/tringuyen/.local/bin/math-mcp`
   - Chức năng: Thống kê mô tả (`describe_data`), vẽ biểu đồ trực quan (`plot_bar`, `plot_histogram`, `plot_timeseries`).
2. **`mcp-mathematics`** (`SHSharkar/MCP-Mathematics`):
   - Đường dẫn thực thi: `/home/tringuyen/.local/bin/mcp-mathematics`
   - Chức năng: 52 hàm tính toán cao cấp, xác suất, chuyển đổi đơn vị (`calculate_statistics`, `calculate_expression`).
3. **`wolframalpha`** (`akalaric/mcp-wolframalpha`):
   - Môi trường: `/home/tringuyen/.local/share/mcp-servers/mcp-wolframalpha/.venv`
   - File cấu hình: `WOLFRAM_API_KEY` trong `/home/tringuyen/xstk/.env`
   - Chức năng: Truy vấn tri thức và giải tích sâu qua Wolfram Alpha (`query_wolfram`).

Cấu hình MCP cho dự án lưu tại:
- `/home/tringuyen/xstk/.mcp.json`
- `/home/tringuyen/xstk/.omp/mcp.json`

---

## 2. Dữ liệu Lịch sử Vietlott Lotto 5/35

- **Phạm vi dữ liệu:** Xem `./xstk.sh status` để biết kỳ mới nhất.
- **Tần suất mở thưởng:** $2$ kỳ mỗi ngày.
- **Các file dữ liệu trong dự án:**
  - `vietlott_535.db` : SQLite DB lưu bảng `draws`
  - `vietlott_535.csv`: File CSV dữ liệu thô
  - `vietlott_535.json`: File JSON
  - `vietlott_535_standardized.csv`: Bảng dữ liệu chuẩn hóa (tổng, Z-score, chẵn lẻ, tài xỉu)
  - `vietlott_535_frequency_stats.csv`: Thống kê tần suất và Z-score của 35 số chính
- **Biểu đồ đã xuất (`charts/`):**
  - `01_frequency_distribution.png`: Tần suất 35 số chính
  - `02_zscore_standardized_balls.png`: Z-score chuẩn hóa 35 số chính
  - `03_sum_histogram.png`: Histogram phân phối tổng 5 số
  - `04_special_numbers.png`: Tần suất 12 số đặc biệt

---

## 3. Mô hình dung sai QR

Với vector đặc trưng [tổng, số lẻ, số cao ≥18, độ rộng, cặp liền kề],
$D^2=(x-\mu)^T\Sigma^{-1}(x-\mu)$ dùng trung bình và hiệp phương sai
trên toàn bộ 324.632 tổ hợp đồng xác suất. Vùng QR là
$D^2\le7.055639346938778$, chứa 259.706 tổ hợp (80,0001%).
Sinh vé đều trên toàn bộ 324.632 tổ hợp bằng SystemRandom (Python) hoặc
crypto.getRandomValues + rejection mapping (web), không lọc QR/SQS/lịch sử.
Nhiều vé không lặp bộ chính; hai vé wheel rời nhau nên phụ thuộc, mỗi vé vẫn đều.
QR chỉ mô tả sau khi sinh; không ưu tiên số cũ, số vắng hoặc chống chia giải.

Entropy khoảng trống và SQS chỉ mô tả hình thái, không phải xác suất.
Đuôi $\chi^2_5$ là tham chiếu xấp xỉ, không phải phân phối chính xác.
Mỗi vé 5+1 có xác suất $1/3895584$ nếu quay công bằng và độc lập.
Vùng này mô phỏng ý tưởng dung sai, không có mã sửa sai để dự đoán xổ số.
Huấn luyện ngưỡng theo thời gian và kiểm tra ngoài mẫu: `./xstk.sh backtest`.

---

## 4. Danh Mục Công Cụ & Script Điều Khiển

Tất cả thao tác có thể thực hiện thông qua `./xstk.sh`:

| Cú pháp | File thực thi | Mô tả |
|---|---|---|
| `./xstk.sh status` | `auto_update.py --status` | Xem số lượng kỳ, ngày/kỳ mới nhất, trạng thái Cron |
| `./xstk.sh update` | `auto_update.py` | Kiểm tra và tải các kỳ mới phát sinh |
| `./xstk.sh plot` | `standardize_and_plot.py` | Chạy lại chuẩn hóa thống kê & làm mới 4 biểu đồ qua `math-mcp` |
| `./xstk.sh scrape-all` | `scrape_vietlott_535.py` | Cào lại toàn bộ lịch sử từ kỳ 1 đến nay |
| `./xstk.sh cron-on` | `auto_update.py --install-cron` | Bật tự động cập nhật ngầm định kỳ (mỗi 30 phút) |
| `./xstk.sh cron-off` | `auto_update.py --remove-cron` | Tắt Cron job |
| `./xstk.sh watch` | `auto_update.py --watch` | Chạy loop theo dõi liên tục trong terminal |
| `./xstk.sh qr <nums>` | `qr_filter.py` | Đánh giá bộ số theo Mahalanobis & Entropy (vd: `./xstk.sh qr 6 15 21 30 34 6`) |
| `./xstk.sh qr --gen N` | `qr_filter.py --gen N` | Sinh đều N bộ trên toàn không gian, QR chỉ mô tả |
| `./xstk.sh logs` | `tail -f auto_update.log` | Xem nhật ký cập nhật |
