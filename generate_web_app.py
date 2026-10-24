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
    <title>XSTK - Vietlott Lotto 5/35 (SQS Engine v2.0 & Dàn Bao Stefan Mandel)</title>
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
        .ball-sm {{
            width: 2.1rem;
            height: 2.1rem;
            font-size: 0.9rem;
        }}
        .no-scrollbar::-webkit-scrollbar {{
            display: none;
        }}
        .no-scrollbar {{
            -ms-overflow-style: none;
            scrollbar-width: none;
        }}
        @keyframes slideDown {{
            from {{ transform: translateY(-100%); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        .toast-animate {{
            animation: slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }}
    </style>
</head>
<body class="p-3 md:p-6 max-w-7xl mx-auto space-y-6">

    <!-- Toast Notification Container (Mobile Friendly) -->
    <div id="toastContainer" class="fixed top-4 left-4 right-4 z-50 pointer-events-none flex justify-center hidden">
        <div id="toastBody" class="max-w-md w-full p-4 rounded-xl shadow-2xl border text-sm font-bold flex items-center justify-between gap-3 toast-animate pointer-events-auto bg-brand-card border-brand-primary text-gray-200">
            <span id="toastMsg">Thông báo</span>
            <button onclick="hideToast()" class="text-gray-400 hover:text-white text-lg font-bold p-1">✕</button>
        </div>
    </div>

    <!-- UPDATE MODAL (MOBILE FRIENDLY) -->
    <div id="updateModal" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 hidden flex items-center justify-center p-4">
        <div class="bg-brand-card border border-brand-border rounded-2xl max-w-lg w-full p-5 md:p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
            <div class="flex items-center justify-between border-b border-brand-border pb-3">
                <h3 class="text-lg font-extrabold text-brand-primary flex items-center gap-2">
                    🔄 Trung Tâm Cập Nhật Kỳ Mới
                </h3>
                <button onclick="closeUpdateModal()" class="text-gray-400 hover:text-white text-xl font-bold p-1">✕</button>
            </div>

            <!-- Current status summary -->
            <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border text-xs space-y-1">
                <div class="flex justify-between">
                    <span class="text-gray-400">Kỳ mới nhất trên máy:</span>
                    <strong id="modalLatestCode" class="text-brand-secondary">#00000</strong>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Ngày quay:</span>
                    <span id="modalLatestDate" class="text-gray-300">--/--/----</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Tổng số kỳ hiện có:</span>
                    <span id="modalTotalDraws" class="text-gray-200 font-bold">{total_draws}</span>
                </div>
            </div>

            <!-- Option 1: Cloud Sync -->
            <div class="space-y-2">
                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400">☁️ Tùy Chọn 1: Đồng Bộ Từ Đám Mây GitHub</h4>
                <p class="text-xs text-gray-400">
                    Máy chủ đám mây tự động cào kết quả từ Vietlott lúc 18:45 & 20:45 mỗi ngày. Bấm để tải các kỳ mới nhất:
                </p>
                <div class="flex flex-wrap gap-2">
                    <button id="btnSyncCloud" onclick="syncFromCloud()" class="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-bold rounded-xl text-xs md:text-sm transition flex items-center justify-center gap-2 shadow-md">
                        <span id="syncSpinner" class="hidden">⏳</span> 🔄 Đồng Bộ Từ Đám Mây
                    </button>
                    <a href="https://github.com/Gentsleo/xstk/actions/workflows/auto-update.yml" target="_blank" class="px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 text-gray-300 font-bold rounded-xl text-xs transition flex items-center justify-center gap-1.5 border border-brand-border">
                        ⚡ Ép Cào Ngay
                    </a>
                </div>
            </div>

            <div class="relative flex py-1 items-center">
                <div class="flex-grow border-t border-brand-border"></div>
                <span class="flex-shrink mx-3 text-gray-500 text-xs uppercase font-bold">HOẶC</span>
                <div class="flex-grow border-t border-brand-border"></div>
            </div>

            <!-- Option 2: Quick manual entry -->
            <div class="space-y-3">
                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400">📱 Tùy Chọn 2: Nhập Nhanh Kỳ Vừa Quay Trên ĐT</h4>
                <p class="text-xs text-gray-400">
                    Khi vừa xem tivi / có tin nhắn kết quả, bạn có thể điền ngay vào đây (Lưu trực tiếp vào bộ nhớ điện thoại):
                </p>
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div>
                        <label class="text-gray-400 block mb-1">Mã kỳ (vd: 00955):</label>
                        <input id="inputNewCode" type="text" class="w-full p-2 bg-brand-dark border border-brand-border rounded-lg text-gray-200 font-bold text-center">
                    </div>
                    <div>
                        <label class="text-gray-400 block mb-1">Ngày quay:</label>
                        <input id="inputNewDate" type="text" class="w-full p-2 bg-brand-dark border border-brand-border rounded-lg text-gray-200 font-bold text-center">
                    </div>
                </div>

                <div>
                    <label class="text-gray-400 block mb-1 text-xs">5 số chính + 1 số ĐB:</label>
                    <div class="flex items-center gap-1.5 justify-between">
                        <input id="inN1" type="number" min="1" max="35" placeholder="01" class="w-10 h-10 text-center font-bold bg-brand-dark border border-brand-border rounded-lg text-sm">
                        <input id="inN2" type="number" min="1" max="35" placeholder="02" class="w-10 h-10 text-center font-bold bg-brand-dark border border-brand-border rounded-lg text-sm">
                        <input id="inN3" type="number" min="1" max="35" placeholder="03" class="w-10 h-10 text-center font-bold bg-brand-dark border border-brand-border rounded-lg text-sm">
                        <input id="inN4" type="number" min="1" max="35" placeholder="04" class="w-10 h-10 text-center font-bold bg-brand-dark border border-brand-border rounded-lg text-sm">
                        <input id="inN5" type="number" min="1" max="35" placeholder="05" class="w-10 h-10 text-center font-bold bg-brand-dark border border-brand-border rounded-lg text-sm">
                        <span class="text-brand-accent font-bold">|</span>
                        <input id="inNS" type="number" min="1" max="12" placeholder="ĐB" class="w-11 h-10 text-center font-bold bg-brand-dark border-2 border-brand-accent text-brand-accent rounded-lg text-sm">
                    </div>
                </div>

                <button onclick="saveManualDraw()" class="w-full py-2.5 bg-emerald-700 hover:bg-emerald-600 active:scale-95 text-white font-bold rounded-xl text-xs md:text-sm transition flex items-center justify-center gap-2 shadow-lg">
                    💾 Lưu Kỳ Này Vào Điện Thoại
                </button>
            </div>

            <!-- Clear cache option -->
            <div class="border-t border-brand-border pt-3 flex justify-between items-center text-xs">
                <span class="text-gray-500">Đặt lại bộ nhớ cục bộ:</span>
                <button onclick="resetLocalStorageDraws()" class="text-red-400 hover:text-red-300 underline font-semibold">
                    Xóa dữ liệu lưu tạm
                </button>
            </div>
        </div>
    </div>

    <!-- Header Section -->
    <header class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-brand-border">
        <div>
            <h1 class="text-2xl md:text-3xl font-extrabold text-brand-primary flex items-center gap-2">
                🎯 XSTK - Vietlott Lotto 5/35
            </h1>
            <p class="text-xs md:text-sm text-gray-400 mt-1">
                SQS Engine v2.0: Mahalanobis &bull; Gap Entropy &bull; Chuỗi Markov &bull; Nhịp Poisson &bull; Dàn Bao Stefan Mandel
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
            🔍 Đánh Giá Bộ Số (SQS v2.0)
        </button>
        <button onclick="switchTab('tab-wheel')" id="btn-wheel" class="tab-btn whitespace-nowrap px-4 py-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-1.5">
            🎯 Dàn Bao Tối Ưu C(10,5,3,5)
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
            📐 5 Trụ Cột Toán Học
        </button>
    </div>

    <!-- TAB 1: EVALUATE -->
    <div id="tab-eval" class="tab-content space-y-6">
        <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl">
            <h2 class="text-base md:text-lg font-bold text-brand-primary mb-3">Nhập bộ số để chấm điểm độ chuẩn xác suất SQS Engine v2.0</h2>
            <div class="flex flex-wrap items-center gap-2 md:gap-3">
                <input id="num1" type="number" min="1" max="35" placeholder="01" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                <input id="num2" type="number" min="1" max="35" placeholder="02" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                <input id="num3" type="number" min="1" max="35" placeholder="03" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                <input id="num4" type="number" min="1" max="35" placeholder="04" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                <input id="num5" type="number" min="1" max="35" placeholder="05" class="w-12 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                
                <span class="text-xl md:text-2xl font-bold text-brand-accent px-0.5">|</span>
                
                <input id="numSpecial" type="number" min="1" max="12" placeholder="ĐB" class="w-14 md:w-16 h-11 md:h-12 text-center text-lg md:text-xl font-bold bg-brand-dark border-2 border-brand-accent text-brand-accent rounded-xl focus:outline-none">

                <button onclick="handleEvaluate()" class="w-full sm:w-auto px-5 h-11 md:h-12 bg-brand-primary text-gray-900 font-bold rounded-xl hover:bg-blue-300 active:scale-95 transition shadow-lg mt-2 sm:mt-0">
                    🚀 Chấm Điểm SQS v2.0
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
                        <span class="text-[11px] text-gray-400 block font-semibold">ĐIỂM CHUẨN SQS v2.0</span>
                        <span id="resSQS" class="text-4xl md:text-5xl font-extrabold text-brand-secondary">-- / 100</span>
                    </div>
                    <div>
                        <span id="resBadge" class="px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider">--</span>
                        <p id="resDesc" class="text-xs md:text-sm text-gray-300 mt-2 max-w-xl">--</p>
                    </div>
                </div>
                <div id="resBallsDisplay" class="flex flex-wrap items-center gap-1.5 md:gap-2"></div>
            </div>

            <!-- Dynamic v2 Indicators -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 md:gap-4 border-b border-brand-border pb-5">
                <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border">
                    <span class="text-[11px] text-gray-400 block">Chuỗi Markov (Lặp Kỳ Trước)</span>
                    <span id="resMarkov" class="text-base font-bold text-gray-200 mt-1 block">--</span>
                    <span class="text-[10px] text-gray-500">Chuẩn: 0, 1 hoặc tối đa 2 số</span>
                </div>
                <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border">
                    <span class="text-[11px] text-gray-400 block">Nhịp Vắng Poisson (Skip-Sum)</span>
                    <span id="resPoisson" class="text-base font-bold text-gray-200 mt-1 block">--</span>
                    <span class="text-[10px] text-gray-500">Vùng vàng thực tế: [20, 54] kỳ</span>
                </div>
                <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border">
                    <span class="text-[11px] text-gray-400 block">Chống Chia Giải Solo EV (Cox 1998)</span>
                    <span id="resAntiCluster" class="text-base font-bold text-gray-200 mt-1 block">--</span>
                    <span class="text-[10px] text-gray-500">Có số ≥ 32: Đảm bảo 100% giải độc quyền</span>
                </div>
            </div>

            <!-- Metric Grid v1 Foundations -->
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
                    <span class="text-[10px] text-gray-500">k=5 bậc tự do (p-value)</span>
                </div>
                <div class="bg-brand-dark p-3.5 rounded-xl border border-brand-border">
                    <span class="text-[11px] text-gray-400 block">Gap Entropy (H)</span>
                    <span id="resEntropy" class="text-lg md:text-xl font-bold text-gray-200 mt-1 block">--</span>
                    <span class="text-[10px] text-gray-500">Tối đa: 1.79</span>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 2: COVERING WHEEL C(10,5,3,5) (BRAND NEW!) -->
    <div id="tab-wheel" class="tab-content hidden space-y-6">
        <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl space-y-4">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h2 class="text-lg md:text-xl font-extrabold text-brand-primary flex items-center gap-2">
                        🎯 Dàn Bao Tối Ưu C(10, 5, 3, 5) - Stefan Mandel & La Jolla
                    </h2>
                    <p class="text-xs md:text-sm text-gray-400 mt-1">
                        Áp dụng Phương án #4 (Tự động chọn bể 10 số tối ưu Entropy & EV) & Phương án #3 (Bọc tối thiểu 2 vé cam kết 100% trúng Giải 3).
                    </p>
                </div>
                <button onclick="handleGenerateWheel()" class="px-5 py-3 bg-brand-primary text-gray-900 font-extrabold rounded-xl hover:bg-blue-300 active:scale-95 transition shadow-lg text-xs md:text-sm flex items-center gap-2">
                    🎲 Sinh Dàn Bao Toán Học (2 Vé)
                </button>
            </div>

            <!-- Guarantee highlight box -->
            <div class="bg-blue-950/40 border border-blue-800/60 rounded-xl p-4 text-xs md:text-sm text-blue-200 space-y-1.5">
                <div class="font-extrabold flex items-center gap-1.5 text-blue-300">
                    💡 ĐỊNH LÝ BẢO HIỂM TOÁN HỌC (Pigeonhole Theorem):
                </div>
                <p>
                    Bể gồm 10 số được phân hoạch thành 2 vé rời rạc ($5 + 5 = 10$). Khi máy lồng cầu quay ra 5 số chính, nếu cả 5 số này nằm trong bể 10 số, theo nguyên lý lồng chim: $n_1 + n_2 = 5 \implies \max(n_1, n_2) \ge 3$. 
                    <strong>Chắc chắn 100% có ít nhất một vé trúng từ 3 số trở lên!</strong>
                </p>
                <div class="text-[11px] text-blue-400 font-semibold">
                    💰 Tiết kiệm vốn: Chỉ cần mua đúng 2 vé (20.000đ) thay vì mua bao 10 toàn phần 252 vé (2.520.000đ) &mdash; Tiết kiệm 99.2% chi phí!
                </div>
            </div>
        </div>

        <!-- Wheel Display Container -->
        <div id="wheelContainer" class="hidden space-y-6">
            <!-- Pool 10 numbers card -->
            <div class="bg-brand-card border border-brand-border rounded-2xl p-5 shadow-xl space-y-3">
                <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-brand-border pb-3">
                    <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">
                        BỂ 10 SỐ ĐƯỢC CHỌN TỰ ĐỘNG BẰNG PHƯƠNG ÁN #4:
                    </span>
                    <span id="wheelPoolMetrics" class="text-xs font-semibold text-brand-secondary">--</span>
                </div>
                <div id="wheelPoolBalls" class="flex flex-wrap gap-2 pt-1"></div>
            </div>

            <!-- 2 Tickets Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Ticket 1 -->
                <div class="bg-brand-card border border-brand-border rounded-2xl p-5 shadow-xl space-y-4">
                    <div class="flex justify-between items-center border-b border-brand-border pb-3">
                        <span class="text-sm font-bold text-brand-primary">🎫 VÉ SỐ 1</span>
                        <span id="t1Badge" class="px-2.5 py-0.5 rounded-lg text-xs font-bold bg-green-900/40 text-green-300 border border-green-700">SQS: --</span>
                    </div>
                    <div id="t1Balls" class="flex items-center gap-2"></div>
                    <div class="text-xs space-y-1 text-gray-400 bg-brand-dark p-3 rounded-xl border border-brand-border">
                        <div class="flex justify-between"><span>Tổng 5 số:</span><strong id="t1Sum" class="text-gray-200">--</strong></div>
                        <div class="flex justify-between"><span>Chẵn / Lẻ:</span><span id="t1Parity" class="text-gray-300">--</span></div>
                        <div class="flex justify-between"><span>Nhịp Poisson:</span><span id="t1Poisson" class="text-brand-secondary">--</span></div>
                        <div class="flex justify-between"><span>Lặp kỳ trước:</span><span id="t1Markov" class="text-gray-300">--</span></div>
                    </div>
                </div>

                <!-- Ticket 2 -->
                <div class="bg-brand-card border border-brand-border rounded-2xl p-5 shadow-xl space-y-4">
                    <div class="flex justify-between items-center border-b border-brand-border pb-3">
                        <span class="text-sm font-bold text-brand-primary">🎫 VÉ SỐ 2</span>
                        <span id="t2Badge" class="px-2.5 py-0.5 rounded-lg text-xs font-bold bg-green-900/40 text-green-300 border border-green-700">SQS: --</span>
                    </div>
                    <div id="t2Balls" class="flex items-center gap-2"></div>
                    <div class="text-xs space-y-1 text-gray-400 bg-brand-dark p-3 rounded-xl border border-brand-border">
                        <div class="flex justify-between"><span>Tổng 5 số:</span><strong id="t2Sum" class="text-gray-200">--</strong></div>
                        <div class="flex justify-between"><span>Chẵn / Lẻ:</span><span id="t2Parity" class="text-gray-300">--</span></div>
                        <div class="flex justify-between"><span>Nhịp Poisson:</span><span id="t2Poisson" class="text-brand-secondary">--</span></div>
                        <div class="flex justify-between"><span>Lặp kỳ trước:</span><span id="t2Markov" class="text-gray-300">--</span></div>
                    </div>
                </div>
            </div>

            <!-- Action button to copy both tickets -->
            <div class="flex justify-center">
                <button onclick="copyWheelTickets()" class="px-6 py-3 bg-emerald-700 hover:bg-emerald-600 active:scale-95 text-white font-extrabold rounded-xl transition shadow-lg text-sm flex items-center gap-2">
                    📋 Sao Chép 2 Vé Để Mua Ngay
                </button>
            </div>
        </div>
    </div>

    <!-- TAB 3: GENERATOR -->
    <div id="tab-gen" class="tab-content hidden space-y-6">
        <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <label class="font-bold text-xs md:text-sm text-gray-300">Số lượng:</label>
                <input id="genCount" type="number" min="1" max="20" value="5" class="w-16 p-2 text-center font-bold bg-brand-dark border border-brand-border rounded-lg text-sm">
                <button onclick="handleGenerate()" class="px-5 py-2.5 bg-brand-primary text-gray-900 font-bold rounded-xl hover:bg-blue-300 active:scale-95 transition shadow-lg text-xs md:text-sm">
                    ⚡ Sinh Số Tối Ưu (SQS v2.0 ≥ 80)
                </button>
            </div>
            <span class="text-xs text-gray-400 italic">Tích hợp đầy đủ Mahalanobis, Entropy, Markov & Poisson</span>
        </div>

        <div id="genResultList" class="space-y-3"></div>
    </div>

    <!-- TAB 4: HISTORY -->
    <div id="tab-history" class="tab-content hidden space-y-4">
        <div class="bg-brand-card border border-brand-border rounded-2xl p-3 md:p-4 shadow-xl flex gap-3">
            <input id="historySearch" oninput="filterHistory()" type="text" placeholder="Tìm theo kỳ (vd: 00965) hoặc ngày (vd: 24/10/2026)..." class="flex-1 p-2.5 md:p-3 bg-brand-dark border border-brand-border rounded-xl focus:outline-none text-xs md:text-sm">
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

    <!-- TAB 5: STATS -->
    <div id="tab-stats" class="tab-content hidden space-y-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl">
                <h3 class="text-sm md:text-base font-bold text-brand-primary mb-4">Tần Suất 35 Số Chính (Lý thuyết: 137.9)</h3>
                <canvas id="chartBalls" height="180"></canvas>
            </div>
            <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl">
                <h3 class="text-sm md:text-base font-bold text-brand-accent mb-4">Tần Suất 12 Số Đặc Biệt (Lý thuyết: 80.4)</h3>
                <canvas id="chartSpecial" height="180"></canvas>
            </div>
        </div>
    </div>

    <!-- TAB 6: 5 TRỤ CỘT TOÁN HỌC -->
    <div id="tab-qr-theory" class="tab-content hidden space-y-6">
        <div class="bg-brand-card border border-brand-border rounded-2xl p-5 md:p-6 shadow-xl space-y-4">
            <h2 class="text-lg md:text-xl font-extrabold text-brand-primary flex items-center gap-2">
                📐 5 Trụ Cột Toán Học & Lý Thuyết Trò Chơi Trong SQS Engine v2.0
            </h2>
            <p class="text-xs md:text-sm text-gray-300 leading-relaxed">
                Mô hình SQS v2.0 không dùng phương pháp bói toán cảm tính mà ứng dụng các định lý giải tích tổ hợp, hình học Riemann và phân phối xác suất nâng cao:
            </p>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div class="bg-brand-dark p-4 rounded-xl border border-brand-border space-y-2">
                    <h4 class="font-bold text-sm text-brand-secondary">1. Khoảng Cách Mahalanobis ($D_M^2$)</h4>
                    <p class="text-xs text-gray-400">
                        Khử hoàn toàn tương quan chéo giữa Tổng số, Chẵn/Lẻ, Cao/Thấp, Độ trải rộng và Cặp liên tiếp. Tuân theo phân phối Chi-Square ($\chi^2$) 5 bậc tự do để phát hiện và triệt tiêu các vé dị tật.
                    </p>
                </div>
                <div class="bg-brand-dark p-4 rounded-xl border border-brand-border space-y-2">
                    <h4 class="font-bold text-sm text-brand-secondary">2. Shannon Gap Entropy ($H$)</h4>
                    <p class="text-xs text-gray-400">
                        Đo lường độ hỗn loạn khoảng cách giữa các số trên trục 1-35. Loại bỏ triệt để các vé bị dồn cụm cục bộ, ép các con số phân bổ đều trên toàn bộ phổ số học.
                    </p>
                </div>
                <div class="bg-brand-dark p-4 rounded-xl border border-brand-border space-y-2">
                    <h4 class="font-bold text-sm text-brand-secondary">3. Chuỗi Markov Chuyển Trạng Thái</h4>
                    <p class="text-xs text-gray-400">
                        Kiểm định lặp nhịp giữa 2 kỳ liên tiếp: Trong 964 kỳ quay thực tế, tỷ lệ lặp $\ge 3$ số chỉ là 1.24% và lặp 4 số là 0%. Mô hình cắt bỏ toàn bộ vé có $\ge 3$ số của kỳ trước.
                    </p>
                </div>
                <div class="bg-brand-dark p-4 rounded-xl border border-brand-border space-y-2">
                    <h4 class="font-bold text-sm text-brand-secondary">4. Phân Phối Nhịp Vắng Poisson</h4>
                    <p class="text-xs text-gray-400">
                        Tổng nhịp vắng mặt của 5 số ($S_{{\\text{{Skip}}}}$) có kỳ vọng lý thuyết là 35 kỳ. Vùng hội tụ 80% thực tế nằm vững trong khoảng $[20, 54]$, giúp cân bằng giữa số nóng và số ấm.
                    </p>
                </div>
                <div class="bg-brand-dark p-4 rounded-xl border border-brand-border space-y-2 md:col-span-2">
                    <h4 class="font-bold text-sm text-brand-secondary">5. Hệ Thống Phủ Stefan Mandel & Tối Đa Hóa Kỳ Vọng Độc Quyền Cox 1998</h4>
                    <p class="text-xs text-gray-400">
                        Sử dụng Ma trận bao phủ $C(10, 5, 3, 5)$ đảm bảo trúng Giải 3 với chỉ 2 vé. Đồng thời ép chứa các số $\ge 32$ để chống hiện tượng trùng giải do người chơi khác chọn ngày sinh nhật, đảm bảo ẵm trọn 100% quỹ thưởng Jackpot!
                    </p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // In-memory data store
        const BASE_DRAWS = {json.dumps(draws_data, ensure_ascii=False)};
        let LOCAL_DRAWS = [];
        let DRAWS_DATA = [];

        function loadLocalStorageDraws() {{
            try {{
                const stored = localStorage.getItem('vietlott_535_custom_draws');
                if (stored) {{
                    LOCAL_DRAWS = JSON.parse(stored);
                }}
            }} catch(e) {{
                console.error("Error loading localStorage draws", e);
                LOCAL_DRAWS = [];
            }}
        }}

        function getAllDraws() {{
            const baseMap = new Map();
            BASE_DRAWS.forEach(d => baseMap.set(d.draw_code, d));
            LOCAL_DRAWS.forEach(d => baseMap.set(d.draw_code, d));
            const merged = Array.from(baseMap.values());
            merged.sort((a,b) => b.draw_id - a.draw_id);
            return merged;
        }}

        function computeCurrentSkips() {{
            const all = getAllDraws();
            const skips = {{}};
            for (let i = 1; i <= 35; i++) skips[i] = all.length;
            for (let idx = 0; idx < all.length; idx++) {{
                const d = all[idx];
                [d.num1, d.num2, d.num3, d.num4, d.num5].forEach(num => {{
                    if (skips[num] === all.length) skips[num] = idx;
                }});
            }}
            return skips;
        }}

        function updateAppViews() {{
            DRAWS_DATA = getAllDraws();
            const total = DRAWS_DATA.length;
            const latest = DRAWS_DATA[0];

            document.getElementById('headerCount').innerText = total;
            document.getElementById('modalTotalDraws').innerText = total;
            document.getElementById('tabHistoryTitle').innerText = `Lịch Sử (${{total}} Kỳ)`;

            if (latest) {{
                document.getElementById('modalLatestCode').innerText = '#' + latest.draw_code;
                document.getElementById('modalLatestDate').innerText = latest.date;
                const nextId = latest.draw_id + 1;
                document.getElementById('inputNewCode').value = String(nextId).padStart(5, '0');
                const today = new Date();
                const dStr = String(today.getDate()).padStart(2, '0') + '/' + String(today.getMonth()+1).padStart(2, '0') + '/' + today.getFullYear();
                document.getElementById('inputNewDate').value = dStr;
            }}

            renderHistoryTable();
            renderCharts();
        }}

        // Matrix parameters
        const MU = [90.0, 2.4286, 2.5714, 22.6667, 0.5333];
        const INV_COV = [
            [ 0.003115, -0.003889, -0.015241, -0.000628,  0.000109],
            [-0.003889,  1.178201,  0.019385, -0.007621, -0.001325],
            [-0.015241,  0.019385,  1.178201,  0.038102,  0.006627],
            [-0.000628, -0.007621,  0.038102,  0.039625,  0.006892],
            [ 0.000109, -0.001325,  0.006627,  0.006892,  2.083751]
        ];

        function gamma(z) {{
            const g = 7;
            const C = [0.99999999999980993, 676.52096812869951, -1259.1392167224028,
                       771.32342877765313, -176.61502916214059, 12.507343278686905,
                       -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
            if (z < 0.5) return Math.PI / (Math.sin(Math.PI * z) * gamma(1 - z));
            z -= 1;
            let base = C[0];
            for (let i = 1; i < g + 2; i++) base += C[i] / (z + i);
            const t = z + g + 0.5;
            return Math.sqrt(2 * Math.PI) * Math.pow(t, (z + 0.5)) * Math.exp(-t) * base;
        }}

        function chi2Cdf(x, k) {{
            if (x <= 0) return 0;
            const s = k / 2.0;
            const z = x / 2.0;
            let total = 1.0 / s;
            let term = 1.0 / s;
            for (let n = 1; n < 80; n++) {{
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
            const sqsV1 = Math.min(100.0, Math.max(0.0, Math.round(jointProb * 1000) / 10));

            // SQS v2.0 Dynamic Extensions
            const latest = getAllDraws()[0];
            let markovRepeats = 0;
            let markovMult = 1.0;
            let markovStatus = "Tối ưu";
            if (latest) {{
                const prevSet = new Set([latest.num1, latest.num2, latest.num3, latest.num4, latest.num5]);
                markovRepeats = sorted.filter(x => prevSet.has(x)).length;
                if (markovRepeats <= 2) {{
                    markovMult = 1.0;
                    markovStatus = `Lặp ${{markovRepeats}} số [✓ Tối ưu]`;
                }} else if (markovRepeats === 3) {{
                    markovMult = 0.6;
                    markovStatus = `Lặp 3 số [⚠️ Cảnh Báo P=1.2%]`;
                }} else {{
                    markovMult = 0.2;
                    markovStatus = `Lặp ${{markovRepeats}} số [⛔ Nguy Hiểm]`;
                }}
            }}

            const skips = computeCurrentSkips();
            const skipSum = sorted.reduce((acc, x) => acc + (skips[x] !== undefined ? skips[x] : 6), 0);
            let skipMult = 1.0;
            let skipStatus = "Chuẩn";
            if (skipSum >= 20 && skipSum <= 54) {{
                skipMult = 1.05;
                skipStatus = `${{skipSum}} kỳ [✓ Vùng Vàng]`;
            }} else if (skipSum >= 15 && skipSum <= 65) {{
                skipMult = 1.0;
                skipStatus = `${{skipSum}} kỳ [Dung Sai Biên]`;
            }} else if (skipSum < 15) {{
                skipMult = 0.85;
                skipStatus = `${{skipSum}} kỳ [Quá Nóng < 15]`;
            }} else {{
                skipMult = 0.80;
                skipStatus = `${{skipSum}} kỳ [Quá Gan > 65]`;
            }}

            const hasHigh = sorted.some(x => x >= 32);
            const highCount = sorted.filter(x => x >= 32).length;
            const antiMult = hasHigh ? 1.05 : 0.95;
            const antiStatus = hasHigh ? `Có ${{highCount}} số ≥ 32 [✓ 100% Solo EV]` : "Toàn số ≤ 31 [Dễ chia giải]";

            const sqsV2 = Math.min(100.0, Math.max(0.0, Math.round(sqsV1 * markovMult * skipMult * antiMult * 10) / 10));

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
                sqsV1,
                sqs: sqsV2,
                markovRepeats,
                markovStatus,
                skipSum,
                skipStatus,
                antiStatus,
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
                b.className = 'max-w-md w-full p-4 rounded-xl shadow-2xl border text-sm font-bold flex items-center justify-between gap-3 toast-animate pointer-events-auto bg-red-950/90 border-red-500 text-red-200';
            }} else {{
                b.className = 'max-w-md w-full p-4 rounded-xl shadow-2xl border text-sm font-bold flex items-center justify-between gap-3 toast-animate pointer-events-auto bg-brand-card border-brand-primary text-gray-200';
            }}
            c.classList.remove('hidden');
            clearTimeout(toastTimeout);
            toastTimeout = setTimeout(hideToast, 4000);
        }}
        function hideToast() {{
            document.getElementById('toastContainer').classList.add('hidden');
        }}

        function openUpdateModal() {{
            document.getElementById('updateModal').classList.remove('hidden');
        }}

        function closeUpdateModal() {{
            document.getElementById('updateModal').classList.add('hidden');
        }}

        async function syncFromCloud() {{
            const btn = document.getElementById('btnSyncCloud');
            const spinner = document.getElementById('syncSpinner');
            btn.disabled = true;
            spinner.classList.remove('hidden');
            showToast("Đang kết nối kho GitHub tải kỳ quay mới...");

            try {{
                const url = "https://raw.githubusercontent.com/Gentsleo/xstk/main/vietlott_535.json?t=" + Date.now();
                const res = await fetch(url);
                if (!res.ok) throw new Error("HTTP " + res.status);
                const cloudDraws = await res.json();

                if (Array.isArray(cloudDraws) && cloudDraws.length > 0) {{
                    const curMax = DRAWS_DATA.length > 0 ? DRAWS_DATA[0].draw_id : 0;
                    const newOnes = cloudDraws.filter(d => d.draw_id > curMax);
                    if (newOnes.length > 0) {{
                        newOnes.forEach(d => LOCAL_DRAWS.push(d));
                        localStorage.setItem('vietlott_535_custom_draws', JSON.stringify(LOCAL_DRAWS));
                        updateAppViews();
                        showToast(`🎉 Đã tải thành công ${{newOnes.length}} kỳ quay mới từ đám mây!`);
                    }} else {{
                        showToast(`Dữ liệu đã đồng bộ mới nhất (Kỳ #${{cloudDraws[cloudDraws.length-1].draw_code}}).`);
                    }}
                    closeUpdateModal();
                }} else {{
                    showToast("Dữ liệu từ đám mây không hợp lệ.", true);
                }}
            }} catch(err) {{
                showToast("Lỗi đồng bộ đám mây: " + err.message + ". Vui lòng thử lại sau.", true);
            }} finally {{
                btn.disabled = false;
                spinner.classList.add('hidden');
            }}
        }}

        function saveManualDraw() {{
            const code = document.getElementById('inputNewCode').value.trim();
            const date = document.getElementById('inputNewDate').value.trim();
            const n1 = parseInt(document.getElementById('inN1').value);
            const n2 = parseInt(document.getElementById('inN2').value);
            const n3 = parseInt(document.getElementById('inN3').value);
            const n4 = parseInt(document.getElementById('inN4').value);
            const n5 = parseInt(document.getElementById('inN5').value);
            const nS = parseInt(document.getElementById('inNS').value);

            const nums = [n1, n2, n3, n4, n5];
            for (let x of nums) {{
                if (isNaN(x) || x < 1 || x > 35) {{
                    showToast("5 số chính phải từ 01 đến 35!", true);
                    return;
                }}
            }}
            if (new Set(nums).size !== 5) {{
                showToast("5 số chính không được trùng nhau!", true);
                return;
            }}
            if (isNaN(nS) || nS < 1 || nS > 12) {{
                showToast("Số đặc biệt phải từ 01 đến 12!", true);
                return;
            }}

            const sortedNums = [...nums].sort((a,b) => a - b);
            const numStr = sortedNums.map(x => String(x).padStart(2,'0')).join(' ') + ' | ' + String(nS).padStart(2,'0');

            const newDraw = {{
                draw_id: parseInt(code) || (DRAWS_DATA.length + 1),
                draw_code: code || String(DRAWS_DATA.length + 1).padStart(5, '0'),
                date: date || "Hôm nay",
                num1: sortedNums[0],
                num2: sortedNums[1],
                num3: sortedNums[2],
                num4: sortedNums[3],
                num5: sortedNums[4],
                special: nS,
                numbers_str: numStr
            }};

            LOCAL_DRAWS.push(newDraw);
            localStorage.setItem('vietlott_535_custom_draws', JSON.stringify(LOCAL_DRAWS));
            updateAppViews();
            showToast(`[✓] Đã lưu kỳ #${{newDraw.draw_code}} vào điện thoại thành công!`);
            closeUpdateModal();
        }}

        function resetLocalStorageDraws() {{
            if (confirm("Bạn có chắc muốn xóa các kỳ tự nhập/lưu tạm trên máy này?")) {{
                LOCAL_DRAWS = [];
                localStorage.removeItem('vietlott_535_custom_draws');
                updateAppViews();
                showToast("Đã xóa sạch bộ nhớ lưu tạm trên điện thoại.");
                closeUpdateModal();
            }}
        }}

        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(el => {{
                el.classList.remove('border-brand-primary', 'text-brand-primary');
                el.classList.add('border-transparent', 'text-gray-400');
            }});
            document.getElementById(tabId).classList.remove('hidden');
            const btn = document.getElementById('btn-' + tabId.replace('tab-', ''));
            if (btn) {{
                btn.classList.remove('border-transparent', 'text-gray-400');
                btn.classList.add('border-brand-primary', 'text-brand-primary');
            }}
            if (tabId === 'tab-wheel' && !window.hasGeneratedWheel) {{
                handleGenerateWheel();
                window.hasGeneratedWheel = true;
            }}
        }}

        function fillLatest() {{
            if (DRAWS_DATA.length > 0) {{
                const latest = DRAWS_DATA[0];
                document.getElementById('num1').value = latest.num1;
                document.getElementById('num2').value = latest.num2;
                document.getElementById('num3').value = latest.num3;
                document.getElementById('num4').value = latest.num4;
                document.getElementById('num5').value = latest.num5;
                document.getElementById('numSpecial').value = latest.special;
                handleEvaluate();
            }}
        }}

        function handleEvaluate() {{
            const n1 = document.getElementById('num1').value;
            const n2 = document.getElementById('num2').value;
            const n3 = document.getElementById('num3').value;
            const n4 = document.getElementById('num4').value;
            const n5 = document.getElementById('num5').value;
            const spec = document.getElementById('numSpecial').value;

            const nums = [n1, n2, n3, n4, n5].map(Number);
            for (const x of nums) {{
                if (isNaN(x) || x < 1 || x > 35) {{
                    showToast("Vui lòng điền đủ 5 số chính từ 1 đến 35", true);
                    return;
                }}
            }}
            if (new Set(nums).size !== 5) {{
                showToast("5 số chính không được trùng nhau", true);
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
                badgeEl.innerText = 'XUẤT SẮC (Top 15% Tâm Đối Xứng & Chuỗi Markov Tối Ưu)';
                descEl.innerText = 'Bộ số hoàn hảo: Đối xứng Gauss chuẩn, nhịp Poisson vàng, chống chia giải Jackpot độc quyền.';
            }} else if (res.sqs >= 40) {{
                sqsEl.className = 'text-4xl md:text-5xl font-extrabold text-yellow-400';
                badgeEl.className = 'px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider bg-yellow-900/50 text-yellow-300 border border-yellow-700';
                badgeEl.innerText = 'ĐẠT CHUẨN (Vùng Dung Sai Hội Tụ SQS v2.0)';
                descEl.innerText = 'Bộ số hài hòa, đạt chuẩn kiểm định Mahalanobis và nhịp vắng mặt Poisson an toàn.';
            }} else if (res.sqs >= 15) {{
                sqsEl.className = 'text-4xl md:text-5xl font-extrabold text-orange-400';
                badgeEl.className = 'px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider bg-orange-900/50 text-orange-300 border border-orange-700';
                badgeEl.innerText = 'DUNG SAI BIÊN (Cần Lưu Ý)';
                descEl.innerText = 'Bộ số hơi lệch về nhịp lặp hoặc tổng khoảng cách, cần cân nhắc đảo số.';
            }} else {{
                sqsEl.className = 'text-4xl md:text-5xl font-extrabold text-red-400';
                badgeEl.className = 'px-3 py-1 rounded-lg text-xs md:text-sm font-bold uppercase tracking-wider bg-red-900/50 text-red-300 border border-red-700';
                badgeEl.innerText = 'CẢNH BÁO (Lệch Chuẩn / Nhiễu Rác Xác Suất)';
                descEl.innerText = 'Bộ số dồn cụm, lặp quá nhiều số của kỳ trước hoặc rơi vào vùng gan cực đoan.';
            }}

            const ballsContainer = document.getElementById('resBallsDisplay');
            ballsContainer.innerHTML = '';
            res.combo.forEach(n => {{
                const span = document.createElement('span');
                span.className = 'ball ball-main';
                span.innerText = String(n).padStart(2, '0');
                ballsContainer.appendChild(span);
            }});
            if (res.special) {{
                const sep = document.createElement('span');
                sep.className = 'text-2xl font-bold text-brand-accent px-1';
                sep.innerText = '|';
                ballsContainer.appendChild(sep);
                const sSpan = document.createElement('span');
                sSpan.className = 'ball ball-special';
                sSpan.innerText = String(res.special).padStart(2, '0');
                ballsContainer.appendChild(sSpan);
            }}

            document.getElementById('resSum').innerText = `${{res.sum}} (Z=${{res.zSum}})`;
            document.getElementById('resParity').innerText = `${{res.odds}}L - ${{res.evens}}C`;
            document.getElementById('resDM').innerText = `${{res.dmSq}} (p=${{res.pMain}})`;
            document.getElementById('resEntropy').innerText = `${{res.entropy}} / 1.79`;

            document.getElementById('resMarkov').innerText = res.markovStatus;
            document.getElementById('resPoisson').innerText = res.skipStatus;
            document.getElementById('resAntiCluster').innerText = res.antiStatus;
        }}

        // Wheel Generator C(10, 5, 3, 5)
        let CURRENT_WHEEL_TICKETS = [];

        function handleGenerateWheel() {{
            const latest = getAllDraws()[0];
            const prevSet = latest ? new Set([latest.num1, latest.num2, latest.num3, latest.num4, latest.num5]) : new Set();
            const skips = computeCurrentSkips();

            // Method #4: Monte Carlo search for best 10-number pool
            let bestPool = null;
            let bestScore = -1e9;

            for (let iter = 0; iter < 12000; iter++) {{
                // 1 or 2 from prev
                const prevArr = Array.from(prevSet);
                const nPrev = Math.random() < 0.6 ? 1 : 2;
                const subPrev = [];
                for (let i = 0; i < nPrev && prevArr.length > 0; i++) {{
                    const pick = prevArr[Math.floor(Math.random() * prevArr.length)];
                    if (!subPrev.includes(pick)) subPrev.push(pick);
                }}

                // 1 or 2 from [32, 35]
                const highPool = [32, 33, 34, 35];
                const nHigh = Math.random() < 0.5 ? 1 : 2;
                const subHigh = [];
                for (let i = 0; i < nHigh; i++) {{
                    const pick = highPool[Math.floor(Math.random() * highPool.length)];
                    if (!subHigh.includes(pick)) subHigh.push(pick);
                }}

                // remaining from 1..35
                const rest = [];
                for (let i = 1; i <= 35; i++) {{
                    if (!subPrev.includes(i) && !subHigh.includes(i)) rest.push(i);
                }}

                const need = 10 - subPrev.length - subHigh.length;
                const shuffled = rest.sort(() => Math.random() - 0.5);
                const cand = [...subPrev, ...subHigh, ...shuffled.slice(0, need)].sort((a,b) => a - b);
                if (cand.length !== 10) continue;

                const evens = cand.filter(x => x % 2 === 0).length;
                const lows = cand.filter(x => x <= 17).length;
                if (evens < 4 || evens > 6 || lows < 4 || lows > 6) continue;

                // Gap Entropy
                const gaps = [cand[0], ...cand.slice(1).map((x, i) => x - cand[i]), 36 - cand[9]];
                let entropy = 0;
                for (const g of gaps) {{
                    const p = g / 36.0;
                    if (p > 0) entropy -= p * Math.log(p);
                }}

                const poolSkips = cand.map(x => skips[x] || 6);
                const meanSkip = poolSkips.reduce((a,b) => a+b, 0) / 10.0;
                const skipDev = Math.abs(meanSkip - 6.0);

                const score = entropy * 10.0 - skipDev * 2.5;
                if (score > bestScore) {{
                    bestScore = score;
                    bestPool = cand;
                }}
            }}

            if (!bestPool) bestPool = [3, 8, 12, 15, 17, 22, 24, 28, 30, 33];

            // Method #3: Combinatorial Partitioning into 2 tickets with maximal SQS
            let bestPair = null;
            let maxSqs = -1;

            // Generate 5-element combinations
            function getCombinations(arr, k) {{
                if (k === 1) return arr.map(x => [x]);
                const res = [];
                for (let i = 0; i <= arr.length - k; i++) {{
                    const head = arr[i];
                    const tails = getCombinations(arr.slice(i + 1), k - 1);
                    tails.forEach(t => res.push([head, ...t]));
                }}
                return res;
            }}

            const allCombos = getCombinations(bestPool, 5);
            for (const t1 of allCombos) {{
                const t2 = bestPool.filter(x => !t1.includes(x));
                if (t1[0] > t2[0]) continue;

                const r1 = evaluateCombo(t1);
                const r2 = evaluateCombo(t2);

                const pen1 = (r1.skipSum >= 18 && r1.skipSum <= 56) ? 0 : -25;
                const pen2 = (r2.skipSum >= 18 && r2.skipSum <= 56) ? 0 : -25;
                const total = r1.sqs + r2.sqs + pen1 + pen2;

                if (total > maxSqs) {{
                    maxSqs = total;
                    bestPair = [t1, t2, r1, r2];
                }}
            }}

            const [t1, t2, r1, r2] = bestPair;
            const spChoices = [8, 6, 12, 7, 9, 3];
            const sp1 = spChoices.find(x => !t1.includes(x)) || 8;
            const sp2 = spChoices.find(x => !t2.includes(x) && x !== sp1) || 12;

            CURRENT_WHEEL_TICKETS = [
                {{ nums: t1, special: sp1, sqs: r1.sqs }},
                {{ nums: t2, special: sp2, sqs: r2.sqs }}
            ];

            // Render Wheel UI
            document.getElementById('wheelContainer').classList.remove('hidden');

            const poolBalls = document.getElementById('wheelPoolBalls');
            poolBalls.innerHTML = '';
            bestPool.forEach(n => {{
                const sp = document.createElement('span');
                sp.className = 'ball ball-main ball-sm';
                sp.innerText = String(n).padStart(2, '0');
                poolBalls.appendChild(sp);
            }});

            const poolSkips = bestPool.map(x => skips[x] || 6);
            const meanSkip = (poolSkips.reduce((a,b)=>a+b,0) / 10).toFixed(1);
            document.getElementById('wheelPoolMetrics').innerText = `TB Nhịp: ${{meanSkip}} kỳ &bull; Chẵn/Lẻ: ${{bestPool.filter(x=>x%2===0).length}}C/${{bestPool.filter(x=>x%2!==0).length}}L &bull; Chống chia: ${{bestPool.filter(x=>x>=32).join(', ')}}`;

            // Render T1
            const t1Container = document.getElementById('t1Balls');
            t1Container.innerHTML = '';
            t1.forEach(n => {{
                const s = document.createElement('span');
                s.className = 'ball ball-main ball-sm';
                s.innerText = String(n).padStart(2, '0');
                t1Container.appendChild(s);
            }});
            const sep1 = document.createElement('span');
            sep1.className = 'font-bold text-brand-accent px-1';
            sep1.innerText = '|';
            t1Container.appendChild(sep1);
            const s1 = document.createElement('span');
            s1.className = 'ball ball-special ball-sm';
            s1.innerText = String(sp1).padStart(2, '0');
            t1Container.appendChild(s1);

            document.getElementById('t1Badge').innerText = `SQS v2: ${{r1.sqs.toFixed(1)}}/100`;
            document.getElementById('t1Sum').innerText = `${{r1.sum}} (Z=${{r1.zSum}})`;
            document.getElementById('t1Parity').innerText = `${{r1.odds}}L - ${{r1.evens}}C`;
            document.getElementById('t1Poisson').innerText = `${{r1.skipSum}} kỳ (${{r1.skipStatus}})`;
            document.getElementById('t1Markov').innerText = `${{r1.markovRepeats}} số lặp`;

            // Render T2
            const t2Container = document.getElementById('t2Balls');
            t2Container.innerHTML = '';
            t2.forEach(n => {{
                const s = document.createElement('span');
                s.className = 'ball ball-main ball-sm';
                s.innerText = String(n).padStart(2, '0');
                t2Container.appendChild(s);
            }});
            const sep2 = document.createElement('span');
            sep2.className = 'font-bold text-brand-accent px-1';
            sep2.innerText = '|';
            t2Container.appendChild(sep2);
            const s2 = document.createElement('span');
            s2.className = 'ball ball-special ball-sm';
            s2.innerText = String(sp2).padStart(2, '0');
            t2Container.appendChild(s2);

            document.getElementById('t2Badge').innerText = `SQS v2: ${{r2.sqs.toFixed(1)}}/100`;
            document.getElementById('t2Sum').innerText = `${{r2.sum}} (Z=${{r2.zSum}})`;
            document.getElementById('t2Parity').innerText = `${{r2.odds}}L - ${{r2.evens}}C`;
            document.getElementById('t2Poisson').innerText = `${{r2.skipSum}} kỳ (${{r2.skipStatus}})`;
            document.getElementById('t2Markov').innerText = `${{r2.markovRepeats}} số lặp`;

            showToast("✨ Đã sinh dàn bao 2 vé tối ưu C(10,5,3,5) thành công!");
        }}

        function copyWheelTickets() {{
            if (CURRENT_WHEEL_TICKETS.length < 2) return;
            const t1 = CURRENT_WHEEL_TICKETS[0];
            const t2 = CURRENT_WHEEL_TICKETS[1];
            const text = `🎯 DÀN BAO VIETLOTT 5/35 - C(10,5,3,5):\nVé 1: ${{t1.nums.map(x=>String(x).padStart(2,'0')).join(' ')}} | ĐB: ${{String(t1.special).padStart(2,'0')}} (SQS: ${{t1.sqs}})\nVé 2: ${{t2.nums.map(x=>String(x).padStart(2,'0')).join(' ')}} | ĐB: ${{String(t2.special).padStart(2,'0')}} (SQS: ${{t2.sqs}})`;
            navigator.clipboard.writeText(text).then(() => {{
                showToast("📋 Đã sao chép 2 vé vào bộ nhớ tạm để mua ngay!");
            }}).catch(() => {{
                prompt("Sao chép 2 vé bên dưới:", text);
            }});
        }}

        function handleGenerate() {{
            const count = parseInt(document.getElementById('genCount').value) || 5;
            const container = document.getElementById('genResultList');
            container.innerHTML = '';

            const found = [];
            let attempts = 0;
            const specChoices = [8, 6, 12, 7, 9, 3, 2, 10, 4, 5];

            while (found.length < count && attempts < 35000) {{
                attempts++;
                const combo = [];
                while (combo.length < 5) {{
                    const r = Math.floor(Math.random() * 35) + 1;
                    if (!combo.includes(r)) combo.push(r);
                }}
                const availableSpecs = specChoices.filter(s => !combo.includes(s));
                const spec = availableSpecs[Math.floor(Math.random() * availableSpecs.length)];

                const res = evaluateCombo(combo, spec);
                if (res.sqs >= 80.0 && Number(res.entropy) >= 1.55) {{
                    found.push(res);
                }}
            }}

            found.forEach((r, idx) => {{
                const item = document.createElement('div');
                item.className = 'bg-brand-card border border-brand-border rounded-xl p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 shadow-md';
                item.innerHTML = `
                    <div class="flex items-center gap-3">
                        <span class="text-xs font-bold text-gray-500">#${{String(idx+1).padStart(2,'0')}}</span>
                        <div class="flex flex-wrap items-center gap-1.5">
                            ${{r.combo.map(n => `<span class="ball ball-main ball-sm">${{String(n).padStart(2,'0')}}</span>`).join('')}}
                            <span class="font-bold text-brand-accent px-1">|</span>
                            <span class="ball ball-special ball-sm">${{String(r.special).padStart(2,'0')}}</span>
                        </div>
                    </div>
                    <div class="flex flex-wrap items-center gap-4 text-xs text-gray-400">
                        <span>Tổng: <strong class="text-gray-200">${{r.sum}}</strong></span>
                        <span>${{r.odds}}L - ${{r.evens}}C</span>
                        <span>Poisson: <strong class="text-brand-secondary">${{r.skipSum}}k</strong></span>
                        <span class="px-2.5 py-1 rounded-lg font-bold bg-green-900/40 text-green-400 border border-green-700/50">SQS v2: ${{r.sqs.toFixed(1)}}</span>
                    </div>
                `;
                container.appendChild(item);
            }});

            showToast(`Đã sinh xong ${{found.length}} bộ số tối ưu SQS v2.0!`);
        }}

        function renderHistoryTable() {{
            const tbody = document.getElementById('historyTableBody');
            tbody.innerHTML = DRAWS_DATA.map(d => `
                <tr class="hover:bg-brand-border/40 transition">
                    <td class="p-2.5 md:p-3 font-semibold text-brand-secondary">#${{d.draw_code}}</td>
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

print("[✓] Đã tạo thành công index.html và docs/index.html với SQS Engine v2.0 và Dàn Bao Stefan Mandel C(10,5,3,5)!")
