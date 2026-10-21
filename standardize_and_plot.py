import subprocess
import json
import sqlite3
import base64
import os
import math
import csv
from collections import Counter
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

class MathMCPClient:
    def __init__(self):
        self.proc = subprocess.Popen(
            ["/home/tringuyen/.local/bin/math-mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "xstk-analysis", "version": "1.0"}
            }
        }
        self.proc.stdin.write(json.dumps(init_req) + "\n")
        self.proc.stdin.flush()
        self.proc.stdout.readline()
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.proc.stdin.flush()

    def call_tool(self, tool_name, arguments):
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "math",
                "arguments": {"tool": tool_name, "arguments": arguments}
            }
        }
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        res = json.loads(line)
        return res.get("result", {}).get("content", [])

    def close(self):
        try:
            self.proc.terminate()
        except Exception:
            pass

def save_image_from_content(content_list, filepath):
    for c in content_list:
        if c.get("type") == "image":
            img_data = base64.b64decode(c.get("data", ""))
            with open(filepath, "wb") as f:
                f.write(img_data)
            print(f"[✓] Đã lưu biểu đồ: {filepath} ({len(img_data)} bytes)")
            return True
    return False

def main():
    print("[*] Khởi động MCP client (math-mcp)...")
    mcp = MathMCPClient()
    
    # 1. Đọc dữ liệu từ SQLite
    conn = sqlite3.connect(os.path.join(BASE_DIR, "vietlott_535.db"))
    cur = conn.cursor()
    rows = cur.execute("SELECT draw_id, draw_code, date, num1, num2, num3, num4, num5, special, numbers_str FROM draws ORDER BY draw_id ASC").fetchall()
    conn.close()
    
    N_draws = len(rows)
    print(f"[*] Đang xử lý {N_draws} kỳ quay...")
    
    # 2. Tính toán lý thuyết và chuẩn hóa Z-Score tổng số (Sum)
    # E[S] = 5 * (1 + 35) / 2 = 90
    # Var(S) = n * sigma_0^2 * (N - n)/(N - 1) = 5 * 102 * 30/34 = 450
    # Sigma(S) = sqrt(450) ≈ 21.2132
    mu_theoretical = 90.0
    sigma_theoretical = math.sqrt(450.0)
    
    standardized_rows = []
    sums = []
    all_main_balls = []
    all_special_balls = []
    
    for r in rows:
        draw_id, code, date_str, n1, n2, n3, n4, n5, spec, s_str = r
        ball_list = [n1, n2, n3, n4, n5]
        all_main_balls.extend(ball_list)
        all_special_balls.append(spec)
        
        s_val = sum(ball_list)
        sums.append(s_val)
        z_sum = (s_val - mu_theoretical) / sigma_theoretical
        
        odd_cnt = sum(1 for x in ball_list if x % 2 != 0)
        even_cnt = 5 - odd_cnt
        high_cnt = sum(1 for x in ball_list if x > 18)
        low_cnt = 5 - high_cnt
        
        standardized_rows.append({
            "draw_id": draw_id,
            "draw_code": code,
            "date": date_str,
            "num1": n1,
            "num2": n2,
            "num3": n3,
            "num4": n4,
            "num5": n5,
            "special": spec,
            "sum_val": s_val,
            "z_score_sum": round(z_sum, 4),
            "odd_count": odd_cnt,
            "even_count": even_cnt,
            "high_count": high_cnt,
            "low_count": low_cnt,
            "numbers_str": s_str
        })
        
    # Lưu bảng chuẩn hóa
    std_csv_path = os.path.join(BASE_DIR, "vietlott_535_standardized.csv")
    with open(std_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["draw_id", "draw_code", "date", "num1", "num2", "num3", "num4", "num5", "special", "sum_val", "z_score_sum", "odd_count", "even_count", "high_count", "low_count", "numbers_str"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(standardized_rows)
    print(f"[✓] Đã tạo file chuẩn hóa: {std_csv_path}")

    # 3. Phân tích thống kê mô tả tổng 5 số qua describe_data
    desc_res = mcp.call_tool("describe_data", {"data": sums})
    desc_stats = json.loads(desc_res[0]["text"])
    
    # 4. Tính tần suất và Z-Score cho 35 quả bóng chính
    # p = 5/35 = 1/7
    # E[count] = 954 * (1/7) = 136.2857
    # sigma_count = sqrt(954 * 1/7 * 6/7) = 10.8087
    ball_counter = Counter(all_main_balls)
    p_ball = 5.0 / 35.0
    mu_count = N_draws * p_ball
    sigma_count = math.sqrt(N_draws * p_ball * (1.0 - p_ball))
    
    ball_stats = []
    ball_categories = [f"{i:02d}" for i in range(1, 36)]
    ball_frequencies = [ball_counter[i] for i in range(1, 36)]
    ball_zscores = [round((ball_counter[i] - mu_count) / sigma_count, 3) for i in range(1, 36)]
    
    for i in range(1, 36):
        cnt = ball_counter[i]
        z = (cnt - mu_count) / sigma_count
        if z > 1.96:
            status = "Hot (+2σ)"
        elif z < -1.96:
            status = "Cold (-2σ)"
        else:
            status = "Normal"
        ball_stats.append({
            "ball": i,
            "count": cnt,
            "expected": round(mu_count, 2),
            "deviation": round(cnt - mu_count, 2),
            "z_score": round(z, 4),
            "pct": round(cnt / N_draws * 100, 2),
            "status": status
        })
    freq_csv_path = os.path.join(BASE_DIR, "vietlott_535_frequency_stats.csv")
    with open(freq_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ball", "count", "expected", "deviation", "z_score", "pct", "status"])
        writer.writeheader()
        writer.writerows(ball_stats)
    print(f"[✓] Đã tạo file thống kê tần suất & Z-Score: {freq_csv_path}")

    # 5. Tạo Biểu đồ qua math-mcp:
    # Biểu đồ 1: Tần suất 35 số chính
    print("[*] Đang vẽ Biểu đồ 1: Tần suất 35 số chính...")
    img1 = mcp.call_tool("plot_bar", {
        "categories": ball_categories,
        "values": ball_frequencies,
        "title": f"Vietlott Lotto 5/35 - Tan suat xuat hien 35 so (N = {N_draws} ky, Ky vong = {mu_count:.1f})",
        "xlabel": "So qua bong (01 - 35)",
        "ylabel": "So lan xuat hien",
        "color": "#1f77b4",
        "xlabel_rotation": 45,
        "show_values": True,
        "value_format": ".0f",
        "figsize": [1200, 600]
    })
    save_image_from_content(img1, f"{CHARTS_DIR}/01_frequency_distribution.png")

    # Biểu đồ 2: Z-Score chuẩn hóa của 35 số
    print("[*] Đang vẽ Biểu đồ 2: Z-Score chuẩn hóa 35 số...")
    img2 = mcp.call_tool("plot_bar", {
        "categories": ball_categories,
        "values": ball_zscores,
        "title": f"Vietlott Lotto 5/35 - Z-Score Chuan hoa (Baseline = 0, Nguong y nghia +-1.96)",
        "xlabel": "So qua bong (01 - 35)",
        "ylabel": "Z-Score (Do lech chuan)",
        "color": "#ff7f0e",
        "show_values": True,
        "value_format": ".2f",
        "figsize": [1200, 600]
    })
    save_image_from_content(img2, f"{CHARTS_DIR}/02_zscore_standardized_balls.png")

    # Biểu đồ 3: Histogram phân phối tổng 5 số (so sánh với phân phối chuẩn)
    print("[*] Đang vẽ Biểu đồ 3: Histogram tong 5 so...")
    img3 = mcp.call_tool("plot_histogram", {
        "data": sums,
        "bins": 28,
        "title": f"Vietlott Lotto 5/35 - Phan phoi tong 5 so (Thuc te: mu={desc_stats['mean']:.1f}, sigma={desc_stats['std']:.1f} vs Ly thuyet: mu=90, sigma=21.2)",
        "xlabel": "Tong 5 so (Sum)",
        "ylabel": "So ky quay (Frequency)",
        "color": "#2ca02c",
        "figsize": [1100, 600]
    })
    save_image_from_content(img3, f"{CHARTS_DIR}/03_sum_histogram.png")

    # Biểu đồ 4: Tần suất 12 số đặc biệt
    print("[*] Đang vẽ Biểu đồ 4: Tan suat 12 so dac biet...")
    spec_counter = Counter(all_special_balls)
    spec_categories = [f"DB_{i:02d}" for i in range(1, 13)]
    spec_frequencies = [spec_counter[i] for i in range(1, 13)]
    img4 = mcp.call_tool("plot_bar", {
        "categories": spec_categories,
        "values": spec_frequencies,
        "title": f"Vietlott Lotto 5/35 - Tan suat So Dac Biet (1-12, Ky vong = {N_draws/12:.1f})",
        "xlabel": "So dac biet (01 - 12)",
        "ylabel": "So lan xuat hien",
        "color": "#d62728",
        "xlabel_rotation": 0,
        "show_values": True,
        "value_format": ".0f",
        "figsize": [900, 500]
    })
    save_image_from_content(img4, f"{CHARTS_DIR}/04_special_numbers.png")

    mcp.close()
    print("[✓] Hoàn tất toàn bộ chuẩn hóa và sinh biểu đồ!")

if __name__ == "__main__":
    main()
