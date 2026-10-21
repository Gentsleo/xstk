import json
import os

with open("/home/tringuyen/xstk/vietlott_535.json", "r", encoding="utf-8") as f:
    draws_data = json.load(f)

html_content = f"""<!DOCTYPE html>
<html lang="vi" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        }}
        .ball {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 1.1rem;
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
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-6xl mx-auto space-y-6">
        <!-- Header -->
        <header class="bg-brand-card border border-brand-border rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <h1 class="text-2xl md:text-3xl font-extrabold text-brand-primary flex items-center gap-2">
                    🎯 XSTK - Vietlott Lotto 5/35
                </h1>
                <p class="text-sm text-gray-400 mt-1">
                    Mô hình dung sai mã QR (Typical Set) kết hợp Khoảng cách Mahalanobis & Shannon Gap Entropy
                </p>
            </div>
            <div class="flex items-center gap-3">
                <span id="headerStatus" class="px-3 py-1 bg-green-900/40 text-green-400 border border-green-700/50 rounded-full text-xs font-semibold">
                    ● 954 Kỳ Quay Lịch Sử
                </span>
                <a href="https://github.com/Gentsleo/xstk" target="_blank" class="px-4 py-2 bg-brand-border hover:bg-slate-700 rounded-lg text-sm font-bold transition flex items-center gap-2">
                    GitHub Repo
                </a>
            </div>
        </header>

        <!-- Navigation Tabs -->
        <div class="flex border-b border-brand-border gap-2 text-sm font-bold overflow-x-auto">
            <button onclick="switchTab('tab-eval')" id="btn-eval" class="tab-btn px-5 py-3 border-b-2 border-brand-primary text-brand-primary flex items-center gap-2">
                🔍 Đánh Giá Bộ Số
            </button>
            <button onclick="switchTab('tab-gen')" id="btn-gen" class="tab-btn px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-2">
                ⚡ Gợi Ý Bộ Số Chuẩn (SQS ≥ 80)
            </button>
            <button onclick="switchTab('tab-history')" id="btn-history" class="tab-btn px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-2">
                📊 Tra Cứu Lịch Sử (954 Kỳ)
            </button>
            <button onclick="switchTab('tab-stats')" id="btn-stats" class="tab-btn px-5 py-3 border-b-2 border-transparent text-gray-400 hover:text-gray-200 flex items-center gap-2">
                📈 Biểu Đồ & Thống Kê
            </button>
        </div>

        <!-- TAB 1: EVALUATE -->
        <div id="tab-eval" class="tab-content space-y-6">
            <div class="bg-brand-card border border-brand-border rounded-2xl p-6 shadow-xl">
                <h2 class="text-lg font-bold text-brand-primary mb-4">Nhập bộ số để chấm điểm độ chuẩn xác suất</h2>
                <div class="flex flex-wrap items-center gap-3">
                    <input id="num1" type="number" min="1" max="35" placeholder="01" class="w-16 h-12 text-center text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    <input id="num2" type="number" min="1" max="35" placeholder="02" class="w-16 h-12 text-center text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    <input id="num3" type="number" min="1" max="35" placeholder="03" class="w-16 h-12 text-center text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    <input id="num4" type="number" min="1" max="35" placeholder="04" class="w-16 h-12 text-center text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    <input id="num5" type="number" min="1" max="35" placeholder="05" class="w-16 h-12 text-center text-xl font-bold bg-brand-dark border border-brand-border rounded-xl focus:border-brand-primary focus:outline-none">
                    
                    <span class="text-2xl font-bold text-brand-accent px-1">|</span>
                    
                    <input id="numSpecial" type="number" min="1" max="12" placeholder="ĐB" class="w-16 h-12 text-center text-xl font-bold bg-brand-dark border-2 border-brand-accent text-brand-accent rounded-xl focus:outline-none">

                    <button onclick="handleEvaluate()" class="px-6 h-12 bg-brand-primary text-gray-900 font-bold rounded-xl hover:bg-blue-300 transition shadow-lg">
                        🚀 Chấm Điểm Ngay
                    </button>
                    <button onclick="fillLatest()" class="px-4 h-12 bg-slate-800 hover:bg-slate-700 text-gray-300 font-bold rounded-xl transition">
                        Kỳ Mới Nhất (#00954)
                    </button>
                </div>
            </div>

            <!-- Result Scorecard -->
            <div id="evalResultCard" class="hidden bg-brand-card border border-brand-border rounded-2xl p-6 shadow-xl space-y-6">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-brand-border pb-6 gap-4">
                    <div class="flex items-center gap-6">
                        <div class="text-center">
                            <span class="text-xs text-gray-400 block font-semibold">ĐIỂM CHUẨN SQS</span>
                            <span id="resSQS" class="text-5xl font-extrabold text-brand-secondary">-- / 100</span>
                        </div>
                        <div>
                            <span id="resBadge" class="px-3 py-1.5 rounded-lg text-sm font-bold uppercase tracking-wider">--</span>
                            <p id="resDesc" class="text-sm text-gray-300 mt-2 max-w-xl">--</p>
                        </div>
                    </div>
                    <div id="resBallsDisplay" class="flex items-center gap-2"></div>
                </div>

                <!-- Metric Grid -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-brand-dark p-4 rounded-xl border border-brand-border">
                        <span class="text-xs text-gray-400 block">Tổng Điểm 5 Số</span>
                        <span id="resSum" class="text-xl font-bold text-gray-200 mt-1 block">--</span>
                        <span class="text-xs text-gray-500">Lý thuyết: 90 ± 21</span>
                    </div>
                    <div class="bg-brand-dark p-4 rounded-xl border border-brand-border">
                        <span class="text-xs text-gray-400 block">Tỷ Lệ Chẵn / Lẻ</span>
                        <span id="resParity" class="text-xl font-bold text-gray-200 mt-1 block">--</span>
                        <span class="text-xs text-gray-500">Chuẩn: 3L-2C hoặc 2L-3C</span>
                    </div>
                    <div class="bg-brand-dark p-4 rounded-xl border border-brand-border">
                        <span class="text-xs text-gray-400 block">Khoảng Cách Mahalanobis</span>
                        <span id="resDM" class="text-xl font-bold text-gray-200 mt-1 block">--</span>
                        <span class="text-xs text-gray-500">D²_M (k=5)</span>
                    </div>
                    <div class="bg-brand-dark p-4 rounded-xl border border-brand-border">
                        <span class="text-xs text-gray-400 block">Shannon Gap Entropy</span>
                        <span id="resEntropy" class="text-xl font-bold text-gray-200 mt-1 block">--</span>
                        <span class="text-xs text-gray-500">Tối đa: 1.79</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: GENERATOR -->
        <div id="tab-gen" class="tab-content hidden space-y-6">
            <div class="bg-brand-card border border-brand-border rounded-2xl p-6 shadow-xl flex flex-wrap items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <label class="font-bold text-sm text-gray-300">Số lượng bộ số cần tạo:</label>
                    <input id="genCount" type="number" min="1" max="20" value="5" class="w-20 p-2 text-center font-bold bg-brand-dark border border-brand-border rounded-lg">
                    <button onclick="handleGenerate()" class="px-6 py-2.5 bg-brand-primary text-gray-900 font-bold rounded-xl hover:bg-blue-300 transition shadow-lg">
                        ⚡ Sinh Số Tối Ưu (SQS ≥ 80)
                    </button>
                </div>
                <span class="text-xs text-gray-400 italic">Áp dụng bộ lọc dung sai đa chiều Mahalanobis và Shannon Entropy</span>
            </div>

            <div id="genResultList" class="space-y-3"></div>
        </div>

        <!-- TAB 3: HISTORY -->
        <div id="tab-history" class="tab-content hidden space-y-4">
            <div class="bg-brand-card border border-brand-border rounded-2xl p-4 shadow-xl flex gap-4">
                <input id="historySearch" oninput="filterHistory()" type="text" placeholder="Tìm theo kỳ (vd: 00954) hoặc ngày (vd: 18/10/2026)..." class="flex-1 p-3 bg-brand-dark border border-brand-border rounded-xl focus:outline-none">
            </div>
            <div class="bg-brand-card border border-brand-border rounded-2xl shadow-xl overflow-x-auto max-h-[600px] overflow-y-auto">
                <table class="w-full text-left text-sm">
                    <thead class="bg-brand-border text-gray-300 font-bold sticky top-0">
                        <tr>
                            <th class="p-3">Kỳ Quay</th>
                            <th class="p-3">Ngày</th>
                            <th class="p-3">Số 1</th>
                            <th class="p-3">Số 2</th>
                            <th class="p-3">Số 3</th>
                            <th class="p-3">Số 4</th>
                            <th class="p-3">Số 5</th>
                            <th class="p-3 text-brand-accent">Số ĐB</th>
                        </tr>
                    </thead>
                    <tbody id="historyTableBody" class="divide-y divide-brand-border"></tbody>
                </table>
            </div>
        </div>

        <!-- TAB 4: CHARTS -->
        <div id="tab-stats" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-brand-card border border-brand-border rounded-2xl p-6 shadow-xl">
                    <h3 class="font-bold text-brand-primary mb-4">Tần Suất 35 Quả Bóng Chính</h3>
                    <canvas id="chartBalls" height="200"></canvas>
                </div>
                <div class="bg-brand-card border border-brand-border rounded-2xl p-6 shadow-xl">
                    <h3 class="font-bold text-brand-accent mb-4">Tần Suất 12 Số Đặc Biệt</h3>
                    <canvas id="chartSpecial" height="200"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Embedded Data & Mathematical Engine -->
    <script>
        const DRAWS_DATA = {json.dumps(draws_data, ensure_ascii=False)};
        
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
            // Approximation for s = 2.5: Gamma(2.5) = 0.75 * sqrt(pi)
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
            const entropyRatio = Math.min(1.0, Math.max(0.0, (entropy - 1.0) / (Math.log(6.0) - 1.0)));

            let specFactor = 1.0;
            if (special !== null && special >= 1 && special <= 12) {{
                const isOverlap = sorted.includes(Number(special));
                const overlapMult = isOverlap ? 0.6 : 1.0;
                const dev = Math.abs(special - 6.5) / 3.452;
                const pSpec = Math.exp(-0.5 * dev * dev) * overlapMult;
                specFactor = 0.8 + 0.2 * pSpec;
            }}

            const jointProb = pMain * (0.8 + 0.2 * entropyRatio) * specFactor;
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

        // Tab Switching
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('border-brand-primary', 'text-brand-primary');
                btn.classList.add('border-transparent', 'text-gray-400');
            }});
            document.getElementById(tabId).classList.remove('hidden');
            const activeBtn = document.getElementById(tabId.replace('tab-', 'btn-'));
            activeBtn.classList.remove('border-transparent', 'text-gray-400');
            activeBtn.classList.add('border-brand-primary', 'text-brand-primary');
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
                alert('Vui lòng nhập đúng 5 số chính khác nhau từ 1 đến 35!');
                return;
            }}

            const res = evaluateCombo(nums, spec ? Number(spec) : null);
            document.getElementById('evalResultCard').classList.remove('hidden');

            const sqsEl = document.getElementById('resSQS');
            const badgeEl = document.getElementById('resBadge');
            const descEl = document.getElementById('resDesc');

            sqsEl.innerText = res.sqs.toFixed(1) + ' / 100';

            if (res.sqs >= 75) {{
                sqsEl.className = 'text-5xl font-extrabold text-green-400';
                badgeEl.className = 'px-3 py-1.5 rounded-lg text-sm font-bold uppercase tracking-wider bg-green-900/50 text-green-300 border border-green-700';
                badgeEl.innerText = 'XUẤT SẮC (Top 25% Tâm Phân Phối)';
                descEl.innerText = 'Bộ số đạt tỷ lệ đối xứng lý tưởng, độ trải đều trên toàn trục số hoàn hảo.';
            }} else if (res.sqs >= 40) {{
                sqsEl.className = 'text-5xl font-extrabold text-yellow-400';
                badgeEl.className = 'px-3 py-1.5 rounded-lg text-sm font-bold uppercase tracking-wider bg-yellow-900/50 text-yellow-300 border border-yellow-700';
                badgeEl.innerText = 'ĐẠT CHUẨN (Vùng Dung Sai 80% QR)';
                descEl.innerText = 'Bộ số hài hòa, nằm vững trong vùng 80% các kỳ quay trúng thưởng thực tế.';
            }} else if (res.sqs >= 10) {{
                sqsEl.className = 'text-5xl font-extrabold text-orange-400';
                badgeEl.className = 'px-3 py-1.5 rounded-lg text-sm font-bold uppercase tracking-wider bg-orange-900/50 text-orange-300 border border-orange-700';
                badgeEl.innerText = 'DUNG SAI BIÊN (Cần Lưu Ý)';
                descEl.innerText = 'Bộ số hơi lệch về tổng hoặc khoảng cách nhưng vẫn nằm trong phạm vi chấp nhận.';
            }} else {{
                sqsEl.className = 'text-5xl font-extrabold text-red-400';
                badgeEl.className = 'px-3 py-1.5 rounded-lg text-sm font-bold uppercase tracking-wider bg-red-900/50 text-red-300 border border-red-700';
                badgeEl.innerText = 'CẢNH BÁO (Lệch Chuẩn / Nhiễu Rác)';
                descEl.innerText = 'Bộ số bị dồn cụm, lệch chẵn/lẻ hoặc tổng quá cực đoan (p-value < 0.05).';
            }}

            // Balls display
            const ballsContainer = document.getElementById('resBallsDisplay');
            ballsContainer.innerHTML = res.combo.map(n => `<span class="ball ball-main">${{String(n).padStart(2,'0')}}</span>`).join('') +
                (res.special ? `<span class="text-xl font-bold text-brand-accent px-1">|</span><span class="ball ball-special">${{String(res.special).padStart(2,'0')}}</span>` : '');

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
                item.className = 'bg-brand-card border border-brand-border rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-lg';
                item.innerHTML = `
                    <div class="flex items-center gap-4">
                        <span class="text-sm font-bold text-gray-400">#${{String(idx+1).padStart(2,'0')}}</span>
                        <div class="flex items-center gap-2">
                            ${{r.combo.map(n => `<span class="ball ball-main text-sm w-9 h-9">${{String(n).padStart(2,'0')}}</span>`).join('')}}
                            <span class="text-brand-accent font-bold px-1">|</span>
                            <span class="ball ball-special text-sm w-9 h-9">${{String(r.special).padStart(2,'0')}}</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-6 text-sm">
                        <span>Tổng: <strong class="text-gray-200">${{r.sum}}</strong></span>
                        <span>${{r.odds}}L - ${{r.evens}}C</span>
                        <span>Entropy: <strong class="text-gray-200">${{r.entropy}}</strong></span>
                        <span class="px-3 py-1 rounded-lg font-bold bg-green-900/40 text-green-400 border border-green-700/50">SQS: ${{r.sqs.toFixed(1)}}/100</span>
                    </div>
                `;
                container.appendChild(item);
            }});
        }}

        function loadHistory() {{
            const tbody = document.getElementById('historyTableBody');
            tbody.innerHTML = DRAWS_DATA.slice().reverse().map(d => `
                <tr class="hover:bg-brand-border/40 transition">
                    <td class="p-3 font-bold text-brand-primary">#${{d.draw_code}}</td>
                    <td class="p-3 text-gray-400">${{d.date}}</td>
                    <td class="p-3 font-bold">${{String(d.num1).padStart(2,'0')}}</td>
                    <td class="p-3 font-bold">${{String(d.num2).padStart(2,'0')}}</td>
                    <td class="p-3 font-bold">${{String(d.num3).padStart(2,'0')}}</td>
                    <td class="p-3 font-bold">${{String(d.num4).padStart(2,'0')}}</td>
                    <td class="p-3 font-bold">${{String(d.num5).padStart(2,'0')}}</td>
                    <td class="p-3 font-bold text-brand-accent">${{String(d.special).padStart(2,'0')}}</td>
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
            // Compute Ball Frequencies
            const ballCounts = Array(35).fill(0);
            const specCounts = Array(12).fill(0);
            DRAWS_DATA.forEach(d => {{
                [d.num1, d.num2, d.num3, d.num4, d.num5].forEach(n => ballCounts[n-1]++);
                specCounts[d.special-1]++;
            }});

            // Chart Balls
            new Chart(document.getElementById('chartBalls'), {{
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

            // Chart Specials
            new Chart(document.getElementById('chartSpecial'), {{
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

        // Init
        loadHistory();
        fillLatest();
    </script>
</body>
</html>
"""

with open("/home/tringuyen/xstk/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

os.makedirs("/home/tringuyen/xstk/docs", exist_ok=True)
with open("/home/tringuyen/xstk/docs/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("[✓] Đã tạo thành công index.html và docs/index.html sẵn sàng cho GitHub Pages!")
