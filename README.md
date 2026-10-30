# 🎯 XSTK - Phân tích Vietlott Lotto 5/35

Ứng dụng xem lịch sử và sinh vé 5+1 bằng **cổng hình thái thực nghiệm** trên 5 số chính (hiệu chuẩn từ kỳ 1–954). Bộ sinh này không lấy mẫu đều trên toàn bộ 324.632 tổ hợp; số đặc biệt vẫn đều và độc lập. Không có bằng chứng chọn vé qua cổng làm tăng xác suất trúng của một vé khi quay công bằng.

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

### 4. Sinh bộ số theo mô hình đã khóa (không dự báo)
```bash
./xstk.sh qr --gen 5     # 1–20 vé, 5 số chính không lặp bộ
```
Python dùng `SystemRandom`, web dùng `crypto.getRandomValues` với rejection
mapping (không dùng `Math.random` dự phòng) để đề xuất bộ chính đồng đều **trước
khi lọc**. Chỉ nhận bộ đạt SQS ≥ 80, entropy khoảng trống thực H ≥ 1,50;
không trả bộ ngoài cổng nếu hết lượt tìm. Số đặc biệt chọn đều 1–12, độc lập
**sau khi** nhận bộ chính; được phép trùng số chính hoặc số đặc biệt vé khác.
Không áp trọng số cho số cũ, số vắng, số cao hay số đặc biệt. Đối chứng
nghiên cứu đều trên toàn không gian, **không lọc**, dùng
`./xstk.sh qr --uniform N` (hàm Python `suggest_uniform`).

`./xstk.sh wheel` tìm hai bộ chính đạt cổng và rời nhau (bể 10 số); đây không
phải lấy mẫu đều của mọi bộ chính hoặc hai vé độc lập. Số đặc biệt của từng vé
vẫn độc lập đồng đều, có thể trùng nhau/trùng số chính.

### 5. Đối chiếu cổng sản xuất và chuẩn QR lý thuyết
```bash
./xstk.sh backtest
./xstk.sh backtest --output audit_model.json
```
Lệnh vẫn thực hiện kiểm tra QR lý thuyết walk-forward: chỉ ngưỡng phân vị
được cập nhật từ các kỳ **trước** khi chấm kỳ tiếp theo. Ngoài ra lệnh duyệt
chính xác 324.632 bộ để tính thể tích vùng cổng sản xuất, vùng QR80 lý thuyết
và giao hai vùng; so sánh riêng tỷ lệ thuộc vùng trong lịch sử và kỳ vọng nếu
quay đều. Cổng thực nghiệm đóng băng trên kỳ 1–954; mọi số liệu với
`draw_id ≤ 954` là **hiệu chuẩn/hồi cứu**. Chỉ `draw_id > 954` nằm ngoài
giai đoạn tính hệ số, nhưng các kỳ >954 **đã xem** trong dữ liệu hiện tại
vẫn là phân tích hồi cứu, **không** phải holdout chưa xem hay đánh giá
tiến cứu. Không điều chỉnh ngưỡng theo các kỳ đó. `--output` ghi JSON gồm
hệ số/nguồn commit, SHA-256 dữ liệu, ngưỡng và cutoff, thể tích vùng,
tỷ lệ nhóm lịch sử/hiệu chuẩn/sau 954 và khoảng Wilson 95% khi có dữ liệu;
từ chối ghi đè. Độ phủ vùng, tỷ lệ thuộc vùng lịch sử và cơ hội thắng của
**một vé cụ thể** là ba đại lượng khác nhau.

Đánh giá mô hình dự báo riêng cho một vé 5+1:
```bash
./xstk.sh predict
./xstk.sh predict --min-train 300
```
Mô hình dùng trọng số tần suất được làm trơn $w_i=1+n_i/20$ và
$P(S)=\prod_{i\in S}w_i/\sum_{|T|=5}\prod_{j\in T}w_j$; bóng đặc biệt
dùng tần suất với giả đếm 5 cho mỗi số. Chọn 5 trọng số lớn nhất và bóng
đặc biệt xác suất lớn nhất trước mỗi kỳ, sau đó mới cập nhật bằng kết quả
kỳ đó. Báo số kỳ khớp 0–5 số chính, đặc biệt, khớp 5+1 và log-loss so với
mốc đồng đều. Đây là phép thử mô hình, không bảo đảm dự báo hay chứng minh
lợi thế; độ phủ QR không phải độ chính xác dự báo một vé.

### 6. Cập nhật dữ liệu từ Vietlott
```bash
# Kiểm tra và nạp kỳ mới 1 lần:
./xstk.sh update

# Bật tự động cập nhật ngầm qua Cron (mỗi 30 phút):
./xstk.sh cron-on
```

### 7. Phòng thí nghiệm RNG/QR

`rng_lab.py` mô phỏng các giả thuyết có kiểm soát, **không sao chép RNG của
OKC/SmartPlay**. Không có thuật toán, seed hay trạng thái nội bộ của thiết bị thật.
Sinh nhiều dữ liệu giả không tạo thêm thông tin về kỳ quay tiếp theo.

Các lệnh `lab` dùng Python hệ thống và NumPy (>=1.22):
```bash
python3 -m pip install 'numpy>=1.22'
```
PyTorch chỉ cần cho bước huấn luyện neural; các bước khác không phụ thuộc torch.

**Giai đoạn 1 — chuẩn chính xác và mô phỏng luồng**
```bash
./xstk.sh lab reference
./xstk.sh lab simulate --draws 1000000000 --batch-size 100000 \
  --seed 20261029 --output billion.json
```
Chuẩn duyệt đủ 324.632 tổ hợp, tính phân phối đặc trưng, hiệp phương sai tổng thể,
vùng QR và 5 nhóm phân vị D². Giữ nguyên `MU`, `INV_COV` đã công bố trong
`qr_filter.py`, không fit lại từ lịch sử. Luồng mô phỏng dùng PCG64, bộ nhớ theo
batch, chỉ lưu tổng đếm và SHA-256, không tạo tệp một tỷ dòng. Tái lập cần giữ
nguyên phiên bản NumPy, seed, mô hình, strength và batch size. CPU đủ để chạy;
đây không phải đầu ra đã khôi phục từ RNG thật.

**Giai đoạn 2 — kiểm định thăm dò và sức phát hiện**
```bash
./xstk.sh lab audit --repetitions 1999 --output audit.json
./xstk.sh lab power --repetitions 999 --lengths 250 976 2000 \
  --strengths .02 .10 .30 --output power.json
```
Các giả thuyết:

| Mã | Cơ chế được cài vào mô phỏng |
|---|---|
| B1 | Trộn với phân phối đều có điều kiện chứa số 1 |
| B2 | Trộn với byte modulo 35, loại cả hàng nếu có số trùng; đặc biệt byte modulo 12 |
| B3 | Sao chép bộ số chính kỳ trước với xác suất `strength` |
| B4 | Mỗi khối 16 kỳ có xác suất `strength` phát lại cùng một mẫu 16 kỳ |
| B5 | Trộn với phân phối đều có điều kiện nằm trong QR80 |

`strength` là xác suất trộn/sao chép/phát lại, không phải mức sai lệch đã ước lượng
của Vietlott. Có thể sinh riêng bằng `lab simulate --model B2 --strength .30`.
Năm thống kê định trước: tần suất chính, tần suất đặc biệt, số giao kỳ liền nhau,
phân bố 5 nhóm QR, số bộ chính lặp ở độ trễ 16. Hai ngân hàng mô phỏng độc lập
hiệu chuẩn p từng thống kê và điểm cực đại toàn họ; báo thêm p Bonferroni.
`power` dùng thêm ngân hàng công bằng độc lập để đo báo động giả và các ngân hàng
lỗi để đo sức phát hiện, kèm khoảng Wilson 95%. Kết luận cỡ mẫu chỉ trên lưới đã
chạy; trường hợp chưa đạt cận dưới sức phát hiện 80% được ghi `null`.
Độ phân giải p nhỏ nhất là `1/(repetitions+1)`; tăng repetitions để giảm nhiễu
Monte Carlo. Các khoảng sức phát hiện là tham khảo từng ô, không phải khoảng
đồng thời cho cả lưới. B2/B4 là ví dụ cơ chế, không phải cáo buộc về thiết bị thật.

**Giai đoạn 3 — dự báo theo thời gian và khóa đánh giá tương lai**
```bash
./xstk.sh lab forecast --output forecast.json
./xstk.sh lab forecast --lock prospective_lock.json
# Sau khi dữ liệu có thêm kỳ mới, dùng đúng tệp khóa, không chọn lại mô hình:
./xstk.sh lab forecast --prospective prospective_lock.json --output future.json
```
So sánh đều, tần suất làm trơn hiện có và mô hình QR theo nhóm D². Mỗi bộ trong
cùng nhóm QR nhận xác suất khối nhóm chia cho số tổ hợp thật của nhóm; mọi nhóm,
kể cả ngoài QR80, luôn có xác suất dương. Chọn một mô hình tần suất/QR bằng
validation theo thời gian rồi đánh giá test bằng log-loss chính, đặc biệt và
joint; cập nhật chỉ sau khi chấm kết quả. Toàn bộ lịch sử hiện có được ghi là
**hồi cứu/đã xem**, không được gọi là holdout chưa từng thấy.

Tệp khóa lưu cấu hình và dấu vân tay tiền tố lịch sử. Lệnh prospective từ chối
tiền tố đã sửa và chỉ chấm các kỳ nối thêm; chưa có kỳ mới thì trạng thái pending.
Không thay tệp khóa sau khi xem kết quả mới để chọn một backtest đẹp.
Likelihood ratio tích lũy của mô hình đã khóa so với mốc đều được báo dưới dạng
`log_evalue`: dưới giả thuyết iid đều, đây là thước đo bằng chứng tuần tự,
không phải xác suất mô hình đúng hay xác suất thắng một vé.

**Giai đoạn 4 — neural/Colab có điều kiện**
```bash
./xstk.sh lab neural --prospective-report future.json --device auto
```
Mặc định không train nếu chưa có ít nhất 100 kỳ mới trong báo cáo prospective
hợp lệ và `log_evalue >= log(20)` của mô hình không đều đã khóa. Đây là cổng
nghiên cứu định trước, không chứng minh có thể dự báo. Mạng nhỏ dự báo khối xác
suất nhóm QR và số đặc biệt, chia đều trong nhóm để chuẩn hóa chính xác.
Train/validation/test theo thời gian, early stopping chỉ nhìn validation.
`--diagnostic` cho phép kiểm tra kỹ thuật huấn luyện, **không vượt cổng tín hiệu**.
Notebook `notebooks/rng_lab_colab.ipynb` hướng dẫn tải dự án lên Colab, gắn Drive
tùy chọn, cài thư viện và lưu checkpoint; GPU phải được người dùng cấp trong Colab.
CPU và CUDA có thể cho số thực khác nhau; không cam kết tái lập bit trên GPU.

**Báo cáo một bộ số**
```bash
./xstk.sh lab ticket 6 15 21 30 34 6
./xstk.sh lab ticket 1 2 3 4 5 1 --no-history
```
Báo xác suất đều, đặc trưng QR, D², phân vị chính xác và trong/ngoài vùng 80%;
nếu có lịch sử, báo thêm xác suất mô hình gán và tỷ lệ so với đều. Với >400 kỳ,
báo cả log-loss hồi cứu của cấu hình train=200, validation=200 cố định để đối chiếu.
Điểm hình thái không phải xác suất thắng; xác suất mô hình chưa có xác nhận
tương lai không phải lợi thế thực tế. Năm số chính luôn phải khác nhau;
số đặc biệt có thể trùng số chính.

Mọi `--output` tạo tệp mới, từ chối ghi đè. Báo cáo chứa seed/cấu hình và hash dữ
liệu khi áp dụng. Dữ liệu thiếu kỳ bị từ chối cho kiểm tra chuỗi; không tự suy ra
buổi quay từ chẵn/lẻ ID. Bộ kiểm tra hành vi:
```bash
python3 -m unittest discover -p 'test_*.py'
```

**Báo cáo lần chạy đã lưu tại `reports/`**

- `rng_reference.json`: chuẩn toàn bộ tổ hợp; `rng_billion.json`: đúng 1 tỷ kỳ
  công bằng, 5 tỷ lượt số chính và 1 tỷ số đặc biệt, không lưu dòng mô phỏng.
- `rng_audit.json`: 1.999 mẫu mỗi ngân hàng; p tần suất chính riêng lẻ 0,0205,
  p toàn họ 0,0745, chưa vượt ngưỡng 5% sau xét đồng thời các kiểm tra.
- `rng_power.json`: 999 mẫu mỗi ngân hàng cho từng cỡ mẫu/mức lỗi;
  `strength` giữa các loại lỗi không đại diện cùng độ lớn thay đổi phân bố.
- `rng_forecast.json`: train 200, validation 200, test hồi cứu 576 kỳ;
  mô hình đều có log-loss joint thấp hơn cả tần suất và QR.
- `rng_prospective_lock.json`: tiền tố thật đã khóa đến kỳ #00976, chọn mô hình
  tần suất bằng validation; không đổi sang QR sau khi nhìn test.
  `rng_prospective_pending.json`: chưa có kỳ mới, không có bằng chứng tiến cứu.
- `rng_ticket.json` và `rng_ticket_boundary.json`: ví dụ một vé trong vùng
  QR và bộ 1–2–3–4–5 ngoài vùng nhưng vẫn có cùng xác suất công bằng.
- `rng_neural_diagnostic.pt`: checkpoint CPU 3 epoch trên lịch sử thật, chỉ
  smoke kỹ thuật; không phải mô hình đã được cổng tín hiệu chấp nhận.

Sau khi nạp kỳ mới, tiếp tục chính thí nghiệm đã khóa (dùng tên báo cáo mới):
```bash
./xstk.sh lab forecast --prospective reports/rng_prospective_lock.json \
  --output reports/rng_future.json
```
Các ô Python mặc định của notebook đã chạy cục bộ trên CPU, bỏ ô cài thư viện
vì đã cài trong môi trường kiểm tra. Chưa xác minh giao diện Colab/Drive hay CUDA.

---

## 📐 Thống kê mô tả và xác suất trúng

Mốc tham chiếu giả định các kỳ quay độc lập với lịch sử. Khi quay đều, mọi bộ 5 số chính cụ thể
có xác suất trúng đủ 5 số chính bằng nhau: $1/\binom{35}{5}=1/324632$ mỗi kỳ.
Số đặc biệt lấy độc lập và đều từ 1 đến 12; trùng một số chính không phải
lý do để loại bỏ hay ưu tiên vé. Tần suất quá khứ không cho biết kết quả kỳ tới.

### Vùng dung sai lấy cảm hứng từ QR

Vùng tham chiếu **lý thuyết** $A_{80}=\{c:D_{\mathrm{fair}}^2(c)\le
7.055639346938778\}$ chứa 259.706/324.632 bộ chính, tính bằng `MU`,
`INV_COV` trên toàn bộ các tổ hợp đều. `in_qr80` chỉ báo cáo chuẩn này,
**không phải điều kiện nhận vé**. Cổng sản xuất dùng các hệ số **thực nghiệm**
khác và hai ngưỡng SQS/H; không đồng nhất tỷ lệ phủ QR80 với tỷ lệ nhận vé.
QR thật có mã sửa sai; hình ảnh dung sai ở đây không phải phương pháp dự
đoán kết quả xổ số.

### SQS và cổng thực nghiệm: chọn hình thái, không đo xác suất trúng

Năm đặc trưng $\mathbf{x}=[\text{Sum},\text{Odds},\text{Highs}_{\ge18},
\text{Span},\text{Consecs}]^T$. `EMPIRICAL_MU =
[91.1069, 2.5681, 2.6237, 23.8512, 0.5755]` và `EMPIRICAL_INV_COV`
trong `qr_filter.py` là hệ số công bố làm tròn từ **kỳ 1–954**, theo bản
`f597fffb6ec5a3ab19134185815fd1e4eddc12ea`; đã khóa, không fit lại
từ các kỳ mới. $D_{\mathrm{emp}}^2=(\mathbf{x}-\boldsymbol{\mu}_{emp})^T
\Sigma^{-1}_{emp}(\mathbf{x}-\boldsymbol{\mu}_{emp})$. Với sáu khoảng trống
$g=(n_1,n_2-n_1,\ldots,n_5-n_4,36-n_5)$, $n_1<\cdots<n_5$:
$$\sum_{i=1}^{6}g_i=36,\quad H=-\sum_{i=1}^{6}(g_i/36)\ln(g_i/36),\quad
\mathrm{SQS}=\operatorname{round}\!\left(
100[1-F_{\chi^2_5}(D_{\mathrm{emp}}^2)]
\left[0.8+0.2\operatorname{clamp}\!\left(
\frac{H-1}{\ln6-1},0,1\right)\right],1\right).$$
Chỉ chọn nếu **SQS ≥ 80 và H thực ≥ 1,50**; H hiển thị được làm tròn
nhưng không dùng giá trị hiển thị để xét cổng. Số đặc biệt 1–12 không tham
gia SQS; thống kê kỳ trước chỉ để tham khảo. Đuôi chi-square là thước tham
chiếu hình thái **xấp xỉ**, không phải xác suất một bộ được quay. Dù vé
được lọc, mỗi vé cụ thể vẫn có xác suất trúng 5+1 bằng $1/3.895.584$ dưới
giả thiết quay công bằng, độc lập; vùng lọc không chứng minh lợi thế dự báo.

MCP (`math-mcp`, `mcp-mathematics`; WolframAlpha chỉ khi có cấu hình)
hỗ trợ **tính toán/đối chiếu nghiên cứu**, không được gọi khi chọn vé hay
tính SQS lúc chạy: mã dùng các hằng số đã đóng băng trong `qr_filter.py`.
`reports/qr_model_verification.json` lưu kiểm tra độc lập trung bình,
ma trận và giới hạn công cụ; không coi MCP là dịch vụ dự báo hoặc nói rằng
WolframAlpha đã xác minh khi thiếu khóa API. `rng_lab.py` và neural/Colab ở
phần dưới là các nhánh nghiên cứu riêng, không phải engine chọn vé này.

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
