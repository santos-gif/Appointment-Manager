import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IntentService } from '../../core/services/intent.service';
import { AuthService } from '../../core/services/auth.service';
import { BookingIntent, IntentStatus } from '../../core/models';

@Component({
  selector: 'app-triage-queue',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="triage-container animate-fade-in">
      <header class="triage-header glass-panel">
        <div>
          <h2>Intent Screening & Triage Review Portal</h2>
          <p class="triage-sub">
            Evaluate incoming public requests routed to intermediate Project Nodes.
            Approve and programmatically escalate high-value opportunities upward to protected executive nodes.
          </p>
        </div>

        <div class="filter-group">
          <label class="form-label">Status Filter:</label>
          <select [(ngModel)]="statusFilter" (change)="loadQueue()" class="form-control">
            <option value="">All Statuses</option>
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="APPROVED">Approved / Escalated</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </header>

      <div class="queue-grid">
        <div *ngFor="let item of queue()" class="triage-card glass-panel" [class.pending]="item.status === 'PENDING_REVIEW'">
          <div class="card-header">
            <div>
              <div class="card-sub">Booking Intent ID: {{ item.id.substring(0, 8) }}...</div>
              <h4 class="booker-heading">{{ item.booker_name }} ({{ item.booker_email }})</h4>
            </div>
            <span class="badge" [ngClass]="getIntentBadgeClass(item.status)">{{ item.status }}</span>
          </div>

          <div class="timing-box">
            <i class="fa-regular fa-calendar-check"></i>
            Requested Slot: <strong>{{ item.requested_start_time | date:'medium' }}</strong>
          </div>

          <!-- Submitted Intake Responses -->
          <div class="intake-answers" *ngIf="hasResponses(item.intake_responses)">
            <h5>Submitted Intake Questionnaire Data:</h5>
            <div *ngFor="let kv of item.intake_responses | keyvalue" class="answer-row">
              <span class="q-label">{{ kv.key }}:</span>
              <span class="q-val">{{ kv.value }}</span>
            </div>
          </div>

          <div *ngIf="item.triage_notes" class="reviewer-notes-box">
            <strong>Triage Officer Notes:</strong> {{ item.triage_notes }}
          </div>

          <div *ngIf="item.escalation_token" class="escalation-token-box">
            <i class="fa-solid fa-key"></i>
            <span>Cryptographic Escalation Token Active (One-Time Use)</span>
          </div>

          <!-- Triage Actions (Only if Pending) -->
          <div *ngIf="item.status === 'PENDING_REVIEW'" class="card-actions">
            <input
              type="text"
              class="form-control"
              placeholder="Reviewer justification or notes..."
              [(ngModel)]="notesMap[item.id]"
            />
            <div class="btn-row">
              <button class="btn btn-accent btn-sm" (click)="escalate(item)">
                <i class="fa-solid fa-arrow-trend-up"></i> Approve & Escalate Upward
              </button>
              <button class="btn btn-secondary btn-sm" (click)="reject(item)">
                <i class="fa-solid fa-xmark"></i> Reject
              </button>
            </div>
          </div>
        </div>

        <div *ngIf="queue().length === 0" class="empty-state glass-panel">
          <i class="fa-solid fa-inbox empty-icon"></i>
          <h4>Triage Queue is Empty</h4>
          <p>No intents matching the current filter require screening.</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .triage-container {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .triage-header {
      padding: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
      flex-wrap: wrap;
    }
    .triage-sub {
      color: var(--text-muted);
      font-size: 13px;
      margin-top: 4px;
    }
    .filter-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .queue-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
    }
    .triage-card {
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      border-radius: var(--radius-lg);
    }
    .triage-card.pending {
      border-color: rgba(245, 158, 11, 0.4);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .card-sub {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
    }
    .booker-heading {
      font-size: 16px;
      margin-top: 4px;
    }
    .timing-box {
      background: var(--bg-secondary);
      padding: 8px 12px;
      border-radius: var(--radius-md);
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--accent-cyan);
    }
    .intake-answers {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px;
      font-size: 12px;
    }
    .intake-answers h5 {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 6px;
    }
    .answer-row {
      display: flex;
      gap: 8px;
      margin-bottom: 4px;
    }
    .q-label {
      font-weight: 600;
      color: var(--text-secondary);
    }
    .q-val {
      color: var(--text-primary);
    }
    .reviewer-notes-box {
      background: rgba(99, 102, 241, 0.1);
      border: 1px solid rgba(99, 102, 241, 0.25);
      border-radius: var(--radius-md);
      padding: 8px 12px;
      font-size: 12px;
      color: #c7d2fe;
    }
    .escalation-token-box {
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.25);
      border-radius: var(--radius-md);
      padding: 8px 12px;
      font-size: 12px;
      color: #6ee7b7;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .card-actions {
      display: flex;
      flex-direction: column;
      gap: 10px;
      border-top: 1px solid var(--border-subtle);
      padding-top: 14px;
    }
    .btn-row {
      display: flex;
      gap: 10px;
    }
    .empty-state {
      grid-column: 1 / -1;
      text-align: center;
      padding: 60px 20px;
      color: var(--text-muted);
    }
    .empty-icon {
      font-size: 38px;
      margin-bottom: 12px;
      color: var(--accent-indigo);
    }
  `]
})
export class TriageQueueComponent implements OnInit {
  private intentService = inject(IntentService);
  private authService = inject(AuthService);

  queue = signal<BookingIntent[]>([]);
  statusFilter = 'PENDING_REVIEW';
  notesMap: Record<string, string> = {};

  ngOnInit(): void {
    this.loadQueue();
  }

  loadQueue(): void {
    const filter = this.statusFilter ? (this.statusFilter as IntentStatus) : undefined;
    this.intentService.getTriageQueue(filter).subscribe({
      next: (res) => this.queue.set(res),
    });
  }

  hasResponses(responses?: Record<string, any>): boolean {
    return !!responses && Object.keys(responses).length > 0;
  }

  escalate(item: BookingIntent): void {
    const note = this.notesMap[item.id] || 'Intake request approved by triage officer.';
    this.intentService.executeTriageAction(item.id, {
      action: 'approve_and_escalate',
      reviewer_notes: note,
    }).subscribe({
      next: () => {
        alert('✓ Booking intent approved! Cryptographic escalation token issued.');
        this.loadQueue();
      },
    });
  }

  reject(item: BookingIntent): void {
    const note = this.notesMap[item.id] || 'Request did not meet intake screening requirements.';
    this.intentService.executeTriageAction(item.id, {
      action: 'reject',
      reviewer_notes: note,
    }).subscribe({
      next: () => {
        alert('Booking intent marked as Rejected.');
        this.loadQueue();
      },
    });
  }

  getIntentBadgeClass(status: string): string {
    if (status === 'APPROVED') return 'badge-public';
    if (status === 'PENDING_REVIEW') return 'badge-restricted';
    return 'badge-hidden';
  }
}
