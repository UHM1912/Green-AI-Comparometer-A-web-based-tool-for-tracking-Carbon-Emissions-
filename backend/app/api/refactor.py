from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.db.connection import get_db_conn
from app.core.security import decode_access_token
from app.services.llm_service import refactor_code_with_gemini
from app.runners.runner import run_in_sandbox
from app.services.impact_service import simulate_efficiency_impact
from app.services.report_service import generate_pdf_report
import time
import json
import logging

logger = logging.getLogger("EcoRefactor.api.refactor")

router = APIRouter(prefix="/api/refactor", tags=["refactor"])

# Models
class CodeSuggestionRequest(BaseModel):
    code: str
    filename: str

class CodeRunRequest(BaseModel):
    original_code: str
    optimized_code: str
    filename: str
    tracker: str  # 'eco2AI' or 'CodeCarbon'
    explanations: list[str]
    risk_level: str = "medium"
    confidence: str = "medium"


class ImpactSimulationRequest(BaseModel):
    original_duration_s: float
    optimized_duration_s: float
    original_power_kwh: float
    optimized_power_kwh: float
    runs_per_day: int = 100
    deployment_type: str = "local_workstation"

# Authentication Dependency
def get_current_user_id(authorization: str = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid credentials."
        )
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid credentials."
        )
    return int(payload["sub"])

@router.post("/suggest")
def suggest_optimization(req: CodeSuggestionRequest, user_id: int = Depends(get_current_user_id)):
    """
    Takes raw user code and queries Gemini for refactored optimized version and explanation lists.
    """
    logger.info(f"Received suggest_optimization request: user_id={user_id}, filename={req.filename}, code_len={len(req.code)}")
    start_time = time.perf_counter()
    
    suggestion = refactor_code_with_gemini(req.code)
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"Completed suggest_optimization request in {elapsed:.4f} seconds for filename={req.filename}")
    
    return {
        "original_code": req.code,
        "optimized_code": suggestion["optimized_code"],
        "explanations": suggestion["explanations"],
        "risk_level": suggestion["risk_level"],
        "confidence": suggestion["confidence"],
        "expected_runtime_impact": suggestion["expected_runtime_impact"],
        "expected_memory_impact": suggestion["expected_memory_impact"],
        "expected_scalability_impact": suggestion["expected_scalability_impact"],
    }

@router.post("/run-compare")
def run_comparison(req: CodeRunRequest, user_id: int = Depends(get_current_user_id)):
    """
    Executes both the original and optimized code in subprocess environments under the selected carbon tracker.
    Saves the comparative metrics to SQLite database history.
    """
    logger.info(f"Received run_comparison request: user_id={user_id}, filename={req.filename}, tracker={req.tracker}")
    total_start = time.perf_counter()
    
    # 1. Run Original Code
    logger.info("Starting Original Code execution in sandbox...")
    orig_start = time.perf_counter()
    original_run = run_in_sandbox(req.original_code, req.filename, req.tracker)
    orig_elapsed = time.perf_counter() - orig_start
    
    if not original_run["success"]:
        logger.error(f"Original code execution failed after {orig_elapsed:.4f} seconds: {original_run['error_message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Original code execution failed: {original_run['error_message']}",
                "console": original_run["console_output"],
                "error_summary": original_run.get("error_summary", ""),
                "failed_version": "original",
            }
        )
    logger.info(f"Original code execution succeeded in {orig_elapsed:.4f} seconds (Emissions: {original_run['co2_emissions_kg']:.6f} kg)")
        
    # 2. Run Optimized Code
    logger.info("Starting Optimized Code execution in sandbox...")
    opt_start = time.perf_counter()
    optimized_run = run_in_sandbox(req.optimized_code, req.filename, req.tracker)
    opt_elapsed = time.perf_counter() - opt_start
    
    if not optimized_run["success"]:
        logger.error(f"Optimized code execution failed after {opt_elapsed:.4f} seconds: {optimized_run['error_message']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Optimized code execution failed: {optimized_run['error_message']}",
                "console": optimized_run["console_output"],
                "error_summary": optimized_run.get("error_summary", ""),
                "failed_version": "optimized",
            }
        )
    logger.info(f"Optimized code execution succeeded in {opt_elapsed:.4f} seconds (Emissions: {optimized_run['co2_emissions_kg']:.6f} kg)")

    # 3. Store Results in Database
    logger.info("Storing benchmark metrics to SQLite database...")
    db_start = time.perf_counter()
    conn = get_db_conn()
    c = conn.cursor()
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    explanations_str = json.dumps(req.explanations)
    
    c.execute("""
        INSERT INTO refactor_jobs (
            user_id, filename, original_code, optimized_code, explanations,
            original_co2, optimized_co2, original_power, optimized_power,
            original_duration, optimized_duration, timestamp,
            original_cpu_time, optimized_cpu_time,
            original_peak_memory_mb, optimized_peak_memory_mb,
            benchmark_runs, risk_level, confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, req.filename, req.original_code, req.optimized_code, explanations_str,
        original_run["co2_emissions_kg"], optimized_run["co2_emissions_kg"],
        original_run["power_kwh"], optimized_run["power_kwh"],
        original_run["duration_s"], optimized_run["duration_s"],
        timestamp,
        original_run["cpu_time_s"], optimized_run["cpu_time_s"],
        original_run["peak_memory_mb"], optimized_run["peak_memory_mb"],
        original_run["benchmark_summary"]["measured_runs"],
        req.risk_level, req.confidence,
    ))
    conn.commit()
    job_id = c.lastrowid
    conn.close()
    db_elapsed = time.perf_counter() - db_start
    logger.info(f"Successfully saved metrics to DB (job_id: {job_id}) in {db_elapsed:.4f} seconds")
    
    impact_simulation = simulate_efficiency_impact(
        original_wall_time_s=original_run["duration_s"],
        optimized_wall_time_s=optimized_run["duration_s"],
        original_power_kwh=original_run["power_kwh"],
        optimized_power_kwh=optimized_run["power_kwh"],
        runs_per_day=100,
        deployment_type="local_workstation",
    )

    total_elapsed = time.perf_counter() - total_start
    logger.info(f"Total run_comparison processing completed in {total_elapsed:.4f} seconds")
    
    return {
        "job_id": job_id,
        "filename": req.filename,
        "tracker": req.tracker,
        "original": {
            "co2_emissions_kg": original_run["co2_emissions_kg"],
            "power_kwh": original_run["power_kwh"],
            "duration_s": original_run["duration_s"],
            "cpu_time_s": original_run["cpu_time_s"],
            "peak_memory_mb": original_run["peak_memory_mb"],
            "benchmark_summary": original_run["benchmark_summary"],
            "console": original_run["console_output"]
        },
        "optimized": {
            "co2_emissions_kg": optimized_run["co2_emissions_kg"],
            "power_kwh": optimized_run["power_kwh"],
            "duration_s": optimized_run["duration_s"],
            "cpu_time_s": optimized_run["cpu_time_s"],
            "peak_memory_mb": optimized_run["peak_memory_mb"],
            "benchmark_summary": optimized_run["benchmark_summary"],
            "console": optimized_run["console_output"]
        },
        "risk_level": req.risk_level,
        "confidence": req.confidence,
        "impact_simulation": impact_simulation,
        "timestamp": timestamp
    }

@router.get("/history")
def get_jobs_history(user_id: int = Depends(get_current_user_id)):
    """
    Retrieves all past refactoring benchmarks executed by the current logged-in user.
    """
    logger.info(f"Received get_jobs_history request: user_id={user_id}")
    start_time = time.perf_counter()
    
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, filename, original_co2, optimized_co2, original_power, 
               optimized_power, original_duration, optimized_duration, timestamp,
               original_cpu_time, optimized_cpu_time,
               original_peak_memory_mb, optimized_peak_memory_mb,
               benchmark_runs, risk_level, confidence
        FROM refactor_jobs 
        WHERE user_id = ? 
        ORDER BY id DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"Completed get_jobs_history request in {elapsed:.4f} seconds; found {len(rows)} records")
    
    return [dict(row) for row in rows]


@router.post("/impact-simulate")
def impact_simulation(req: ImpactSimulationRequest, user_id: int = Depends(get_current_user_id)):
    logger.info(
        "Received impact_simulation request: user_id=%s, runs_per_day=%s, deployment_type=%s",
        user_id,
        req.runs_per_day,
        req.deployment_type,
    )

    return simulate_efficiency_impact(
        original_wall_time_s=req.original_duration_s,
        optimized_wall_time_s=req.optimized_duration_s,
        original_power_kwh=req.original_power_kwh,
        optimized_power_kwh=req.optimized_power_kwh,
        runs_per_day=req.runs_per_day,
        deployment_type=req.deployment_type,
    )

@router.get("/download-report/{job_id}")
def download_pdf_report(job_id: int, user_id: int = Depends(get_current_user_id)):
    """
    Composes a styled PDF comparing execution reports and savings calculations.
    """
    logger.info(f"Received download_pdf_report request: user_id={user_id}, job_id={job_id}")
    start_time = time.perf_counter()
    
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM refactor_jobs WHERE id = ? AND user_id = ?
    """, (job_id, user_id))
    job_row = c.fetchone()
    conn.close()
    
    if not job_row:
        logger.warning(f"Report download aborted: job_id={job_id} not found for user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report job not found."
        )
        
    job_data = dict(job_row)
    pdf_buffer = generate_pdf_report(job_data)
    
    headers = {
        'Content-Disposition': f'attachment; filename="EcoRefactor_Report_{job_data["filename"]}.pdf"'
    }
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"Completed download_pdf_report in {elapsed:.4f} seconds for job_id={job_id}")
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
