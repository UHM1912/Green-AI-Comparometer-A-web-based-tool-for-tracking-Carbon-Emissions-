import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

export interface CodeRefactorResponse {
  original_code: string;
  optimized_code: string;
  explanations: string[];
  risk_level: string;
  confidence: string;
  expected_runtime_impact: string;
  expected_memory_impact: string;
  expected_scalability_impact: string;
}

export interface BenchmarkSummary {
  measured_runs: number;
  wall_time_median_s: number;
  wall_time_best_s: number;
  wall_time_p95_s: number;
  cpu_time_median_s: number;
  peak_memory_median_mb: number;
  co2_emissions_median_kg: number;
  power_kwh_median: number;
}

export interface ImpactSimulationResponse {
  runs_per_day: number;
  deployment_type: string;
  time_saved_per_run_s: number;
  estimated_time_saved_per_year_hours: number;
  estimated_energy_proxy_saved_per_year_kwh: number;
  estimated_cost_proxy_saved_per_year_usd: number;
  impact_band: string;
  summary: string;
}

export interface RunCompareResponse {
  job_id: number;
  filename: string;
  tracker: string;
  risk_level: string;
  confidence: string;
  original: {
    co2_emissions_kg: number;
    power_kwh: number;
    duration_s: number;
    cpu_time_s: number;
    peak_memory_mb: number;
    benchmark_summary: BenchmarkSummary;
    console: string;
  };
  optimized: {
    co2_emissions_kg: number;
    power_kwh: number;
    duration_s: number;
    cpu_time_s: number;
    peak_memory_mb: number;
    benchmark_summary: BenchmarkSummary;
    console: string;
  };
  impact_simulation: ImpactSimulationResponse;
  timestamp: string;
}

export interface JobHistoryItem {
  id: number;
  filename: string;
  original_co2: number;
  optimized_co2: number;
  original_power: number;
  optimized_power: number;
  original_duration: number;
  optimized_duration: number;
  original_cpu_time: number;
  optimized_cpu_time: number;
  original_peak_memory_mb: number;
  optimized_peak_memory_mb: number;
  benchmark_runs: number;
  risk_level: string;
  confidence: string;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000/api/refactor';

  constructor(private http: HttpClient, private authService: AuthService) {}

  private getHeaders(): HttpHeaders {
    const token = this.authService.getToken();
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
  }

  suggestRefactoring(code: string, filename: string): Observable<CodeRefactorResponse> {
    const headers = this.getHeaders();
    return this.http.post<CodeRefactorResponse>(
      `${this.apiUrl}/suggest`, 
      { code, filename }, 
      { headers }
    );
  }

  runComparison(
    original_code: string, 
    optimized_code: string, 
    filename: string, 
    tracker: string,
    explanations: string[],
    risk_level: string,
    confidence: string
  ): Observable<RunCompareResponse> {
    const headers = this.getHeaders();
    return this.http.post<RunCompareResponse>(
      `${this.apiUrl}/run-compare`,
      { original_code, optimized_code, filename, tracker, explanations, risk_level, confidence },
      { headers }
    );
  }

  simulateImpact(
    original_duration_s: number,
    optimized_duration_s: number,
    original_power_kwh: number,
    optimized_power_kwh: number,
    runs_per_day: number,
    deployment_type: string
  ): Observable<ImpactSimulationResponse> {
    const headers = this.getHeaders();
    return this.http.post<ImpactSimulationResponse>(
      `${this.apiUrl}/impact-simulate`,
      {
        original_duration_s,
        optimized_duration_s,
        original_power_kwh,
        optimized_power_kwh,
        runs_per_day,
        deployment_type
      },
      { headers }
    );
  }

  getHistory(): Observable<JobHistoryItem[]> {
    const headers = this.getHeaders();
    return this.http.get<JobHistoryItem[]>(`${this.apiUrl}/history`, { headers });
  }

  downloadReport(jobId: number): Observable<Blob> {
    const headers = this.getHeaders();
    return this.http.get(`${this.apiUrl}/download-report/${jobId}`, {
      headers,
      responseType: 'blob'
    });
  }
}
