#!/usr/bin/env python3
"""Thí nghiệm mạng QR theo thời gian; không thay thế xác suất quay đều.

Một xác suất dương cho mọi bộ 5+1: softmax khối D² rồi chia đều theo
số tổ hợp trong khối, nhân softmax độc lập của số đặc biệt. Huấn luyện
chỉ sau cổng bằng chứng dự báo tiến cứu, trừ --diagnostic (kỹ thuật).
"""

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
TOTAL = math.comb(35, 5)
WINDOW = 32
# Khối ngũ phân vị D² thuộc tham chiếu lý thuyết, không học từ lịch sử.
N_BINS = 5
FEATURES = 35 + N_BINS + 12
MIN_NEW = 100
MIN_LOG_E = math.log(20)


def _digest(rows):
    from rng_lab import history_digest
    return history_digest(rows)


def _rows(source):
    from rng_lab import load_history
    return load_history(source)


def _gate(report_path, rows, data_hash):
    """Only a verified prefix-frozen prospective report qualifies for research.

    The report is a local research artifact, not a cryptographic attestation;
    an edited or untrusted report must not be treated as evidence.
    """
    if report_path is None:
        return False, "Chưa cung cấp báo cáo dự báo tiến cứu đã khóa trước dữ liệu."
    try:
        with report_path.open(encoding="utf-8") as stream:
            report = json.load(stream)
    except (OSError, ValueError) as exc:
        return False, f"Không thể đọc báo cáo tiến cứu: {exc}"
    if not isinstance(report, dict):
        return False, "Báo cáo tiến cứu phải là JSON object."
    evidence = report.get("evidence")
    if not isinstance(evidence, dict):
        return False, "Báo cáo không có evidence tiến cứu hợp lệ."
    if (report.get("mode") != "prospective" or report.get("status") != "prospective"
            or evidence.get("prospective") is not True):
        return False, "Báo cáo hồi cứu/không tiến cứu không mở cổng huấn luyện."
    if evidence.get("prefix_verified") is not True:
        return False, "Tiền tố lịch sử trước khóa chưa được xác minh."
    selected = evidence.get("selected_model")
    if selected not in ("frequency", "qr") or selected != report.get("selected_model"):
        return False, "Mô hình đánh giá không được chọn cố định trước khi thử."
    n_new = evidence.get("n_new")
    log_e = evidence.get("log_evalue")
    if isinstance(n_new, bool) or not isinstance(n_new, int) or n_new < MIN_NEW:
        return False, f"Cần ít nhất {MIN_NEW} kỳ MỚI sau khóa."
    if isinstance(log_e, bool) or not isinstance(log_e, (int, float)) or not math.isfinite(log_e):
        return False, "Thiếu tổng log tỷ số khả dĩ hợp lệ."
    if log_e < MIN_LOG_E:
        return False, "Bằng chứng chưa vượt ngưỡng tiền đăng ký log(20)."
    # Compare both complete data and frozen prefix against the actual history.
    if report.get("history_sha256") != data_hash:
        return False, "Hash toàn bộ lịch sử không khớp báo cáo tiến cứu."
    if n_new >= len(rows):
        return False, "Số kỳ mới nhiều hơn tiền tố dữ liệu có trước khi khóa."
    old = rows[:-n_new]
    if (report.get("locked_prefix_sha256") != _digest(old)
            or report.get("locked_last_draw_id") != old[-1]["draw_id"]):
        return False, "Tiền tố khóa trước dữ liệu không khớp lịch sử."
    if (report.get("evaluated_draws") != n_new
            or report.get("history_draws") != len(rows)
            or report.get("evaluated_draw_ids") != [rows[-n_new]["draw_id"], rows[-1]["draw_id"]]):
        return False, "Khoảng kỳ tiến cứu không khớp lịch sử."
    test = report.get("test")
    if not isinstance(test, dict) or not isinstance(test.get(selected), dict) or not isinstance(test.get("uniform"), dict):
        return False, "Thiếu log-loss mô hình đã khóa và mốc công bằng."
    chosen_loss = test[selected].get("mean_logloss_joint")
    fair_loss = test["uniform"].get("mean_logloss_joint")
    if (type(chosen_loss) not in (int, float) or type(fair_loss) not in (int, float)
            or not math.isfinite(chosen_loss) or not math.isfinite(fair_loss)
            or test[selected].get("draws") != n_new or test["uniform"].get("draws") != n_new
            or not math.isclose(log_e, n_new * (fair_loss - chosen_loss), rel_tol=1e-7, abs_tol=1e-5)):
        return False, "Tỷ số khả dĩ không khớp log-loss tiến cứu công bố."
    return True, "Đủ cổng nghiên cứu: >=100 kỳ mới, e-value >=20 theo tỷ số khả dĩ đã khóa."


def _reference_bins():
    """Dùng nguyên khối QR năm ngũ phân vị từ tham chiếu lý thuyết."""
    from rng_lab import reference
    ref = reference()
    counts = ref["bin_counts"]
    if len(ref["d2"]) != TOTAL or len(counts) != N_BINS or np.any(counts == 0):
        raise ValueError("Khối QR rỗng hoặc tham chiếu thiếu tổ hợp")
    return ref["bins"], counts, ref["cuts"]


def _dataset(rows, bins):
    """Mỗi vector tại t chỉ xem các kỳ [t-WINDOW,t)."""
    from rng_lab import rank_combos
    indices = rank_combos([row["combo"] for row in rows])
    combo_bins = np.asarray(bins[indices], dtype=np.int64)
    specials = np.array([row["special"] - 1 for row in rows], dtype=np.int64)
    n = len(rows) - WINDOW
    if n < 100:
        raise ValueError("Cần ít nhất 132 kỳ để chia train/validation/test sau cửa sổ 32 kỳ")
    x = np.empty((n, FEATURES), dtype=np.float32)
    for t in range(WINDOW, len(rows)):
        recent = rows[t - WINDOW:t]
        main = np.bincount([v - 1 for row in recent for v in row["combo"]], minlength=35)
        prior_bins = np.bincount(combo_bins[t - WINDOW:t], minlength=N_BINS)
        prior_special = np.bincount(specials[t - WINDOW:t], minlength=12)
        x[t - WINDOW] = np.concatenate((main / (5 * WINDOW),
                                        prior_bins / WINDOW, prior_special / WINDOW))
    return x, combo_bins[WINDOW:], specials[WINDOW:]


def _split(n):
    train_end, valid_end = int(n * .6), int(n * .8)
    return (slice(0, train_end), slice(train_end, valid_end), slice(valid_end, n))


def _train(rows, data_hash, epochs, seed, device, checkpoint, diagnostic, gate_message):
    # cuBLAS requires a workspace configuration for deterministic CUDA matmul.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    try:
        import torch
        from torch import nn
        from torch.nn import functional as F
    except ImportError as exc:
        raise RuntimeError("Cần PyTorch cho huấn luyện: pip install torch") from exc
    if device == "cuda" and not torch.cuda.is_available():
        raise ValueError("Đã yêu cầu CUDA nhưng CUDA không khả dụng")
    backend = "cuda" if device == "cuda" or (device == "auto" and torch.cuda.is_available()) else "cpu"
    torch.manual_seed(seed)
    if backend == "cuda":
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
    bins, counts, cuts = _reference_bins()
    x, y_bin, y_special = _dataset(rows, bins)
    train, valid, test = _split(len(x))
    xs = torch.as_tensor(x, device=backend)
    ys = torch.as_tensor(y_bin, device=backend)
    ss = torch.as_tensor(y_special, device=backend)
    log_counts = torch.as_tensor(np.log(counts), device=backend, dtype=torch.float32)
    network = nn.Sequential(nn.Linear(FEATURES, 16), nn.ReLU(),
                            nn.Linear(16, N_BINS + 12)).to(backend)
    optimizer = torch.optim.Adam(network.parameters(), lr=0.001)
    rng = np.random.default_rng(seed)
    best_loss, best_epoch, stale, best_state = float("inf"), 0, 0, None

    def losses(idx):
        logits = network(xs[idx])
        main_loss = F.cross_entropy(logits[:, :N_BINS], ys[idx], reduction="none") + log_counts[ys[idx]]
        special_loss = F.cross_entropy(logits[:, N_BINS:], ss[idx], reduction="none")
        return main_loss, special_loss

    for epoch in range(1, epochs + 1):
        network.train()
        for indices in np.array_split(rng.permutation(train.stop),
                                      math.ceil(train.stop / 64)):
            optimizer.zero_grad(set_to_none=True)
            main_loss, special_loss = losses(indices)
            (main_loss + special_loss).mean().backward()
            optimizer.step()
        network.eval()
        with torch.no_grad():
            v_main, v_special = losses(valid)
            score = (v_main + v_special).mean().item()
        if score < best_loss - 1e-6:
            best_loss, best_epoch, stale = score, epoch, 0
            best_state = deepcopy(network.state_dict())
        else:
            stale += 1
            if stale >= 12:
                break
    network.load_state_dict(best_state)
    network.eval()
    metrics = {}
    with torch.no_grad():
        for name, segment in (("train", train), ("validation", valid), ("test", test)):
            main_loss, special_loss = losses(segment)
            main_avg, special_avg = main_loss.mean().item(), special_loss.mean().item()
            metrics[name] = {"n": segment.stop - segment.start,
                             "first_draw_id": int(rows[WINDOW + segment.start]["draw_id"]),
                             "last_draw_id": int(rows[WINDOW + segment.stop - 1]["draw_id"]),
                             "logloss_main": main_avg, "logloss_special": special_avg,
                             "logloss_joint": main_avg + special_avg,
                             "uniform_joint": math.log(TOTAL * 12),
                             "joint_minus_uniform": main_avg + special_avg - math.log(TOTAL * 12)}
    metadata = {"status": "diagnostic_only" if diagnostic else "research_gate_passed",
                "caveat": "Nghiên cứu hồi cứu: không chứng minh RNG có thể dự báo hay tăng xác suất trúng; diagnostic không là tín hiệu.",
                "gate": gate_message, "device": backend, "seed": seed, "epochs_requested": epochs,
                "torch_version": str(torch.__version__), "numpy_version": np.__version__,
                "split_fractions": [0.6, 0.2, 0.2],
                "best_epoch": best_epoch, "window": WINDOW,
                "cuts_d2": [float(v) for v in cuts],
                "bin_counts": [int(c) for c in counts], "data_hash": data_hash,
                "metrics": metrics, "architecture": "52->16 ReLU->17 (5 QR bins + 12 special)",
                "within_bin": "uniform_exact", "checkpoint": str(checkpoint)}
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    if checkpoint.exists():
        raise FileExistsError(f"Checkpoint đã tồn tại: {checkpoint}")
    # Exclusive creation avoids overwriting previous experiments.
    with checkpoint.open("xb") as output:
        torch.save({"state_dict": network.state_dict(), "metadata": metadata}, output)
    return metadata


def _synthetic(n, seed):
    if n < 132:
        raise ValueError("--synthetic-draws cần ít nhất 132")
    rng = np.random.default_rng(seed)
    return [{"draw_id": i + 1, "date": "synthetic", "combo": tuple(sorted(
        int(v) for v in rng.choice(np.arange(1, 36), size=5, replace=False))),
             "special": int(rng.integers(1, 13))} for i in range(n)]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Thí nghiệm PyTorch QR 5/35; cổng tiến cứu bắt buộc trừ diagnostic.")
    parser.add_argument("--source", type=Path, default=ROOT / "vietlott_535.json")
    parser.add_argument("--prospective-report", type=Path, help="Báo cáo có khóa trước dữ liệu, KHÔNG phải kiểm tra hồi cứu")
    parser.add_argument("--diagnostic", action="store_true", help="Chạy kỹ thuật hồi cứu, KHÔNG phải bằng chứng/tín hiệu")
    parser.add_argument("--synthetic-draws", type=int, help="Chỉ cùng --diagnostic; mô phỏng công bằng có gắn nhãn")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "rng_neural.pt")
    args = parser.parse_args(argv)
    if args.synthetic_draws is not None and not args.diagnostic:
        parser.error("--synthetic-draws chỉ dùng cùng --diagnostic")
    if args.epochs < 1:
        parser.error("--epochs phải dương")
    if args.seed < 0:
        parser.error("--seed không được âm")
    try:
        rows = _synthetic(args.synthetic_draws, args.seed) if args.synthetic_draws is not None else _rows(args.source)
        data_hash = (hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                     if args.synthetic_draws is not None else _digest(rows))
        if args.diagnostic:
            allowed, reason = True, "Chỉ kiểm thử kỹ thuật, không được sử dụng như bằng chứng tiến cứu."
        else:
            allowed, reason = _gate(args.prospective_report, rows, data_hash)
        if not allowed:
            result = {"status": "deferred", "reason": reason, "data_hash": data_hash,
                      "source": str(args.source), "checkpoint_created": False,
                      "caveat": "Báo cáo do người dùng cung cấp không được xác thực mật mã; chỉ dùng dữ liệu tiến cứu khóa trước."}
        else:
            result = _train(rows, data_hash, args.epochs, args.seed, args.device,
                            args.checkpoint, args.diagnostic, reason)
            result["source"] = "synthetic_fair_iid" if args.synthetic_draws is not None else str(args.source)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return result
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
