#!/usr/bin/env python3
"""Prequential probability model for 5/35 + special, with fair-draw baseline.

Weights are smoothed historical marginal frequencies. A 5-subset receives
probability proportional to the product of its five weights; the elementary
symmetric polynomial normalizes over all C(35,5) subsets. This is a model,
not evidence that lottery outcomes are predictable.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
from qr_backtest import load_draws, wilson_interval

DATA = Path(__file__).resolve().with_name('vietlott_535.json')
TOTAL = math.comb(35, 5)
PRIOR_MAIN = 20.0
PRIOR_SPECIAL = 5.0


def model(counts, special_counts):
    weights = [1.0 + counts[i] / PRIOR_MAIN for i in range(1, 36)]
    normalizer = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for w in weights:
        for k in range(5, 0, -1):
            normalizer[k] += w * normalizer[k - 1]
    special_total = sum(special_counts.values()) + 12 * PRIOR_SPECIAL
    special_probs = [(special_counts[i] + PRIOR_SPECIAL) / special_total for i in range(1, 13)]
    return weights, normalizer[5], special_probs


def train_add(counts, special_counts, combo, special):
    counts.update(combo)
    special_counts[special] += 1


def main():
    parser = argparse.ArgumentParser(description='Train and evaluate a chronological 5+1 probability model.')
    parser.add_argument('--source', type=Path, default=DATA, help='Project-format JSON history')
    parser.add_argument('--min-train', type=int, default=200, help='Initial training draws (minimum 50)')
    args = parser.parse_args()
    if args.min_train < 50:
        parser.error('--min-train must be at least 50')
    try:
        draws = load_draws(args.source)
        with args.source.open(encoding='utf-8') as f:
            records = json.load(f)
        specials = {int(row['draw_id']): int(row['special']) for row in records}
        if len(specials) != len(draws) or any(not 1 <= specials[d[0]] <= 12 for d in draws):
            raise ValueError('invalid or missing special numbers')
        if len(draws) <= args.min_train:
            raise ValueError('not enough draws for training and evaluation')
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    counts, special_counts = Counter(), Counter()
    for identifier, _, combo in draws[:args.min_train]:
        train_add(counts, special_counts, combo, specials[identifier])
    hits = [0] * 6
    special_hits = full_hits = 0
    logloss_main = logloss_special = 0.0
    for identifier, _, actual in draws[args.min_train:]:
        weights, norm, sp_probs = model(counts, special_counts)
        predicted = sorted(range(1, 36), key=lambda i: (-weights[i-1], i))[:5]
        predicted_special = max(range(1, 13), key=lambda i: (sp_probs[i-1], -i))
        match = len(set(predicted).intersection(actual))
        hits[match] += 1
        sp_hit = predicted_special == specials[identifier]
        special_hits += sp_hit
        full_hits += match == 5 and sp_hit
        logloss_main += math.log(norm) - sum(math.log(weights[i-1]) for i in actual)
        logloss_special -= math.log(sp_probs[specials[identifier]-1])
        train_add(counts, special_counts, actual, specials[identifier])

    n = len(draws) - args.min_train
    print(f'Nguồn: {args.source}; {len(draws)} kỳ; train ban đầu: {args.min_train}; ngoài mẫu: {n} kỳ #{draws[args.min_train][0]:05d}–#{draws[-1][0]:05d}')
    print('Một vé dự báo trước mỗi kỳ; sau đó mới cập nhật tần suất. Tie-break theo số nhỏ; tham số cố định trước đánh giá.')
    lo, hi = wilson_interval(sum(hits[3:]), n)
    print(f'Khoảng Wilson 95% cho tỷ lệ khớp ≥3: [{lo:.3%}, {hi:.3%}] (giả định Bernoulli độc lập cùng xác suất; mô hình cập nhật nên chỉ tham khảo)')
    print('Khớp 5 số chính | Quan sát | Tỷ lệ | Mốc quay đều (xấp xỉ số kỳ)')
    for k, observed in enumerate(hits):
        p = math.comb(5, k) * math.comb(30, 5-k) / TOTAL
        print(f'{k:>16} | {observed:>8} | {observed/n:>7.3%} | {p:>7.3%} ({n*p:.2f})')
    print(f'Khớp ≥3 số chính: {sum(hits[3:])}/{n} ({sum(hits[3:])/n:.3%}); mốc {sum(math.comb(5,k)*math.comb(30,5-k) for k in range(3,6))/TOTAL:.3%}')
    print(f'Khớp số đặc biệt: {special_hits}/{n} ({special_hits/n:.3%}); mốc 8.333%')
    print(f'Khớp đủ 5+1: {full_hits}/{n}; mốc kỳ vọng {n/(TOTAL*12):.6f} lần')
    print(f'Log-loss chính trung bình: {logloss_main/n:.6f}; mốc đều {math.log(TOTAL):.6f}; chênh {logloss_main/n-math.log(TOTAL):+.6f} (thấp hơn tốt hơn)')
    print(f'Log-loss đặc biệt trung bình: {logloss_special/n:.6f}; mốc đều {math.log(12):.6f}; chênh {logloss_special/n-math.log(12):+.6f}')
    weights, _, sp_probs = model(counts, special_counts)
    predicted = sorted(sorted(range(1, 36), key=lambda i: (-weights[i-1], i))[:5])
    sp = max(range(1, 13), key=lambda i: (sp_probs[i-1], -i))
    print('Dự báo mô hình cho kỳ tiếp theo (không bảo đảm):', ' '.join(f'{x:02}' for x in predicted), '| ĐB:', f'{sp:02}')
    print('Đây là một mô hình thống kê thực nghiệm, không chứng minh lợi thế; log-loss là điểm dự báo, không phải xác suất trúng thực tế. Độ tin cậy của kết quả rất hạn chế với biến cố hiếm.')


if __name__ == '__main__':
    main()
