# 🎯 XSTK - Vietlott Lotto 5/35 Analysis & QR Tolerance Engine

Ứng dụng phân tích dữ liệu, chuẩn hóa xác suất thống kê và dự đoán bộ số cho **Vietlott Lotto 5/35** dựa trên **Mô hình Dung sai mã QR (Typical Set)** kết hợp **Khoảng cách Mahalanobis** và **Shannon Gap Entropy**.

Tích hợp trực tiếp với các Model Context Protocol (**MCP**) trong Oh My Pi (`math-mcp`, `mcp-mathematics`, `wolframalpha`).

---

## 🌟 Tính Năng Nổi Bật

1. **Giao diện đa nền tảng:**
   - **Desktop GUI (PyQt5):** Giao diện máy tính trực quan, chạy mượt mà trên Windows / WSL2 / Linux.
   - **Web App (GitHub Pages):** Ứng dụng web hiện đại (Single Page App với Tailwind CSS & Chart.js), có thể host trực tiếp trên GitHub Pages không cần server backend.
2. **Cơ sở dữ liệu toàn diện:**
   - Thu thập toàn bộ 954 kỳ quay lịch sử từ kỳ đầu tiên `#00001` đến nay.
   - Định dạng lưu trữ: SQLite DB (`vietlott_535.db`), CSV, JSON.
3. **Mô hình toán học đột phá (QR Error-Correction & Mahalanobis Engine):**
   - Áp dụng ý tưởng mã QR dung sai lỗi $25\%$ (Level Q).
   - Sử dụng ma trận hiệp phương sai thực nghiệm $\boldsymbol{\Sigma}^{-1}$ để khử triệt để hiện tượng đa cộng tuyến giữa Tổng điểm và Tài/Xỉu.
   - Tính toán chính xác $p$-value theo phân phối Chi-Square $\chi^2(5)$.
   - Đo lường độ phân tán không gian qua Shannon Gap Entropy.
4. **Hệ thống tự động hóa:**
   - Tự động kiểm tra và cập nhật sau mỗi kỳ quay mới (Cron Job).

---

## 🚀 Hướng Dẫn Sử Dụng Nhanh

### 1. Khởi chạy Giao diện Desktop (PyQt5)
```bash
./xstk.sh gui
# Hoặc:
.venv/bin/python qt_app.py
```

### 2. Khởi chạy Giao diện Web trên trình duyệt cục bộ
```bash
./xstk.sh web 8080
# Sau đó mở trình duyệt tại: http://localhost:8080
```

### 3. Đánh giá bộ số bằng CLI
```bash
# Cú pháp: ./xstk.sh qr <số_1> <số_2> <số_3> <số_4> <số_5> <số_ĐB>
./xstk.sh qr 06 15 21 30 34 06
```

### 4. Tự động gợi ý N bộ số chuẩn xác suất (SQS ≥ 80/100)
```bash
./xstk.sh qr --gen 5
```

### 5. Cập nhật dữ liệu từ Vietlott
```bash
# Kiểm tra và nạp kỳ mới 1 lần:
./xstk.sh update

# Bật tự động cập nhật ngầm qua Cron (mỗi 30 phút):
./xstk.sh cron-on
```

---

## 📐 Mô Hình Toán Học Cốt Lõi: Lý Thuyết Dung Sai Mã QR (QR Tolerance Engine)

Mô hình lấy cảm hứng từ nguyên lý **Mã Sửa Sai (Error-Correcting Code - Reed-Solomon Level Q)** trong công nghệ mã QR:
> **"Một mã QR bị mất hoặc nhòe 20% – 25% diện tích vẫn có thể quét thành công nhờ các Điểm Neo Bất Biến (Finder Patterns) và Vạch Nhịp Đồng Bộ (Timing Patterns)."**

Áp dụng vào Xác suất Thống kê Vietlott Lotto 5/35:
* Không gian tổ hợp có tới $C_{35}^5 = 324,632$ bộ số. Thay vì cố gắng dự đoán chính xác tuyệt đối từng quả bóng vi mô (điều bất khả thi do tính ngẫu nhiên), mô hình đi tìm **Vùng Dung Sai Điển Hình (Typical Set)** nơi mà **$75\% - 80\%$ các kỳ quay thực tế trong lịch sử bắt buộc phải hội tụ về**.
* Bất kỳ bộ số nào nằm ngoài vùng dung sai này đều bị coi là **"nhiễu rác làm hỏng mã QR"** (như bộ số toàn chẵn, toàn lẻ, hoặc dồn cục `16-17-18-19-20`) và bị loại bỏ.

### 1. Bảng đối chiếu triết lý: Mã QR ↔ Xác Suất Vietlott

| Thành phần Mã QR | Vai trò trong Mã QR | Tương ứng trong Mô hình XSTK 5/35 | Công thức Toán học áp dụng |
|---|---|---|---|
| **Dung sai lỗi 20–25% (Level Q)** | Cho phép mất 20–25% diện tích mà camera vẫn quét được dữ liệu gốc | Vùng bao phủ $75–80\%$ các kỳ quay thực tế, lọc bỏ $70\%$ các bộ số rác | **Phân phối Chi-Square $\chi^2(5)$** với ngưỡng $p \ge 0.20$ ($D_M^2 \le 7.09$) |
| **3 Ô vuông góc (Finder Patterns)** | Điểm neo định vị toạ độ, giúp máy quét nhận diện góc quay | Điểm cân bằng vĩ mô bất biến: Trọng tâm Tổng điểm, Tỷ lệ Chẵn/Lẻ, Tài/Xỉu | Vector kỳ vọng $\boldsymbol{\mu} = [91.1, 2.57, 2.62, 23.85, 0.58]^T$ |
| **Ma trận khử nhiễu (Reed-Solomon)** | Bóc tách nhiễu đa chiều trên trường Galois $GF(2^8)$, không phạt trùng lặp | Khử triệt để hiện tượng đa cộng tuyến giữa Tổng và Số Lớn ($\rho = +0.876$) | **Khoảng cách Mahalanobis** $D_M^2 = (\mathbf{x} - \boldsymbol{\mu})^T \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu})$ |
| **Vạch nhịp đồng bộ (Timing Patterns)** | Các dải xen kẽ đen/trắng giúp chống hiện tượng pixel vón thành cục | Đảm bảo 5 quả bóng không bị dồn cục, rải đều hài hòa trên dải $[1, 35]$ | **Shannon Gap Entropy** $H(\text{Gaps}) = -\sum p_i \ln p_i$ |
| **Dữ liệu Payload cốt lõi** | Thông điệp nguyên bản được khôi phục trọn vẹn | Bộ số hoàn chỉnh $5$ số chính $+ 1$ số đặc biệt đạt điểm SQS cao | **Chỉ số SQS (Thang điểm 100)** |

---

### 2. Các Công thức Toán học Chi tiết

#### A. Khoảng cách Mahalanobis Khử Tương Quan Chéo ($D_M^2$)
$$D_M^2(\mathbf{x}) = (\mathbf{x} - \boldsymbol{\mu})^T \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu})$$
Với $\mathbf{x} = [\text{Sum}, \text{Odds}, \text{Highs}, \text{Span}, \text{Consecs}]^T$. Biến ngẫu nhiên $D_M^2$ tuân theo phân phối Chi-Square với $k=5$ bậc tự do:
$$p = 1 - F_{\chi^2_5}(D_M^2)$$

#### B. Shannon Gap Entropy ($H_{\text{Gaps}}$ - Đo độ rải đều)
$$H(\text{Gaps}) = -\sum_{i=1}^6 p_i \ln p_i \quad \left(p_i = \frac{g_i}{36}\right)$$
Đo lường độ rải đều của 5 số trên trục số $[1, 35]$. Ngưỡng tối ưu: $H \ge 1.60$ (cực đại lý thuyết $\ln(6) \approx 1.79$).

#### C. Thang Điểm Chất Lượng Chuẩn Hóa (SQS 0 - 100)
$$\text{SQS} = \text{Score}_{\text{main}} \times 0.85 + \text{Score}_{\text{special}} \times 0.15$$
* $\text{SQS} \ge 75/100$: **XUẤT SẮC** (Top 25% tâm phân phối đối xứng hoàn hảo).
* $40 \le \text{SQS} < 75$: **ĐẠT CHUẨN** (Vùng dung sai 80% QR Code).
* $10 \le \text{SQS} < 40$: **DUNG SAI BIÊN** (Lệch nhẹ).
* $\text{SQS} < 10$: **CẢNH BÁO** (Dị tật, dồn cụm, lệch chẵn/lẻ $p < 0.05$).
---

## 🌐 Triển Khai Lên GitHub & GitHub Pages

1. Đăng nhập GitHub và tạo repository mới (ví dụ `xstk`).
2. Đẩy code lên GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: complete xstk project with qt app and web ui"
   git branch -M main
   git remote add origin https://github.com/Gentsleo/xstk.git
   git push -u origin main
   ```
3. **Bật GitHub Pages để có Web App trực tiếp:**
   - Vào Settings của repository trên GitHub $\rightarrow$ **Pages**.
   - Tại mục **Build and deployment** $\rightarrow$ Chọn Source: **Deploy from a branch**.
   - Chọn Branch: **main** $\rightarrow$ Thư mục: **/docs** $\rightarrow$ Bấm **Save**.
   - Sau 1 phút, trang web của bạn sẽ hoạt động tại:  
     `https://gentsleo.github.io/xstk/`

---

## 📄 Bản Quyền
Dự án được phân phối dưới giấy phép MIT License.
