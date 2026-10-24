# 🎯 XSTK - Phân tích Vietlott Lotto 5/35

Ứng dụng xem lịch sử kỳ quay và gợi ý các bộ số cân đối về hình thức. Không dự đoán kết quả, không tăng xác suất trúng của từng bộ số.

Tích hợp trực tiếp với các Model Context Protocol (**MCP**) trong Oh My Pi (`math-mcp`, `mcp-mathematics`, `wolframalpha`).

---

## 🌟 Tính Năng Nổi Bật

1. **Giao diện đa nền tảng:**
   - **Desktop GUI (PyQt5):** Giao diện máy tính trực quan, chạy mượt mà trên Windows / WSL2 / Linux.
   - **Web App (GitHub Pages):** Ứng dụng web hiện đại (Single Page App với Tailwind CSS & Chart.js), có thể host trực tiếp trên GitHub Pages không cần server backend.
2. **Dữ liệu lịch sử:**
   - Lưu các kỳ quay đã thu thập; cập nhật kỳ mới qua công cụ đồng bộ.
   - Định dạng lưu trữ: SQLite DB (`vietlott_535.db`), CSV, JSON.
3. **Thống kê mô tả 5 số chính:**
   - Khoảng cách Mahalanobis của tổng, số lẻ, số cao, độ rộng và cặp liền kề; tham chiếu chi-square chỉ là xấp xỉ mô tả.
   - Shannon gap entropy đo độ rải đều, không đo cơ hội trúng.
   - Số đặc biệt 1–12 được chọn đều, độc lập với 5 số chính.
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

### 4. Gợi ý N bộ số cân đối về hình thức (không dự báo)
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

## 📐 Thống kê mô tả và xác suất trúng

Mỗi kỳ quay độc lập với lịch sử. Với giả thiết quay đều, mọi bộ 5 số chính cụ thể
có xác suất trúng đủ 5 số chính bằng nhau: $1/\binom{35}{5}=1/324632$ mỗi kỳ.
Số đặc biệt lấy độc lập và đều từ 1 đến 12; trùng một số chính không phải
lý do để loại bỏ hay ưu tiên vé. Tần suất quá khứ không cho biết kết quả kỳ tới.

### SQS: điểm mô tả, không phải xác suất

SQS (0–100) chỉ đánh giá tính cân đối hình thức của **5 số chính**. Vector
đặc trưng $\mathbf{x}=[\text{Sum},\text{Odds},\text{Highs},\text{Span},\text{Consecs}]^T$
và khoảng cách Mahalanobis
$D_M^2=(\mathbf{x}-\boldsymbol{\mu})^T\boldsymbol{\Sigma}^{-1}
(\mathbf{x}-\boldsymbol{\mu})$ giúp mô tả độ lệch của các đặc trưng có tương quan.
Giá trị $1-F_{\chi^2_5}(D_M^2)$ chỉ là **tham chiếu chi-square xấp xỉ**:
các đặc trưng rời rạc không bảo đảm $D_M^2$ phân phối chính xác theo $\chi^2_5$.
Đây không phải xác suất một bộ số được quay ra, cũng không phải lợi thế của SQS cao.

Độ rải đều có thể mô tả bằng entropy của sáu khoảng trống dương
$g=(n_1,n_2-n_1,\ldots,n_5-n_4,36-n_5)$, với $n_1<\cdots<n_5$:
$$\sum_{i=1}^{6}g_i=36,\qquad \overline g=6,\qquad
H(g)=-\sum_{i=1}^{6}\frac{g_i}{36}\ln\frac{g_i}{36}.$$
Chọn vé cân đối chỉ phục vụ sở thích trình bày; bộ số dồn cụm cũng có
xác suất trúng đúng 5 số chính bằng một bộ số rải đều.

### Hai vé có 5 số chính không giao nhau

Nếu **cả 5 số trúng chính** đều nằm trong hợp 10 số chính của hai vé
không giao nhau, nguyên lý chuồng bồ câu bảo đảm ít nhất một vé khớp
từ 3 số chính trở lên. Đây là **bảo đảm có điều kiện**, không phải bảo đảm
trúng trong một kỳ quay bất kỳ. Với hai vé cố định như vậy, xác suất
**vô điều kiện** ít nhất một vé khớp từ 3 số chính trở lên là
$9002/\binom{35}{5}=9002/324632$ (chỉ xét 5 số chính).

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
