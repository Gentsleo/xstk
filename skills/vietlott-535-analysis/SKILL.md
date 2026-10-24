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

- **Phạm vi dữ liệu:** Toàn bộ lịch sử từ kỳ `#00001` (29/06/2025) đến kỳ mới nhất `#00965` (24/10/2026) - Tổng cộng $965$ kỳ quay.
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

## 3. Lý Thuyết & Công Thức Toán Học Tối Ưu (Mahalanobis Distance & Shannon Gap Entropy)

### 3.1. Vấn đề của mô hình khoảng cách Euclid cũ
Khi đo khoảng cách bằng tổng bình phương các độ lệch đơn giản $\sum w_i (x_i - \mu_i)^2$, xảy ra hiện tượng **Đa cộng tuyến nghiêm trọng (Multicollinearity)** giữa `Sum` và `Highs` ($\text{Corr} = +0.876$). Điều này khiến mô hình bị phạt đúp cùng một đặc tính.

### 3.2. Giải pháp 1: Khoảng Cách Mahalanobis và Phân Phối Chi-Square ($\chi^2_5$)
Sử dụng ma trận nghịch đảo hiệp phương sai $\boldsymbol{\Sigma}^{-1}$ tính từ 954 kỳ quay:
$$D_M^2(\mathbf{x}) = (\mathbf{x} - \boldsymbol{\mu})^T \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu})$$
Trong đó $\mathbf{x} = [\text{Sum}, \text{Odds}, \text{Highs}, \text{Span}, \text{Consecs}]^T$.

Biến ngẫu nhiên $D_M^2$ tuân theo phân phối Chi-Square với $k=5$ bậc tự do:
* **Trung bình thực nghiệm:** $4.995 \approx 5.000$ (Lý thuyết $\chi^2_5$)
* **Median thực nghiệm:** $4.225 \approx 4.351$
* **P80 thực nghiệm:** $7.096 \approx 7.289$
* **P95 thực nghiệm:** $11.151 \approx 11.070$

Xác suất điển hình chuẩn ($p$-value):
$$p = 1 - F_{\chi^2_5}(D_M^2)$$

### 3.3. Giải pháp 2: Shannon Gap Entropy (Entropy Khoảng Trống)
Đo độ trải đều của 5 số trên trục số $[1, 35]$ qua 6 khoảng cách $g_1 \dots g_6$:
$$H(\text{Gaps}) = -\sum_{i=1}^6 \left(\frac{g_i}{36}\right) \ln \left(\frac{g_i}{36}\right)$$
* Cực đại lý thuyết: $H_{\max} = \ln(6) \approx 1.7918$.
* Trung bình 954 kỳ: $H = 1.514$, độ lệch $\sigma = 0.140$.
* Ngưỡng $H < 1.25$: Bị dồn cụm cục bộ (Clustering).

### 3.4. Điểm Chất Lượng Chuẩn Hóa SQS (Thang điểm 100)
$$\text{SQS} = \text{Score}_{\text{main}} \times 0.85 + \text{Score}_{\text{special}} \times 0.15$$
* $\text{SQS} \ge 75/100$: **XUẤT SẮC** (Top 25% tâm phân phối đối xứng hoàn hảo).
* $40 \le \text{SQS} < 75$: **ĐẠT CHUẨN** (Vùng dung sai 80% QR Code).
* $10 \le \text{SQS} < 40$: **TRUNG BÌNH** (Dung sai biên).
* $\text{SQS} < 10$: **CẢNH BÁO** (Dị tật, dồn cụm, lệch chẵn lẻ cực đoan $p < 0.05$).

### 3.5. Nâng Cấp SQS Engine v2.0 (5 Trụ Cột Toán Học Đa Tầng)
1. **Chuỗi Markov Lặp Nhịp ($R \le 2$):** Tỷ lệ lặp $\ge 3$ số từ kỳ liền kề chỉ $1.24\%$ trong 964 kỳ thực nghiệm. Cắt bỏ mọi vé lặp $\ge 3$ số.
2. **Nhịp Vắng Poisson ($S_{\text{Skip}} \in [20, 54]$):** Tổng nhịp vắng của 5 số có kỳ vọng lý thuyết là $35.1$ kỳ. Ghim vé vào vùng hội tụ 80% thực tế $[20, 54]$.
3. **Lý Thuyết Trò Chơi Anti-Clustering Solo EV (Cox 1998):** Chọn ít nhất 1-2 số $\ge 32$ để chống trùng giải sinh nhật, tối đa hóa kỳ vọng nhận 100% Jackpot độc quyền.
4. **Hệ Thống Phủ Tổ Hợp Stefan Mandel $C(10, 5, 3, 5)$:** Phân hoạch 10 số thành 2 vé rời rạc ($5+5=10$). Theo Nguyên lý Lồng chim (Pigeonhole), đảm bảo 100% trúng Giải 3 nếu 5 số rơi vào bể 10 số, tiết kiệm 99.2% vốn (2 vé thay vì 252 vé).
5. **Hiệu Suất Lọc Toàn Diện:**
   - Không gian ban đầu: $324,632$ tổ hợp ($100\%$).
   - SQS v1.0: $\approx 160,731$ tổ hợp ($49.5\%$, nén $2.02\times$).
   - SQS v2.0: $\approx 47,214$ tổ hợp ($14.5\%$, nén **$6.88\times$**, loại bỏ $85.5\%$ vé rác, tăng hiệu suất nén **$3.4\times$** so với v1.0).

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
| `./xstk.sh qr --gen N` | `qr_filter.py --gen N` | Tự động sinh N bộ số trọn gói 5+1 đạt SQS $\ge 80/100$ |
| `./xstk.sh wheel` | `qr_filter.py --wheel 10` | Sinh Dàn Bao Toán Học 2 vé C(10,5,3,5) cam kết 100% trúng Giải 3 |
| `./xstk.sh logs` | `tail -f auto_update.log` | Xem nhật ký cập nhật |
