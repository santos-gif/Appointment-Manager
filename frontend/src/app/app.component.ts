import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from './core/services/auth.service';
import { ProviderDashboardComponent } from './features/provider-dashboard/provider-dashboard.component';
import { BookerDashboardComponent } from './features/booker-dashboard/booker-dashboard.component';
import { TriageQueueComponent } from './features/triage-portal/triage-queue.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    ProviderDashboardComponent,
    BookerDashboardComponent,
    TriageQueueComponent,
  ],
  template: `
    <div class="app-shell">
      <!-- Main Application Shell Top Navigation Header -->
      <header class="app-header glass-panel">
        <div class="brand-group">
          <div class="brand-logo">
            <i class="fa-solid fa-network-wired logo-icon"></i>
          </div>
          <div>
            <h1 class="brand-title">NexusGov</h1>
            <p class="brand-subtitle">Hierarchical Resource Governance & Scheduling</p>
          </div>
        </div>

        <!-- DUAL-CONTEXT WORKFLOW TOGGLE -->
        <div class="dual-context-toggle">
          <button
            class="context-toggle-btn"
            [class.active]="activeContextView === 'provider'"
            (click)="activeContextView = 'provider'"
          >
            <i class="fa-solid fa-briefcase"></i>
            <span>Provider Host</span>
          </button>

          <button
            class="context-toggle-btn"
            [class.active]="activeContextView === 'booker'"
            (click)="activeContextView = 'booker'"
          >
            <i class="fa-solid fa-compass"></i>
            <span>Booker Explorer</span>
          </button>

          <button
            class="context-toggle-btn"
            [class.active]="activeContextView === 'triage'"
            (click)="activeContextView = 'triage'"
          >
            <i class="fa-solid fa-filter-circle-dollar"></i>
            <span>Triage Screening</span>
          </button>
        </div>

        <!-- User Identity & Mock SSO Switcher -->
        <div class="auth-group">
          <!-- Quick Mock SSO Dropdown -->
          <div class="sso-switcher">
            <span class="sso-label">Simulate OIDC SSO:</span>
            <select class="form-control sso-select" (change)="onSelectSSO($event)">
              <option value="stanford_faculty">Dr. Eleanor Smith (Stanford Faculty)</option>
              <option value="acme_executive">Alex Vance (Acme EVP Strategy)</option>
              <option value="student">Sarah Lee (Stanford Student)</option>
            </select>
          </div>

          <!-- User Profile Indicator -->
          <div class="user-pill" *ngIf="currentUser()">
            <div class="avatar-dot"></div>
            <div class="user-details">
              <span class="user-name">{{ currentUser()?.full_name }}</span>
              <span class="user-role">{{ currentUser()?.roles?.join(', ') }}</span>
            </div>
            <button class="logout-icon-btn" (click)="logout()" title="Logout">
              <i class="fa-solid fa-arrow-right-from-bracket"></i>
            </button>
          </div>
        </div>
      </header>

      <!-- Dynamic Dual-Interface View Container -->
      <main class="app-main-content">
        <app-provider-dashboard *ngIf="activeContextView === 'provider'"></app-provider-dashboard>
        <app-booker-dashboard *ngIf="activeContextView === 'booker'"></app-booker-dashboard>
        <app-triage-queue *ngIf="activeContextView === 'triage'"></app-triage-queue>
      </main>
    </div>
  `,
  styles: [`
    .app-shell {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.08) 0%, transparent 50%), var(--bg-primary);
    }
    .app-header {
      margin: 16px 20px;
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      border-radius: var(--radius-lg);
      flex-wrap: wrap;
    }
    .brand-group {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo {
      width: 40px;
      height: 40px;
      border-radius: var(--radius-md);
      background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-indigo) 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 15px var(--accent-cyan-glow);
    }
    .logo-icon {
      font-size: 20px;
      color: #fff;
    }
    .brand-title {
      font-size: 18px;
      font-weight: 800;
      letter-spacing: -0.02em;
      line-height: 1.1;
      background: linear-gradient(90deg, #fff 0%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .brand-subtitle {
      font-size: 11px;
      color: var(--text-muted);
    }
    .dual-context-toggle {
      display: flex;
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-full);
      padding: 4px;
      gap: 4px;
    }
    .context-toggle-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 18px;
      border-radius: var(--radius-full);
      background: transparent;
      border: 0;
      color: var(--text-secondary);
      font-weight: 600;
      font-size: 13px;
      cursor: pointer;
      transition: all var(--transition-fast);
    }
    .context-toggle-btn:hover {
      color: var(--text-primary);
    }
    .context-toggle-btn.active {
      background: linear-gradient(135deg, var(--accent-indigo) 0%, #4f46e5 100%);
      color: #fff;
      box-shadow: 0 2px 10px var(--accent-indigo-glow);
    }
    .auth-group {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .sso-switcher {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .sso-label {
      font-size: 11px;
      color: var(--text-muted);
    }
    .sso-select {
      font-size: 12px;
      padding: 6px 10px;
      background: var(--bg-secondary);
    }
    .user-pill {
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-full);
      padding: 4px 12px;
    }
    .avatar-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--accent-emerald);
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
    }
    .user-details {
      display: flex;
      flex-direction: column;
    }
    .user-name {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-primary);
    }
    .user-role {
      font-size: 10px;
      color: var(--text-muted);
    }
    .logout-icon-btn {
      background: transparent;
      border: 0;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 14px;
      transition: color var(--transition-fast);
    }
    .logout-icon-btn:hover {
      color: var(--accent-rose);
    }
    .app-main-content {
      flex: 1;
      padding: 0 20px 24px 20px;
    }
  `]
})
export class AppComponent {
  private authService = inject(AuthService);

  activeContextView: 'provider' | 'booker' | 'triage' = 'booker';
  currentUser = this.authService.currentUser;

  onSelectSSO(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const preset = target.value as 'stanford_faculty' | 'acme_executive' | 'student';
    this.authService.mockSSO(preset).subscribe();
  }

  logout(): void {
    this.authService.logout().subscribe();
  }
}
