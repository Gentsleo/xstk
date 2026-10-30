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

## 3. Cổng hình thái sản xuất và chuẩn QR lý thuyết

Vector [tổng, số lẻ, số cao ≥18, độ rộng, cặp liền kề]. Cổng sản xuất dùng
`EMPIRICAL_MU = [91.1069, 2.5681, 2.6237, 23.8512, 0.5755]` và
`EMPIRICAL_INV_COV` trong `qr_filter.py`, cố định từ kỳ 1–954 theo bản
`f597fffb6ec5a3ab19134185815fd1e4eddc12ea`. Không cập nhật theo
kết quả mới. Với $D_{\rm emp}^2=(x-\mu_{\rm emp})^T\Sigma_{\rm emp}^{-1}
(x-\mu_{\rm emp})$ và entropy sáu khoảng trống
$H=-\sum(g_i/36)\ln(g_i/36)$:
$$\mathrm{SQS}=\operatorname{round}\left(
100[1-F_{\chi^2_5}(D_{\rm emp}^2)]
[0.8+0.2\operatorname{clamp}((H-1)/(\ln6-1),0,1)],1\right).$$
Chỉ nhận bộ chính khi SQS ≥ 80 và **H chưa làm tròn ≥ 1,50**; đề xuất
đồng đều bằng nguồn ngẫu nhiên bảo mật trước cổng, không lặp bộ đã nhận.
Số đặc biệt được lấy đều, độc lập 1–12 *sau khi* bộ chính đạt cổng, được
phép trùng số chính hoặc số đặc biệt của vé khác. Wheel tìm hai bộ chính
đạt cổng và rời nhau; `./xstk.sh qr --uniform N` là mốc nghiên cứu lấy mẫu
không lọc.

Chuẩn **lý thuyết** riêng dùng `MU`, `INV_COV` trên 324.632 bộ đều:
$D_{\rm fair}^2\le7.055639346938778$ chứa 259.706 bộ. Cờ QR80 chỉ mô tả,
không phải cổng chọn vé. Đuôi chi-square xấp xỉ là điểm hình thái, không
phải xác suất trúng; mỗi vé cố định 5+1 vẫn có xác suất $1/3895584$ nếu
quay đều độc lập. `./xstk.sh backtest --output audit_model.json` đối chiếu
thể tích vùng, tỷ lệ lịch sử và chuẩn fair: kỳ ≤954 là hồi cứu/hiệu
chuẩn; kỳ >954 nằm ngoài giai đoạn tính hệ số nhưng nếu đã xem vẫn là
hồi cứu, không phải holdout chưa thấy. MCP chỉ phục vụ tính toán/đối
chiếu nghiên cứu, runtime dùng hệ số đã khóa; báo cáo
`reports/qr_model_verification.json` ghi cách kiểm tra độc lập, không phải
lệnh MCP chạy mỗi khi sinh vé. Lab/neural là nghiên cứu riêng, không phải
engine này; không suy ra lợi thế dự báo từ độ phủ.

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
| `./xstk.sh qr --gen N` | `qr_filter.py --gen N` | Sinh 1–20 vé với bộ chính qua cổng SQS/H, số đặc biệt độc lập đều |
| `./xstk.sh qr --uniform N` | `qr_filter.py --uniform N` | Mốc nghiên cứu đồng đều không lọc trên toàn không gian |
| `./xstk.sh wheel` | `qr_filter.py --wheel 10` | Hai bộ chính qua cổng, rời nhau; bảo đảm khớp 3 chỉ có điều kiện |
| `./xstk.sh logs` | `tail -f auto_update.log` | Xem nhật ký cập nhật |
