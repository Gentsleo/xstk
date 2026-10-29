#!/usr/bin/env python3
"""Prequential comparison of fair, frequency and QR-bin 5+1 models.

Historical evaluation is retrospective, not a claim of a virgin holdout or of
an advantage against a fair independent lottery. A lock freezes the selected
model and history prefix before any prospective draws are scored.
"""

import argparse
from bisect import bisect_left
from collections import Counter
from functools import lru_cache
import json
import math
from pathlib import Path

import numpy as np

from qr_filter import QR80_THRESHOLD, distance_squared
from qr_predict import PRIOR_MAIN, PRIOR_SPECIAL, model as frequency_model, train_add


DATA = Path(__file__).resolve().with_name('vietlott_535.json')
TOTAL = math.comb(35, 5)
LOG_FAIR_MAIN = math.log(TOTAL)
LOG_FAIR_SPECIAL = math.log(12)
LOG_FAIR_JOINT = math.log(TOTAL * 12)
BIN_PRIOR = 20.0
VERSION = 1
MODELS = ('uniform', 'frequency', 'qr')
SELECTION_RULE = 'tối thiểu log-loss joint validation giữa frequency và qr; hòa chọn frequency'


@lru_cache(maxsize=1)
def _bins():
    """Fixed equal-quantile D² boundaries on the complete fair reference."""
    from rng_lab import reference  # The lab imports this module only at CLI dispatch.

    ref = reference()
    if len(ref['d2']) != TOTAL or len(ref['combos']) != TOTAL:
        raise ValueError('reference must contain all C(35,5) combinations')
    edges = tuple(float(x) for x in ref['cuts'])
    sizes = tuple(int(x) for x in ref['bin_counts'])
    members = tuple(np.flatnonzero(ref['bins'] == k) for k in range(5))
    if any(size == 0 for size in sizes):
        raise ValueError('QR reference quantile ties left an empty bin')
    return edges, sizes, members, ref['combos']


def _qr_bin(combo, edges):
    d2 = distance_squared(combo)
    bucket = bisect_left(edges, d2)
    if any(abs(d2 - edge) < 1e-10 for edge in edges):
        # Scalar and NumPy accumulation can differ by a last bit at a tie.
        # Use the reference's exact bin label so every probability sums to 1.
        from rng_lab import reference
        rank, previous = 0, 0
        for position, x in enumerate(combo):
            remaining = 5 - position
            rank += math.comb(35 - previous, remaining) - math.comb(36 - x, remaining)
            previous = x
        return int(reference()['bins'][rank])
    return bucket


def _qr_masses(bin_counts, sizes, n):
    return tuple((bin_counts[k] + BIN_PRIOR * sizes[k] / TOTAL) / (n + BIN_PRIOR)
                 for k in range(5))


def _state(rows):
    counts, specials, bins = Counter(), Counter(), [0] * 5
    edges = _bins()[0]
    for row in rows:
        combo, special = row['combo'], row['special']
        train_add(counts, specials, combo, special)
        bins[_qr_bin(combo, edges)] += 1
    return counts, specials, bins


def _add(state, row, edges):
    counts, specials, bins = state
    train_add(counts, specials, row['combo'], row['special'])
    bins[_qr_bin(row['combo'], edges)] += 1


def _empty_score():
    return {name: {'sum_main': 0.0, 'sum_special': 0.0,
                   'main_hits': [0] * 6, 'special_hits': 0} for name in MODELS}


def _ticket_uniform(seed, draw_id):
    rng = np.random.default_rng(np.random.SeedSequence([seed, draw_id, 0]))
    return set(int(x) for x in rng.choice(35, size=5, replace=False) + 1), int(rng.integers(1, 13))


def _ticket_qr(seed, draw_id, masses, members, combos, special_probs):
    rng = np.random.default_rng(np.random.SeedSequence([seed, draw_id, 2]))
    bucket = int(rng.choice(5, p=masses))
    index = int(members[bucket][int(rng.integers(len(members[bucket])))])
    special = max(range(1, 13), key=lambda x: (special_probs[x - 1], -x))
    return set(int(x) for x in combos[index]), special


def _score(row, state, scores, seed, edges, sizes, members, combos):
    counts, special_counts, bin_counts = state
    combo, special, draw_id = row['combo'], row['special'], row['draw_id']
    weights, norm, special_probs = frequency_model(counts, special_counts)
    masses = _qr_masses(bin_counts, sizes, sum(bin_counts))
    qr_bin = _qr_bin(combo, edges)
    uniform_ticket, uniform_special = _ticket_uniform(seed, draw_id)
    freq_ticket = set(sorted(range(1, 36), key=lambda i: (-weights[i - 1], i))[:5])
    freq_special = max(range(1, 13), key=lambda x: (special_probs[x - 1], -x))
    qr_ticket, qr_special = _ticket_qr(seed, draw_id, masses, members, combos, special_probs)
    tickets = ((uniform_ticket, uniform_special), (freq_ticket, freq_special),
               (qr_ticket, qr_special))
    main_losses = (0.0, math.log(norm) - sum(math.log(weights[i - 1]) for i in combo),
                   -math.log(masses[qr_bin] / sizes[qr_bin]))
    special_loss = -math.log(special_probs[special - 1])
    special_losses = (0.0, special_loss, special_loss)
    for name, (ticket, ticket_special), main_loss, special_loss in zip(
            MODELS, tickets, main_losses, special_losses):
        result = scores[name]
        result['sum_main'] += main_loss
        result['sum_special'] += special_loss
        result['main_hits'][len(ticket.intersection(combo))] += 1
        result['special_hits'] += int(ticket_special == special)
    _add(state, row, edges)  # Never update with the outcome before scoring it.


def _summary(scores, count):
    if not count:
        return None
    result = {}
    for name, score in scores.items():
        main = LOG_FAIR_MAIN if name == 'uniform' else score['sum_main'] / count
        special = LOG_FAIR_SPECIAL if name == 'uniform' else score['sum_special'] / count
        joint = LOG_FAIR_JOINT if name == 'uniform' else main + special
        result[name] = {
            'mean_logloss_main': main,
            'mean_logloss_special': special,
            'mean_logloss_joint': joint,
            'delta_vs_uniform_main': main - LOG_FAIR_MAIN,
            'delta_vs_uniform_special': special - LOG_FAIR_SPECIAL,
            'delta_vs_uniform_joint': joint - LOG_FAIR_JOINT,
            'main_hits_0_to_5': score['main_hits'],
            'special_hits': score['special_hits'],
            'draws': count,
        }
    return result


def _evaluate(rows, state, seed):
    edges, sizes, members, combos = _bins()
    scores = _empty_score()
    for row in rows:
        _score(row, state, scores, seed, edges, sizes, members, combos)
    return _summary(scores, len(rows))


def _config(seed, train, validation):
    edges, sizes, _, _ = _bins()
    return {'version': VERSION, 'seed': seed, 'min_train': train, 'validation': validation,
            'bin_edges_d2': list(edges), 'bin_sizes': list(sizes),
            'bin_prior': BIN_PRIOR, 'frequency_prior_main': PRIOR_MAIN,
            'prior_special': PRIOR_SPECIAL, 'ticket_rng': 'seed-sequence(seed, draw_id, model)'}


def _select(validation):
    # Joint logloss only; predetermined tie break in favor of the simpler model.
    return min(('frequency', 'qr'),
               key=lambda name: (validation[name]['mean_logloss_joint'], name != 'frequency'))


def _retrospective(rows, seed, train, validation, digest):
    if len(rows) < train + validation:
        raise ValueError('cần đủ kỳ train và validation để chọn mô hình')
    state = _state(rows[:train])
    valid = _evaluate(rows[train:train + validation], state, seed)
    selected = _select(valid)
    test = _evaluate(rows[train + validation:], state, seed)
    cfg = _config(seed, train, validation)
    report = {
        'mode': 'retrospective', 'status': 'retrospective_already_inspected',
        'evidence': {'prospective': False, 'n_new': 0, 'selected_model': selected,
                     'log_evalue': None, 'prefix_verified': False},
        'note': 'Toàn bộ lịch sử hiện có đã có thể được xem; test không phải holdout nguyên sơ. Không có bằng chứng lợi thế dự báo từ kết quả hồi cứu.',
        'config': cfg, 'history_sha256': digest, 'history_draws': len(rows),
        'last_draw_id': rows[-1]['draw_id'], 'selected_model': selected,
        'selection_rule': SELECTION_RULE,
        'validation_draw_ids': [rows[train]['draw_id'], rows[train + validation - 1]['draw_id']],
        'test_draw_ids': ([rows[train + validation]['draw_id'], rows[-1]['draw_id']]
                          if test else None),
        'validation': valid, 'test': test,
        'next_ticket': _next_ticket(state, seed, rows[-1]['draw_id'] + 1, selected),
    }
    return report


def _next_ticket(state, seed, draw_id, selected):
    counts, special_counts, bin_counts = state
    weights, _, probs = frequency_model(counts, special_counts)
    if selected == 'frequency':
        combo = sorted(sorted(range(1, 36), key=lambda i: (-weights[i - 1], i))[:5])
        special = max(range(1, 13), key=lambda x: (probs[x - 1], -x))
    else:
        _, sizes, members, combos = _bins()
        masses = _qr_masses(bin_counts, sizes, sum(bin_counts))
        combo_set, special = _ticket_qr(seed, draw_id, masses, members, combos, probs)
        combo = sorted(combo_set)
    return {'for_draw_id': draw_id, 'main': combo, 'special': special,
            'method': 'frequency top weights' if selected == 'frequency' else 'QR probability sample',
            'note': 'Chỉ vé minh họa, không bảo đảm trúng; quay công bằng cho mọi vé cùng xác suất.'}


def report_ticket(rows, combo, special=None):
    """Probability assigned to a 5+1 ticket after training on ALL supplied rows.

    Descriptive retrospective probabilities only; do not use the supplied
    history to claim prospective predictive skill. ``special=None`` reports
    main-ball probabilities without assigning a special-ball probability.
    """
    if (len(combo) != 5 or any(type(x) is not int or not 1 <= x <= 35 for x in combo)
            or len(set(combo)) != 5 or
            (special is not None and (type(special) is not int or not 1 <= special <= 12))):
        raise ValueError('vé phải gồm 5 số chính khác nhau 1..35 và số đặc biệt 1..12 nếu cung cấp')
    combo = tuple(sorted(combo))
    state = _state(rows)
    weights, norm, special_probs = frequency_model(state[0], state[1])
    edges, sizes, _, _ = _bins()
    bucket = _qr_bin(combo, edges)
    masses = _qr_masses(state[2], sizes, len(rows))
    frequency_main = math.prod(weights[i - 1] for i in combo) / norm
    qr_main = masses[bucket] / sizes[bucket]
    fair_main = 1 / TOTAL
    probabilities = {'uniform': (fair_main, 1 / 12 if special is not None else None),
                     'frequency': (frequency_main, special_probs[special - 1] if special is not None else None),
                     'qr': (qr_main, special_probs[special - 1] if special is not None else None)}
    performance = None
    if len(rows) > 400:
        from rng_lab import history_digest
        historical = _retrospective(rows, 535, 200, 200, history_digest(rows))
        performance = {
            'status': 'retrospective_already_inspected',
            'config': historical['config'], 'test_draw_ids': historical['test_draw_ids'],
            'test': historical['test'],
            'note': 'Fixed train=200, validation=200; descriptive historical scores, not prospective evidence.',
        }
    d2 = distance_squared(combo)
    return {
        'main': list(combo), 'special': special, 'trained_draws': len(rows),
        'qr_bin': bucket, 'd2': d2,
        'inside_qr80': d2 <= QR80_THRESHOLD,
        'models': {name: {'main': p, 'special': sp, 'joint': p * sp if sp is not None else None,
                          'main_ratio_vs_uniform': p * TOTAL,
                          'joint_ratio_vs_uniform': p * sp * TOTAL * 12 if sp is not None else None}
                   for name, (p, sp) in probabilities.items()},
        'retrospective_performance': performance,
        'note': 'Xác suất mô hình được gán sau khi đã xem lịch sử đầu vào; không phải xác suất trúng thực tế nếu quay công bằng.'
    }


def _snapshot(rows):
    return [{'draw_id': row['draw_id'], 'date': row['date'],
             'combo': list(row['combo']), 'special': row['special']} for row in rows]


def _prospective(rows, manifest, digest):
    from rng_lab import history_digest

    if not isinstance(manifest, dict):
        raise ValueError('manifest không hợp lệ')
    cfg = manifest.get('config')
    if not isinstance(cfg, dict):
        raise ValueError('thiếu cấu hình manifest')
    seed, train, validation = (cfg.get('seed'), cfg.get('min_train'), cfg.get('validation'))
    if (type(seed) is not int or seed < 0 or type(train) is not int or train < 1
            or type(validation) is not int or validation < 1
            or cfg != _config(seed, train, validation)):
        raise ValueError('cấu hình manifest không khớp phiên bản/tham chiếu hiện tại')
    length, last_id, prefix_hash = (manifest.get('prefix_draws'), manifest.get('last_draw_id'),
                                    manifest.get('prefix_sha256'))
    if (type(length) is not int or length < train + validation or len(rows) < length
            or type(last_id) is not int or rows[length - 1]['draw_id'] != last_id
            or not isinstance(prefix_hash, str)
            or history_digest(rows[:length]) != prefix_hash
            or manifest.get('prefix_records') != _snapshot(rows[:length])):
        raise ValueError('tiền tố lịch sử thay đổi hoặc bị rút ngắn; từ chối đánh giá prospective')
    selected = manifest.get('selected_model')
    if (selected not in ('frequency', 'qr') or
            manifest.get('selection_rule') != SELECTION_RULE or
            not isinstance(manifest.get('validation'), dict) or
            _select(manifest['validation']) != selected):
        raise ValueError('manifest không nhất quán với chọn mô hình validation đã khóa')
    appended = rows[length:]
    report = {
        'mode': 'prospective', 'status': 'prospective' if appended else 'pending',
        'note': ('Chỉ đánh giá những kỳ bổ sung sau khi khóa; không chứng minh lợi thế dự báo.'
                 if appended else 'Chưa có kỳ mới sau khi khóa; chưa có kết quả prospective.'),
        'config': cfg, 'locked_prefix_sha256': prefix_hash, 'history_sha256': digest,
        'locked_last_draw_id': last_id, 'history_draws': len(rows), 'evaluated_draws': len(appended),
        'selected_model': selected, 'selection_rule': SELECTION_RULE,
        'evaluated_draw_ids': [appended[0]['draw_id'], appended[-1]['draw_id']] if appended else None,
        'test': None, 'next_ticket': None,
        'evidence': {'prospective': bool(appended), 'n_new': len(appended),
                     'selected_model': selected, 'log_evalue': None, 'prefix_verified': True},
    }
    if appended:
        state = _state(rows[:length])
        report['test'] = _evaluate(appended, state, seed)
        report['evidence']['log_evalue'] = len(appended) * (
            report['test']['uniform']['mean_logloss_joint'] -
            report['test'][selected]['mean_logloss_joint'])
        report['next_ticket'] = _next_ticket(state, seed, rows[-1]['draw_id'] + 1, selected)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='So sánh xác suất 5+1 theo thời gian; không bảo đảm lợi thế dự báo.')
    parser.add_argument('--source', type=Path, default=DATA, help='Lịch sử JSON hoặc SQLite')
    parser.add_argument('--min-train', type=int, default=None, help='Số kỳ train ban đầu (mặc định 200)')
    parser.add_argument('--validation', type=int, default=None, help='Số kỳ validation (mặc định 200)')
    parser.add_argument('--seed', type=int, default=None, help='Hạt giống vé QR và vé quay đều (mặc định 535)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--lock', type=Path, help='Tạo manifest khóa từ lịch sử hiện tại (chỉ tạo mới)')
    group.add_argument('--prospective', type=Path, help='Chấm kỳ mới theo manifest đã khóa, không chọn lại')
    parser.add_argument('--output', type=Path, help='Ghi báo cáo JSON (chỉ tạo mới); mặc định in stdout')
    args = parser.parse_args(argv)
    from rng_lab import history_digest, load_history

    try:
        rows = load_history(args.source)
        if not rows:
            raise ValueError('lịch sử trống')
        digest = history_digest(rows)
        if args.lock is not None and args.output is not None and args.lock.resolve() == args.output.resolve():
            raise ValueError('manifest và báo cáo phải là hai đường dẫn khác nhau')
        if args.output is not None and args.output.exists():
            raise ValueError(f'báo cáo đã tồn tại: {args.output}')
        if args.prospective is not None:
            with args.prospective.open(encoding='utf-8') as f:
                manifest = json.load(f)
            cfg = manifest.get('config') if isinstance(manifest, dict) else None
            if not isinstance(cfg, dict):
                raise ValueError('manifest không hợp lệ')
            for supplied, key in ((args.seed, 'seed'), (args.min_train, 'min_train'),
                                  (args.validation, 'validation')):
                if supplied is not None and supplied != cfg.get(key):
                    raise ValueError(f'--{key.replace("_", "-")} khác manifest đã khóa')
            report = _prospective(rows, manifest, digest)
            report['locked_manifest_path'] = str(args.prospective)
        else:
            seed = args.seed if args.seed is not None else 535
            train = args.min_train if args.min_train is not None else 200
            validation = args.validation if args.validation is not None else 200
            if seed < 0 or train < 1 or validation < 1:
                raise ValueError('seed không âm, min-train và validation phải dương')
            report = _retrospective(rows, seed, train, validation, digest)
            if args.lock is not None:
                manifest = {
                    'config': report['config'], 'prefix_draws': len(rows),
                    'prefix_sha256': digest, 'last_draw_id': rows[-1]['draw_id'],
                    'prefix_records': _snapshot(rows),
                    'selected_model': report['selected_model'], 'selection_rule': report['selection_rule'],
                    'validation': report['validation'],
                    'note': 'Khóa sau khi đã xem lịch sử; chỉ các kỳ bổ sung sau khi khóa mới là prospective.'
                }
                with args.lock.open('x', encoding='utf-8') as f:
                    json.dump(manifest, f, ensure_ascii=False, indent=2, allow_nan=False)
                    f.write('\n')
                report['locked_manifest_path'] = str(args.lock)
        report['source'] = str(args.source)
        report['provenance'] = {'version': VERSION, 'seed': report['config']['seed'],
                                'data_sha256': digest, 'last_id': rows[-1]['draw_id']}
        encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output is None:
            print(encoded, end='')
        else:
            with args.output.open('x', encoding='utf-8') as f:
                f.write(encoded)
    except (OSError, ValueError, TypeError, KeyError, OverflowError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
