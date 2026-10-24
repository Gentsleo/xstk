import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "vietlott_535.json"), "r", encoding="utf-8") as f:
    draws_data = json.load(f)

total_draws = len(draws_data)

html_content = f"""<!DOCTYPE html>
<html lang="vi" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>XSTK - Vietlott Lotto 5/35 (Mô Hình Dung Sai QR & Mahalanobis)</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        brand: {{
                            primary: '#89b4fa',
                            secondary: '#a6e3a1',
                            accent: '#f38ba8',
                            dark: '#1e1e2e',
                            card: '#181825',
                            border: '#313244'
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{
            background-color: #11111b;
            color: #cdd6f4;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            -webkit-tap-highlight-color: transparent;
        }}
        .ball {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 1.05rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }}
        .ball-main {{
            background: linear-gradient(135deg, #89b4fa 0%, #3b82f6 100%);
            color: #11111b;
        }}
        .ball-special {{
            background: linear-gradient(135deg, #f38ba8 0%, #ef4444 100%);
            color: #ffffff;
        }}
        /* Toast Animation */
        @keyframes slideDown {{
            from {{ transform: translateY(-100%); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        .toast-animate {{
            animation: slideDown 0.3s ease-out forwards;
        }}
    </style>
</head>
<body class="min-h-screen p-3 md:p-8">
    <!-- Toast Notification -->
    <div id="toastContainer" class="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-11/12 max-w-md hidden">
        <div id="toastBody" class="p-4 rounded-xl shadow-2xl border text-sm font-bold flex items-center justify-between gap-3 toast-animate bg-brand-card border-brand-primary text-gray-200">
            <span id="toastMsg">Thông báo</span>
            <button onclick="hideToast()" class="text-gray-400 hover:text-white text-lg font-bold px-1">✕</button>
        </div>
    </div>

    <!-- Modal Update Center -->
    <div id="updateModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 hidden flex items-center justify-center p-4">
        <div class="bg-brand-card border border-brand-border rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6">
            <div class="flex justify-between items-center border-b border-brand-border pb-4">
                <h3 class="text-lg font-extrabold text-brand-primary flex items-center gap-2">
                    🔄 Trung Tâm Cập Nhật Kỳ Mới
                </h3>
                <button onclick="closeUpdateModal()" class="text-gray-400 hover:text-white text-xl font-bold p-1">✕</button>
            </div>

            <!-- Current State -->
            <div class="bg-brand-dark p-4 rounded-xl border border-brand-border flex items-center justify-between">
                <div>
                    <span class="text-xs text-gray-400 block font-semibold">KỲ HIỆN TẠI TRÊN MÁY:</span>
                    <span id="modalCurrentDraw" class="text-xl font-extrabold text-brand-secondary">#00954</span>
                </div>
                <div class="text-right">
                    <span class="text-xs text-gray-400 block font-semibold">TỔNG SỐ KỲ:</span>
                    <span id="modalTotalDraws" class="text-xl font-extrabold text-gray-200">{total_draws}</span>
                </div>
            </div>

            <!-- Option 1: Cloud Sync -->
            <div class="space-y-3">
                <h4 class="text-sm font-bold text-gray-300 flex items-center gap-2">
                    ☁️ Tùy Chọn 1: Đồng bộ từ GitHub (Đám mây)
                </h4>
                <p class="text-xs text-gray-400 leading-relaxed">
                    Hệ thống GitHub Actions tự động cào từ Vietlott mỗi ngày lúc <strong>18:45 VN</strong> và <strong>20:45 VN</strong>. Bấm nút dưới để nạp kỳ mới nếu đám mây đã cào xong:
                </p>
                <div class="flex flex-col sm:flex-row gap-2">
                    <button onclick="syncLatestDraws()" id="btnSyncModal" class="flex-1 py-2.5 bg-emerald-700 hover:bg-emerald-600 text-white rounded-xl text-sm font-bold transition flex items-center justify-center gap-2 shadow">
                        🔄 Đồng Bộ Từ Đám Mây
                    </button>
                    <a href="https://github.com/Gentsleo/xstk/actions/workflows/auto-update.yml" target="_blank" class="py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-gray-300 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 border border-brand-border text-center">
                        ⚡ Ép Cào Ngay (GitHub)
                    </a>
                </div>
            </div>

            <!-- Option 2: Quick Manual Entry for Mobile -->
            <div class="border-t border-brand-border pt-4 space-y-3">
                <h4 class="text-sm font-bold text-yellow-400 flex items-center gap-2">
                    📱 Tùy Chọn 2: Nhập nhanh kỳ vừa quay trên điện thoại
                </h4>
                <p class="text-xs text-gray-400 leading-relaxed">
                    Nếu bạn vừa xem tivi / Vietlott SMS có kết quả mà chưa kịp chờ máy chủ, bạn có thể nhập thẳng vào đây. Web sẽ lưu ngay vào điện thoại của bạn:
                </p>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[11px] text-gray-400 font-semibold block mb-1">Mã Kỳ (vd: 00955):</label>
                        <input id="manualDrawCode" type="text" placeholder="00955" class="w-full p-2 text-sm font-bold bg-brand-dark border border-brand-border rounded-lg text-center">
                    </div>
                    <div>
                        <label class="text-[11px] text-gray-400 font-semibold block mb-1">Ngày Quay:</label>
                        <input id="manualDrawDate" type="text" placeholder="dd/mm/yyyy" class="w-full p-2 text-sm font-bold bg-brand-dark border border-brand-border rounded-lg text-center">
                    </div>
                </div>

                <div>
                    <label class="text-[11px] text-gray-400 font-semibold block mb-1">5 Số Chính (1 - 35) & 1 Số ĐB (1 - 12):</label>
                    <div class="flex items-center gap-1.5">
                        <input id="mNum1" type="number" min="1" max="35" class="w-full p-2 text-center text-sm font-bold bg-brand-dark border border-brand-border rounded-lg">
                        <input id="mNum2" type="number" min="1" max="35" class="w-full p-2 text-center text-sm font-bold bg-brand-dark border border-brand-border rounded-lg">
                        <input id="mNum3" type="number" min="1" max="35" class="w-full p-2 text-center text-sm font-bold bg-brand-dark border border-brand-border rounded-lg">
                        <input id="mNum4" type="number" min="1" max="35" class="w-full p-2 text-center text-sm font-bold bg-brand-dark border border-brand-border rounded-lg">
                        <input id="mNum5" type="number" min="1" max="35" class="w-full p-2 text-center text-sm font-bold bg-brand-dark border border-brand-border rounded-lg">
                        <span class="text-brand-accent font-bold">|</span>
                        <input id="mNumSpec" type="number" min="1" max="12" placeholder="ĐB" class="w-14 p-2 text-center text-sm font-bold bg-brand-dark border-2 border-brand-accent text-brand-accent rounded-lg">
                    </div>
                </div>

                <div class="flex gap-2 pt-1">
                    <button onclick="handleSaveManualDraw()" class="flex-1 py-2.5 bg-brand-primary text-gray-900 rounded-xl text-sm font-bold hover:bg-blue-300 transition shadow">
                        💾 Lưu Kỳ Này Vào Điện Thoại
                    </button>
                    <button onclick="handleClearCustomDraws()" class="py-2.5 px-3 bg-red-950/40 hover:bg-red-900 text-red-300 rounded-xl text-xs font-bold transition border border-red-800/50">
                        Xóa Nhập Tay
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="max-w-6xl mx-auto space-y-6">
        <!-- Header -->
        <header class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <h1 class="text-2xl md:text-3xl font-extrabold text-brand-primary flex items-center gap-2">
                    🎯 XSTK - Vietlott Lotto 5/35
                </h1>
                <p class="text-xs md:text-sm text-gray-400 mt-1">
                    Mô hình dung sai mã QR (Typical Set) kết hợp Khoảng cách Mahalanobis & Shannon Gap Entropy
                </p>
            </div>
            <div class="flex flex-wrap items-center justify-center gap-2.5 w-full md:w-auto">
                <span id="headerStatus" class="px-3 py-1.5 bg-green-900/40 text-green-400 border border-green-700/50 rounded-full text-xs font-semibold">
                    ● <span id="headerCount">{total_draws}</span> Kỳ Lịch Sử
                </span>
                <button onclick="openUpdateModal()" class="px-3.5 py-2 bg-emerald-700 hover:bg-emerald-600 active:scale-95 text-white rounded-xl text-xs md:text-sm font-bold transition flex items-center gap-1.5 shadow-lg">
                    🔄 Cập Nhật Kỳ Mới
                </button>
                <a href="https://github.com/Gentsleo/xstk" target="_blank" class="px-3.5 py-2 bg-brand-border hover:bg-slate-700 text-gray-200 rounded-xl text-xs md:text-sm font-bold transition flex items-center gap-1.5">
                    GitHub
                </a>
            </div>
        </header>

        <!-- Navigation Tabs -->
        <div class="flex border-b border-brand-border gap-1 md:gap-2 text-xs md:text-sm font-bold overflow-x-auto no-scrollbar">
            <button onclick="switchTab('tab-eval')" id="btn-eval" class="tab-btn whitespace-nowrap px-4 py-3 border-b-2 border-brand-primary text-brand-primary flex items-center gap-1.5">
                🔍 Đánh Giá Bộ Số
            </button>
            <button onclick="switchTab('tab-gen')" id="btn-gen" class="tab-btn whitespace-nowrap px-4 py-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-1.5">
                ⚡ Gợi Ý Bộ Số (SQS ≥ 80)
            </button>
            <button onclick="switchTab('tab-history')" id="btn-history" class="tab-btn whitespace-nowrap px-4 py-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-1.5">
                📊 <span id="tabHistoryTitle">Lịch Sử ({total_draws} Kỳ)</span>
            </button>
            <button onclick="switchTab('tab-stats')" id="btn-stats" class="tab-btn whitespace-nowrap px-4 py-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-1.5">
                📈 Biểu Đồ Thống Kê
            </button>
            <button onclick="switchTab('tab-qr-theory')" id="btn-qr-theory" class="tab-btn whitespace-nowrap px-4 py-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-1.5">
                📐 Lý Thuyết Mã QR
            </button>
        </div>

        <!-- TAB 1: EVALUATE -->
        <div id="tab-eval" class="tab-content space-y-6">
            <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl">
                <h2 class="text-base md:text-lg font-bold text-brand-primary mb-3">Nhập bộ số để chấm điểm độ chuẩn xác suất</h2>
                <div class="flex flex-wrap items-center gap-2 md:gap-3">
                    <input id="num1" type="number" min="1" max="35" placeholder="01" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    <input id="num2" type="number" min="1" max="35" placeholder="02" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    <input id="num3" type="number" min="1" max="35" placeholder="03" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    <input id="num4" type="number" min="1" max="35" placeholder="04" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    <input id="num5" type="number" min="1" max="35" placeholder="05" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    
                    <span class="text-xl md:text-2xl font-bold text-brand-accent px-0.5">|</span>
                    
                    <input id="numSpecial" type="number" min="1" max="12" placeholder="ĐB" class="w-14 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border-2 border-brand-accent text-brand-accent rounded-xl focus:outline-none">

                    <button onclick="handleEvaluate()" class="w-full sm:w-auto px-5 h-11 md:h-12 bg-brand-primary text-gray-900 font-bold rounded-xl hover:bg-blue-300 active:scale-95 transition shadow-lg mt-2 sm:mt-0">
                        🚀 Chấm Điểm
                    </button>
                    <button onclick="fillLatest()" class="w-full sm:w-auto px-4 h-11 md:h-12 bg-slate-800 hover:bg-slate-700 text-gray-300 font-bold rounded-xl transition text-xs md:text-sm">
                        Kỳ Mới Nhất
                    </button>
                </div>
            </div>

            <!-- Result Scorecard -->
            <div id="evalResultCard" class="hidden bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl space-y-6">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-brand-border pb-6 gap-4">
                    <div class="flex items-center gap-4 md:gap-6">
                        <div class="text-center">
                            <span class="text-[11px] text-gray-400 block font-semibold">ĐIỂM CHUẨN SQS</span>
                            <span id="resSQS" class="text-4xl md:text-5xl font-extrabold text-brand-secondary">-- / 100</span>
                        </div>
                        <div>
                            <span id="resBadge" class="px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider">--</span>
                            <p id="resDesc" class="text-xs md:text-sm text-gray-300 mt-2 max-w-xl">--</p>
                        </div>
                    </div>
                    <div id="resBallsDisplay" class="flex flex-wrap items-center gap-1.5 md:gap-2"></div>
                </div>

                <!-- Metric Grid -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
                    <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border">
                        <span class="text-[11px] text-gray-400 block">Tổng Điểm 5 Số</span>
                        <span id="resSum" class="text-lg md:text-xl font-bold text-gray-200 mt-1 block">--</span>
                        <span class="text-[10px] text-gray-500">Lý thuyết: 90 ± 21</span>
                    </div>
                    <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border">
                        <span class="text-[11px] text-gray-400 block">Tỷ Lệ Chẵn / Lẻ</span>
                        <span id="resParity" class="text-lg md:text-xl font-bold text-gray-200 mt-1 block">--</span>
                        <span class="text-[10px] text-gray-500">Chuẩn: 3L-2C / 2L-3C</span>
                    </div>
                    <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border">
                        <span class="text-[11px] text-gray-400 block">Mahalanobis (D²_M)</span>
                        <span id="resDM" class="text-lg md:text-xl font-bold text-gray-200 mt-1 block">--</span>
                        <span class="text-[10px] text-gray-500">k=5 bậc tự do</span>
                    </div>
                    <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border">
                        <span class="text-[11px] text-gray-400 block">Gap Entropy (H)</span>
                        <span id="resEntropy" class="text-lg md:text-xl font-bold text-gray-200 mt-1 block">--</span>
                        <span class="text-[10px] text-gray-500">Tối đa: 1.79</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: GENERATOR -->
        <div id="tab-gen" class="tab-content hidden space-y-6">
            <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl flex flex-wrap items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <label class="font-bold text-xs md:text-sm text-gray-300">Số lượng:</label>
                    <input id="genCount" type="number" min="1" max="20" value="5" class="w-16 p-2 text-center font-bold bg-brand-dark border border-brand-border rounded-lg text-sm">
                    <button onclick="handleGenerate()" class="px-5 py-2.5 bg-brand-primary text-gray-900 font-bold rounded-xl hover:bg-blue-300 active:scale-95 transition shadow-lg text-xs md:text-sm">
                        ⚡ Sinh Số Tối Ưu (SQS ≥ 80)
                    </button>
                </div>
                <span class="text-xs text-gray-400 italic">Bộ lọc đa chiều Mahalanobis và Shannon Entropy</span>
            </div>

            <div id="genResultList" class="space-y-3"></div>
        </div>

        <!-- TAB 3: HISTORY -->
        <div id="tab-history" class="tab-content hidden space-y-4">
            <div class="bg-brand-card border border-brand-border rounded-2xl p-3 md:p-4 shadow-xl flex gap-3">
                <input id="historySearch" oninput="filterHistory()" type="text" placeholder="Tìm theo kỳ (vd: 00954) hoặc ngày (vd: 18/10/2026)..." class="flex-1 p-2.5 md:p-3 bg-brand-dark border border-brand-border rounded-xl focus:outline-none text-xs md:text-sm">
            </div>
            <div class="bg-brand-card border border-brand-border rounded-2xl shadow-xl overflow-x-auto max-h-[600px] overflow-y-auto">
                <table class="w-full text-left text-xs md:text-sm">
                    <thead class="bg-brand-border text-gray-300 font-bold sticky top-0">
                        <tr>
                            <th class="p-2.5 md:p-3">Kỳ</th>
                            <th class="p-2.5 md:p-3">Ngày</th>
                            <th class="p-2.5 md:p-3">Số 1</th>
                            <th class="p-2.5 md:p-3">Số 2</th>
                            <th class="p-2.5 md:p-3">Số 3</th>
                            <th class="p-2.5 md:p-3">Số 4</th>
                            <th class="p-2.5 md:p-3">Số 5</th>
                            <th class="p-2.5 md:p-3 text-brand-accent">Số ĐB</th>
                        </tr>
                    </thead>
                    <tbody id="historyTableBody" class="divide-y divide-brand-border"></tbody>
                </table>
            </div>
        </div>

        <!-- TAB 4: CHARTS -->
        <div id="tab-stats" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl">
                    <h3 class="font-bold text-brand-primary mb-4 text-sm md:text-base">Tần Suất 35 Quả Bóng Chính</h3>
                    <canvas id="chartBalls" height="200"></canvas>
                </div>
                <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl">
                    <h3 class="font-bold text-brand-accent mb-4 text-sm md:text-base">Tần Suất 12 Số Đặc Biệt</h3>
                    <canvas id="chartSpecial" height="200"></canvas>
                </div>
            </div>
        </div>

        <!-- TAB 5: QR THEORY -->
        <div id="tab-qr-theory" class="tab-content hidden space-y-6">
            <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl space-y-5">
                <div class="border-b border-brand-border pb-4">
                    <h2 class="text-lg md:text-xl font-bold text-brand-primary flex items-center gap-2">
                        📐 Lý Thuyết Dung Sai Mã QR (QR Tolerance Theory)
                    </h2>
                    <p class="text-xs md:text-sm text-gray-400 mt-1">
                        Ứng dụng nguyên lý Mã Sửa Sai Reed-Solomon (Level Q - Dung sai 25%) vào Không Gian Xác Suất Vietlott 5/35
                    </p>
                </div>

                <div class="bg-brand-dark p-4 md:p-5 rounded-xl border border-brand-border">
                    <h3 class="font-bold text-yellow-400 mb-2 text-sm">💡 Triết Lý Cốt Lõi:</h3>
                    <p class="text-gray-300 text-xs md:text-sm leading-relaxed">
                        Một mã QR bị mất hoặc nhòe 20% – 25% diện tích vẫn có thể quét thành công nhờ các <strong>Điểm Neo Định Vị (Finder Patterns)</strong> và <strong>Vạch Nhịp Đồng Bộ (Timing Patterns)</strong>. Tương tự, trong 324,632 bộ số của Lotto 5/35, ta không cần đoán vi mô từng quả bóng mà đi tìm <strong>Vùng Dung Sai Điển Hình (Typical Set)</strong> nơi mà <strong>75% - 80% các kỳ quay thực tế bắt buộc phải hội tụ về</strong>. Bất kỳ bộ số nào nằm ngoài vùng này (dồn cụm, toàn chẵn, toàn lẻ, v.v.) đều bị xem là nhiễu làm hỏng mã QR và bị loại bỏ.
                    </p>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs md:text-sm border border-brand-border rounded-xl">
                        <thead class="bg-brand-border text-gray-200 font-bold">
                            <tr>
                                <th class="p-2.5 md:p-3">Thành phần Mã QR</th>
                                <th class="p-2.5 md:p-3">Vai trò trong Mã QR</th>
                                <th class="p-2.5 md:p-3">Tương ứng trong Vietlott 5/35</th>
                                <th class="p-2.5 md:p-3 text-brand-primary">Công thức Toán học</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-brand-border text-gray-300">
                            <tr>
                                <td class="p-2.5 md:p-3 font-bold text-yellow-400">Dung sai lỗi 20–25% (Level Q)</td>
                                <td class="p-2.5 md:p-3">Mất 25% dữ liệu máy ảnh vẫn giải mã được</td>
                                <td class="p-2.5 md:p-3">Vùng bao phủ 75–80% kỳ quay thực tế, lọc bỏ 70% bộ số rác</td>
                                <td class="p-2.5 md:p-3 font-mono text-[11px] text-brand-secondary">Chi-Square χ²(5) với p ≥ 0.20 (D²_M ≤ 7.09)</td>
                            </tr>
                            <tr>
                                <td class="p-2.5 md:p-3 font-bold text-blue-400">3 Ô vuông góc (Finder Patterns)</td>
                                <td class="p-2.5 md:p-3">Điểm neo định vị toạ độ và góc xoay</td>
                                <td class="p-2.5 md:p-3">Trọng tâm Tổng điểm (90), Cân bằng Chẵn/Lẻ (3:2, 2:3), Tài/Xỉu</td>
                                <td class="p-2.5 md:p-3 font-mono text-[11px] text-brand-secondary">Vector kỳ vọng μ = [91.1, 2.57, 2.62, 23.85, 0.58]ᵀ</td>
                            </tr>
                            <tr>
                                <td class="p-2.5 md:p-3 font-bold text-purple-400">Ma trận giải mã (Reed-Solomon)</td>
                                <td class="p-2.5 md:p-3">Khử nhiễu đa chiều trên trường hữu hạn GF(2⁸)</td>
                                <td class="p-2.5 md:p-3">Khử sạch đa cộng tuyến giữa Tổng và Số Lớn (Corr = +0.876)</td>
                                <td class="p-2.5 md:p-3 font-mono text-[11px] text-brand-secondary">Khoảng cách Mahalanobis: D²_M = (x - μ)ᵀ Σ⁻¹ (x - μ)</td>
                            </tr>
                            <tr>
                                <td class="p-2.5 md:p-3 font-bold text-emerald-400">Vạch nhịp (Timing Patterns)</td>
                                <td class="p-2.5 md:p-3">Đường xen kẽ sọc đen/trắng chống vón cục pixel</td>
                                <td class="p-2.5 md:p-3">Đảm bảo 5 quả bóng trải đều khắp dải [1, 35], chống dồn cụm</td>
                                <td class="p-2.5 md:p-3 font-mono text-[11px] text-brand-secondary">Shannon Gap Entropy: H(Gaps) = -Σ p_i ln(p_i)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Embedded Data & Mathematical Engine -->
    <script>
        const BASE_DRAWS = {json.dumps(draws_data, ensure_ascii=False)};
        let DRAWS_DATA = [...BASE_DRAWS];

        // Load custom draws from LocalStorage (Mobile friendly)
        function loadLocalStorageDraws() {{
            try {{
                const saved = localStorage.getItem('xstk_custom_draws');
                if (saved) {{
                    const customList = JSON.parse(saved);
                    customList.forEach(cd => {{
                        if (!DRAWS_DATA.some(d => d.draw_code === cd.draw_code)) {{
                            DRAWS_DATA.push(cd);
                        }}
                    }});
                    DRAWS_DATA.sort((a,b) => a.draw_id - b.draw_id);
                }}
            }} catch(e) {{
                console.error('Lỗi nạp local storage:', e);
            }}
        }}

        // Mathematical Constants (from 954 historical draws)
        const MU = [91.1069, 2.5681, 2.6237, 23.8512, 0.5755];
        const INV_COV = [
            [ 0.009367, -0.004928, -0.164895, -0.000941, -0.008335],
            [-0.004928,  0.896688,  0.078079, -0.001084, -0.001216],
            [-0.164895,  0.078079,  3.775486,  0.027999,  0.141572],
            [-0.000941, -0.001084,  0.027999,  0.030715,  0.072989],
            [-0.008335, -0.001216,  0.141572,  0.072989,  2.300800]
        ];

        function gamma(s) {{
            if (Math.abs(s - 2.5) < 1e-6) return 0.75 * Math.sqrt(Math.PI);
            return Math.sqrt(2 * Math.PI / s) * Math.pow((s + 1 / (12 * s - 1 / (10 * s))) / Math.E, s);
        }}

        function chi2Cdf(x, k=5) {{
            if (x <= 0) return 0.0;
            const s = k / 2.0;
            const z = x / 2.0;
            let term = 1.0 / s;
            let total = term;
            for (let n = 1; n < 100; n++) {{
                term *= z / (s + n);
                total += term;
                if (Math.abs(term) < 1e-12) break;
            }}
            const gammaInc = Math.exp(-z) * Math.pow(z, s) * total;
            return Math.min(1.0, Math.max(0.0, gammaInc / gamma(s)));
        }}

        function evaluateCombo(combo, special=null) {{
            const sorted = [...combo].map(Number).sort((a,b) => a - b);
            const sum = sorted.reduce((a,b) => a + b, 0);
            const zSum = (sum - 90.0) / 21.2132;
            const odds = sorted.filter(x => x % 2 !== 0).length;
            const highs = sorted.filter(x => x >= 18).length;
            const span = sorted[4] - sorted[0];
            let consecs = 0;
            for (let i = 0; i < 4; i++) if (sorted[i+1] - sorted[i] === 1) consecs++;

            const vec = [sum - MU[0], odds - MU[1], highs - MU[2], span - MU[3], consecs - MU[4]];
            let dmSq = 0;
            for (let i = 0; i < 5; i++) {{
                for (let j = 0; j < 5; j++) {{
                    dmSq += vec[i] * INV_COV[i][j] * vec[j];
                }}
            }}
            const pMain = 1.0 - chi2Cdf(dmSq, 5);

            // Gap Entropy
            const gaps = [sorted[0], sorted[1]-sorted[0], sorted[2]-sorted[1], sorted[3]-sorted[2], sorted[4]-sorted[3], 36-sorted[4]];
            let entropy = 0;
            for (const g of gaps) {{
                const p = g / 36.0;
                if (p > 0) entropy -= p * Math.log(p);
            }}
            const entropyFactor = Math.min(1.0, Math.max(0.0, (entropy - 1.0) / (Math.log(6.0) - 1.0)));

            let specFactor = 1.0;
            if (special !== null && special >= 1 && special <= 12) {{
                const isOverlap = sorted.includes(Number(special));
                const overlapMult = isOverlap ? 0.6 : 1.0;
                const dev = Math.abs(special - 6.5) / 3.452;
                const pSpec = Math.exp(-0.5 * dev * dev) * overlapMult;
                specFactor = 0.8 + 0.2 * pSpec;
            }}

            const jointProb = pMain * (0.8 + 0.2 * entropyFactor) * specFactor;
            const sqs = Math.min(100.0, Math.max(0.0, Math.round(jointProb * 1000) / 10));

            return {{
                combo: sorted,
                sum,
                zSum: zSum.toFixed(2),
                odds,
                evens: 5 - odds,
                highs,
                lows: 5 - highs,
                span,
                consecs,
                dmSq: dmSq.toFixed(2),
                pMain: pMain.toFixed(4),
                entropy: entropy.toFixed(3),
                sqs,
                special: special ? Number(special) : null
            }};
        }}

        // Toast Helper (Mobile friendly)
        let toastTimeout;
        function showToast(msg, isError=false) {{
            const c = document.getElementById('toastContainer');
            const b = document.getElementById('toastBody');
            const m = document.getElementById('toastMsg');
            m.innerText = msg;
            if (isError) {{
                b.className = 'p-4 rounded-xl shadow-2xl border text-sm font-bold flex items-center justify-between gap-3 toast-animate bg-red-950/90 border-red-500 text-red-200';
            }} else {{
                b.className = 'p-4 rounded-xl shadow-2xl border text-sm font-bold flex items-center justify-between gap-3 toast-animate bg-brand-card border-brand-primary text-gray-200';
            }}
            c.classList.remove('hidden');
            clearTimeout(toastTimeout);
            toastTimeout = setTimeout(hideToast, 4000);
        }}
        function hideToast() {{
            document.getElementById('toastContainer').classList.add('hidden');
        }}

        // Modal Controls
        function openUpdateModal() {{
            const latest = DRAWS_DATA[DRAWS_DATA.length - 1];
            document.getElementById('modalCurrentDraw').innerText = '#' + latest.draw_code + ' (' + latest.date + ')';
            document.getElementById('modalTotalDraws').innerText = DRAWS_DATA.length + ' kỳ';
            
            // Prefill manual form with next draw code
            const nextCode = String(latest.draw_id + 1).padStart(5, '0');
            document.getElementById('manualDrawCode').value = nextCode;
            const today = new Date();
            const d = String(today.getDate()).padStart(2, '0');
            const mo = String(today.getMonth() + 1).padStart(2, '0');
            document.getElementById('manualDrawDate').value = `${{d}}/${{mo}}/${{today.getFullYear()}}`;
            
            document.getElementById('updateModal').classList.remove('hidden');
        }}

        function closeUpdateModal() {{
            document.getElementById('updateModal').classList.add('hidden');
        }}

        // Online Sync with GitHub Repo
        async function syncLatestDraws() {{
            const btn = document.getElementById('btnSyncModal');
            const orig = btn.innerHTML;
            btn.innerHTML = '⏳ Đang đồng bộ...';
            btn.disabled = true;

            try {{
                const resp = await fetch('https://raw.githubusercontent.com/Gentsleo/xstk/main/vietlott_535.json?t=' + Date.now());
                if (!resp.ok) throw new Error('Không thể tải từ GitHub.');
                const freshData = await resp.json();
                
                const oldCount = DRAWS_DATA.length;
                const newCount = freshData.length;
                if (newCount > oldCount) {{
                    DRAWS_DATA = freshData;
                    loadLocalStorageDraws(); // re-merge
                    updateAppViews();
                    showToast(`🎉 Đã cập nhật thành công ${{DRAWS_DATA.length - oldCount}} kỳ mới!`);
                    closeUpdateModal();
                }} else {{
                    showToast(`Dữ liệu đã là mới nhất (Kỳ #${{freshData[freshData.length - 1].draw_code}})!`);
                }}
            }} catch (err) {{
                showToast('Lỗi đồng bộ: ' + err.message, true);
            }} finally {{
                btn.innerHTML = orig;
                btn.disabled = false;
            }}
        }}

        // Save Manual Draw on Mobile (LocalStorage)
        function handleSaveManualDraw() {{
            const code = document.getElementById('manualDrawCode').value.trim();
            const date = document.getElementById('manualDrawDate').value.trim();
            const n1 = Number(document.getElementById('mNum1').value);
            const n2 = Number(document.getElementById('mNum2').value);
            const n3 = Number(document.getElementById('mNum3').value);
            const n4 = Number(document.getElementById('mNum4').value);
            const n5 = Number(document.getElementById('mNum5').value);
            const spec = Number(document.getElementById('mNumSpec').value);

            const nums = [n1, n2, n3, n4, n5];
            if (!code || !date) {{
                showToast('Vui lòng điền mã kỳ và ngày quay!', true);
                return;
            }}
            if (nums.some(n => !n || n < 1 || n > 35) || new Set(nums).size !== 5) {{
                showToast('5 số chính phải từ 1 đến 35 và không được trùng nhau!', true);
                return;
            }}
            if (!spec || spec < 1 || spec > 12) {{
                showToast('Số đặc biệt phải từ 1 đến 12!', true);
                return;
            }}

            const sorted = [...nums].sort((a,b) => a - b);
            const drawId = parseInt(code, 10);
            const newObj = {{
                draw_id: drawId,
                draw_code: code,
                date: date,
                num1: sorted[0],
                num2: sorted[1],
                num3: sorted[2],
                num4: sorted[3],
                num5: sorted[4],
                special: spec,
                numbers_str: `${{String(sorted[0]).padStart(2,'0')}} ${{String(sorted[1]).padStart(2,'0')}} ${{String(sorted[2]).padStart(2,'0')}} ${{String(sorted[3]).padStart(2,'0')}} ${{String(sorted[4]).padStart(2,'0')}} | ${{String(spec).padStart(2,'0')}}`
            }};

            // Save to LocalStorage
            let customList = [];
            try {{
                const saved = localStorage.getItem('xstk_custom_draws');
                if (saved) customList = JSON.parse(saved);
            }} catch(e) {{}}
            
            customList = customList.filter(d => d.draw_code !== code);
            customList.push(newObj);
            localStorage.setItem('xstk_custom_draws', JSON.stringify(customList));

            // Add to current in-memory data
            DRAWS_DATA = DRAWS_DATA.filter(d => d.draw_code !== code);
            DRAWS_DATA.push(newObj);
            DRAWS_DATA.sort((a,b) => a.draw_id - b.draw_id);

            updateAppViews();
            showToast(`Đã lưu thành công kỳ #${{code}} vào điện thoại!`);
            closeUpdateModal();
        }}

        function handleClearCustomDraws() {{
            if (confirm('Bạn có chắc muốn xóa các kỳ nhập tay trên điện thoại và khôi phục dữ liệu gốc?')) {{
                localStorage.removeItem('xstk_custom_draws');
                DRAWS_DATA = [...BASE_DRAWS];
                updateAppViews();
                showToast('Đã khôi phục dữ liệu gốc từ máy chủ!');
                closeUpdateModal();
            }}
        }}

        function updateAppViews() {{
            const total = DRAWS_DATA.length;
            document.getElementById('headerCount').innerText = total;
            document.getElementById('tabHistoryTitle').innerText = `Lịch Sử (${{total}} Kỳ)`;
            loadHistory();
            fillLatest();
            if (window.chartsRendered) renderCharts();
        }}

        // Tab Switching
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('border-brand-primary', 'text-brand-primary');
                btn.classList.add('border-transparent', 'text-gray-400');
            }});
            document.getElementById(tabId).classList.remove('hidden');
            const activeBtn = document.getElementById(tabId.replace('tab-', 'btn-'));
            if (activeBtn) {{
                activeBtn.classList.remove('border-transparent', 'text-gray-400');
                activeBtn.classList.add('border-brand-primary', 'text-brand-primary');
            }}
            if (tabId === 'tab-stats' && !window.chartsRendered) {{
                renderCharts();
                window.chartsRendered = true;
            }}
        }}

        function fillLatest() {{
            const latest = DRAWS_DATA[DRAWS_DATA.length - 1];
            document.getElementById('num1').value = latest.num1;
            document.getElementById('num2').value = latest.num2;
            document.getElementById('num3').value = latest.num3;
            document.getElementById('num4').value = latest.num4;
            document.getElementById('num5').value = latest.num5;
            document.getElementById('numSpecial').value = latest.special;
            handleEvaluate();
        }}

        function handleEvaluate() {{
            const nums = [
                document.getElementById('num1').value,
                document.getElementById('num2').value,
                document.getElementById('num3').value,
                document.getElementById('num4').value,
                document.getElementById('num5').value,
            ].map(Number);
            const spec = document.getElementById('numSpecial').value;

            if (nums.some(n => !n || n < 1 || n > 35) || new Set(nums).size !== 5) {{
                showToast('Vui lòng nhập đúng 5 số chính khác nhau từ 1 đến 35!', true);
                return;
            }}

            const res = evaluateCombo(nums, spec ? Number(spec) : null);
            document.getElementById('evalResultCard').classList.remove('hidden');

            const sqsEl = document.getElementById('resSQS');
            const badgeEl = document.getElementById('resBadge');
            const descEl = document.getElementById('resDesc');

            sqsEl.innerText = res.sqs.toFixed(1) + ' / 100';

            if (res.sqs >= 75) {{
                sqsEl.className = 'text-4xl md:text-5xl font-extrabold text-green-400';
                badgeEl.className = 'px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider bg-green-900/50 text-green-300 border border-green-700';
                badgeEl.innerText = 'XUẤT SẮC (Top 25% Tâm Phân Phối)';
                descEl.innerText = 'Bộ số đạt tỷ lệ đối xứng lý tưởng, độ trải đều trên toàn trục số hoàn hảo.';
            }} else if (res.sqs >= 40) {{
                sqsEl.className = 'text-4xl md:text-5xl font-extrabold text-yellow-400';
                badgeEl.className = 'px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider bg-yellow-900/50 text-yellow-300 border border-yellow-700';
                badgeEl.innerText = 'ĐẠT CHUẨN (Vùng Dung Sai 80% QR)';
                descEl.innerText = 'Bộ số hài hòa, nằm vững trong vùng 80% các kỳ quay trúng thưởng thực tế.';
            }} else if (res.sqs >= 10) {{
                sqsEl.className = 'text-4xl md:text-5xl font-extrabold text-orange-400';
                badgeEl.className = 'px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider bg-orange-900/50 text-orange-300 border border-orange-700';
                badgeEl.innerText = 'DUNG SAI BIÊN (Cần Lưu Ý)';
                descEl.innerText = 'Bộ số hơi lệch về tổng hoặc khoảng cách nhưng vẫn nằm trong phạm vi chấp nhận.';
            }} else {{
                sqsEl.className = 'text-4xl md:text-5xl font-extrabold text-red-400';
                badgeEl.className = 'px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider bg-red-900/50 text-red-300 border border-red-700';
                badgeEl.innerText = 'CẢNH BÁO (Lệch Chuẩn / Nhiễu Rác)';
                descEl.innerText = 'Bộ số bị dồn cụm, lệch chẵn/lẻ hoặc tổng quá cực đoan (p-value < 0.05).';
            }}

            // Balls display
            const ballsContainer = document.getElementById('resBallsDisplay');
            ballsContainer.innerHTML = res.combo.map(n => `<span class="ball ball-main text-sm w-9 h-9 md:w-10 md:h-10">${{String(n).padStart(2,'0')}}</span>`).join('') +
                (res.special ? `<span class="text-lg md:text-xl font-bold text-brand-accent px-1">|</span><span class="ball ball-special text-sm w-9 h-9 md:w-10 md:h-10">${{String(res.special).padStart(2,'0')}}</span>` : '');

            document.getElementById('resSum').innerText = `${{res.sum}} (${{res.zSum > 0 ? '+' : ''}}${{res.zSum}}σ)`;
            document.getElementById('resParity').innerText = `${{res.odds}} Lẻ - ${{res.evens}} Chẵn`;
            document.getElementById('resDM').innerText = `${{res.dmSq}} (p=${{res.pMain}})`;
            document.getElementById('resEntropy').innerText = `${{res.entropy}} / 1.79`;
        }}

        function handleGenerate() {{
            const count = Number(document.getElementById('genCount').value) || 5;
            const container = document.getElementById('genResultList');
            container.innerHTML = '';

            const found = [];
            const specChoices = [3, 7, 9, 12, 1, 2, 8, 10, 4, 5];
            let attempts = 0;

            while (found.length < count && attempts < 25000) {{
                attempts++;
                const pool = Array.from({{length: 35}}, (_, i) => i + 1);
                const combo = [];
                for (let i = 0; i < 5; i++) {{
                    const idx = Math.floor(Math.random() * pool.length);
                    combo.push(pool.splice(idx, 1)[0]);
                }}
                combo.sort((a,b) => a - b);
                const availableSpec = specChoices.filter(s => !combo.includes(s));
                const spec = availableSpec[Math.floor(Math.random() * availableSpec.length)] || (Math.floor(Math.random() * 12) + 1);

                const res = evaluateCombo(combo, spec);
                if (res.sqs >= 80.0 && Number(res.entropy) >= 1.50) {{
                    found.push(res);
                }}
            }}

            found.forEach((r, idx) => {{
                const item = document.createElement('div');
                item.className = 'bg-brand-card border border-brand-border rounded-xl p-3.5 md:p-4 flex flex-col md:flex-row items-center justify-between gap-3 shadow-lg';
                item.innerHTML = `
                    <div class="flex items-center gap-3">
                        <span class="text-xs font-bold text-gray-400">#${{String(idx+1).padStart(2,'0')}}</span>
                        <div class="flex items-center gap-1.5">
                            ${{r.combo.map(n => `<span class="ball ball-main text-xs md:text-sm w-8 h-8 md:w-9 md:h-9">${{String(n).padStart(2,'0')}}</span>`).join('')}}
                            <span class="text-brand-accent font-bold px-0.5">|</span>
                            <span class="ball ball-special text-xs md:text-sm w-8 h-8 md:w-9 md:h-9">${{String(r.special).padStart(2,'0')}}</span>
                        </div>
                    </div>
                    <div class="flex flex-wrap items-center justify-center gap-3 md:gap-6 text-xs md:text-sm">
                        <span>Tổng: <strong class="text-gray-200">${{r.sum}}</strong></span>
                        <span>${{r.odds}}L - ${{r.evens}}C</span>
                        <span>Entropy: <strong class="text-gray-200">${{r.entropy}}</strong></span>
                        <span class="px-2.5 py-1 rounded-lg font-bold bg-green-900/40 text-green-400 border border-green-700/50">SQS: ${{r.sqs.toFixed(1)}}</span>
                    </div>
                `;
                container.appendChild(item);
            }});
        }}

        function loadHistory() {{
            const tbody = document.getElementById('historyTableBody');
            tbody.innerHTML = DRAWS_DATA.slice().reverse().map(d => `
                <tr class="hover:bg-brand-border/40 transition">
                    <td class="p-2.5 md:p-3 font-bold text-brand-primary">#${{d.draw_code}}</td>
                    <td class="p-2.5 md:p-3 text-gray-400">${{d.date}}</td>
                    <td class="p-2.5 md:p-3 font-bold">${{String(d.num1).padStart(2,'0')}}</td>
                    <td class="p-2.5 md:p-3 font-bold">${{String(d.num2).padStart(2,'0')}}</td>
                    <td class="p-2.5 md:p-3 font-bold">${{String(d.num3).padStart(2,'0')}}</td>
                    <td class="p-2.5 md:p-3 font-bold">${{String(d.num4).padStart(2,'0')}}</td>
                    <td class="p-2.5 md:p-3 font-bold">${{String(d.num5).padStart(2,'0')}}</td>
                    <td class="p-2.5 md:p-3 font-bold text-brand-accent">${{String(d.special).padStart(2,'0')}}</td>
                </tr>
            `).join('');
        }}

        function filterHistory() {{
            const q = document.getElementById('historySearch').value.trim().toLowerCase();
            const rows = document.getElementById('historyTableBody').getElementsByTagName('tr');
            for (let i = 0; i < rows.length; i++) {{
                const text = rows[i].innerText.toLowerCase();
                rows[i].style.display = text.includes(q) ? '' : 'none';
            }}
        }}

        function renderCharts() {{
            const ballCounts = Array(35).fill(0);
            const specCounts = Array(12).fill(0);
            DRAWS_DATA.forEach(d => {{
                [d.num1, d.num2, d.num3, d.num4, d.num5].forEach(n => ballCounts[n-1]++);
                specCounts[d.special-1]++;
            }});

            if (window.myBallChart) window.myBallChart.destroy();
            window.myBallChart = new Chart(document.getElementById('chartBalls'), {{
                type: 'bar',
                data: {{
                    labels: Array.from({{length: 35}}, (_, i) => String(i+1).padStart(2,'0')),
                    datasets: [{{
                        label: 'Số lần xuất hiện',
                        data: ballCounts,
                        backgroundColor: '#3b82f6'
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{ beginAtZero: false, min: 100, max: 175, grid: {{ color: '#313244' }} }},
                        x: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});

            if (window.mySpecChart) window.mySpecChart.destroy();
            window.mySpecChart = new Chart(document.getElementById('chartSpecial'), {{
                type: 'bar',
                data: {{
                    labels: Array.from({{length: 12}}, (_, i) => 'ĐB ' + String(i+1).padStart(2,'0')),
                    datasets: [{{
                        label: 'Số lần xuất hiện',
                        data: specCounts,
                        backgroundColor: '#ef4444'
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{ beginAtZero: false, min: 65, max: 95, grid: {{ color: '#313244' }} }},
                        x: {{ grid: {{ display: false }} }}
                    }}
                }}
            }});
        }}

        // Initialize App
        loadLocalStorageDraws();
        updateAppViews();
    </script>
</body>
</html>
"""

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

os.makedirs(os.path.join(BASE_DIR, "docs"), exist_ok=True)
with open(os.path.join(BASE_DIR, "docs/index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print("[✓] Đã tạo thành công index.html và docs/index.html với Mobile Update Modal và LocalStorage!")
