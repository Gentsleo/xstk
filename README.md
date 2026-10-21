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

## 📐 Mô Hình Toán Học Cốt Lõi

### 1. Khoảng cách Mahalanobis ($D_M^2$)
$$D_M^2(\mathbf{x}) = (\mathbf{x} - \boldsymbol{\mu})^T \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu})$$
Với $\mathbf{x} = [\text{Sum}, \text{Odds}, \text{Highs}, \text{Span}, \text{Consecs}]^T$. Biến ngẫu nhiên $D_M^2$ tuân theo phân phối $\chi^2(5)$:
$$p = 1 - F_{\chi^2_5}(D_M^2)$$

### 2. Shannon Gap Entropy ($H_{\text{Gaps}}$)
$$H(\text{Gaps}) = -\sum_{i=1}^6 p_i \ln p_i \quad \left(p_i = \frac{g_i}{36}\right)$$
Đo lường độ rải đều của 5 số trên trục số $[1, 35]$.

### 3. Thang Điểm Chất Lượng Chuẩn Hóa (SQS 0 - 100)
$$\text{SQS} = \text{Score}_{\text{main}} \times 0.85 + \text{Score}_{\text{special}} \times 0.15$$
* $\text{SQS} \ge 75/100$: **XUẤT SẮC** (Top 25% tâm phân phối).
* $40 \le \text{SQS} < 75$: **ĐẠT CHUẨN** (Vùng dung sai 80% QR Code).
* $\text{SQS} < 10$: **CẢNH BÁO** (Dị biệt, dồn cụm).

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
