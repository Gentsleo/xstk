import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys

folder = Path(sys.argv[1]).resolve()
session = "xstk-qr-prize-30b-20261030-01"
cli = shutil.which("colab")
if not cli:
    raise RuntimeError("google-colab-cli is unavailable")
status = {"state": "starting", "session": session, "target_draws": 30_000_000_000}
def save(**fields):
    status.update(fields)
    status["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    temporary = folder / "status.tmp"
    temporary.write_text(json.dumps(status, ensure_ascii=False, indent=2))
    temporary.replace(folder / "status.json")
def run(*args, timeout):
    print("RUN:", *args, flush=True)
    subprocess.run([cli, "--auth=oauth2", *args], check=True, timeout=timeout)
success = False
try:
    save(state="allocating")
    run("new", "-s", session, "--gpu", "T4", timeout=300)
    save(state="running")
    run("exec", "-s", session, "--timeout", "3600", "-f", str(folder / "remote_job.py"), timeout=3660)
    save(state="downloading")
    run("download", "-s", session, "/content/qr_prize_30b.json", str(folder / "qr_prize_30b.json"), timeout=180)
    run("download", "-s", session, "/content/qr_prize_30b_checkpoint.json", str(folder / "checkpoint.json"), timeout=180)
    report = json.loads((folder / "qr_prize_30b.json").read_text())
    if report.get("status") != "complete" or report.get("device") != "cuda" or report.get("completed_draws") != 30_000_000_000:
        raise RuntimeError("GPU report does not prove completed 30B CUDA prize tally")
    success = True
except BaseException as exc:
    save(state="failed", error=repr(exc))
    print("FAILED:", repr(exc), flush=True)
finally:
    save(cleanup="stopping")
    stopped = False
    try:
        run("stop", "-s", session, timeout=120)
        stopped = True
    except BaseException as exc:
        save(cleanup_error=repr(exc))
    save(state="completed" if success and stopped else "failed", runtime_stopped=stopped)
    print("FINAL_STATUS:", json.dumps(status, ensure_ascii=False), flush=True)
