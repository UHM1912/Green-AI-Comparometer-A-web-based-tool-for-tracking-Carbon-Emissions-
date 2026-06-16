import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login';
import { WorkspaceComponent } from './components/workspace/workspace';
import { HistoryComponent } from './components/history/history';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'workspace', component: WorkspaceComponent },
  { path: 'history', component: HistoryComponent },
  { path: '', redirectTo: '/workspace', pathMatch: 'full' },
  { path: '**', redirectTo: '/workspace' }
];
