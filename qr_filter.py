#!/usr/bin/env python3
"""
Vietlott 5/35: thống kê mô tả vé và sinh đều vé trên toàn bộ C(35,5) tổ hợp.
Điểm hình thái không phải xác suất trúng; mọi vé hợp lệ có cùng xác suất trong kỳ quay công bằng.
"""

import math
import random
import sqlite3
import argparse
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "vietlott_535.db")
JSON_PATH = os.path.join(os.path.dirname(__file__), "vietlott_535.json")

# Trung bình và nghịch đảo hiệp phương sai của toàn bộ C(35,5) tổ hợp đồng xác suất.
MU = [90.0, 18/7, 18/7, 24.0, 4/7]
INV_COV = [
    [0.008922, -0.004452, -0.156333, -0.000572, -0.001458],
    [-0.004452, 0.912853, 0.103882, -0.007780, 0.010327],
    [-0.156333, 0.103882, 3.647779, 0.013338, 0.034020],
    [-0.000572, -0.007780, 0.013338, 0.032009, 0.081643],
    [-0.001458, 0.010327, 0.034020, 0.081643, 2.448486]
]

# Bách phân vị 80% của D² trên toàn bộ C(35,5) tổ hợp, dùng hệ số trên.
QR80_THRESHOLD = 7.055639346938778
QR80_SIZE = 259706
TOTAL_COMBINATIONS = math.comb(35, 5)
_RNG = random.SystemRandom()


def distance_squared(combo):
    """Khoảng cách chưa làm tròn; combo phải là 5 số hợp lệ đã sắp xếp."""
    vec = [sum(combo) - MU[0], sum(x % 2 for x in combo) - MU[1],
           sum(x >= 18 for x in combo) - MU[2], combo[-1] - combo[0] - MU[3],
           sum(combo[i+1] - combo[i] == 1 for i in range(4)) - MU[4]]
    return sum(vec[i] * INV_COV[i][j] * vec[j] for i in range(5) for j in range(5))

def sample_uniform_ticket():
    """Lấy mẫu đều một bộ 5 số chính từ toàn bộ C(35,5) tổ hợp."""
    return tuple(sorted(_RNG.sample(range(1, 36), 5)))

def chi2_cdf(x, k=5):
    """CDF chi bình phương 5 bậc tự do, dùng như thước đo hình thái xấp xỉ."""
    if k != 5:
        raise ValueError("Chỉ hỗ trợ 5 bậc tự do")
    if x <= 0:
        return 0.0
    s = x / 2.0
    return min(1.0, max(0.0, math.erf(math.sqrt(s)) -
        2 * math.sqrt(s / math.pi) * math.exp(-s) * (1 + 2*s/3)))

def load_special_frequencies():
    """Tải tần suất xuất hiện thực tế của số đặc biệt (1-12)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT special, COUNT(*) FROM draws GROUP BY special")
        freqs = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT COUNT(*) FROM draws")
        total = cur.fetchone()[0]
        conn.close()
        return freqs, total
    except Exception:
        return {i: 79 for i in range(1, 13)}, 965

def get_history_context():
    """Tải kỳ quay gần nhất và tính nhịp vắng mặt (skips) của 35 số."""
    draws = []
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                draws = json.load(f)
        except Exception:
            pass
    if not draws and os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT draw_id, draw_code, draw_date, num1, num2, num3, num4, num5, special FROM draws ORDER BY draw_id ASC")
            for r in cur.fetchall():
                draws.append({
                    "draw_id": r[0], "draw_code": r[1], "date": r[2],
                    "num1": r[3], "num2": r[4], "num3": r[5], "num4": r[6], "num5": r[7], "special": r[8]
                })
            conn.close()
        except Exception:
            pass

    if not draws:
        return None, {i: 6 for i in range(1, 36)}

    draws = sorted(draws, key=lambda x: x["draw_id"])
    latest_draw = draws[-1]
    
    last_seen = {i: -1 for i in range(1, 36)}
    for idx, d in enumerate(draws):
        for j in range(1, 6):
            last_seen[d[f"num{j}"]] = idx
    current_skips = {i: (len(draws) - 1) - last_seen[i] for i in range(1, 36)}

    return latest_draw, current_skips

def evaluate_combination(combo, special=None, context=None):
    """Đánh giá hình thái bộ số; các thống kê lịch sử chỉ để tham khảo."""
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
    
    # 1. Khoảng cách Mahalanobis (D_M^2)
    dm_sq = distance_squared(combo)
    p_val_main = 1.0 - chi2_cdf(dm_sq, 5)
    
    # 2. Shannon Gap Entropy
    gaps = [combo[0], combo[1]-combo[0], combo[2]-combo[1], combo[3]-combo[2], combo[4]-combo[3], 36-combo[4]]
    p_gaps = [g / 36.0 for g in gaps]
    gap_entropy = -sum(p * math.log(p) for p in p_gaps)
    entropy_ratio = gap_entropy / math.log(6.0)
    
    # Lồng cầu riêng: mọi số đặc biệt 1..12 đồng xác suất; chỉ báo cáo tần suất.
    special_info = None
    if special is not None:
        special = int(special)
        if not 1 <= special <= 12:
            raise ValueError(f"Số đặc biệt {special} phải nằm trong khoảng 1 - 12")
        spec_freqs, total_draws = load_special_frequencies()
        expected_cnt = total_draws / 12.0
        sigma_spec = math.sqrt(total_draws * (1/12) * (11/12)) if total_draws else 1.0
        observed_cnt = spec_freqs.get(special, 0)
        special_info = {
            "special": special,
            "parity": "Lẻ" if special % 2 else "Chẵn",
            "tier": "Cao (7-12)" if special >= 7 else "Thấp (1-6)",
            "observed_count": observed_cnt,
            "expected_count": round(expected_cnt, 1),
            "z_freq": round((observed_cnt - expected_cnt) / sigma_spec, 2),
            "is_overlap": special in combo,
        }

    # SQS chỉ là chỉ số hình thái; không phải xác suất trúng.
    entropy_factor = min(1.0, max(0.0, (gap_entropy - 1.0) / (math.log(6.0) - 1.0)))
    sqs_v1 = round(100 * p_val_main * (0.8 + 0.2 * entropy_factor), 1)

    # Các thống kê kỳ trước không tham gia điểm cân đối.
    if context is None:
        latest_draw, current_skips = get_history_context()
    else:
        latest_draw, current_skips = context

    # Giao nhau với kỳ trước và thời gian vắng là thống kê mô tả, không dự đoán.
    markov_info = {"repeats": 0, "prev_code": "N/A", "status": "Không có dữ liệu"}
    if latest_draw:
        prev_nums = {latest_draw[f"num{j}"] for j in range(1, 6)}
        repeats = len(set(combo) & prev_nums)
        markov_info = {
            "repeats": repeats,
            "prev_code": latest_draw["draw_code"],
            "status": f"{repeats} số lặp kỳ trước (thống kê mô tả)"
        }
    skip_sum = sum(current_skips.get(x, 6) for x in combo)
    skip_info = {
        "skip_sum": skip_sum,
        "mean_skip": round(skip_sum / 5.0, 1),
        "status": f"Tổng vắng {skip_sum} kỳ (không dự báo)"
    }

    # 5C. Thông tin dải số cao (>= 32) mang tính mô tả, không áp đặt phạt điểm để tránh bias
    has_high = any(x >= 32 for x in combo)
    high_count = sum(1 for x in combo if x >= 32)
    anti_info = {
        "has_high_zone": has_high,
        "high_count": high_count,
        "status": f"Có {high_count} số >= 32" if has_high else "Không có số >= 32"
    }

    sqs_v2 = sqs_v1
    if sqs_v2 >= 75:
        grade, color = "CÂN ĐỐI", "\033[0;32m"
    elif sqs_v2 >= 40:
        grade, color = "TƯƠNG ĐỐI CÂN ĐỐI", "\033[1;33m"
    else:
        grade, color = "ÍT CÂN ĐỐI", "\033[0;33m"
    rec = "Mỗi bộ số hợp lệ vẫn có cùng xác suất trúng nếu kỳ quay công bằng."

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
        "in_qr80": dm_sq <= QR80_THRESHOLD,
        "p_val_main": round(p_val_main, 4),
        "gap_entropy": round(gap_entropy, 3),
        "entropy_pct": round(entropy_ratio * 100, 1),
        "special_info": special_info,
        "sqs_v1": sqs_v1,
        "sqs": sqs_v2,
        "sqs_v2": sqs_v2,
        "markov_info": markov_info,
        "skip_info": skip_info,
        "anti_info": anti_info,
        "grade": grade,
        "color": color,
        "recommendation": rec
    }

def print_result(res):
    """In kết quả trực quan trên giao diện dòng lệnh."""
    NC = "\033[0m"
    combo_str = ' '.join(f'{x:02d}' for x in res['combo'])
    sp = res.get("special_info")
    header_str = f"{combo_str} | ĐB: {sp['special']:02d}" if sp else combo_str

    print("=" * 72)
    print("  PHÂN TÍCH HÌNH THÁI BỘ SỐ (KHÔNG DỰ BÁO XÁC SUẤT TRÚNG)")
    print(f"  Bộ số: [ {header_str} ]")
    print("=" * 72)
    print("1. HÌNH THÁI VÀ KHOẢNG CÁCH MAHALANOBIS:")
    print(f"   • Tổng số:          {res['sum']:>3}  (Z-Score = {res['z_sum']:>+.2f}, Trung bình lý thuyết = 90)")
    print(f"   • Tỷ lệ Chẵn / Lẻ:  {res['evens']} Chẵn - {res['odds']} Lẻ (Chuẩn 2/3 hoặc 3/2)")
    print(f"   • Tỷ lệ Cao / Thấp: {res['highs']} Cao  - {res['lows']} Thấp (Ngưỡng phân cách: 18)")
    print(f"   • Khoảng trải rộng: {res['span']:>2} số  | Số cặp liên tiếp: {res['consecs']}")
    print(f"   • Mahalanobis D_M^2:{res['dm_sq']:>6.2f} (đuôi Chi2(5) xấp xỉ: {res['p_val_main']:.4f})")
    print(f"   • Vùng QR 80% (chỉ mô tả, không lọc vé): {'Trong vùng' if res['in_qr80'] else 'Ngoài vùng'} (D² ≤ {QR80_THRESHOLD:.6f})")
    print(f"   • Shannon Gap H:    {res['gap_entropy']:>6.3f} ({res['entropy_pct']}% cực đại lý thuyết)")
    
    if sp:
        print(f"\n2. SỐ ĐẶC BIỆT (#{sp['special']:02d}):")
        print(f"   • Tần suất lịch sử: {sp['observed_count']} lần (kỳ vọng: {sp['expected_count']}; Z={sp['z_freq']:+.2f})")
        print(f"   • Mỗi số 01–12 đều có xác suất 1/12 ở kỳ sau nếu quay công bằng.")

    m = res['markov_info']
    s = res['skip_info']
    a = res['anti_info']
    print(f"\n3. THỐNG KÊ MÔ TẢ (KHÔNG DỰ BÁO):")
    print(f"   • Kỳ #{m['prev_code']}: {m['status']}")
    print(f"   • Nhịp vắng hình học: {s['status']} (TB: {s['mean_skip']} kỳ/số)")
    print(f"   • Cấu trúc dải số: {a['status']}")
    print("-" * 72)
    print(f"• ĐIỂM CÂN ĐỐI HÌNH THÁI: {res['color']}{res['sqs']:>5.1f} / 100{NC}")
    print(f"• PHÂN LOẠI MÔ HÌNH:           {res['color']}{res['grade']}{NC}")
    print(f"• NHẬN ĐỊNH TOÁN HỌC:          {res['recommendation']}")
    print("=" * 72)


def generate_covering_wheel(v=10):
    """Chia 10 số lấy mẫu đều thành hai vé rời; mỗi vé biên đều trên C(35,5).

    Hai vé phụ thuộc nhau vì không chung số chính; số đặc biệt độc lập cho từng vé.
    """
    if v != 10:
        raise ValueError("Chỉ hỗ trợ bể 10 số")
    context = get_history_context()
    numbers = _RNG.sample(range(1, 36), 10)
    t1, t2 = tuple(sorted(numbers[:5])), tuple(sorted(numbers[5:]))
    best_pool = sorted(numbers)
    sp1, sp2 = _RNG.randrange(1, 13), _RNG.randrange(1, 13)
    r1 = evaluate_combination(t1, sp1, context=context)
    r2 = evaluate_combination(t2, sp2, context=context)
    print(f"[*] Bể 10 số của hai vé rời: {best_pool}")

    print("\n" + "=" * 72)
    print("  HAI VÉ RỜI TRÊN BỂ 10 SỐ — MỖI VÉ ĐỀU, HAI VÉ PHỤ THUỘC")
    print("=" * 72)
    print(f"🎫 VÉ SỐ 1: [ {' '.join(f'{x:02d}' for x in t1)} | ĐB: {sp1:02d} ]")
    print(f"   • SQS v2.0: {r1['sqs']:>5.1f}/100 ({r1['grade']})")
    print(f"   • Tổng số : {r1['sum']:>3} (Z={r1['z_sum']:>+.2f}) | {r1['odds']}L-{r1['evens']}C | Entropy: {r1['gap_entropy']:.2f}")
    print(f"   • Nhịp vắng: {r1['skip_info']['status']} | Lặp kỳ trước: {r1['markov_info']['repeats']} số")
    print(f"   • QR 80% (chỉ mô tả): {'Trong vùng' if r1['in_qr80'] else 'Ngoài vùng'}")

    print(f"\n🎫 VÉ SỐ 2: [ {' '.join(f'{x:02d}' for x in t2)} | ĐB: {sp2:02d} ]")
    print(f"   • SQS v2.0: {r2['sqs']:>5.1f}/100 ({r2['grade']})")
    print(f"   • Tổng số : {r2['sum']:>3} (Z={r2['z_sum']:>+.2f}) | {r2['odds']}L-{r2['evens']}C | Entropy: {r2['gap_entropy']:.2f}")
    print(f"   • Nhịp vắng: {r2['skip_info']['status']} | Lặp kỳ trước: {r2['markov_info']['repeats']} số")
    print(f"   • QR 80% (chỉ mô tả): {'Trong vùng' if r2['in_qr80'] else 'Ngoài vùng'}")

    print("-" * 72)
    print(f"   Nếu cả 5 số kết quả thuộc bể 10 số, ít nhất một vé khớp >=3 số.")
    print(f"   Xác suất >=3 số chính trên ít nhất một vé: 9002/324632 = 2.773%.")
    print(f"   Không bảo đảm trúng giải; hai vé khác nhau có xác suất trúng đúng 5 số 2/324632.")
    print("=" * 72)
    return best_pool, [t1, t2]

def suggest_uniform(count=5):
    """Lấy mẫu đều các bộ 5 số không lặp trên toàn bộ C(35,5); không xếp hạng."""
    if not 1 <= count <= TOTAL_COMBINATIONS:
        raise ValueError(f"Số lượng phải nằm trong khoảng 1–{TOTAL_COMBINATIONS}")
    context = get_history_context()
    seen = set()
    results = []
    while len(results) < count:
        combo = sample_uniform_ticket()
        if combo in seen:
            continue
        seen.add(combo)
        results.append(evaluate_combination(combo, _RNG.randrange(1, 13), context=context))
    return results

def generate_candidates(count=5):
    """Sinh đều các vé không trùng số chính trên toàn bộ C(35,5) tổ hợp."""
    found = suggest_uniform(count)
    print(f"[*] Đã lấy mẫu {count} bộ số trên toàn bộ {TOTAL_COMBINATIONS} tổ hợp (QR chỉ mô tả):\n")
            
    for idx, r in enumerate(found, 1):
        s_str = ' '.join(f'{x:02d}' for x in r['combo'])
        sp = r['special_info']['special']
        m = r['markov_info']
        s = r['skip_info']
        print(f"  Bộ {idx:02d}: [{s_str} | ĐB: {sp:02d}]  QR 80%: {'Trong' if r['in_qr80'] else 'Ngoài'} (chỉ mô tả) | Tổng: {r['sum']:>3} | SQS: {r['sqs_v2']:>4.1f}/100 | Lặp: {m['repeats']} | Vắng: {s['skip_sum']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Đánh giá hình thái vé Vietlott 5/35 (không dự báo)")
    parser.add_argument("numbers", nargs="*", type=int, help="5 số chính, kèm số đặc biệt thứ 6 nếu có (ví dụ: 6 15 21 30 34 6)")
    parser.add_argument("-s", "--special", type=int, default=None, help="Số đặc biệt (1-12)")
    parser.add_argument("--gen", type=int, default=None, help=f"Sinh N vé đều trên toàn bộ {TOTAL_COMBINATIONS} tổ hợp (1–{TOTAL_COMBINATIONS})")
    parser.add_argument("--wheel", type=int, default=None, help="Chia bể 10 số lấy mẫu đều thành hai vé rời")

    args = parser.parse_args()

    if args.gen is not None and not 1 <= args.gen <= TOTAL_COMBINATIONS:
        parser.error(f"--gen phải nằm trong khoảng 1–{TOTAL_COMBINATIONS}")
    if args.wheel is not None and args.wheel != 10:
        parser.error("--wheel chỉ hỗ trợ bể 10 số cho hai vé 5 số")
    if args.gen is not None and args.wheel is not None:
        parser.error("Chọn --gen hoặc --wheel, không dùng cả hai")

    if args.wheel is not None:
        generate_covering_wheel(args.wheel)
    elif args.gen is not None:
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
        generate_covering_wheel(10)
