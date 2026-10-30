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

TOTAL = math.comb(35, 5)
TARGET_DRAWS = 30_000_000_000
BATCH_SIZE = 20_000_000
CHECKPOINT_EVERY_BATCHES = 100
SEED = 5_350_000_030
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
REFERENCE_COMMIT = "f597fffb6ec5a3ab19134185815fd1e4eddc12ea"
CHECKPOINT_PATH = Path("/content/qr_gate_30b_checkpoint.json")
REPORT_PATH = Path("/content/qr_gate_30b.json")


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


def exact_gate_mask():
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
    return accepted


if not torch.cuda.is_available():
    raise RuntimeError("CUDA required; refusing CPU fallback")
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
device = torch.device("cuda")
gpu_name = torch.cuda.get_device_name(device)
print(f"GPU: {gpu_name}", flush=True)
mask_cpu = exact_gate_mask()
accepted_exact = int(mask_cpu.sum().item())
if accepted_exact != 44_232:
    raise RuntimeError(f"Unexpected exact accepted volume: {accepted_exact}")
mask = mask_cpu.to(device=device)
expected_probability = accepted_exact / TOTAL
start = time.monotonic()
accepted_draws = 0
special_counts = torch.zeros(12, dtype=torch.int64)
completed = 0
batch_number = 0
while completed < TARGET_DRAWS:
    n = min(BATCH_SIZE, TARGET_DRAWS - completed)
    main_indices = torch.randint(TOTAL, (n,), device=device)
    accepted_draws += int(mask[main_indices].sum().item())
    specials = torch.randint(0, 12, (n,), device=device)
    special_counts += torch.bincount(specials, minlength=12).cpu()
    completed += n
    batch_number += 1
    if batch_number % CHECKPOINT_EVERY_BATCHES == 0 or completed == TARGET_DRAWS:
        elapsed = time.monotonic() - start
        checkpoint = {
            "state": "running" if completed < TARGET_DRAWS else "complete",
            "updated_at": utc_now(),
            "target_draws": TARGET_DRAWS,
            "completed_draws": completed,
            "accepted_draws": accepted_draws,
            "elapsed_seconds": elapsed,
            "throughput_draws_per_second": completed / elapsed,
            "special_counts": [int(value) for value in special_counts.tolist()],
        }
        write_json(CHECKPOINT_PATH, checkpoint)
        print(json.dumps(checkpoint), flush=True)

torch.cuda.synchronize()
elapsed = time.monotonic() - start
observed_probability = accepted_draws / completed
standard_error = math.sqrt(expected_probability * (1.0 - expected_probability) / completed)
expected_special = completed / 12
special_chi_square = sum((int(count) - expected_special) ** 2 / expected_special for count in special_counts)
report = {
    "status": "complete",
    "purpose": "Monte Carlo implementation check of the frozen main-number gate and independent special draw; exact enumeration is the authoritative gate volume.",
    "warning": "Uniform simulation does not test future lottery prediction, create an out-of-sample advantage, or estimate any fixed-ticket jackpot probability beyond the exact fair value.",
    "reference_commit": REFERENCE_COMMIT,
    "device": "cuda",
    "gpu_name": gpu_name,
    "torch_version": torch.__version__,
    "python_version": platform.python_version(),
    "seed": SEED,
    "target_draws": TARGET_DRAWS,
    "completed_draws": completed,
    "batch_size": BATCH_SIZE,
    "exact_main_combinations": TOTAL,
    "exact_accepted_main_combinations": accepted_exact,
    "exact_gate_probability": expected_probability,
    "observed_accepted_draws": accepted_draws,
    "observed_gate_probability": observed_probability,
    "observed_minus_exact": observed_probability - expected_probability,
    "z_vs_exact_binomial": (observed_probability - expected_probability) / standard_error,
    "expected_binomial_standard_error": standard_error,
    "special_counts": [int(value) for value in special_counts.tolist()],
    "special_expected_count": expected_special,
    "special_chi_square_11df": special_chi_square,
    "elapsed_seconds": elapsed,
    "throughput_draws_per_second": completed / elapsed,
    "generated_at": utc_now(),
}
write_json(REPORT_PATH, report)
write_json(CHECKPOINT_PATH, {"state": "complete", "report": str(REPORT_PATH), "updated_at": utc_now(), "completed_draws": completed})
print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
print("MONTE_CARLO_30B_COMPLETE", flush=True)
