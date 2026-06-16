import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrls: ['./login.css']
})
export class LoginComponent {
  authService = inject(AuthService);
  router = inject(Router);

  isLoginMode = signal<boolean>(true);
  errorMsg = signal<string>('');
  successMsg = signal<string>('');
  isLoading = signal<boolean>(false);

  // Form fields
  name = '';
  email = '';
  password = '';

  toggleMode() {
    this.isLoginMode.update(val => !val);
    this.errorMsg.set('');
    this.successMsg.set('');
    this.name = '';
    this.email = '';
    this.password = '';
  }

  onSubmit() {
    if (!this.email || !this.password || (!this.isLoginMode() && !this.name)) {
      this.errorMsg.set('Please fill out all required fields.');
      return;
    }

    this.isLoading.set(true);
    this.errorMsg.set('');
    this.successMsg.set('');

    if (this.isLoginMode()) {
      this.authService.login(this.email, this.password).subscribe({
        next: () => {
          this.isLoading.set(false);
          this.router.navigate(['/workspace']);
        },
        error: (err) => {
          this.isLoading.set(false);
          this.errorMsg.set(err.error?.detail || 'Authentication failed. Please check your credentials.');
        }
      });
    } else {
      this.authService.register(this.name, this.email, this.password).subscribe({
        next: () => {
          this.isLoading.set(false);
          this.successMsg.set('Registration successful! Please log in below.');
          this.toggleMode();
        },
        error: (err) => {
          this.isLoading.set(false);
          this.errorMsg.set(err.error?.detail || 'Registration failed. Email might already be taken.');
        }
      });
    }
  }
}
