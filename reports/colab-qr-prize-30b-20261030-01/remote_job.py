import datetime
import itertools
import json
import math
import os
from pathlib import Path
import platform
import time

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import torch

TOTAL_MAIN = math.comb(35, 5)
TOTAL_TICKETS = TOTAL_MAIN * 12
TARGET_DRAWS = 30_000_000_000
BATCH_SIZE = 20_000_000
CHECKPOINT_EVERY_BATCHES = 100
SEED = 5_350_000_031
WINNING_DRAW_ID = 977
WINNING_MAIN = [3, 8, 21, 30, 34]
WINNING_SPECIAL = 11
EMPIRICAL_MU = [91.1069, 2.5681, 2.6237, 23.8512, 0.5755]
EMPIRICAL_INV_COV = [
    [0.009367, -0.004928, -0.164895, -0.000941, -0.008335],
    [-0.004928, 0.896688, 0.078079, -0.001084, -0.001216],
    [-0.164895, 0.078079, 3.775486, 0.027999, 0.141572],
    [-0.000941, -0.001084, 0.027999, 0.030715, 0.072989],
    [-0.008335, -0.001216, 0.141572, 0.072989, 2.300800],
]
MIN_SQS = 80.0
MIN_ENTROPY = 1.50
PRIZE_LABELS = [
    "jackpot_5_main_plus_special",
    "first_5_main",
    "second_4_main_plus_special",
    "third_4_main",
    "fourth_3_main_plus_special",
    "fifth_3_main",
    "encouragement_special_plus_0_to_2_main",
    "not_a_prize",
]
CHECKPOINT_PATH = Path("/content/qr_prize_30b_checkpoint.json")
REPORT_PATH = Path("/content/qr_prize_30b.json")


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
    temp.replace(path)


def chi2_cdf_5(x):
    if x <= 0:
        return 0.0
    s = x / 2.0
    return min(1.0, max(0.0, math.erf(math.sqrt(s)) -
        2.0 * math.sqrt(s / math.pi) * math.exp(-s) * (1.0 + 2.0 * s / 3.0)))


def exact_main_data():
    combos = torch.tensor(list(itertools.combinations(range(1, 36), 5)), dtype=torch.float64)
    odds = torch.remainder(combos, 2).sum(dim=1)
    highs = (combos >= 18).sum(dim=1)
    adjacent = (combos[:, 1:] - combos[:, :-1] == 1).sum(dim=1)
    features = torch.column_stack((combos.sum(dim=1), odds, highs,
                                   combos[:, 4] - combos[:, 0], adjacent))
    centered = features - torch.tensor(EMPIRICAL_MU, dtype=torch.float64)
    inverse = torch.tensor(EMPIRICAL_INV_COV, dtype=torch.float64)
    distance = torch.einsum("bi,ij,bj->b", centered, inverse, centered)
    gaps = torch.column_stack((combos[:, :1], combos[:, 1:] - combos[:, :-1], 36 - combos[:, -1:]))
    probabilities = gaps / 36.0
    entropy = -(probabilities * torch.log(probabilities)).sum(dim=1)
    p_main = torch.tensor([1.0 - chi2_cdf_5(float(value)) for value in distance], dtype=torch.float64)
    factor = ((entropy - 1.0) / (math.log(6.0) - 1.0)).clamp(0.0, 1.0)
    sqs = torch.round(1000.0 * p_main * (0.8 + 0.2 * factor)) / 10.0
    accepted = (sqs >= MIN_SQS) & (entropy >= MIN_ENTROPY)
    winner = torch.tensor(WINNING_MAIN, dtype=torch.float64)
    overlap = (combos[:, :, None] == winner[None, None, :]).any(dim=2).sum(dim=1).to(torch.int64)
    return accepted, overlap


def prize_codes(overlap, special_matches):
    codes = torch.full(overlap.shape, 7, device=overlap.device, dtype=torch.int64)
    codes[(overlap == 5) & special_matches] = 0
    codes[(overlap == 5) & ~special_matches] = 1
    codes[(overlap == 4) & special_matches] = 2
    codes[(overlap == 4) & ~special_matches] = 3
    codes[(overlap == 3) & special_matches] = 4
    codes[(overlap == 3) & ~special_matches] = 5
    codes[(overlap <= 2) & special_matches] = 6
    return codes


def named_counts(values):
    return {label: int(value) for label, value in zip(PRIZE_LABELS, values.tolist())}


if not torch.cuda.is_available():
    raise RuntimeError("CUDA required; refusing CPU fallback")
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
device = torch.device("cuda")
gpu_name = torch.cuda.get_device_name(device)
print(f"GPU: {gpu_name}", flush=True)
accepted_cpu, overlap_cpu = exact_main_data()
accepted_exact = int(accepted_cpu.sum().item())
if accepted_exact != 44_232:
    raise RuntimeError(f"Unexpected exact accepted volume: {accepted_exact}")
winning_combo_is_accepted = bool(accepted_cpu[overlap_cpu == 5].item())
matching_special = torch.ones(TOTAL_MAIN, dtype=torch.bool)
nonmatching_special = torch.zeros(TOTAL_MAIN, dtype=torch.bool)
exact_codes_matching = prize_codes(overlap_cpu, matching_special)
exact_codes_nonmatching = prize_codes(overlap_cpu, nonmatching_special)
exact_all = torch.bincount(exact_codes_matching, minlength=8) + 11 * torch.bincount(exact_codes_nonmatching, minlength=8)
exact_selected = (torch.bincount(exact_codes_matching[accepted_cpu], minlength=8) +
                  11 * torch.bincount(exact_codes_nonmatching[accepted_cpu], minlength=8))
if int(exact_all.sum()) != TOTAL_TICKETS or int(exact_selected.sum()) != accepted_exact * 12:
    raise RuntimeError("Exact ticket partition is incomplete")
accepted = accepted_cpu.to(device)
overlap = overlap_cpu.to(device)
all_counts = torch.zeros(8, dtype=torch.int64)
selected_counts = torch.zeros(8, dtype=torch.int64)
selected_ticket_count = 0
completed = 0
batch_number = 0
start = time.monotonic()
while completed < TARGET_DRAWS:
    n = min(BATCH_SIZE, TARGET_DRAWS - completed)
    indices = torch.randint(TOTAL_MAIN, (n,), device=device)
    special_matches = torch.randint(0, 12, (n,), device=device) == (WINNING_SPECIAL - 1)
    codes = prize_codes(overlap[indices], special_matches)
    selected = accepted[indices]
    all_counts += torch.bincount(codes, minlength=8).cpu()
    selected_counts += torch.bincount(codes[selected], minlength=8).cpu()
    selected_ticket_count += int(selected.sum().item())
    completed += n
    batch_number += 1
    if batch_number % CHECKPOINT_EVERY_BATCHES == 0 or completed == TARGET_DRAWS:
        elapsed = time.monotonic() - start
        checkpoint = {
            "state": "running" if completed < TARGET_DRAWS else "complete",
            "updated_at": utc_now(),
            "target_draws": TARGET_DRAWS,
            "completed_draws": completed,
            "all_prize_counts": named_counts(all_counts),
            "selected_ticket_count": selected_ticket_count,
            "selected_prize_counts": named_counts(selected_counts),
            "elapsed_seconds": elapsed,
        }
        write_json(CHECKPOINT_PATH, checkpoint)
        print(json.dumps(checkpoint), flush=True)

torch.cuda.synchronize()
elapsed = time.monotonic() - start
report = {
    "status": "complete",
    "purpose": "Prize-tier tally for 30B independent uniform 5+1 tickets against the already observed fixed draw #00977; exact enumeration supplies the reference probabilities.",
    "warning": "This is a retrospective arithmetic simulation against one fixed past draw. It is not a prediction, a payout forecast, or evidence that the gate improves odds.",
    "official_prize_rules": "https://vietlott.vn/vi/choi/lotto535/gioi-thieu-san-pham-535",
    "device": "cuda",
    "gpu_name": gpu_name,
    "torch_version": torch.__version__,
    "python_version": platform.python_version(),
    "seed": SEED,
    "target_draws": TARGET_DRAWS,
    "completed_draws": completed,
    "batch_size": BATCH_SIZE,
    "winning_draw": {"draw_id": WINNING_DRAW_ID, "main": WINNING_MAIN, "special": WINNING_SPECIAL},
    "winning_main_passes_gate": winning_combo_is_accepted,
    "exact_total_5_plus_1_tickets": TOTAL_TICKETS,
    "exact_all_ticket_category_counts": named_counts(exact_all),
    "exact_selected_ticket_category_counts": named_counts(exact_selected),
    "exact_selected_ticket_count": accepted_exact * 12,
    "all_ticket_category_counts": named_counts(all_counts),
    "selected_ticket_count": selected_ticket_count,
    "selected_ticket_category_counts": named_counts(selected_counts),
    "elapsed_seconds": elapsed,
    "throughput_draws_per_second": completed / elapsed,
    "generated_at": utc_now(),
}
write_json(REPORT_PATH, report)
write_json(CHECKPOINT_PATH, {"state": "complete", "report": str(REPORT_PATH), "updated_at": utc_now(), "completed_draws": completed})
print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
print("PRIZE_MONTE_CARLO_30B_COMPLETE", flush=True)
