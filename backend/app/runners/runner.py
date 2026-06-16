import json
import logging
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from textwrap import dedent

import pandas as pd

logger = logging.getLogger("EcoRefactor.runners.runner")

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
SESSIONS_DIR = BACKEND_ROOT / "temp_sessions"
WARMUP_RUNS = 1
MEASURED_RUNS = 3
RUN_TIMEOUT_SECONDS = 180


def _extract_error_summary(stderr_text: str, stdout_text: str) -> str:
    combined_lines = [
        line.strip()
        for line in (stderr_text + "\n" + stdout_text).splitlines()
        if line.strip()
    ]
    if not combined_lines:
        return "Execution failed without a clear error message."

    for line in reversed(combined_lines):
        if "Error" in line or "Exception" in line:
            return line

    return combined_lines[-1]


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (len(sorted_values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def _build_wrapped_code(indented_user_code: str, tracker_type: str) -> str:
    tracker_type_lower = tracker_type.lower()

    if tracker_type_lower == "eco2ai":
        tracker_import = dedent("""
from eco2ai import Tracker

tracker = Tracker(
    project_name="EcoRefactor",
    experiment_description="Sandbox eco2AI Execution",
    file_name="my_emission.csv"
)
""").strip()
        tracker_stop = "tracker.stop()"
        tracker_file_name = "my_emission.csv"
    elif tracker_type_lower == "codecarbon":
        tracker_import = dedent("""
from codecarbon import EmissionsTracker

tracker = EmissionsTracker(output_file="emissions.csv")
""").strip()
        tracker_stop = "tracker.stop()"
        tracker_file_name = "emissions.csv"
    else:
        raise ValueError(f"Unknown tracker type: {tracker_type}")

    return dedent(f"""
import json
import logging
import time
import tracemalloc
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
logging.getLogger("eco2ai").setLevel(logging.ERROR)
logging.getLogger("codecarbon").setLevel(logging.ERROR)

{tracker_import}

metrics_path = Path("metrics_summary.json")
tracker.start()
tracemalloc.start()
wall_start = time.perf_counter()
cpu_start = time.process_time()
success = True
error_message = ""

try:
    # --- USER CODE START ---
{indented_user_code}
    # --- USER CODE END ---
except Exception as exc:
    success = False
    error_message = str(exc)
    raise
finally:
    current_memory, peak_memory = tracemalloc.get_traced_memory()
    wall_time = time.perf_counter() - wall_start
    cpu_time = time.process_time() - cpu_start
    tracemalloc.stop()
    tracker.stop()

    metrics_path.write_text(
        json.dumps({{
            "success": success,
            "error_message": error_message,
            "wall_time_s": wall_time,
            "cpu_time_s": cpu_time,
            "peak_memory_mb": peak_memory / (1024 * 1024),
            "tracker_file": "{tracker_file_name}"
        }}),
        encoding="utf-8"
    )
""").strip() + "\n"


def _extract_tracker_metrics(run_dir: Path, tracker_type: str) -> tuple[float, float, float]:
    tracker_type_lower = tracker_type.lower()
    if tracker_type_lower == "eco2ai":
        emission_csv = run_dir / "my_emission.csv"
        if not emission_csv.exists():
            return 0.0, 0.0, 0.0

        df = pd.read_csv(emission_csv)
        if df.empty:
            return 0.0, 0.0, 0.0

        latest = df.iloc[-1]
        return (
            float(latest.get("CO2_emissions(kg)", 0.0)),
            float(latest.get("power_consumption(kWh)", 0.0)),
            float(latest.get("duration(s)", 0.0)),
        )

    emission_csv = run_dir / "emissions.csv"
    if not emission_csv.exists():
        return 0.0, 0.0, 0.0

    df = pd.read_csv(emission_csv)
    if df.empty:
        return 0.0, 0.0, 0.0

    latest = df.iloc[-1]
    return (
        float(latest.get("emissions", 0.0)),
        float(latest.get("energy_consumed", 0.0)),
        float(latest.get("duration", 0.0)),
    )


def _aggregate_runs(run_metrics: list[dict]) -> dict:
    wall_times = sorted(metric["wall_time_s"] for metric in run_metrics)
    cpu_times = sorted(metric["cpu_time_s"] for metric in run_metrics)
    peak_memories = sorted(metric["peak_memory_mb"] for metric in run_metrics)
    co2_values = sorted(metric["co2_emissions_kg"] for metric in run_metrics)
    power_values = sorted(metric["power_kwh"] for metric in run_metrics)

    return {
        "measured_runs": len(run_metrics),
        "wall_time_median_s": _percentile(wall_times, 0.5),
        "wall_time_best_s": wall_times[0],
        "wall_time_p95_s": _percentile(wall_times, 0.95),
        "cpu_time_median_s": _percentile(cpu_times, 0.5),
        "peak_memory_median_mb": _percentile(peak_memories, 0.5),
        "co2_emissions_median_kg": _percentile(co2_values, 0.5),
        "power_kwh_median": _percentile(power_values, 0.5),
    }


def run_in_sandbox(code_content: str, filename: str, tracker_type: str) -> dict:
    session_id = str(uuid.uuid4())
    session_dir = SESSIONS_DIR / session_id
    logger.info("Creating sandbox session %s in %s", session_id, session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    console_output = ""

    try:
        is_notebook = filename.endswith(".ipynb")
        run_filename = "user_script.ipynb" if is_notebook else "user_script.py"
        code_file_path = session_dir / run_filename
        code_file_path.write_text(code_content, encoding="utf-8")

        if is_notebook:
            logger.info("[%s] Converting notebook to Python script...", tracker_type)
            conversion = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "jupyter",
                    "nbconvert",
                    "--to",
                    "python",
                    str(code_file_path),
                    "--output",
                    "converted_script",
                ],
                cwd=session_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if conversion.returncode != 0:
                raise RuntimeError(f"Notebook conversion failed: {conversion.stderr}")
            script_to_run_path = session_dir / "converted_script.py"
        else:
            script_to_run_path = code_file_path

        user_code = script_to_run_path.read_text(encoding="utf-8")
        indented_user_code = "\n".join(
            "    " + line if line.strip() else line for line in user_code.splitlines()
        )

        run_metrics: list[dict] = []
        console_logs: list[str] = []
        total_runs = WARMUP_RUNS + MEASURED_RUNS

        for run_index in range(total_runs):
            is_warmup = run_index < WARMUP_RUNS
            phase_label = "warmup" if is_warmup else f"measure-{run_index - WARMUP_RUNS + 1}"
            run_dir = session_dir / phase_label
            run_dir.mkdir(parents=True, exist_ok=True)

            wrapped_code_path = run_dir / "wrapped_runner.py"
            wrapped_code_path.write_text(
                _build_wrapped_code(indented_user_code, tracker_type),
                encoding="utf-8",
            )

            logger.info("[%s] Starting %s run (timeout: %ss)...", tracker_type, phase_label, RUN_TIMEOUT_SECONDS)
            proc = subprocess.run(
                [sys.executable, str(wrapped_code_path)],
                cwd=run_dir,
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT_SECONDS,
                check=False,
            )

            console_logs.append(
                f"=== {phase_label.upper()} STDOUT ===\n{proc.stdout}\n\n=== {phase_label.upper()} STDERR ===\n{proc.stderr}"
            )

            metrics_file = run_dir / "metrics_summary.json"
            if not metrics_file.exists():
                return {
                    "success": False,
                    "error_message": f"Metrics summary was not generated during {phase_label}.",
                    "console_output": "\n\n".join(console_logs),
                    "co2_emissions_kg": 0.0,
                    "power_kwh": 0.0,
                    "duration_s": 0.0,
                    "cpu_time_s": 0.0,
                    "peak_memory_mb": 0.0,
                    "error_summary": "Metrics summary was not generated.",
                    "benchmark_summary": None,
                }

            metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
            if proc.returncode != 0 or not metrics.get("success", True):
                return {
                    "success": False,
                    "error_message": metrics.get("error_message") or f"Execution failed with code {proc.returncode}",
                    "console_output": "\n\n".join(console_logs),
                    "co2_emissions_kg": 0.0,
                    "power_kwh": 0.0,
                    "duration_s": 0.0,
                    "cpu_time_s": 0.0,
                    "peak_memory_mb": 0.0,
                    "error_summary": _extract_error_summary(proc.stderr, proc.stdout),
                    "benchmark_summary": None,
                }

            co2_emissions_kg, power_kwh, tracker_duration_s = _extract_tracker_metrics(run_dir, tracker_type)

            if not is_warmup:
                run_metrics.append(
                    {
                        "wall_time_s": float(metrics.get("wall_time_s", 0.0)),
                        "cpu_time_s": float(metrics.get("cpu_time_s", 0.0)),
                        "peak_memory_mb": float(metrics.get("peak_memory_mb", 0.0)),
                        "co2_emissions_kg": co2_emissions_kg,
                        "power_kwh": power_kwh,
                        "tracker_duration_s": tracker_duration_s,
                    }
                )

        benchmark_summary = _aggregate_runs(run_metrics)
        console_output = "\n\n".join(console_logs)

        return {
            "success": True,
            "error_message": "",
            "console_output": console_output,
            "co2_emissions_kg": benchmark_summary["co2_emissions_median_kg"],
            "power_kwh": benchmark_summary["power_kwh_median"],
            "duration_s": benchmark_summary["wall_time_median_s"],
            "cpu_time_s": benchmark_summary["cpu_time_median_s"],
            "peak_memory_mb": benchmark_summary["peak_memory_median_mb"],
            "error_summary": "",
            "benchmark_summary": benchmark_summary,
        }

    except subprocess.TimeoutExpired:
        logger.error("[%s] Execution timed out after %s seconds.", tracker_type, RUN_TIMEOUT_SECONDS)
        return {
            "success": False,
            "error_message": f"Execution timed out (limit: {RUN_TIMEOUT_SECONDS} seconds).",
            "console_output": console_output,
            "co2_emissions_kg": 0.0,
            "power_kwh": 0.0,
            "duration_s": 0.0,
            "cpu_time_s": 0.0,
            "peak_memory_mb": 0.0,
            "error_summary": "Execution timed out before results were produced.",
            "benchmark_summary": None,
        }
    except Exception as exc:
        logger.error("[%s] Unexpected runner exception: %s", tracker_type, exc, exc_info=True)
        return {
            "success": False,
            "error_message": str(exc),
            "console_output": console_output,
            "co2_emissions_kg": 0.0,
            "power_kwh": 0.0,
            "duration_s": 0.0,
            "cpu_time_s": 0.0,
            "peak_memory_mb": 0.0,
            "error_summary": str(exc),
            "benchmark_summary": None,
        }
    finally:
        try:
            if session_dir.exists():
                shutil.rmtree(session_dir)
                logger.info("Sandbox session directory cleaned up")
        except Exception as cleanup_err:
            logger.warning("Sandbox cleanup error: %s", cleanup_err, exc_info=True)
