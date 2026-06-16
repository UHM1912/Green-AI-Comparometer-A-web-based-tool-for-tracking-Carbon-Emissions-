import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ApiService, JobHistoryItem } from '../../services/api.service';

@Component({
  selector: 'app-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './history.html',
  styleUrls: ['./history.css']
})
export class HistoryComponent implements OnInit {
  authService = inject(AuthService);
  apiService = inject(ApiService);
  router = inject(Router);

  isLoading = signal<boolean>(false);
  errorMsg = signal<string>('');
  
  historyList = signal<JobHistoryItem[]>([]);

  ngOnInit() {
    // Auth route guard
    if (!this.authService.isLoggedIn()) {
      this.router.navigate(['/login']);
      return;
    }
    this.fetchHistory();
  }

  fetchHistory() {
    this.isLoading.set(true);
    this.errorMsg.set('');

    this.apiService.getHistory().subscribe({
      next: (data) => {
        this.isLoading.set(false);
        this.historyList.set(data);
      },
      error: () => {
        this.isLoading.set(false);
        this.errorMsg.set('Failed to fetch historical runs.');
      }
    });
  }

  downloadReport(jobId: number, filename: string) {
    this.apiService.downloadReport(jobId).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `EcoRefactor_${filename}_Report.pdf`;
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

  goToWorkspace() {
    this.router.navigate(['/workspace']);
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  calcSavingsPercent(orig: number, opt: number): number {
    if (orig === 0) return 0;
    return ((orig - opt) / orig) * 100;
  }
}
