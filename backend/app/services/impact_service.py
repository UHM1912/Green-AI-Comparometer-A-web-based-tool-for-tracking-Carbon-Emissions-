from typing import Literal


DeploymentType = Literal["local_workstation", "shared_server", "cloud_vm", "serverless"]

DEPLOYMENT_COST_PER_HOUR = {
    "local_workstation": 0.12,
    "shared_server": 0.28,
    "cloud_vm": 0.45,
    "serverless": 0.65,
}

DEPLOYMENT_POWER_MULTIPLIER = {
    "local_workstation": 1.0,
    "shared_server": 1.2,
    "cloud_vm": 1.35,
    "serverless": 1.5,
}


def _classify_efficiency_change(percent_improvement: float) -> str:
    if percent_improvement >= 40:
        return "high"
    if percent_improvement >= 15:
        return "medium"
    if percent_improvement > 0:
        return "low"
    if percent_improvement == 0:
        return "unchanged"
    return "negative"


def _build_summary(
    time_saved_hours_year: float,
    cost_saved_year: float,
    energy_saved_kwh_year: float,
    runtime_change_pct: float,
) -> str:
    impact_level = _classify_efficiency_change(runtime_change_pct)
    if impact_level == "high":
        prefix = "This optimization is strong enough to matter even in moderate usage."
    elif impact_level == "medium":
        prefix = "This optimization becomes meaningful when the code runs repeatedly."
    elif impact_level == "low":
        prefix = "This is a small improvement per run, but it compounds over time."
    elif impact_level == "negative":
        prefix = "This version appears slower at scale, so it likely needs review before adoption."
    else:
        prefix = "This version is broadly similar in runtime, so the main value is likely readability or maintainability."

    return (
        f"{prefix} Estimated yearly savings: {time_saved_hours_year:.1f} developer or compute hours, "
        f"about {energy_saved_kwh_year:.2f} kWh, and roughly ${cost_saved_year:.2f} in infrastructure proxy cost."
    )


def simulate_efficiency_impact(
    original_wall_time_s: float,
    optimized_wall_time_s: float,
    original_power_kwh: float,
    optimized_power_kwh: float,
    runs_per_day: int,
    deployment_type: DeploymentType,
) -> dict:
    safe_runs_per_day = max(int(runs_per_day), 1)
    deployment = deployment_type if deployment_type in DEPLOYMENT_COST_PER_HOUR else "local_workstation"

    time_saved_per_run_s = max(original_wall_time_s - optimized_wall_time_s, 0.0)
    energy_saved_per_run_kwh = max(original_power_kwh - optimized_power_kwh, 0.0)

    yearly_runs = safe_runs_per_day * 365
    time_saved_year_s = time_saved_per_run_s * yearly_runs
    time_saved_year_h = time_saved_year_s / 3600

    energy_multiplier = DEPLOYMENT_POWER_MULTIPLIER[deployment]
    energy_saved_year_kwh = energy_saved_per_run_kwh * yearly_runs * energy_multiplier

    if energy_saved_year_kwh == 0 and time_saved_year_h > 0:
        # Fallback proxy when tracker energy is too small to be meaningful.
        energy_saved_year_kwh = time_saved_year_h * 0.06 * energy_multiplier

    cost_saved_year = time_saved_year_h * DEPLOYMENT_COST_PER_HOUR[deployment]

    runtime_change_pct = 0.0
    if original_wall_time_s > 0:
        runtime_change_pct = ((original_wall_time_s - optimized_wall_time_s) / original_wall_time_s) * 100

    return {
        "runs_per_day": safe_runs_per_day,
        "deployment_type": deployment,
        "time_saved_per_run_s": time_saved_per_run_s,
        "estimated_time_saved_per_year_hours": time_saved_year_h,
        "estimated_energy_proxy_saved_per_year_kwh": energy_saved_year_kwh,
        "estimated_cost_proxy_saved_per_year_usd": cost_saved_year,
        "impact_band": _classify_efficiency_change(runtime_change_pct),
        "summary": _build_summary(
            time_saved_year_h,
            cost_saved_year,
            energy_saved_year_kwh,
            runtime_change_pct,
        ),
    }
