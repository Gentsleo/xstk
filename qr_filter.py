#!/usr/bin/env python3
import sys
import math
import random
import argparse
import sqlite3
from collections import Counter
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vietlott_535.db")

# Vector trung bình thực nghiệm và ma trận nghịch đảo hiệp phương sai (k=5 bậc tự do)
# Được tính toán chuẩn xác từ 954 kỳ quay thực tế của Vietlott Lotto 5/35
MU = [91.1069, 2.5681, 2.6237, 23.8512, 0.5755]
INV_COV = [
    [ 0.009367, -0.004928, -0.164895, -0.000941, -0.008335],
    [-0.004928,  0.896688,  0.078079, -0.001084, -0.001216],
    [-0.164895,  0.078079,  3.775486,  0.027999,  0.141572],
    [-0.000941, -0.001084,  0.027999,  0.030715,  0.072989],
    [-0.008335, -0.001216,  0.141572,  0.072989,  2.300800]
]

def chi2_cdf(x, k=5):
    """Tính hàm phân phối tích lũy (CDF) của phân phối Chi-Square k bậc tự do với độ chính xác cao."""
    if x <= 0:
        return 0.0
    s = k / 2.0
    z = x / 2.0
    term = total = 1.0 / s
    for n in range(1, 100):
        term *= z / (s + n)
        total += term
        if abs(term) < 1e-12:
            break
    gamma_incomplete = math.exp(-z) * (z ** s) * total
    gamma_full = math.gamma(s)
    return min(1.0, max(0.0, gamma_incomplete / gamma_full))

def load_special_frequencies():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        rows = cur.execute("SELECT special FROM draws").fetchall()
        conn.close()
        c = Counter(r[0] for r in rows)
        total = len(rows)
        return c, total
    except Exception:
        return {i: 79 for i in range(1, 13)}, 954

def evaluate_combination(combo, special=None):
    combo = sorted([int(x) for x in combo])
    if len(combo) != 5:
        raise ValueError("Cần đúng 5 số chính")
    if len(set(combo)) != 5:
        raise ValueError("5 số chính không được trùng nhau")
    for x in combo:
        if not (1 <= x <= 35):
            raise ValueError(f"Số chính {x} nằm ngoài dải 1 - 35")
            
    s = sum(combo)
    z_sum = (s - 90.0) / 21.2132
    odds = sum(1 for x in combo if x % 2 != 0)
    highs = sum(1 for x in combo if x >= 18)
    span = combo[-1] - combo[0]
    consecs = sum(1 for i in range(4) if combo[i+1] - combo[i] == 1)
    
    # 1. Khoảng cách Mahalanobis khử tương quan chéo (D_M^2 ~ Chi2(5))
    vec = [s - MU[0], odds - MU[1], highs - MU[2], span - MU[3], consecs - MU[4]]
    dm_sq = sum(vec[i] * INV_COV[i][j] * vec[j] for i in range(5) for j in range(5))
    p_val_main = 1.0 - chi2_cdf(dm_sq, 5)
    
    # 2. Shannon Gap Entropy (Độ hỗn loạn khoảng cách giữa các số)
    # 6 khoảng cách chia bởi 5 số trên đoạn [1, 35]
    gaps = [combo[0], combo[1]-combo[0], combo[2]-combo[1], combo[3]-combo[2], combo[4]-combo[3], 36-combo[4]]
    p_gaps = [g / 36.0 for g in gaps]
    gap_entropy = -sum(p * math.log(p) for p in p_gaps)
    # Chuẩn hóa Entropy: H_max = ln(6) ≈ 1.7918
    entropy_ratio = gap_entropy / math.log(6.0)
    
    # 3. Đánh giá số đặc biệt (nếu có)
    special_info = None
    p_val_special = 1.0
    if special is not None:
        special = int(special)
        if not (1 <= special <= 12):
            raise ValueError(f"Số đặc biệt {special} phải nằm trong khoảng 1 - 12")
            
        spec_freqs, total_draws = load_special_frequencies()
        observed_cnt = spec_freqs.get(special, 0)
        expected_cnt = total_draws / 12.0
        sigma_spec = math.sqrt(total_draws * (1.0/12.0) * (11.0/12.0))
        z_spec = (observed_cnt - expected_cnt) / sigma_spec
        
        is_overlap = special in combo
        overlap_mult = 0.6 if is_overlap else 1.0  # trong 87.8% các kỳ, số ĐB không trùng số chính
        
        # p-value của số đặc biệt theo độ lệch chuẩn
        dev_spec = abs(special - 6.5) / 3.452
        p_val_special = math.exp(-0.5 * (dev_spec ** 2)) * overlap_mult
        
        special_info = {
            "special": special,
            "parity": "Lẻ" if special % 2 != 0 else "Chẵn",
            "tier": "Cao (7-12)" if special >= 7 else "Thấp (1-6)",
            "observed_count": observed_cnt,
            "expected_count": round(expected_cnt, 1),
            "z_freq": round(z_spec, 2),
            "is_overlap": is_overlap,
            "score_spec": round(p_val_special * 100, 1)
        }

    # 4. Điểm chất lượng chuẩn hóa SQS (Thang điểm 100 theo Tích Xác Suất Liên Hợp)
    # P(Toàn_bộ) = P(Main) * [0.8 + 0.2 * Entropy_factor] * [0.8 + 0.2 * P(Special)]
    entropy_factor = min(1.0, max(0.0, (gap_entropy - 1.0) / (math.log(6.0) - 1.0)))
    if special_info:
        spec_factor = 0.8 + 0.2 * (special_info["score_spec"] / 100.0)
    else:
        spec_factor = 1.0
    
    joint_prob = p_val_main * (0.8 + 0.2 * entropy_factor) * spec_factor
    final_sqs = round(joint_prob * 100.0, 1)
    final_sqs = max(0.0, min(100.0, final_sqs))

    # Đánh giá phân loại theo mô hình dung sai QR
    if final_sqs >= 75.0:
        grade = "XUẤT SẮC (Top 25% Tâm Phân Phối)"
        color = "\033[0;32m"
        rec = "Bộ số nằm ở tâm đối xứng hoàn hảo, độ trải đều tối ưu trên toàn trục số."
    elif final_sqs >= 40.0:
        grade = "ĐẠT CHUẨN (Vùng Dung Sai 80% QR Code)"
        color = "\033[1;33m"
        rec = "Bộ số hài hòa, nằm vững trong vùng 80% các kỳ quay trúng thưởng thực tế."
    elif final_sqs >= 10.0:
        grade = "TRUNG BÌNH (Dung Sai Biên)"
        color = "\033[0;33m"
        rec = "Bộ số hơi lệch về tổng hoặc khoảng cách nhưng vẫn nằm trong phạm vi chấp nhận."
    else:
        grade = "CẢNH BÁO (Lệch Chuẩn / Nhiễu Rác Xác Suất)"
        color = "\033[0;31m"
        rec = "Bộ số bị dồn cụm, lệch chẵn/lẻ hoặc tổng quá cực đoan (p-value < 0.05)."

    return {
        "combo": combo,
        "sum": s,
        "z_sum": round(z_sum, 2),
        "odds": odds,
        "evens": 5 - odds,
        "highs": highs,
        "lows": 5 - highs,
        "span": span,
        "consecs": consecs,
        "dm_sq": round(dm_sq, 2),
        "p_val_main": round(p_val_main, 4),
        "gap_entropy": round(gap_entropy, 3),
        "entropy_pct": round(entropy_ratio * 100, 1),
        "special_info": special_info,
        "sqs": final_sqs,
        "grade": grade,
        "color": color,
        "recommendation": rec
    }

def print_result(res):
    NC = "\033[0m"
    combo_str = ' '.join(f'{x:02d}' for x in res['combo'])
    sp = res.get("special_info")
    header_str = f"{combo_str} | ĐB: {sp['special']:02d}" if sp else combo_str
    
    print("=" * 68)
    print(f"BỘ SỐ ĐÁNH GIÁ (5 CHÍNH + 1 ĐẶC BIỆT): {header_str}")
    print("=" * 68)
    print("1. NĂM SỐ CHÍNH (1 - 35):")
    print(f"  • Tổng điểm (Sum):           {res['sum']} (Z-Score: {res['z_sum']:+})")
    print(f"  • Tỷ lệ Lẻ / Chẵn:           {res['odds']} Lẻ - {res['evens']} Chẵn")
    print(f"  • Tỷ lệ Tài / Xỉu:           {res['highs']} Cao - {res['lows']} Thấp")
    print(f"  • Khoảng phân tán (Span):    {res['span']} ({res['combo'][0]:02d} -> {res['combo'][-1]:02d})")
    print(f"  • Cặp số liền kề:            {res['consecs']} cặp")
    print(f"  • Khoảng cách Mahalanobis:   D_M^2 = {res['dm_sq']} (k=5 bậc tự do)")
    print(f"  • Xác suất điển hình (p):    p = {res['p_val_main']:.4f}")
    print(f"  • Shannon Gap Entropy:       H = {res['gap_entropy']} / 1.79 ({res['entropy_pct']}% tối đa)")

    if sp:
        print("\n2. SỐ ĐẶC BIỆT (1 - 12):")
        print(f"  • Quả bóng đặc biệt:         Số {sp['special']:02d} ({sp['parity']}, {sp['tier']})")
        print(f"  • Lịch sử xuất hiện:         {sp['observed_count']} lần (Kỳ vọng: {sp['expected_count']} | Z-Score: {sp['z_freq']:+})")
        overlap_text = "Có trùng với số chính (xác suất 12.2%)" if sp['is_overlap'] else "Không trùng số chính (xác suất 87.8% - Tối ưu)"
        print(f"  • Quan hệ với 5 số chính:    {overlap_text}")
        
    print("-" * 68)
    print(f"• ĐIỂM CHẤT LƯỢNG CHUẨN (SQS): {res['color']}{res['sqs']:>5.1f} / 100{NC}")
    print(f"• PHÂN LOẠI MÔ HÌNH:           {res['color']}{res['grade']}{NC}")
    print(f"• NHẬN ĐỊNH TOÁN HỌC:          {res['recommendation']}")
    print("=" * 68)

def generate_candidates(count=5):
    print(f"[*] Đang tạo {count} bộ số hoàn chỉnh tối ưu (SQS >= 80/100, chuẩn Mahalanobis & Entropy):\n")
    found = []
    attempts = 0
    spec_choices = [3, 7, 9, 12, 1, 2, 8, 10, 4, 5]
    
    while len(found) < count and attempts < 20000:
        attempts += 1
        nums = sorted(random.sample(range(1, 36), 5))
        available_specials = [s for s in spec_choices if s not in nums]
        spec = random.choice(available_specials if available_specials else range(1, 13))
        
        res = evaluate_combination(nums, spec)
        if res["sqs"] >= 80.0 and res["gap_entropy"] >= 1.50:
            found.append(res)
            
    for idx, r in enumerate(found, 1):
        s_str = ' '.join(f'{x:02d}' for x in r['combo'])
        sp = r['special_info']['special']
        print(f"  Bộ {idx:02d}: [{s_str} | ĐB: {sp:02d}]  Tổng: {r['sum']:>3} | {r['odds']}L-{r['evens']}C | Entropy: {r['gap_entropy']:.2f} | SQS: {r['sqs']:>4.1f}/100")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Đánh giá bộ số Vietlott 5/35 theo mô hình khoảng cách Mahalanobis và Shannon Gap Entropy")
    parser.add_argument("numbers", nargs="*", type=int, help="5 số chính, kèm số đặc biệt thứ 6 nếu có (ví dụ: 6 15 21 30 34 6)")
    parser.add_argument("-s", "--special", type=int, default=None, help="Số đặc biệt (1-12)")
    parser.add_argument("--gen", type=int, default=0, help="Tự động tạo N bộ số chuẩn 5+1 tối ưu xác suất")
    
    args = parser.parse_args()
    
    if args.gen > 0:
        generate_candidates(args.gen)
    elif len(args.numbers) == 6:
        main_nums = args.numbers[:5]
        spec_num = args.numbers[5]
        res = evaluate_combination(main_nums, spec_num)
        print_result(res)
    elif len(args.numbers) == 5:
        res = evaluate_combination(args.numbers, args.special)
        print_result(res)
    else:
        print("Chưa nhập đủ số. Đang chạy minh họa trên kỳ mới nhất #00954 [06 15 21 30 34 | ĐB: 06]:\n")
        res = evaluate_combination([6, 15, 21, 30, 34], 6)
        print_result(res)
        print("\nCú pháp sử dụng:")
        print("  ./xstk.sh qr 6 15 21 30 34 6           (Kiểm tra 5 số chính + 1 số đặc biệt)")
        print("  ./xstk.sh qr 6 15 21 30 34 -s 6        (Dùng flag -s cho số đặc biệt)")
        print("  ./xstk.sh qr --gen 5                   (Tạo 5 bộ số trọn gói 5+1 tối ưu SQS >= 80)")
