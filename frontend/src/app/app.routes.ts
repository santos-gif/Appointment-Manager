import { Routes } from '@angular/router';
import { BookerDashboardComponent } from './features/booker-dashboard/booker-dashboard.component';
import { ProviderDashboardComponent } from './features/provider-dashboard/provider-dashboard.component';
import { TriageQueueComponent } from './features/triage-portal/triage-queue.component';

export const routes: Routes = [
  { path: '', redirectTo: 'booker', pathMatch: 'full' },
  { path: 'booker', component: BookerDashboardComponent },
  { path: 'provider', component: ProviderDashboardComponent },
  { path: 'triage', component: TriageQueueComponent },
  { path: '**', redirectTo: 'booker' },
];
