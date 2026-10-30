#!/usr/bin/env python3
import sys
import os
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit, QSpinBox, QGroupBox,
    QMessageBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon

# Import evaluation logic
from qr_filter import (
    CALIBRATION_LAST_DRAW, MAX_SUGGESTIONS, MIN_ENTROPY, MIN_SQS,
    evaluate_combination, suggest_model,
)

BASE_DIR = "/home/tringuyen/xstk"
DB_PATH = os.path.join(BASE_DIR, "vietlott_535.db")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")

class UpdateThread(QThread):
    finished_signal = pyqtSignal(str)
    
    def run(self):
        try:
            import subprocess
            res = subprocess.run([sys.executable, os.path.join(BASE_DIR, "auto_update.py")], capture_output=True, text=True)
            msg = res.stdout.strip()
            if not msg:
                msg = res.stderr.strip()
            self.finished_signal.emit(msg if msg else "Đã hoàn thành kiểm tra cập nhật.")
        except Exception as e:
            self.finished_signal.emit(f"Lỗi khi cập nhật: {e}")

class XSTKMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XSTK - Vietlott Lotto 5/35 (Gợi ý theo mô hình QR)")
        self.resize(1100, 750)
        self.apply_theme()
        self.init_ui()
        self.load_history_data()

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QWidget {
                color: #cdd6f4;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #313244;
                background-color: #181825;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1e1e2e;
                color: #a6adc8;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #89b4fa;
                color: #11111b;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #89b4fa;
            }
            QLineEdit, QSpinBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
                color: #cdd6f4;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #89b4fa;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton#btnUpdate {
                background-color: #a6e3a1;
            }
            QPushButton#btnUpdate:hover {
                background-color: #94e2d5;
            }
            QTableWidget {
                background-color: #181825;
                border: 1px solid #313244;
                gridline-color: #313244;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px;
                font-family: monospace;
            }
        """)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Top Bar
        top_bar = QHBoxLayout()
        title_label = QLabel("🎯 PHÂN TÍCH & GỢI Ý BỘ SỐ VIETLOTT LOTTO 5/35")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #89b4fa;")
        
        self.btn_auto_update = QPushButton("🔄 Cập Nhật Kỳ Mới")
        self.btn_auto_update.setObjectName("btnUpdate")
        self.btn_auto_update.clicked.connect(self.trigger_update)
        
        top_bar.addWidget(title_label)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_auto_update)
        main_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_evaluate_tab(), "🔍 Đánh Giá Bộ Số")
        self.tabs.addTab(self.create_generator_tab(), "⚡ Gợi Ý Theo Mô Hình")
        self.tabs.addTab(self.create_history_tab(), "📊 Lịch Sử Kỳ Quay")
        self.tabs.addTab(self.create_charts_tab(), "📈 Biểu Đồ Thống Kê")
        self.tabs.addTab(self.create_qr_theory_tab(), "📐 Giải Thích Thống Kê")
        main_layout.addWidget(self.tabs)

    # ------------------ TAB 1: ĐÁNH GIÁ BỘ SỐ ------------------
    def create_evaluate_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        input_group = QGroupBox("Nhập bộ số cần kiểm tra (5 số chính 1 - 35 và 1 số đặc biệt 1 - 12)")
        input_layout = QHBoxLayout(input_group)
        input_layout.setSpacing(10)

        self.inputs_main = []
        for i in range(5):
            inp = QLineEdit()
            inp.setPlaceholderText(f"Số {i+1}")
            inp.setAlignment(Qt.AlignCenter)
            inp.setMaxLength(2)
            self.inputs_main.append(inp)
            input_layout.addWidget(inp)

        sep_label = QLabel("|")
        sep_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f38ba8;")
        input_layout.addWidget(sep_label)

        self.input_special = QLineEdit()
        self.input_special.setPlaceholderText("ĐB (1-12)")
        self.input_special.setAlignment(Qt.AlignCenter)
        self.input_special.setMaxLength(2)
        self.input_special.setStyleSheet("border: 2px solid #f38ba8; color: #f38ba8;")
        input_layout.addWidget(self.input_special)

        btn_eval = QPushButton("🚀 Chấm Điểm")
        btn_eval.clicked.connect(self.run_evaluation)
        input_layout.addWidget(btn_eval)

        btn_fill_latest = QPushButton("Gán Kỳ Mới Nhất")
        btn_fill_latest.setStyleSheet("background-color: #45475a; color: #cdd6f4;")
        btn_fill_latest.clicked.connect(self.fill_latest_draw)
        input_layout.addWidget(btn_fill_latest)

        layout.addWidget(input_group)

        # Result display
        result_group = QGroupBox("Điểm mô hình thực nghiệm (không dự báo xác suất trúng)")
        res_layout = QVBoxLayout(result_group)

        # Score card
        score_card = QHBoxLayout()
        self.lbl_score_val = QLabel("-- / 100")
        self.lbl_score_val.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self.lbl_score_val.setStyleSheet("color: #89b4fa; padding: 10px;")
        
        self.lbl_grade = QLabel("Nhập số và bấm 'Chấm Điểm' để bắt đầu")
        self.lbl_grade.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_grade.setStyleSheet("color: #a6adc8;")
        
        score_card.addWidget(self.lbl_score_val)
        score_card.addWidget(self.lbl_grade)
        score_card.addStretch()
        res_layout.addLayout(score_card)

        # Detail text
        self.txt_eval_detail = QTextEdit()
        self.txt_eval_detail.setReadOnly(True)
        res_layout.addWidget(self.txt_eval_detail)

        layout.addWidget(result_group)
        return tab

    def fill_latest_draw(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            row = cur.execute("SELECT num1, num2, num3, num4, num5, special FROM draws ORDER BY draw_id DESC LIMIT 1").fetchone()
            conn.close()
            if row:
                for i in range(5):
                    self.inputs_main[i].setText(f"{row[i]:02d}")
                self.input_special.setText(f"{row[5]:02d}")
                self.run_evaluation()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể lấy kỳ mới nhất: {e}")

    def run_evaluation(self):
        try:
            nums = []
            for inp in self.inputs_main:
                val = inp.text().strip()
                if not val:
                    raise ValueError("Vui lòng điền đủ 5 số chính.")
                nums.append(int(val))

            spec_val = self.input_special.text().strip()
            spec = int(spec_val) if spec_val else None

            res = evaluate_combination(nums, spec)
            
            # Update Score Display
            sqs = res["sqs"]
            self.lbl_score_val.setText(f"{sqs:>4.1f} / 100")
            if res["model_accepted"]:
                self.lbl_score_val.setStyleSheet("color: #a6e3a1; font-size: 36px; font-weight: bold;")
                self.lbl_grade.setText("Đạt bộ lọc mô hình")
                self.lbl_grade.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            else:
                self.lbl_score_val.setStyleSheet("color: #f38ba8; font-size: 36px; font-weight: bold;")
                self.lbl_grade.setText("Không đạt bộ lọc mô hình")
                self.lbl_grade.setStyleSheet("color: #f38ba8; font-weight: bold;")

            sp = res.get("special_info")
            detail = [
                f"=== CHI TIẾT ĐÁNH GIÁ TOÁN HỌC ===",
                f"• Bộ số chính:                {' '.join(f'{x:02d}' for x in res['combo'])}",
                f"• Tổng điểm (Sum):            {res['sum']} (Z-Score: {res['z_sum']:+})",
                f"• Tỷ lệ Lẻ / Chẵn:            {res['odds']} Lẻ - {res['evens']} Chẵn",
                f"• Tỷ lệ Tài / Xỉu:            {res['highs']} Cao (>=18) - {res['lows']} Thấp (<18)",
                f"• Độ rộng bộ số (Span):       {res['span']} ({res['combo'][0]:02d} -> {res['combo'][-1]:02d})",
                f"• Cặp số liền kề:             {res['consecs']} cặp",
                f"• Khoảng cách Mahalanobis:    D_M^2 = {res['dm_sq']:.2f} (mô hình thực nghiệm kỳ 1–{CALIBRATION_LAST_DRAW})",
                f"• QR 80% lý thuyết:           {'Trong vùng' if res['in_qr80'] else 'Ngoài vùng'} (mốc riêng, không dùng lọc vé)",
                f"• Điểm tham chiếu χ²(5):      {res['p_val_main']:.4f} (xấp xỉ, không phải xác suất trúng)",
                f"• Shannon Gap Entropy:        H = {res['gap_entropy']:.3f} / 1.79 ({res['entropy_pct']}% tối đa)",
            ]
            if sp:
                detail.extend([
                    f"\n=== SỐ ĐẶC BIỆT ===",
                    f"• Số đặc biệt:                Số {sp['special']:02d} ({sp['parity']}, {sp['tier']})",
                    f"• Tần suất lịch sử:           {sp['observed_count']} lần (Kỳ vọng: {sp['expected_count']} | Z-Score: {sp['z_freq']:+})",
                    f"• So với số chính:            {'Trùng một số chính' if sp['is_overlap'] else 'Không trùng số chính'} (không ảnh hưởng xác suất)",
                ])
            detail.extend([
                f"\n=== KẾT LUẬN ===",
                f"• SQS mô hình:                {res['sqs']:.1f} / 100",
                f"• Bộ lọc SQS ≥ {MIN_SQS:g} và H ≥ {MIN_ENTROPY:.2f}: {'Đạt' if res['model_accepted'] else 'Không đạt'} (dùng giá trị H chưa làm tròn)",
                "• Mô hình không làm thay đổi xác suất trúng: mỗi bộ 5 số có xác suất trúng chính 1/324.632 khi quay công bằng."
            ])
            self.txt_eval_detail.setPlainText("\n".join(detail))

        except Exception as e:
            QMessageBox.warning(self, "Lỗi nhập liệu", str(e))

    # ------------------ TAB 2: GỢI Ý BỘ SỐ ------------------
    def create_generator_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        ctrl_group = QGroupBox(f"Gợi ý theo mô hình thực nghiệm kỳ 1–{CALIBRATION_LAST_DRAW} (SQS ≥ {MIN_SQS:g}, H ≥ {MIN_ENTROPY:.2f}; không tăng xác suất trúng)")
        ctrl_layout = QHBoxLayout(ctrl_group)
        
        ctrl_layout.addWidget(QLabel("Số lượng bộ số cần tạo:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, MAX_SUGGESTIONS)
        self.spin_count.setValue(5)
        ctrl_layout.addWidget(self.spin_count)

        btn_gen = QPushButton("⚡ Gợi Ý Vé Theo Mô Hình")
        btn_gen.clicked.connect(self.run_generation)
        ctrl_layout.addWidget(btn_gen)
        ctrl_layout.addStretch()

        layout.addWidget(ctrl_group)

        # Output table
        self.table_gen = QTableWidget()
        self.table_gen.setColumnCount(8)
        self.table_gen.setHorizontalHeaderLabels(["STT", "Bộ 5 Số Chính", "Đặc Biệt", "Tổng", "Chẵn/Lẻ", "Entropy", "SQS", "Đánh Giá"])
        self.table_gen.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_gen)

        return tab

    def run_generation(self):
        count = self.spin_count.value()
        try:
            found = suggest_model(count)
        except (RuntimeError, ValueError) as exc:
            QMessageBox.warning(self, "Không thể gợi ý vé", str(exc))
            return

        self.table_gen.setRowCount(len(found))
        for row_idx, r in enumerate(found):
            combo_str = "  ".join(f"{x:02d}" for x in r["combo"])
            sp_str = f"{r['special_info']['special']:02d}"
            
            self.table_gen.setItem(row_idx, 0, QTableWidgetItem(f"{row_idx + 1:02d}"))
            self.table_gen.setItem(row_idx, 1, QTableWidgetItem(combo_str))
            
            item_sp = QTableWidgetItem(sp_str)
            item_sp.setForeground(QColor("#f38ba8"))
            self.table_gen.setItem(row_idx, 2, item_sp)
            
            self.table_gen.setItem(row_idx, 3, QTableWidgetItem(str(r["sum"])))
            self.table_gen.setItem(row_idx, 4, QTableWidgetItem(f"{r['odds']}L - {r['evens']}C"))
            self.table_gen.setItem(row_idx, 5, QTableWidgetItem(f"{r['gap_entropy']:.2f}"))
            
            item_sqs = QTableWidgetItem(f"{r['sqs']:.1f}")
            item_sqs.setForeground(QColor("#a6e3a1"))
            self.table_gen.setItem(row_idx, 6, item_sqs)
            
            self.table_gen.setItem(row_idx, 7, QTableWidgetItem("Đạt bộ lọc mô hình" if r["model_accepted"] else "Không đạt bộ lọc"))

    # ------------------ TAB 3: LỊCH SỬ KỲ QUAY ------------------
    def create_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Tìm kiếm theo kỳ (vd: 00954) hoặc ngày (vd: 18/10/2026)...")
        self.txt_search.textChanged.connect(self.filter_history)
        search_layout.addWidget(self.txt_search)

        btn_reload = QPushButton("Nạp Lại")
        btn_reload.clicked.connect(self.load_history_data)
        search_layout.addWidget(btn_reload)
        layout.addLayout(search_layout)

        self.table_history = QTableWidget()
        self.table_history.setColumnCount(8)
        self.table_history.setHorizontalHeaderLabels(["Kỳ Quay", "Ngày", "Số 1", "Số 2", "Số 3", "Số 4", "Số 5", "Số ĐB"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_history)

        return tab

    def load_history_data(self):
        try:
            if not os.path.exists(DB_PATH):
                return
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            rows = cur.execute("SELECT draw_code, date, num1, num2, num3, num4, num5, special FROM draws ORDER BY draw_id DESC").fetchall()
            conn.close()

            self.history_cache = rows
            self.display_history_rows(rows)
        except Exception as e:
            print(f"Error loading history: {e}")

    def display_history_rows(self, rows):
        self.table_history.setRowCount(len(rows))
        for r_idx, r in enumerate(rows):
            self.table_history.setItem(r_idx, 0, QTableWidgetItem(f"#{r[0]}"))
            self.table_history.setItem(r_idx, 1, QTableWidgetItem(r[1]))
            for c in range(5):
                self.table_history.setItem(r_idx, 2 + c, QTableWidgetItem(f"{r[2+c]:02d}"))
            item_sp = QTableWidgetItem(f"{r[7]:02d}")
            item_sp.setForeground(QColor("#f38ba8"))
            self.table_history.setItem(r_idx, 7, item_sp)

    def filter_history(self, text):
        if not hasattr(self, "history_cache"):
            return
        query = text.strip().lower()
        if not query:
            self.display_history_rows(self.history_cache)
            return
        filtered = [r for r in self.history_cache if query in r[0].lower() or query in r[1].lower()]
        self.display_history_rows(filtered)

    # ------------------ TAB 4: BIỂU ĐỒ THỐNG KÊ ------------------
    def create_charts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        btn_layout = QHBoxLayout()
        charts = [
            ("Tần Suất 35 Số", "01_frequency_distribution.png"),
            ("Z-Score 35 Số", "02_zscore_standardized_balls.png"),
            ("Histogram Tổng 5 Số", "03_sum_histogram.png"),
            ("12 Số Đặc Biệt", "04_special_numbers.png")
        ]
        
        self.lbl_chart_img = QLabel("Chọn biểu đồ bên trên để xem.")
        self.lbl_chart_img.setAlignment(Qt.AlignCenter)
        self.lbl_chart_img.setStyleSheet("background-color: #11111b; border-radius: 8px;")

        for title, fname in charts:
            btn = QPushButton(title)
            btn.clicked.connect(lambda checked, f=fname: self.display_chart(f))
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        layout.addWidget(self.lbl_chart_img)

        # Mặc định mở biểu đồ 1 nếu có
        self.display_chart("01_frequency_distribution.png")
        return tab

    def display_chart(self, filename):
        path = os.path.join(CHARTS_DIR, filename)
        if os.path.exists(path):
            pix = QPixmap(path)
            self.lbl_chart_img.setPixmap(pix.scaled(1000, 560, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_chart_img.setText(f"Chưa có file biểu đồ {filename}.\nVui lòng chạy './xstk.sh plot' trước.")

    # ------------------ TAB 5: GIẢI THÍCH THỐNG KÊ ------------------
    def create_qr_theory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        txt = QTextEdit()
        txt.setReadOnly(True)
        html = f"""
        <h2 style='color: #89b4fa;'>📐 CHỌN VÉ THEO MÔ HÌNH, KHÔNG DỰ ĐOÁN</h2>
        <p>Mô hình thực nghiệm được hiệu chuẩn từ các kỳ 1–{CALIBRATION_LAST_DRAW};
        đây không phải bằng chứng hiệu quả ngoài mẫu sau kỳ {CALIBRATION_LAST_DRAW}.
        Mỗi kỳ quay là độc lập. Mỗi bộ 5 số chính cụ thể có cùng xác suất
        khớp 5 số chính: 1/C(35,5) = 1/324.632, vé 5+1 là 1/3.895.584.</p>
        <p>Vé gợi ý lấy mẫu ngẫu nhiên bằng bộ sinh an toàn rồi chỉ nhận nếu
        SQS ≥ {MIN_SQS:g} và entropy khoảng trống H ≥ {MIN_ENTROPY:.2f}
        (kiểm tra H chưa làm tròn); loại bộ số chính trùng lặp. Điểm SQS lấy
        khoảng cách Mahalanobis với trung tâm và nghịch đảo hiệp phương sai
        thực nghiệm của năm đặc trưng: tổng, số lẻ, số ≥18, độ rộng, số cặp liền kề.
        SQS = round(100 × (1 − Fχ²₅(D²)) ×
        (0,8 + 0,2 × clamp((H−1)/(ln 6−1), 0, 1)), 1).
        Đuôi &chi;<sup>2</sup>(5) chỉ là thang tham chiếu, không phải xác suất trúng.</p>
        <p>QR 80% <b>lý thuyết riêng</b> tính theo trung tâm và hiệp phương sai của
        toàn bộ 324.632 bộ đồng xác suất; D² lý thuyết ≤ 7,055639346938778
        chứa 259.706 tổ hợp. QR chỉ dùng để đối chiếu, không dùng làm ngưỡng
        cho khoảng cách thực nghiệm hay để lọc vé.</p>
        <p>Số đặc biệt được chọn đều và độc lập trong 1–12 <b>sau khi</b>
        bộ chính đạt mô hình, có thể trùng số chính hoặc số đặc biệt vé khác.
        Không cấm số từng ra, không ưu tiên số vắng hay số ở giữa; mô hình
        không tạo lợi thế dự đoán kết quả quay tiếp theo.</p>
        """
        txt.setHtml(html)
        layout.addWidget(txt)
        return tab

    def trigger_update(self):
        self.btn_auto_update.setEnabled(False)
        self.btn_auto_update.setText("⏳ Đang cập nhật...")
        self.up_thread = UpdateThread()
        self.up_thread.finished_signal.connect(self.on_update_finished)
        self.up_thread.start()

    def on_update_finished(self, msg):
        self.btn_auto_update.setEnabled(True)
        self.btn_auto_update.setText("🔄 Cập Nhật Kỳ Mới")
        QMessageBox.information(self, "Thông báo cập nhật", msg)
        self.load_history_data()

def main():
    app = QApplication(sys.argv)
    window = XSTKMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
