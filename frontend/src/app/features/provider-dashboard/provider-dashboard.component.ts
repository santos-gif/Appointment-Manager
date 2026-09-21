import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormArray, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { SchedulingService } from '../../core/services/scheduling.service';
import { IntegrationsService } from '../../core/services/integrations.service';
import { AvailabilityRule, CalendarIntegration, IntakeField, IntakeFormSchema, PaymentEscrowConfig, ResourceCapacity } from '../../core/models';

@Component({
  selector: 'app-provider-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <div class="provider-container animate-fade-in">
      <!-- Top Context Capacity Header -->
      <header class="provider-header glass-panel">
        <div class="capacity-info">
          <div class="icon-avatar">
            <i class="fa-solid fa-user-tie"></i>
          </div>
          <div>
            <div class="context-label">Active Host Capacity Context</div>
            <h2 class="context-title">
              {{ activeContext()?.name || 'No Resource Capacity Selected' }}
            </h2>
            <div class="context-meta">
              <span class="badge badge-resource">Leaf Resource</span>
              <span class="badge" [ngClass]="getTierBadgeClass(activeContext()?.tier)">{{ activeContext()?.tier }}</span>
              <span class="path-text">{{ activeContext()?.path }}</span>
            </div>
          </div>
        </div>

        <!-- Capacity Selector for Identity vs Capacity Separation -->
        <div class="capacity-switcher" *ngIf="capacities().length > 1">
          <label class="form-label">Switch Operational Capacity:</label>
          <select class="form-control" [ngModel]="activeContext()?.node_id" (ngModelChange)="onContextChange($event)">
            <option *ngFor="let cap of capacities()" [value]="cap.node_id">
              {{ cap.name }} ({{ cap.capacity_title }})
            </option>
          </select>
        </div>
      </header>

      <!-- Navigation Tabs -->
      <nav class="tabs-nav">
        <button class="tab-btn" [class.active]="activeTab === 'availability'" (click)="activeTab = 'availability'">
          <i class="fa-solid fa-calendar-days"></i> Operational Availability Matrix
        </button>
        <button class="tab-btn" [class.active]="activeTab === 'calendar-sync'" (click)="activeTab = 'calendar-sync'">
          <i class="fa-solid fa-arrows-rotate"></i> Multi-Calendar Synchronization
        </button>
        <button class="tab-btn" [class.active]="activeTab === 'intake-builder'" (click)="activeTab = 'intake-builder'">
          <i class="fa-solid fa-list-check"></i> Intake Form Builder
        </button>
        <button class="tab-btn" [class.active]="activeTab === 'escrow'" (click)="activeTab = 'escrow'">
          <i class="fa-solid fa-shield-halved"></i> Escrow & Payment Config
        </button>
      </nav>

      <!-- TAB 1: Operational Availability Rules Matrix (Reactive Forms) -->
      <section *ngIf="activeTab === 'availability'" class="tab-content glass-panel">
        <div class="section-heading">
          <div>
            <h3>Contextual Availability Rules Matrix</h3>
            <p class="section-sub">
              Define operational capacity hours specific to this resource node.
              (e.g., Free for PhD Advising Mondays 09:00-13:00; Lab Supervision on Wednesdays).
            </p>
          </div>
          <button class="btn btn-secondary btn-sm" (click)="addRule()">
            <i class="fa-solid fa-plus"></i> Add Time Rule
          </button>
        </div>

        <form [formGroup]="matrixForm" (ngSubmit)="saveMatrix()">
          <div formArrayName="rules" class="rules-list">
            <div *ngFor="let ruleGroup of rulesArray.controls; let i = index" [formGroupName]="i" class="rule-card">
              <div class="rule-row">
                <div class="form-group flex-1">
                  <label class="form-label">Day of Week</label>
                  <select formControlName="day_of_week" class="form-control">
                    <option [ngValue]="0">Monday</option>
                    <option [ngValue]="1">Tuesday</option>
                    <option [ngValue]="2">Wednesday</option>
                    <option [ngValue]="3">Thursday</option>
                    <option [ngValue]="4">Friday</option>
                    <option [ngValue]="5">Saturday</option>
                    <option [ngValue]="6">Sunday</option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">Start Time</label>
                  <input type="text" formControlName="start_time" class="form-control" placeholder="09:00" />
                </div>

                <div class="form-group">
                  <label class="form-label">End Time</label>
                  <input type="text" formControlName="end_time" class="form-control" placeholder="17:00" />
                </div>

                <div class="form-group">
                  <label class="form-label">Slot Duration (Min)</label>
                  <select formControlName="slot_duration_minutes" class="form-control">
                    <option [ngValue]="15">15 min</option>
                    <option [ngValue]="30">30 min</option>
                    <option [ngValue]="45">45 min</option>
                    <option [ngValue]="60">60 min</option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">Buffer (Min)</label>
                  <input type="number" formControlName="buffer_minutes" class="form-control" style="width: 80px;" />
                </div>

                <button type="button" class="btn btn-secondary delete-btn" (click)="removeRule(i)" title="Remove Rule">
                  <i class="fa-solid fa-trash"></i>
                </button>
              </div>
            </div>

            <div *ngIf="rulesArray.length === 0" class="empty-state">
              <i class="fa-regular fa-clock empty-icon"></i>
              <p>No operational rules configured for this node. Click "Add Time Rule" to begin.</p>
            </div>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" [disabled]="savingMatrix">
              <i class="fa-solid fa-cloud-arrow-up"></i>
              {{ savingMatrix ? 'Saving Changes...' : 'Save Availability Matrix' }}
            </button>
            <span *ngIf="matrixSuccessMsg" class="success-banner">{{ matrixSuccessMsg }}</span>
          </div>
        </form>
      </section>

      <!-- TAB 2: Multi-Calendar Synchronization -->
      <section *ngIf="activeTab === 'calendar-sync'" class="tab-content glass-panel">
        <div class="section-heading">
          <div>
            <h3>Multi-Calendar Synchronization</h3>
            <p class="section-sub">
              Aggregate real-time busy slots across Google Calendar and Microsoft Outlook to eliminate scheduling conflicts.
            </p>
          </div>
        </div>

        <div class="calendar-cards-grid">
          <!-- Google Calendar -->
          <div class="integration-card" [class.connected]="googleSync()?.sync_active">
            <div class="card-top">
              <div class="provider-brand">
                <i class="fa-brands fa-google brand-icon google-color"></i>
                <div>
                  <h4>Google Calendar</h4>
                  <p class="brand-sub">Real-Time Busy Slot Ingestion</p>
                </div>
              </div>
              <span class="badge" [class.badge-public]="googleSync()?.sync_active" [class.badge-restricted]="!googleSync()?.sync_active">
                {{ googleSync()?.sync_active ? 'Active & Synced' : 'Disconnected' }}
              </span>
            </div>

            <div class="integration-details">
              <p><strong>Account:</strong> {{ googleSync()?.account_email || 'Not connected' }}</p>
              <p><strong>Status:</strong> {{ googleSync()?.sync_status_message }}</p>
              <p *ngIf="googleSync()?.last_synced_at">
                <strong>Last Updated:</strong> {{ googleSync()?.last_synced_at | date:'short' }}
              </p>
            </div>

            <button class="btn btn-secondary btn-sm" (click)="connectOAuth('google')">
              <i class="fa-solid fa-link"></i>
              {{ googleSync()?.sync_active ? 'Re-authenticate Google' : 'Connect Google Calendar' }}
            </button>
          </div>

          <!-- Microsoft Outlook -->
          <div class="integration-card" [class.connected]="outlookSync()?.sync_active">
            <div class="card-top">
              <div class="provider-brand">
                <i class="fa-brands fa-microsoft brand-icon ms-color"></i>
                <div>
                  <h4>Microsoft Outlook</h4>
                  <p class="brand-sub">Office 365 Enterprise Sync</p>
                </div>
              </div>
              <span class="badge" [class.badge-public]="outlookSync()?.sync_active" [class.badge-restricted]="!outlookSync()?.sync_active">
                {{ outlookSync()?.sync_active ? 'Active & Synced' : 'Disconnected' }}
              </span>
            </div>

            <div class="integration-details">
              <p><strong>Account:</strong> {{ outlookSync()?.account_email || 'Not connected' }}</p>
              <p><strong>Status:</strong> {{ outlookSync()?.sync_status_message }}</p>
            </div>

            <button class="btn btn-secondary btn-sm" (click)="connectOAuth('outlook')">
              <i class="fa-solid fa-link"></i>
              {{ outlookSync()?.sync_active ? 'Re-authenticate Outlook' : 'Connect Microsoft Outlook' }}
            </button>
          </div>
        </div>
      </section>

      <!-- TAB 3: Interactive Intake Form Builder -->
      <section *ngIf="activeTab === 'intake-builder'" class="tab-content glass-panel">
        <div class="section-heading">
          <div>
            <h3>Interactive Schema Intake Form Builder</h3>
            <p class="section-sub">
              Define custom metadata fields to capture from bookers during checkout.
            </p>
          </div>
          <button class="btn btn-secondary btn-sm" (click)="addIntakeField()">
            <i class="fa-solid fa-plus"></i> Add Question Field
          </button>
        </div>

        <div class="intake-builder-layout">
          <!-- Left: Schema Editor -->
          <div class="builder-editor">
            <div class="form-group">
              <label class="form-label">Form Title</label>
              <input type="text" [(ngModel)]="intakeSchema.title" class="form-control" />
            </div>
            <div class="form-group">
              <label class="form-label">Form Instructions</label>
              <textarea [(ngModel)]="intakeSchema.description" class="form-control" rows="2"></textarea>
            </div>

            <div class="fields-list">
              <div *ngFor="let f of intakeSchema.fields_json; let idx = index" class="field-item-card">
                <div class="field-item-header">
                  <span class="field-num">#{{ idx + 1 }}</span>
                  <input type="text" [(ngModel)]="f.label" class="form-control" placeholder="Field Question / Label" />
                  <select [(ngModel)]="f.type" class="form-control" style="width: 140px;">
                    <option value="text">Single Line Text</option>
                    <option value="textarea">Paragraph</option>
                    <option value="select">Dropdown Menu</option>
                    <option value="checkbox">Checkbox Confirmation</option>
                  </select>
                  <label class="checkbox-label">
                    <input type="checkbox" [(ngModel)]="f.required" /> Required
                  </label>
                  <button class="btn btn-secondary delete-btn" (click)="removeIntakeField(idx)">
                    <i class="fa-solid fa-trash"></i>
                  </button>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button class="btn btn-primary" (click)="saveIntakeSchema()">
                <i class="fa-solid fa-check"></i> Save Intake Schema
              </button>
              <span *ngIf="intakeSuccessMsg" class="success-banner">{{ intakeSuccessMsg }}</span>
            </div>
          </div>

          <!-- Right: Live Preview -->
          <div class="builder-preview">
            <div class="preview-header">
              <i class="fa-regular fa-eye"></i> Booker Checkout Preview
            </div>
            <div class="preview-card">
              <h4>{{ intakeSchema.title }}</h4>
              <p class="preview-sub">{{ intakeSchema.description }}</p>
              <hr class="divider" />
              <div *ngFor="let f of intakeSchema.fields_json" class="preview-field">
                <label class="form-label">
                  {{ f.label }} <span *ngIf="f.required" style="color: var(--accent-rose);">*</span>
                </label>
                <input *ngIf="f.type === 'text'" type="text" class="form-control" [placeholder]="f.placeholder || 'Your response...'" disabled />
                <textarea *ngIf="f.type === 'textarea'" class="form-control" disabled></textarea>
                <select *ngIf="f.type === 'select'" class="form-control" disabled>
                  <option>Select an option...</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- TAB 4: Escrow & Payment Configuration -->
      <section *ngIf="activeTab === 'escrow'" class="tab-content glass-panel">
        <div class="section-heading">
          <div>
            <h3>Escrow & Payment Configuration</h3>
            <p class="section-sub">
              Stripe and PayPal integration management panel enabling paid consultations and deposit escrow terms.
            </p>
          </div>
        </div>

        <div class="escrow-form-layout">
          <div class="form-group">
            <label class="checkbox-label toggle-label">
              <input type="checkbox" [(ngModel)]="escrowConfig.is_enabled" />
              <strong>Enable Paid Consultation Fee for this Node</strong>
            </label>
          </div>

          <div *ngIf="escrowConfig.is_enabled" class="escrow-fields animate-fade-in">
            <div class="rule-row">
              <div class="form-group">
                <label class="form-label">Payment Gateway</label>
                <select [(ngModel)]="escrowConfig.provider" class="form-control">
                  <option value="stripe">Stripe Connect Escrow</option>
                  <option value="paypal">PayPal Commerce Platform</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">Price per Session (Cents)</label>
                <input type="number" [(ngModel)]="escrowConfig.amount_cents" class="form-control" placeholder="15000" />
                <span class="help-text">{{ (escrowConfig.amount_cents / 100) | currency:escrowConfig.currency }}</span>
              </div>

              <div class="form-group">
                <label class="form-label">Currency</label>
                <select [(ngModel)]="escrowConfig.currency" class="form-control">
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Escrow Release Policy</label>
              <select [(ngModel)]="escrowConfig.escrow_policy" class="form-control">
                <option value="escrow_hold_until_session">Escrow Hold: Released 1 hour after session completes</option>
                <option value="instant_capture">Instant Capture: Released immediately on booking confirmation</option>
                <option value="refundable_until_24h">Strict 24h Window: Full refund if cancelled 24 hours prior</option>
              </select>
            </div>
          </div>

          <div class="form-actions">
            <button class="btn btn-primary" (click)="saveEscrowConfig()">
              <i class="fa-solid fa-shield-check"></i> Save Escrow Settings
            </button>
            <span *ngIf="escrowSuccessMsg" class="success-banner">{{ escrowSuccessMsg }}</span>
          </div>
        </div>
      </section>
    </div>
  `,
  styles: [`
    .provider-container {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .provider-header {
      padding: 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      flex-wrap: wrap;
    }
    .capacity-info {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .icon-avatar {
      width: 48px;
      height: 48px;
      border-radius: var(--radius-md);
      background: linear-gradient(135deg, var(--accent-indigo) 0%, var(--accent-purple) 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      color: #fff;
    }
    .context-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      font-weight: 600;
    }
    .context-title {
      font-size: 22px;
      font-weight: 700;
      color: var(--text-primary);
    }
    .context-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 4px;
    }
    .path-text {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-secondary);
    }
    .capacity-switcher {
      min-width: 280px;
    }
    .tabs-nav {
      display: flex;
      gap: 10px;
      border-bottom: 1px solid var(--border-subtle);
      padding-bottom: 8px;
      overflow-x: auto;
    }
    .tab-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 18px;
      background: transparent;
      border: 1px solid transparent;
      border-radius: var(--radius-md);
      color: var(--text-secondary);
      font-weight: 500;
      cursor: pointer;
      transition: all var(--transition-fast);
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: var(--text-primary);
      background: var(--bg-surface);
    }
    .tab-btn.active {
      color: var(--text-primary);
      background: var(--bg-surface-elevated);
      border-color: var(--border-subtle);
      box-shadow: var(--shadow-sm);
    }
    .tab-content {
      padding: 24px;
    }
    .section-heading {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
      gap: 16px;
    }
    .section-sub {
      color: var(--text-muted);
      font-size: 13px;
      margin-top: 4px;
    }
    .rule-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px;
      margin-bottom: 12px;
    }
    .rule-row {
      display: flex;
      align-items: flex-end;
      gap: 12px;
      flex-wrap: wrap;
    }
    .flex-1 { flex: 1; min-width: 150px; }
    .delete-btn {
      height: 38px;
      width: 38px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--accent-rose);
      margin-bottom: 14px;
    }
    .delete-btn:hover {
      background: rgba(244, 63, 94, 0.15);
      border-color: var(--accent-rose);
    }
    .form-actions {
      display: flex;
      align-items: center;
      gap: 14px;
      margin-top: 20px;
    }
    .success-banner {
      color: var(--accent-emerald);
      font-size: 13px;
      font-weight: 500;
    }
    .calendar-cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
    }
    .integration-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .integration-card.connected {
      border-color: rgba(16, 185, 129, 0.3);
    }
    .card-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .provider-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-icon {
      font-size: 28px;
    }
    .google-color { color: #ea4335; }
    .ms-color { color: #00a4ef; }
    .brand-sub {
      font-size: 12px;
      color: var(--text-muted);
    }
    .integration-details {
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.6;
    }
    .intake-builder-layout {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 24px;
    }
    @media (max-width: 900px) {
      .intake-builder-layout { grid-template-columns: 1fr; }
    }
    .field-item-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px;
      margin-bottom: 10px;
    }
    .field-item-header {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .field-num {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-muted);
    }
    .checkbox-label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: var(--text-secondary);
      cursor: pointer;
    }
    .toggle-label {
      font-size: 15px;
      color: var(--text-primary);
    }
    .preview-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px;
    }
    .preview-header {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 8px;
    }
    .preview-sub {
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    .divider {
      border: 0;
      border-top: 1px solid var(--border-subtle);
      margin: 14px 0;
    }
    .preview-field {
      margin-bottom: 12px;
    }
    .empty-state {
      text-align: center;
      padding: 30px;
      color: var(--text-muted);
    }
    .empty-icon {
      font-size: 32px;
      margin-bottom: 8px;
    }
  `]
})
export class ProviderDashboardComponent implements OnInit {
  private authService = inject(AuthService);
  private schedulingService = inject(SchedulingService);
  private integrationsService = inject(IntegrationsService);
  private fb = inject(FormBuilder);

  activeTab: 'availability' | 'calendar-sync' | 'intake-builder' | 'escrow' = 'availability';

  capacities = this.authService.activeCapacities;
  activeContext = this.authService.activeContextNode;

  // Availability Matrix Form
  matrixForm: FormGroup = this.fb.group({
    rules: this.fb.array([]),
  });
  savingMatrix = false;
  matrixSuccessMsg = '';

  // Calendar Integrations
  googleSync = signal<CalendarIntegration | null>(null);
  outlookSync = signal<CalendarIntegration | null>(null);

  // Intake Form Schema
  intakeSchema: IntakeFormSchema = {
    node_id: '',
    title: 'Pre-Consultation Intake Questionnaire',
    description: 'Please describe the context and objectives for this appointment.',
    fields_json: [
      { id: 'q1', type: 'text', label: 'Primary Meeting Objective', required: true },
      { id: 'q2', type: 'select', label: 'Urgency / Impact Level', required: true, options: ['Low', 'Medium', 'Critical'] },
      { id: 'q3', type: 'textarea', label: 'Background Context & Documentation', required: false },
    ],
  };
  intakeSuccessMsg = '';

  // Escrow Configuration
  escrowConfig: PaymentEscrowConfig = {
    node_id: '',
    provider: 'stripe',
    is_enabled: false,
    amount_cents: 15000,
    currency: 'USD',
    escrow_policy: 'escrow_hold_until_session',
  };
  escrowSuccessMsg = '';

  get rulesArray(): FormArray {
    return this.matrixForm.get('rules') as FormArray;
  }

  ngOnInit(): void {
    this.loadNodeContextData();
  }

  loadNodeContextData(): void {
    const node = this.activeContext();
    if (!node) return;

    // 1. Load availability matrix
    this.schedulingService.getAvailabilityMatrix(node.node_id).subscribe({
      next: (res) => {
        this.rulesArray.clear();
        if (res.rules && res.rules.length > 0) {
          res.rules.forEach((r) => this.rulesArray.push(this.createRuleGroup(r)));
        } else {
          // Default initial rules
          this.rulesArray.push(this.createRuleGroup({
            day_of_week: 0,
            start_time: '09:00',
            end_time: '13:00',
            slot_duration_minutes: 30,
            buffer_minutes: 10,
            is_active: true,
          }));
          this.rulesArray.push(this.createRuleGroup({
            day_of_week: 2,
            start_time: '10:00',
            end_time: '15:00',
            slot_duration_minutes: 45,
            buffer_minutes: 15,
            is_active: true,
          }));
        }
      },
    });

    // 2. Load calendar sync status
    this.integrationsService.getCalendarSync(node.node_id).subscribe({
      next: (res) => {
        const g = res.find((i) => i.provider === 'google');
        const o = res.find((i) => i.provider === 'outlook');
        if (g) this.googleSync.set(g);
        if (o) this.outlookSync.set(o);
      },
    });

    // 3. Load Escrow config
    this.integrationsService.getEscrowConfig(node.node_id).subscribe({
      next: (res) => {
        if (res) this.escrowConfig = res;
      },
    });

    // 4. Load Intake schema
    this.integrationsService.getIntakeSchema(node.node_id).subscribe({
      next: (res) => {
        if (res) {
          this.intakeSchema = {
            ...res,
            fields_json: (res.fields_json as any) || this.intakeSchema.fields_json,
          };
        }
      },
    });
  }

  createRuleGroup(rule?: Partial<AvailabilityRule>): FormGroup {
    return this.fb.group({
      day_of_week: [rule?.day_of_week ?? 0, Validators.required],
      start_time: [rule?.start_time ?? '09:00', Validators.required],
      end_time: [rule?.end_time ?? '17:00', Validators.required],
      slot_duration_minutes: [rule?.slot_duration_minutes ?? 30, Validators.required],
      buffer_minutes: [rule?.buffer_minutes ?? 10, Validators.required],
      is_active: [rule?.is_active ?? true],
    });
  }

  addRule(): void {
    this.rulesArray.push(this.createRuleGroup());
  }

  removeRule(index: number): void {
    this.rulesArray.removeAt(index);
  }

  saveMatrix(): void {
    const node = this.activeContext();
    if (!node) return;

    this.savingMatrix = true;
    this.matrixSuccessMsg = '';
    const rules: AvailabilityRule[] = this.matrixForm.value.rules;

    this.schedulingService.updateAvailabilityMatrix(node.node_id, rules).subscribe({
      next: () => {
        this.savingMatrix = false;
        this.matrixSuccessMsg = '✓ Operational availability rules matrix successfully updated.';
        setTimeout(() => (this.matrixSuccessMsg = ''), 4000);
      },
      error: () => (this.savingMatrix = false),
    });
  }

  connectOAuth(provider: 'google' | 'outlook'): void {
    const node = this.activeContext();
    if (!node) return;
    this.integrationsService.connectCalendar(node.node_id, provider).subscribe({
      next: () => {
        this.loadNodeContextData();
      },
    });
  }

  addIntakeField(): void {
    const newId = 'q' + (this.intakeSchema.fields_json.length + 1);
    this.intakeSchema.fields_json.push({
      id: newId,
      type: 'text',
      label: 'New Question',
      required: true,
    });
  }

  removeIntakeField(idx: number): void {
    this.intakeSchema.fields_json.splice(idx, 1);
  }

  saveIntakeSchema(): void {
    const node = this.activeContext();
    if (!node) return;
    this.intakeSchema.node_id = node.node_id;
    this.integrationsService.saveIntakeSchema(node.node_id, this.intakeSchema).subscribe({
      next: () => {
        this.intakeSuccessMsg = '✓ Custom intake form schema saved.';
        setTimeout(() => (this.intakeSuccessMsg = ''), 4000);
      },
    });
  }

  saveEscrowConfig(): void {
    const node = this.activeContext();
    if (!node) return;
    this.escrowConfig.node_id = node.node_id;
    this.integrationsService.updateEscrowConfig(node.node_id, this.escrowConfig).subscribe({
      next: () => {
        this.escrowSuccessMsg = '✓ Escrow and payment configurations saved.';
        setTimeout(() => (this.escrowSuccessMsg = ''), 4000);
      },
    });
  }

  onContextChange(nodeId: string): void {
    const target = this.capacities().find((c) => c.node_id === nodeId);
    if (target) {
      this.authService.setActiveContext(target);
      this.loadNodeContextData();
    }
  }

  getTierBadgeClass(tier?: string): string {
    if (tier === 'PUBLIC') return 'badge-public';
    if (tier === 'RESTRICTED') return 'badge-restricted';
    return 'badge-hidden';
  }
}
