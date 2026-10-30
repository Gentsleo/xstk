#!/usr/bin/env python3
"""Audit the frozen production gate and chronological theoretical QR coverage.

The theoretical walk-forward test trains only its changing cutoff. The production
gate instead uses coefficients frozen from draws 1..954: observations through
954 are retrospective calibration, never an unseen holdout for that gate.
Neither region coverage nor historical inclusion measures ticket win odds.
"""

import argparse
from bisect import bisect_right, insort
from datetime import datetime
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import sqlite3

from qr_filter import (CALIBRATION_LAST_DRAW, EMPIRICAL_INV_COV, EMPIRICAL_MU,
                       MIN_ENTROPY, MIN_SQS, QR80_SIZE, QR80_THRESHOLD,
                       distance_squared, score_main)


TOTAL_COMBINATIONS = math.comb(35, 5)
QUANTILE = 0.80
DEFAULT_JSON = Path(__file__).resolve().with_name("vietlott_535.json")
DEFAULT_DB = Path(__file__).resolve().with_name("vietlott_535.db")

MODEL_REFERENCE = "f597fffb6ec5a3ab19134185815fd1e4eddc12ea"



def load_draws(path):
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as source:
            rows = json.load(source)
        if not isinstance(rows, list):
            raise ValueError("JSON source must be a list of draw records")
    elif path.suffix.lower() in (".db", ".sqlite", ".sqlite3"):
        # URI mode=ro must not silently create a missing database.
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = [dict(row) for row in conn.execute(
                "SELECT draw_id, date, num1, num2, num3, num4, num5 "
                "FROM draws ORDER BY draw_id ASC")]
    else:
        raise ValueError("Source must be a .json or .db/.sqlite/.sqlite3 file")

    parsed = []
    for position, row in enumerate(rows, 1):
        try:
            identifier = int(row["draw_id"])
            date_text = row["date"]
            date = datetime.strptime(date_text, "%d/%m/%Y").date()
            combo = tuple(sorted(int(row[f"num{j}"]) for j in range(1, 6)))
            if identifier < 1 or len(set(combo)) != 5 or combo[0] < 1 or combo[-1] > 35:
                raise ValueError("invalid draw ID or five main balls")
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise ValueError(f"Invalid draw at source row {position}: {exc}") from exc
        parsed.append((identifier, date, combo))

    parsed.sort(key=lambda draw: draw[0])
    for previous, current in zip(parsed, parsed[1:]):
        if previous[0] == current[0]:
            raise ValueError(f"Duplicate draw_id {current[0]}")
        if previous[1] > current[1]:
            raise ValueError(f"Draw date decreases from #{previous[0]} to #{current[0]}; "
                             "cannot trust chronological order")
    return parsed


def percentile_80(sorted_distances):
    """Nearest-rank empirical P80, including all ties at the cutoff."""
    return sorted_distances[math.ceil(QUANTILE * len(sorted_distances)) - 1]


def wilson_interval(successes, count):
    """Unadjusted two-sided 95% Wilson interval for the fixed-rule rate."""
    z = 1.959963984540054
    p = successes / count
    denominator = 1 + z * z / count
    center = (p + z * z / (2 * count)) / denominator
    margin = z * math.sqrt(p * (1 - p) / count + z * z / (4 * count * count)) / denominator
    return center - margin, center + margin


def describe_draw(draw):
    identifier, date, _ = draw
    return f"#{identifier:05d} ({date.isoformat()})"


def run(draws, min_train, source):
    if len(draws) <= min_train:
        raise ValueError(f"Need more than {min_train} valid draws (training prefix plus "
                         f"at least one held-out draw); found {len(draws)} in {source}")

    # Fixed theoretical reference enumerated exactly once, independent of the
    # observed draws; a binary search determines each changing region's volume.
    reference = sorted(distance_squared(combo)
                       for combo in combinations(range(1, 36), 5))
    if len(reference) != TOTAL_COMBINATIONS:
        raise RuntimeError("Theoretical combination enumeration is incomplete")
    fixed_volume = bisect_right(reference, QR80_THRESHOLD)
    if fixed_volume != QR80_SIZE:
        raise RuntimeError(f"QR coefficients/threshold no longer agree with the "
                           f"published reference size: {fixed_volume} != {QR80_SIZE}")

    # The fixed feature map is never fit to history. Only the empirical rank
    # threshold learns, first on the prefix, then after each test observation.
    history = sorted(distance_squared(combo) for _, _, combo in draws[:min_train])
    learned_hits = fixed_hits = both_hits = 0
    expected = variance = 0.0
    first_cutoff = last_cutoff = None
    first_volume = last_volume = None
    for _, _, combo in draws[min_train:]:
        cutoff = percentile_80(history)  # computed before observing this draw
        volume = bisect_right(reference, cutoff)
        p_fair = volume / TOTAL_COMBINATIONS
        observed_distance = distance_squared(combo)
        learned = observed_distance <= cutoff
        fixed = observed_distance <= QR80_THRESHOLD
        learned_hits += learned
        fixed_hits += fixed
        both_hits += learned and fixed
        expected += p_fair
        variance += p_fair * (1 - p_fair)
        if first_cutoff is None:
            first_cutoff, first_volume = cutoff, volume
        last_cutoff, last_volume = cutoff, volume
        insort(history, observed_distance)  # update strictly AFTER scoring

    holdout = draws[min_train:]
    n = len(holdout)
    low, high = wilson_interval(fixed_hits, n)
    fixed_p = fixed_volume / TOTAL_COMBINATIONS
    fixed_expected = n * fixed_p
    fixed_sd = math.sqrt(n * fixed_p * (1 - fixed_p))
    missing_ids = draws[-1][0] - draws[0][0] + 1 - len(draws)
    print(f"Source: {source} ({len(draws)} draws; {missing_ids} missing draw IDs in range)")
    print(f"Training prefix: {min_train} draws, {describe_draw(draws[0])} to "
          f"{describe_draw(draws[min_train - 1])}")
    print(f"Held-out one-step-forward: {n} draws, {describe_draw(holdout[0])} to "
          f"{describe_draw(holdout[-1])}")
    print("Features: fixed theoretical MU/INV_COV; only the empirical nearest-rank "
          "P80 cutoff is updated after each held-out draw (ties included).")
    print(f"Fixed theoretical QR cutoff D² <= {QR80_THRESHOLD:.15f}: "
          f"{fixed_volume}/{TOTAL_COMBINATIONS} main combinations; "
          f"fair inclusion probability {fixed_p:.4%}.")
    print(f"Fixed-rule held-out coverage: {fixed_hits}/{n} ({fixed_hits/n:.2%}); "
          f"fair expectation {fixed_expected:.1f}/{n}, "
          f"fair SD {fixed_sd:.1f} hits; observed minus fair expectation "
          f"{fixed_hits - fixed_expected:+.1f} hits; unadjusted 95% Wilson "
          f"interval [{low:.2%}, {high:.2%}].")
    print(f"Trained-rule held-out coverage: {learned_hits}/{n} ({learned_hits/n:.2%}); "
          f"conditional fair expectation {expected:.1f}/{n} ({expected/n:.2%}), "
          f"approx. fair SD {math.sqrt(variance):.1f} hits; observed minus "
          f"conditional fair expectation {learned_hits - expected:+.1f} hits.")
    print(f"Learned regions at first/last held-out prediction: cutoff "
          f"{first_cutoff:.9f}/{last_cutoff:.9f}; volume "
          f"{first_volume}/{last_volume} ({first_volume/TOTAL_COMBINATIONS:.2%}/"
          f"{last_volume/TOTAL_COMBINATIONS:.2%} of fair combinations).")
    print(f"Paired overlap: both {both_hits}, fixed only {fixed_hits - both_hits}, "
          f"trained only {learned_hits - both_hits}, "
          f"neither {n - fixed_hits - learned_hits + both_hits}.")
    if n < 30:
        print("Caution: fewer than 30 held-out draws; rate/normal-approximation "
              "summaries are especially imprecise.")
    print("Interpretation: coverage measures how often a drawn main combination "
          "falls within a region, NOT the chance a chosen ticket wins. Under a "
          f"fair draw every specified main ticket has probability 1/{TOTAL_COMBINATIONS}; "
          f"each specified 5+special ticket has probability 1/{TOTAL_COMBINATIONS * 12}. "
          "A region containing many combinations is expected to cover many fair draws "
          "without improving per-ticket odds. The special ball is not modeled.")
    print("Uncertainty: the fixed-rule Wilson interval assumes independent fair "
          "draws; the trained-rule conditional expectation/SD is a descriptive "
          "fair-draw benchmark with adaptive past-only cutoffs, not a formal "
          "post-selection confidence interval. Searching multiple windows, "
          "thresholds or models multiplies false-positive opportunities; these "
          "unadjusted comparisons establish no predictive advantage or reason "
          "to adopt the trained cutoff automatically.")


def production_audit(draws, source):
    """Enumerate exact model/fair regions, then count chronological draw groups."""
    accepted = overlap = fair_volume = 0
    for combo in combinations(range(1, 36), 5):
        model = score_main(combo)
        fair = distance_squared(combo) <= QR80_THRESHOLD
        accepted += model["model_accepted"]
        fair_volume += fair
        overlap += model["model_accepted"] and fair
    if fair_volume != QR80_SIZE:
        raise RuntimeError(f"Fair QR reference size changed: {fair_volume} != {QR80_SIZE}")

    fair_probability = fair_volume / TOTAL_COMBINATIONS
    model_probability = accepted / TOTAL_COMBINATIONS

    def summarize(rows, label):
        n = len(rows)
        model_hits = fair_hits = both_hits = 0
        for _, _, combo in rows:
            selected = score_main(combo)["model_accepted"]
            fair = distance_squared(combo) <= QR80_THRESHOLD
            model_hits += selected
            fair_hits += fair
            both_hits += selected and fair
        return {
            "label": label,
            "count": n,
            "model_hits": model_hits,
            "model_rate": model_hits / n if n else None,
            "model_fair_expected_hits": n * model_probability,
            "fair_qr_hits": fair_hits,
            "fair_qr_rate": fair_hits / n if n else None,
            "fair_qr_expected_hits": n * fair_probability,
            "model_and_fair_qr_hits": both_hits,
            "model_wilson_95": list(wilson_interval(model_hits, n)) if n else None,
            "fair_qr_wilson_95": list(wilson_interval(fair_hits, n)) if n else None,
            "model_fair_sd_hits": math.sqrt(n * model_probability *
                                            (1 - model_probability)),
            "fair_qr_fair_sd_hits": math.sqrt(n * fair_probability *
                                            (1 - fair_probability)),
        }

    calibration = summarize([d for d in draws if d[0] <= CALIBRATION_LAST_DRAW],
                            "calibration/retrospective; NOT unseen holdout")
    post = summarize([d for d in draws if d[0] > CALIBRATION_LAST_DRAW],
                     "post-calibration draw_id > 954; retrospective if already examined")
    historical = summarize(draws, "all observed draws; includes calibration")
    digest = hashlib.sha256()
    with source.open("rb") as data:
        for chunk in iter(lambda: data.read(1024 * 1024), b""):
            digest.update(chunk)

    report = {
        "audit": "frozen empirical production main gate; no held-out tuning",
        "model_reference_commit": MODEL_REFERENCE,
        "source": str(source),
        "source_sha256": digest.hexdigest(),
        "coefficients": {
            "feature_order": ["sum", "odds", "highs_ge_18", "span", "consecutive_pairs"],
            "empirical_mu": EMPIRICAL_MU,
            "empirical_inv_cov": EMPIRICAL_INV_COV,
            "frozen_calibration_last_draw_id": CALIBRATION_LAST_DRAW,
            "sqs_min_inclusive": MIN_SQS,
            "gap_entropy_min_inclusive": MIN_ENTROPY,
            "sqs_formula": "round(100*(1-chi2CDF5(empirical_dm_sq))*(0.8+0.2*clamp((H-1)/(ln(6)-1),0,1)),1)",
            "gap_entropy_uses_unrounded_value": True,
        },
        "regions": {
            "total_main_combinations": TOTAL_COMBINATIONS,
            "model_accepted_main_combinations": accepted,
            "model_fair_inclusion_probability": model_probability,
            "fair_qr80_main_combinations": fair_volume,
            "fair_qr80_inclusion_probability": fair_probability,
            "model_and_fair_qr80_main_combinations": overlap,
            "fair_qr80_threshold": QR80_THRESHOLD,
            "fair_qr80_role": "separate fixed theoretical baseline, not the production gate",
        },
        "draws": {
            "historical": historical,
            "calibration_retrospective": calibration,
            "post_954": post,
        },
        "interpretation": {
            "region_coverage": "fraction of fair main combinations inside a fixed region",
            "historical_inclusion": "observed main draws inside each region, not ticket odds",
            "ticket_fair_main_jackpot_probability": 1 / TOTAL_COMBINATIONS,
            "ticket_fair_5_plus_special_jackpot_probability": 1 / (12 * TOTAL_COMBINATIONS),
            "special": "independently uniform in 1..12; not scored or gated",
            "uncertainty": "unadjusted Wilson 95% for observed model and QR rates under "
                           "independent draws; calibration and all-history are retrospective, "
                           "and examined post-954 draws are not an untouched prospective "
                           "holdout. Post-954 intervals exist only if such draws exist",
            "conclusion": "conditioning on model shape does not improve any fixed ticket's "
                          "fair-draw jackpot probability or prove predictive advantage",
        },
    }
    print(f"\nFrozen production model (source draws 1..{CALIBRATION_LAST_DRAW}; "
          f"commit {MODEL_REFERENCE}): SQS >= {MIN_SQS:g}, raw H >= {MIN_ENTROPY:.2f}.")
    print(f"Exact main gate: {accepted}/{TOTAL_COMBINATIONS} "
          f"({model_probability:.2%}) fair-region inclusion; model ∩ independent "
          f"theoretical QR80: {overlap}/{TOTAL_COMBINATIONS}.")
    print(f"Separate theoretical QR80 baseline: {fair_volume}/{TOTAL_COMBINATIONS} "
          f"({fair_probability:.2%}); it does not select production tickets.")
    for summary in (calibration, post, historical):
        n = summary["count"]
        rate = f'{summary["model_rate"]:.2%}' if n else "n/a"
        fair_rate = f'{summary["fair_qr_rate"]:.2%}' if n else "n/a"
        print(f"{summary['label']}: model {summary['model_hits']}/{n} ({rate}), "
              f"fair expected {summary['model_fair_expected_hits']:.1f}; "
              f"QR80 {summary['fair_qr_hits']}/{n} ({fair_rate}), "
              f"fair expected {summary['fair_qr_expected_hits']:.1f}.")
        if summary is post and n:
            low, high = summary["model_wilson_95"]
            fair_low, fair_high = summary["fair_qr_wilson_95"]
            print(f"Post-calibration unadjusted Wilson 95%: model "
                  f"[{low:.2%}, {high:.2%}], fair QR80 "
                  f"[{fair_low:.2%}, {fair_high:.2%}]; fair-draw SD "
                  f"{summary['model_fair_sd_hits']:.1f}/"
                  f"{summary['fair_qr_fair_sd_hits']:.1f} hits (model/QR80).")
    print("Only draw_id > 954 falls outside the coefficient calibration period; "
          "already examined later draws are retrospective, not untouched "
          "prospective validation. Region inclusion is not a per-ticket win "
          f"probability; under fair independent draws each fixed 5+1 ticket has "
          f"chance 1/{12 * TOTAL_COMBINATIONS}. No predictive advantage is established.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Draws .json or .db file "
                        "(default: project JSON, or project database if JSON absent)")
    parser.add_argument("--min-train", type=int, default=200, metavar="N",
                        help="Chronological prefix size before one-step-forward scoring "
                        "(at least 50; default: 200)")
    parser.add_argument("--output", type=Path, help="Save structured production audit JSON "
                        "(new file only; refuses to overwrite)")
    args = parser.parse_args()
    if args.min_train < 50:
        parser.error("--min-train must be at least 50 draws")
    source = args.source or (DEFAULT_JSON if DEFAULT_JSON.exists() else DEFAULT_DB)
    try:
        draws = load_draws(source)
        run(draws, args.min_train, source)
        report = production_audit(draws, source)
        if args.output is not None:
            with args.output.open("x", encoding="utf-8") as target:
                json.dump(report, target, ensure_ascii=False, indent=2)
                target.write("\n")
    except (OSError, ValueError, sqlite3.Error, json.JSONDecodeError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
