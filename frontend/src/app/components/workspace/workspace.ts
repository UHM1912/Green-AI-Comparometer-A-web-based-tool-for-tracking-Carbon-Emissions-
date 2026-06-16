import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import {
  ApiService,
  CodeRefactorResponse,
  ImpactSimulationResponse,
  RunCompareResponse
} from '../../services/api.service';

@Component({
  selector: 'app-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './workspace.html',
  styleUrls: ['./workspace.css']
})
export class WorkspaceComponent implements OnInit {
  authService = inject(AuthService);
  apiService = inject(ApiService);
  router = inject(Router);

  // States
  isLoadingSuggest = signal<boolean>(false);
  isLoadingRun = signal<boolean>(false);
  
  errorMsg = signal<string>('');
  successMsg = signal<string>('');
  benchmarkFailure = signal<{ failedVersion: string; errorSummary: string } | null>(null);
  
  // Refactoring Outputs
  refactorResult = signal<CodeRefactorResponse | null>(null);
  
  // Benchmark Outputs
  benchmarkResult = signal<RunCompareResponse | null>(null);
  impactSimulation = signal<ImpactSimulationResponse | null>(null);

  // Inputs
  filename = 'main.py';
  inputCode = `def calculate_square_sums(limit):
    # Inefficient loop-based computation
    total_sum = 0
    for i in range(limit):
        total_sum += i ** 2
    return total_sum

# Let's test it
calculate_square_sums(100000)`;

  optimizedCode = '';
  explanations: string[] = [];
  riskLevel = 'medium';
  confidence = 'medium';
  expectedRuntimeImpact = 'unknown';
  expectedMemoryImpact = 'unknown';
  expectedScalabilityImpact = 'unknown';
  selectedTracker = 'eco2AI'; // default
  projectedRunsPerDay = 100;
  deploymentType = 'local_workstation';

  ngOnInit() {
    // Auth route guard
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/login']);
    }
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  goToHistory() {
    this.router.navigate(['/history']);
  }

  triggerRefactoring() {
    if (!this.inputCode.trim()) {
      this.errorMsg.set('Please enter some Python code to optimize.');
      return;
    }

    this.isLoadingSuggest.set(true);
    this.errorMsg.set('');
    this.successMsg.set('');
    this.refactorResult.set(null);
    this.benchmarkResult.set(null);
    this.impactSimulation.set(null);
    this.benchmarkFailure.set(null);

    this.apiService.suggestRefactoring(this.inputCode, this.filename).subscribe({
      next: (res) => {
        this.isLoadingSuggest.set(false);
        this.refactorResult.set(res);
        this.optimizedCode = res.optimized_code;
        this.explanations = res.explanations;
        this.riskLevel = res.risk_level;
        this.confidence = res.confidence;
        this.expectedRuntimeImpact = res.expected_runtime_impact;
        this.expectedMemoryImpact = res.expected_memory_impact;
        this.expectedScalabilityImpact = res.expected_scalability_impact;
      },
      error: (err) => {
        this.isLoadingSuggest.set(false);
        this.errorMsg.set(err.error?.detail || 'Failed to generate code suggestions from Gemini API.');
      }
    });
  }

  triggerBenchmark() {
    if (!this.optimizedCode.trim()) {
      this.errorMsg.set('Optimized code cannot be empty.');
      return;
    }

    this.isLoadingRun.set(true);
    this.errorMsg.set('');
    this.successMsg.set('');
    this.benchmarkResult.set(null);
    this.impactSimulation.set(null);
    this.benchmarkFailure.set(null);

    this.apiService.runComparison(
      this.inputCode,
      this.optimizedCode,
      this.filename,
      this.selectedTracker,
      this.explanations,
      this.riskLevel,
      this.confidence
    ).subscribe({
      next: (res) => {
        this.isLoadingRun.set(false);
        this.benchmarkResult.set(res);
        this.impactSimulation.set(res.impact_simulation);
        this.successMsg.set('Benchmark complete! Scroll down to see metrics.');
      },
      error: (err) => {
        this.isLoadingRun.set(false);
        const detail = err.error?.detail;
        if (typeof detail === 'object' && detail !== null) {
          this.errorMsg.set(detail.message || 'Execution error.');
          this.benchmarkFailure.set({
            failedVersion: detail.failed_version || 'code',
            errorSummary: detail.error_summary || 'Execution failed before benchmark metrics were produced.'
          });
        } else {
          this.errorMsg.set(detail || 'Benchmark execution failed.');
        }
      }
    });
  }

  downloadReport() {
    const res = this.benchmarkResult();
    if (!res || res.job_id === 0) return;

    this.apiService.downloadReport(res.job_id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `EcoRefactor_${this.filename}_Report.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: () => {
        this.errorMsg.set('Failed to download PDF report.');
      }
    });
  }

  refreshImpactSimulation() {
    const result = this.benchmarkResult();
    if (!result || result.job_id === 0) return;

    this.apiService.simulateImpact(
      result.original.duration_s,
      result.optimized.duration_s,
      result.original.power_kwh,
      result.optimized.power_kwh,
      this.projectedRunsPerDay,
      this.deploymentType
    ).subscribe({
      next: (simulation) => {
        this.impactSimulation.set(simulation);
      },
      error: () => {
        this.errorMsg.set('Failed to refresh the impact estimate.');
      }
    });
  }

  // Savings helper utilities
  calcSavingsPercent(orig: number, opt: number): number {
    if (orig === 0) return 0;
    return ((orig - opt) / orig) * 100;
  }
}
