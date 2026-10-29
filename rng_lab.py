#!/usr/bin/env python3
"""Exact QR reference and controlled RNG hypotheses, not an OKC emulator."""
import argparse
from functools import lru_cache
import hashlib
from itertools import chain, combinations
import json
import math
from pathlib import Path
import platform
import sqlite3

import numpy as np

from qr_backtest import load_draws, wilson_interval
from qr_filter import MU, INV_COV, QR80_SIZE, QR80_THRESHOLD, distance_squared

VERSION = 1
TOTAL = math.comb(35, 5)
DEFAULT_SOURCE = Path(__file__).resolve().with_name('vietlott_535.json')
MODELS = ('uniform', 'B1', 'B2', 'B3', 'B4', 'B5')
STAT_NAMES = ('main_frequency', 'special_frequency', 'adjacent_overlap',
              'qr_shape', 'lag16_recurrence')
HYPOTHESES = {
    'uniform': 'Uniform combination index + independent uniform special; PCG64 research simulator.',
    'B1': 'Mixture with uniform subsets conditioned on containing number 1; special stays fair.',
    'B2': 'Mixture with byte modulo 35, reject entire duplicate rows; special byte modulo 12.',
    'B3': 'With probability strength copy previous main subset; special stays independent.',
    'B4': 'Each 16-draw block replays a fixed main/special template with probability strength.',
    'B5': 'Mixture with uniform subsets conditioned on the existing QR80 region; special fair.',
}


@lru_cache(maxsize=1)
def reference():
    combos = np.fromiter(chain.from_iterable(combinations(range(1, 36), 5)),
                         dtype=np.int16, count=TOTAL * 5).reshape(TOTAL, 5)
    features = np.column_stack((combos.sum(1), (combos % 2).sum(1),
                               (combos >= 18).sum(1), combos[:, -1] - combos[:, 0],
                               (np.diff(combos, axis=1) == 1).sum(1))).astype(float)
    centered = features - np.asarray(MU)
    # Match scalar accumulation order and the published rounded inverse exactly.
    d2 = np.zeros(TOTAL)
    for i in range(5):
        for j in range(5):
            d2 += centered[:, i] * INV_COV[i][j] * centered[:, j]
    inside = d2 <= QR80_THRESHOLD
    if int(inside.sum()) != QR80_SIZE:
        raise RuntimeError('Existing QR threshold and combination volume disagree')
    cuts = np.quantile(d2, [0.2, 0.4, 0.6, 0.8], method='inverted_cdf')
    bins = np.searchsorted(cuts, d2, side='left')
    return dict(combos=combos, features=features, d2=d2, inside=inside,
                cuts=cuts, bins=bins, bin_counts=np.bincount(bins, minlength=5))


def load_history(source):
    source = Path(source)
    draws = load_draws(source)
    if source.suffix.lower() == '.json':
        records = json.loads(source.read_text(encoding='utf-8'))
    else:
        with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as conn:
            conn.row_factory = sqlite3.Row
            records = [dict(r) for r in conn.execute('SELECT draw_id, special FROM draws')]
    specials = {}
    for r in records:
        identifier, special = int(r['draw_id']), int(r['special'])
        if not 1 <= special <= 12 or identifier in specials:
            raise ValueError('Invalid special number or duplicate draw ID')
        specials[identifier] = special
    if not draws:
        raise ValueError('Empty history')
    if any(b[0] != a[0] + 1 for a, b in zip(draws, draws[1:])):
        raise ValueError('Missing draw IDs: sequence tests require contiguous history')
    return [dict(draw_id=i, date=d.strftime('%d/%m/%Y'), combo=c, special=specials[i])
            for i, d, c in draws]


def history_digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def provenance(seed=None, rows=None):
    info = dict(version=VERSION, python=platform.python_version(), numpy=np.__version__,
                generator='NumPy PCG64', seed=seed,
                warning='Controlled hypotheses only; not a reconstruction of OKC/SmartPlay RNG.')
    if rows is not None:
        info.update(n_draws=len(rows), first_id=rows[0]['draw_id'], last_id=rows[-1]['draw_id'],
                    data_sha256=history_digest(rows))
    return info


def json_output(value, path=None):
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    if path:
        with Path(path).open('x', encoding='utf-8') as out:
            out.write(text + '\n')
    print(text)


def rank_combos(combos):
    """Lexicographic rank for sorted 1-based five-subsets, vectorized."""
    combos = np.asarray(combos, dtype=int)
    result = np.zeros(len(combos), dtype=np.int64)
    previous = np.zeros(len(combos), dtype=int)
    for j in range(5):
        remaining = 5 - j
        table = np.array([math.comb(k, remaining) if k >= remaining else 0
                          for k in range(36)], dtype=np.int64)
        result += table[35 - previous] - table[36 - combos[:, j]]
        previous = combos[:, j]
    return result


class Simulator:
    """Bounded-memory reproducible stream; same results for a fixed batch configuration."""
    def __init__(self, model, strength, seed):
        if model not in MODELS or not math.isfinite(strength) or not 0 <= strength <= 1:
            raise ValueError('Unknown model or strength outside [0,1]')
        self.model, self.strength = model, strength
        self.rng = np.random.Generator(np.random.PCG64(seed))
        self.previous = None
        self.offset = 0
        self.template = None
        self.replay = False
        ref = reference()
        self.preferred = np.flatnonzero(ref['combos'][:, 0] == 1) if model == 'B1' else (
            np.flatnonzero(ref['inside']) if model == 'B5' else None)
        if model == 'B4':
            self.template = (self.rng.integers(TOTAL, size=16), self.rng.integers(1, 13, size=16))

    def generate(self, n):
        rng = self.rng
        indices = rng.integers(TOTAL, size=n)
        specials = rng.integers(1, 13, size=n)
        if self.model in ('B1', 'B5'):
            mask = rng.random(n) < self.strength
            indices[mask] = rng.choice(self.preferred, size=int(mask.sum()))
        elif self.model == 'B2':
            mask = rng.random(n) < self.strength
            k = int(mask.sum())
            numbers = np.sort(rng.integers(0, 256, size=(k, 5)) % 35 + 1, axis=1)
            duplicate = np.any(np.diff(numbers, axis=1) == 0, axis=1)
            while duplicate.any():
                numbers[duplicate] = np.sort(rng.integers(0, 256, size=(int(duplicate.sum()), 5)) % 35 + 1, axis=1)
                duplicate = np.any(np.diff(numbers, axis=1) == 0, axis=1)
            indices[mask] = rank_combos(numbers)
            specials[mask] = rng.integers(0, 256, size=k) % 12 + 1
        elif self.model == 'B3':
            copy = rng.random(n) < self.strength
            for i in range(n):
                if copy[i] and self.previous is not None:
                    indices[i] = self.previous
                self.previous = indices[i]
        elif self.model == 'B4':
            start = 0
            while start < n:
                pos = (self.offset + start) % 16
                if pos == 0:
                    self.replay = rng.random() < self.strength
                take = min(16 - pos, n - start)
                if self.replay:
                    indices[start:start + take] = self.template[0][pos:pos + take]
                    specials[start:start + take] = self.template[1][pos:pos + take]
                start += take
        self.offset += n
        return indices, specials


def statistics(indices, specials):
    ref = reference()
    n = len(indices)
    if n < 17:
        raise ValueError('At least 17 draws required for lag16 diagnostics')
    balls = ref['combos'][indices]
    counts = np.bincount(balls.ravel(), minlength=36)[1:]
    sp_counts = np.bincount(specials, minlength=13)[1:]
    overlaps = (balls[1:, :, None] == balls[:-1, None, :]).sum(axis=(1, 2))
    overlap_mean = 25 / 35
    overlap_var = 5 * (5 / 35) * (30 / 35) * (30 / 34)
    bcounts = np.bincount(ref['bins'][indices], minlength=5)
    expected_bins = n * ref['bin_counts'] / TOTAL
    return np.array([
        ((counts - n / 7) ** 2 / (n / 7)).sum(),
        ((sp_counts - n / 12) ** 2 / (n / 12)).sum(),
        abs(overlaps.mean() - overlap_mean) / math.sqrt(overlap_var / (n - 1)),
        ((bcounts - expected_bins) ** 2 / expected_bins).sum(),
        (indices[16:] == indices[:-16]).sum(),
    ], dtype=float)


def null_bank(n, repetitions, seed_sequence):
    rng = np.random.default_rng(seed_sequence)
    return np.array([statistics(rng.integers(TOTAL, size=n), rng.integers(1, 13, size=n))
                     for _ in range(repetitions)])


def marginal_p(values, bank):
    values = np.atleast_2d(values)
    return np.column_stack([(1 + len(bank) - np.searchsorted(np.sort(bank[:, j]), values[:, j], side='left'))
                            / (len(bank) + 1) for j in range(bank.shape[1])])


def omnibus(values, calibration):
    # Max surprise over the predeclared family; upper-tail/ties are conservative.
    return -np.log(marginal_p(values, calibration).min(axis=1))


def global_p(values, calibration, null_scores):
    scores = omnibus(values, calibration)
    return (1 + len(null_scores) - np.searchsorted(np.sort(null_scores), scores, side='left')) / (len(null_scores) + 1)


def exact_report():
    ref = reference()
    distributions = []
    for j, name in enumerate(('sum', 'odd', 'high_ge18', 'span', 'adjacent_pairs')):
        values, counts = np.unique(ref['features'][:, j], return_counts=True)
        distributions.append(dict(feature=name, counts={str(int(v)): int(c) for v, c in zip(values, counts)}))
    return dict(provenance=provenance(), total_main=TOTAL, total_5plus1=12 * TOTAL,
                fair_ticket_probability=1 / (12 * TOTAL), mean=ref['features'].mean(0).tolist(),
                covariance_population=np.cov(ref['features'], rowvar=False, bias=True).tolist(),
                distance_definition='Existing qr_filter.MU and rounded INV_COV; not refit to history.',
                qr_threshold=QR80_THRESHOLD, qr_size=int(ref['inside'].sum()), qr_coverage=QR80_SIZE / TOTAL,
                bin_cuts=ref['cuts'].tolist(), bin_counts=ref['bin_counts'].tolist(),
                feature_distributions=distributions)


def audit(rows, repetitions, seed):
    seeds = np.random.SeedSequence(seed).spawn(2)
    calibration = null_bank(len(rows), repetitions, seeds[0])
    bank = null_bank(len(rows), repetitions, seeds[1])
    indices = rank_combos([r['combo'] for r in rows])
    observed = statistics(indices, np.array([r['special'] for r in rows]))
    raw_p = marginal_p(observed, calibration)[0]
    return dict(provenance=provenance(seed, rows), repetitions_per_bank=repetitions,
                method='Independent marginal calibration and max-surprise null bank; familywise Monte Carlo p.',
                exploratory=True, null='iid uniform five-subsets and independent uniform special',
                statistics={name: dict(value=float(v), raw_p=float(p),
                                      bonferroni_p=min(1., float(p) * len(STAT_NAMES)))
                            for name, v, p in zip(STAT_NAMES, observed, raw_p)},
                familywise_p=float(global_p(observed, calibration, omnibus(bank, calibration))[0]),
                caveat='Exploratory historical audit; not RNG certification, fault attribution or predictive evidence.')


def power(lengths, strengths, repetitions, seed, alpha):
    seeds = iter(np.random.SeedSequence(seed).spawn(len(lengths) * (3 + 5 * len(strengths))))
    results = []
    for n in lengths:
        calibration = null_bank(n, repetitions, next(seeds))
        bank = null_bank(n, repetitions, next(seeds))
        null_scores = omnibus(bank, calibration)
        validation = null_bank(n, repetitions, next(seeds))
        k = int((global_p(validation, calibration, null_scores) <= alpha).sum())
        row = dict(n_draws=n, false_positive=dict(rejected=k, trials=repetitions,
                   rate=k / repetitions, wilson95=list(wilson_interval(k, repetitions))), alternatives=[])
        for model in MODELS[1:]:
            for strength in strengths:
                rng = np.random.default_rng(next(seeds))
                stats = []
                for _ in range(repetitions):
                    sim = Simulator(model, strength, int(rng.integers(0, 2**63)))
                    stats.append(statistics(*sim.generate(n)))
                k = int((global_p(np.array(stats), calibration, null_scores) <= alpha).sum())
                row['alternatives'].append(dict(model=model, strength=strength, rejected=k,
                    trials=repetitions, power=k / repetitions,
                    wilson95=list(wilson_interval(k, repetitions))))
        results.append(row)
    detectable = []
    for model in MODELS[1:]:
        for strength in strengths:
            candidates = [r['n_draws'] for r in results if any(
                a['model'] == model and a['strength'] == strength and a['wilson95'][0] >= .8
                for a in r['alternatives'])]
            detectable.append(dict(model=model, strength=strength,
                                   smallest_tested_n_with_power_lower95_ge80=min(candidates) if candidates else None))
    return dict(provenance=provenance(seed), alpha=alpha, repetitions_per_bank=repetitions,
                statistics=list(STAT_NAMES), hypotheses=HYPOTHESES,
                definition='strength is a mixture/reset/copy probability, NOT an estimated real-world bias.',
                method='Independent calibration, max-surprise null, independent fair validation and fault banks.',
                results=results, sample_size_grid=detectable,
                caveat='Power applies only to specified faults and tested lengths; null means insufficient grid evidence, not impossible detection.')


def simulate(n, batch_size, model, strength, seed):
    sim = Simulator(model, strength, seed)
    ref = reference()
    main = np.zeros(35, dtype=np.int64)
    special = np.zeros(12, dtype=np.int64)
    qr = 0
    digest = hashlib.sha256()
    for start in range(0, n, batch_size):
        indices, sp = sim.generate(min(batch_size, n - start))
        main += np.bincount(ref['combos'][indices].ravel(), minlength=36)[1:]
        special += np.bincount(sp, minlength=13)[1:]
        qr += int(ref['inside'][indices].sum())
        # Explicit endian and fixed record layout; records are not stored on disk.
        records = np.empty((len(indices), 2), dtype='<i8')
        records[:, 0], records[:, 1] = indices, sp
        digest.update(records.tobytes())
    return dict(provenance=provenance(seed), model=model, hypothesis=HYPOTHESES[model],
                strength=strength, draws=n, batch_size=batch_size,
                stream_sha256=digest.hexdigest(), main_counts=main.tolist(), special_counts=special.tolist(),
                qr_hits=qr, qr_coverage=qr / n,
                reproducibility='Fix NumPy version, seed, model, strength AND batch size; no billion-row history is retained.')


def ticket_report(numbers, rows=None):
    if len(numbers) not in (5, 6):
        raise ValueError('Provide five main numbers and optionally one special')
    combo = tuple(sorted(numbers[:5]))
    if len(set(combo)) != 5 or combo[0] < 1 or combo[-1] > 35:
        raise ValueError('Five distinct main numbers must be in 1..35')
    special = numbers[5] if len(numbers) == 6 else None
    if special is not None and not 1 <= special <= 12:
        raise ValueError('Special must be in 1..12')
    ref = reference()
    idx = int(rank_combos([combo])[0])
    d2 = distance_squared(combo)
    result = dict(combo=list(combo), special=special, fair_main_probability=1 / TOTAL,
                  fair_special_probability=1 / 12, fair_5plus1_probability=1 / (12 * TOTAL),
                  feature_names=['sum', 'odd', 'high_ge18', 'span', 'adjacent_pairs'],
                  features=ref['features'][idx].astype(int).tolist(), d2=d2,
                  d2_percentile=float(np.mean(ref['d2'] <= d2)), inside_qr80=bool(d2 <= QR80_THRESHOLD),
                  qr_coverage=QR80_SIZE / TOTAL,
                  warning='QR describes morphology, not individual winning probability; model probabilities are unproven assignments.')
    if rows is not None:
        from rng_forecast import report_ticket
        result['models'] = report_ticket(rows, combo, special)
        result['provenance'] = provenance(rows=rows)
    return result


def main(argv=None):
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == 'forecast':
        from rng_forecast import main as forecast_main
        return forecast_main(argv[1:])
    if argv and argv[0] == 'neural':
        from rng_neural import main as neural_main
        return neural_main(argv[1:])
    parser = argparse.ArgumentParser(description='QR RNG laboratory; controlled hypotheses, not an OKC clone.')
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('forecast', help='Chronological comparison and locked prospective evaluation')
    subs.add_parser('neural', help='Evidence-gated PyTorch/Colab experiment')
    for name in ('reference', 'audit', 'power', 'simulate', 'ticket'):
        p = subs.add_parser(name)
        p.add_argument('--output', type=Path, help='Create new JSON artifact, never overwrite')
        if name in ('audit', 'ticket'):
            p.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
        if name in ('audit', 'power', 'simulate'):
            p.add_argument('--seed', type=int, default=20261029)
        if name in ('audit', 'power'):
            p.add_argument('--repetitions', type=int, default=500)
        if name == 'power':
            p.add_argument('--lengths', type=int, nargs='+', default=[250, 976, 2000])
            p.add_argument('--strengths', type=float, nargs='+', default=[.02, .10, .30])
            p.add_argument('--alpha', type=float, default=.05)
        if name == 'simulate':
            p.add_argument('--draws', type=int, default=1000000)
            p.add_argument('--batch-size', type=int, default=100000)
            p.add_argument('--model', choices=MODELS, default='uniform')
            p.add_argument('--strength', type=float, default=.1)
        if name == 'ticket':
            p.add_argument('numbers', nargs='+', type=int)
            p.add_argument('--no-history', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command in ('audit', 'power') and args.repetitions < 99:
            raise ValueError('Use at least 99 repetitions per bank; prefer >=999 for reporting')
        if args.command == 'reference':
            result = exact_report()
        elif args.command == 'audit':
            result = audit(load_history(args.source), args.repetitions, args.seed)
        elif args.command == 'power':
            if min(args.lengths) < 17 or not 0 < args.alpha < 1 or any(
                    not math.isfinite(s) or not 0 <= s <= 1 for s in args.strengths):
                raise ValueError('Invalid lengths, alpha or strength')
            result = power(sorted(set(args.lengths)), sorted(set(args.strengths)),
                           args.repetitions, args.seed, args.alpha)
        elif args.command == 'simulate':
            if args.draws < 1 or args.batch_size < 1 or args.draws > np.iinfo(np.int64).max // 5:
                raise ValueError('Draw count and batch size must be positive and counters must fit int64')
            result = simulate(args.draws, args.batch_size, args.model, args.strength, args.seed)
        else:
            result = ticket_report(args.numbers, None if args.no_history else load_history(args.source))
        json_output(result, args.output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
