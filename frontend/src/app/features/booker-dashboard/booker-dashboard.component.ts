import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NodeService } from '../../core/services/node.service';
import { SearchService } from '../../core/services/search.service';
import { SchedulingService } from '../../core/services/scheduling.service';
import { IntentService } from '../../core/services/intent.service';
import { AuthService } from '../../core/services/auth.service';
import { IntegrationsService } from '../../core/services/integrations.service';
import { Appointment, AvailableSlot, BookingIntent, IntakeFormSchema, NodeItem, NodeTreeItem, SearchResultItem, VisibilityTier } from '../../core/models';

@Component({
  selector: 'app-booker-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="booker-container animate-fade-in">
      <!-- Top Explorer Header -->
      <header class="booker-header glass-panel">
        <div>
          <h2 class="booker-title">Centralized Discovery & Scheduling Portal</h2>
          <p class="booker-sub">
            Explore authorized organizations, discover academic hosts & executive assets, and book conflict-free appointments across timezones.
          </p>
        </div>

        <div class="system-tz-indicator">
          <i class="fa-solid fa-earth-americas tz-icon"></i>
          <div>
            <div class="tz-label">Client Timezone Engine</div>
            <select [(ngModel)]="detectedTimezone" (change)="onTimezoneChange()" class="form-control tz-select">
              <option value="America/Los_Angeles">America/Los_Angeles (PT)</option>
              <option value="America/New_York">America/New_York (ET)</option>
              <option value="Europe/London">Europe/London (GMT/BST)</option>
              <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
              <option value="UTC">UTC (Universal Coordinated)</option>
            </select>
          </div>
        </div>
      </header>

      <!-- Main Workspace Grid: Left = Unified Directory; Right = Timezone Calendar & Booking Engine -->
      <div class="workspace-grid">
        <!-- LEFT PANEL: Unified Directory (Search + Hierarchy Tree) -->
        <aside class="directory-panel glass-panel">
          <div class="search-box">
            <i class="fa-solid fa-magnifying-glass search-icon"></i>
            <input
              type="text"
              class="form-control search-input"
              [(ngModel)]="searchQuery"
              (input)="onSearchInput()"
              placeholder="Search by topic, faculty, or tags..."
            />
          </div>

          <!-- Tree / Search Toggle -->
          <div class="view-toggle">
            <button class="btn btn-sm" [class.btn-primary]="activeDirectoryTab === 'tree'" [class.btn-secondary]="activeDirectoryTab !== 'tree'" (click)="activeDirectoryTab = 'tree'">
              <i class="fa-solid fa-folder-tree"></i> Structural Tree
            </button>
            <button class="btn btn-sm" [class.btn-primary]="activeDirectoryTab === 'search'" [class.btn-secondary]="activeDirectoryTab !== 'search'" (click)="activeDirectoryTab = 'search'">
              <i class="fa-solid fa-bolt"></i> Semantic Discovery ({{ searchResults().length }})
            </button>
          </div>

          <!-- Mode A: Hierarchical Multi-Tenant Tree Explorer -->
          <div *ngIf="activeDirectoryTab === 'tree'" class="tree-explorer">
            <div *ngFor="let root of rootOrgs()" class="org-tree-block">
              <div class="tree-node org-node" (click)="selectNode(root)">
                <i class="fa-solid fa-landmark node-icon text-indigo"></i>
                <span class="node-name">{{ root.name }}</span>
                <span class="badge badge-org">Tenant Root</span>
              </div>

              <!-- Children Subtree -->
              <div *ngIf="treeData() && treeData()!.id === root.id" class="subtree-block">
                <ng-container *ngTemplateOutlet="recursiveTree; context: { $implicit: treeData()!.children }"></ng-container>
              </div>
            </div>
          </div>

          <!-- Mode B: Semantic Search Results List -->
          <div *ngIf="activeDirectoryTab === 'search'" class="search-results-list">
            <div *ngFor="let item of searchResults()" class="search-result-card" [class.selected]="selectedResource()?.id === item.id" (click)="selectSearchResult(item)">
              <div class="result-header">
                <span class="result-title">{{ item.name }}</span>
                <span class="badge" [ngClass]="getTierBadgeClass(item.visibility_tier)">{{ item.visibility_tier }}</span>
              </div>
              <p class="result-path">{{ item.path }}</p>
              <div class="result-footer">
                <span *ngIf="item.capacity_title" class="capacity-tag">{{ item.capacity_title }}</span>
                <span *ngIf="item.triage_required" class="badge badge-hidden">
                  <i class="fa-solid fa-lock"></i> Intent Triage Required
                </span>
                <span *ngIf="item.direct_booking_allowed" class="badge badge-public">
                  <i class="fa-solid fa-calendar-check"></i> Direct Booking
                </span>
              </div>
            </div>

            <div *ngIf="searchResults().length === 0" class="empty-state">
              <p>No nodes matching query visible under current authorization.</p>
            </div>
          </div>
        </aside>

        <!-- RIGHT PANEL: Timezone Engine Calendar & Appointment Scheduler -->
        <main class="scheduler-panel glass-panel">
          <div *ngIf="!selectedResource()" class="empty-scheduler">
            <div class="pulse-indicator empty-icon-wrap">
              <i class="fa-solid fa-calendar-plus empty-big-icon"></i>
            </div>
            <h3>Select a Resource to View Conflict-Free Slots</h3>
            <p>
              Choose an academic advisor, laboratory asset, or executive partner from the Unified Directory on the left.
            </p>
          </div>

          <div *ngIf="selectedResource()" class="active-scheduler animate-fade-in">
            <!-- Selected Resource Banner -->
            <div class="host-banner">
              <div>
                <div class="host-pre">Target Operational Capacity</div>
                <h3 class="host-name">{{ selectedResource()!.name }}</h3>
                <div class="host-meta">
                  <span class="badge badge-resource">Leaf Host</span>
                  <span class="badge" [ngClass]="getTierBadgeClass(getSelectedTier())">
                    {{ getSelectedTier() }}
                  </span>
                  <span class="host-path">{{ selectedResource()!.path }}</span>
                </div>
              </div>

              <div *ngIf="isTriageRequired(selectedResource()!)" class="guardrail-alert">
                <i class="fa-solid fa-shield-halved guardrail-icon"></i>
                <div>
                  <strong>Intent-Based Routing Guardrail Active</strong>
                  <p>Executive calendar protected. Requests are screened by the Intake Triage Layer.</p>
                </div>
              </div>
            </div>

            <!-- Date Picker & Timezone Bar -->
            <div class="date-picker-bar">
              <div class="form-group">
                <label class="form-label">Booking Date</label>
                <input type="date" [(ngModel)]="targetDate" (change)="loadAvailableSlots()" class="form-control" />
              </div>

              <div class="tz-display-pill">
                <i class="fa-regular fa-clock"></i>
                Slots Adjusted for: <strong>{{ detectedTimezone }}</strong>
              </div>
            </div>

            <!-- Conflict-Free Available Slot Tiles -->
            <div class="slots-section">
              <h4>Available Conflict-Free Time Windows</h4>
              <p class="slots-sub">Cross-referenced against provider's rules matrix and external calendar sync blocks.</p>

              <div class="slots-grid">
                <button
                  *ngFor="let slot of availableSlots()"
                  class="slot-tile"
                  [class.unavailable]="!slot.is_available"
                  [class.selected]="selectedSlot === slot"
                  [disabled]="!slot.is_available"
                  (click)="selectSlot(slot)"
                >
                  <span class="slot-time">{{ slot.formatted_start }} – {{ slot.formatted_end }}</span>
                  <span class="slot-status">{{ slot.is_available ? 'Available' : 'Reserved' }}</span>
                </button>
              </div>

              <div *ngIf="availableSlots().length === 0" class="empty-slots">
                <i class="fa-regular fa-calendar-xmark"></i>
                <p>No operational availability slots configured for {{ targetDate }}.</p>
              </div>
            </div>

            <!-- Checkout / Booking Action Bar -->
            <div *ngIf="selectedSlot" class="booking-checkout-box glass-panel animate-fade-in">
              <div class="checkout-summary">
                <div>
                  <div class="summary-label">Selected Reservation Window:</div>
                  <div class="summary-val">
                    {{ selectedSlot.formatted_start }} - {{ selectedSlot.formatted_end }} ({{ detectedTimezone }}) on {{ targetDate }}
                  </div>
                </div>

                <button class="btn btn-accent" (click)="openBookingModal()">
                  <i class="fa-solid fa-arrow-right"></i>
                  {{ isTriageRequired(selectedResource()!) ? 'Submit for Intake Triage' : 'Confirm Direct Booking' }}
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>

      <!-- BOTTOM SECTION: Status Tracker (Sent Booking Intents & Confirmed Appointments) -->
      <section class="tracker-section glass-panel">
        <div class="tracker-header">
          <div>
            <h3>Sent Booking Engagements & Intent Lifecycles</h3>
            <p class="section-sub">Pipeline tracking for exploratory requests and triage review escalations.</p>
          </div>
          <button class="btn btn-secondary btn-sm" (click)="refreshTracker()">
            <i class="fa-solid fa-rotate"></i> Refresh
          </button>
        </div>

        <div class="intents-tracker-list">
          <div *ngFor="let intent of userIntents()" class="tracker-item">
            <div class="tracker-main">
              <div class="tracker-title">Request for Target Resource: {{ intent.target_node_id }}</div>
              <div class="tracker-meta">
                Requested: {{ intent.requested_start_time | date:'medium' }}
              </div>
            </div>

            <!-- Stepper Visual Component -->
            <div class="lifecycle-pipeline">
              <div class="pipeline-step" [class.done]="true">
                <div class="step-dot">✓</div>
                <span>Submitted</span>
              </div>
              <div class="pipeline-line" [class.done]="intent.status !== 'PENDING_REVIEW'"></div>
              <div class="pipeline-step" [class.done]="intent.status === 'APPROVED' || intent.status === 'COMPLETED'" [class.active]="intent.status === 'PENDING_REVIEW'">
                <div class="step-dot">{{ intent.status === 'PENDING_REVIEW' ? '•' : '✓' }}</div>
                <span>Triage Review</span>
              </div>
              <div class="pipeline-line" [class.done]="intent.status === 'COMPLETED'"></div>
              <div class="pipeline-step" [class.done]="intent.status === 'COMPLETED'" [class.active]="intent.status === 'APPROVED'">
                <div class="step-dot">{{ intent.status === 'COMPLETED' ? '✓' : '•' }}</div>
                <span>Escalated & Confirmed</span>
              </div>
            </div>

            <div class="tracker-status">
              <span class="badge" [ngClass]="getIntentBadgeClass(intent.status)">{{ intent.status }}</span>
              <button *ngIf="intent.status === 'APPROVED' && intent.escalation_token" class="btn btn-accent btn-sm" (click)="confirmEscalated(intent)">
                Confirm Escalation Slot
              </button>
            </div>
          </div>

          <div *ngIf="userIntents().length === 0" class="empty-state">
            <p>No outgoing appointment requests or intents tracked yet.</p>
          </div>
        </div>
      </section>

      <!-- MODAL: Intake Form Questionnaire & Atomic Checkout -->
      <div *ngIf="showBookingModal" class="modal-backdrop">
        <div class="modal-dialog glass-panel animate-fade-in">
          <div class="modal-header">
            <h4>{{ isTriageRequired(selectedResource()!) ? 'Screening Intake Questionnaire' : 'Confirm Appointment Reservation' }}</h4>
            <button class="close-btn" (click)="showBookingModal = false">✕</button>
          </div>

          <div class="modal-body">
            <div class="form-group">
              <label class="form-label">Your Name</label>
              <input type="text" [(ngModel)]="bookerForm.name" class="form-control" />
            </div>

            <div class="form-group">
              <label class="form-label">Your Email</label>
              <input type="email" [(ngModel)]="bookerForm.email" class="form-control" />
            </div>

            <div class="form-group">
              <label class="form-label">Session Title / Topic</label>
              <input type="text" [(ngModel)]="bookerForm.title" class="form-control" />
            </div>

            <!-- Dynamic Schema Fields from Node's Intake Schema -->
            <div *ngIf="intakeSchema" class="dynamic-schema-block">
              <h5 class="schema-heading">{{ intakeSchema.title }}</h5>
              <div *ngFor="let field of intakeSchema.fields_json" class="form-group">
                <label class="form-label">
                  {{ field.label }} <span *ngIf="field.required" style="color: var(--accent-rose);">*</span>
                </label>
                <input *ngIf="field.type === 'text'" type="text" [(ngModel)]="bookerForm.intakeResponses[field.id]" class="form-control" />
                <textarea *ngIf="field.type === 'textarea'" [(ngModel)]="bookerForm.intakeResponses[field.id]" class="form-control"></textarea>
                <select *ngIf="field.type === 'select'" [(ngModel)]="bookerForm.intakeResponses[field.id]" class="form-control">
                  <option *ngFor="let opt of field.options" [value]="opt">{{ opt }}</option>
                </select>
              </div>
            </div>

            <div *ngIf="bookingError" class="error-banner">
              {{ bookingError }}
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" (click)="showBookingModal = false">Cancel</button>
            <button class="btn btn-primary" [disabled]="submittingBooking" (click)="submitBooking()">
              {{ submittingBooking ? 'Processing...' : (isTriageRequired(selectedResource()!) ? 'Submit for Triage' : 'Book with Concurrency Lock') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Recursive Tree Node Template -->
    <ng-template #recursiveTree let-children>
      <div *ngFor="let node of children" class="tree-node-wrapper">
        <div class="tree-node" (click)="selectNode(node)">
          <i class="node-icon" [ngClass]="getNodeIcon(node.node_type)"></i>
          <span class="node-name">{{ node.name }}</span>
          <span class="badge" [ngClass]="getNodeBadgeClass(node.node_type)">{{ node.node_type }}</span>
          <span class="badge" [ngClass]="getTierBadgeClass(node.visibility_settings?.tier)">
            {{ node.visibility_settings?.tier }}
          </span>
        </div>

        <div *ngIf="node.children && node.children.length > 0" class="subtree-block">
          <ng-container *ngTemplateOutlet="recursiveTree; context: { $implicit: node.children }"></ng-container>
        </div>
      </div>
    </ng-template>
  `,
  styles: [`
    .booker-container {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .booker-header {
      padding: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
      flex-wrap: wrap;
    }
    .booker-title {
      font-size: 24px;
      font-weight: 700;
    }
    .booker-sub {
      color: var(--text-muted);
      font-size: 13px;
      margin-top: 4px;
    }
    .system-tz-indicator {
      display: flex;
      align-items: center;
      gap: 12px;
      background: var(--bg-secondary);
      padding: 10px 16px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border-subtle);
    }
    .tz-icon {
      font-size: 24px;
      color: var(--accent-cyan);
    }
    .tz-label {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
      font-weight: 600;
    }
    .tz-select {
      background: transparent;
      border: 0;
      color: var(--text-primary);
      font-weight: 600;
      padding: 0;
      cursor: pointer;
    }
    .workspace-grid {
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: 20px;
    }
    @media (max-width: 960px) {
      .workspace-grid { grid-template-columns: 1fr; }
    }
    .directory-panel {
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      max-height: 800px;
      overflow-y: auto;
    }
    .search-box {
      position: relative;
    }
    .search-icon {
      position: absolute;
      left: 12px;
      top: 12px;
      color: var(--text-muted);
    }
    .search-input {
      padding-left: 36px;
      width: 100%;
    }
    .view-toggle {
      display: flex;
      gap: 8px;
    }
    .tree-explorer {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .tree-node-wrapper {
      margin-left: 14px;
      border-left: 1px dashed var(--border-subtle);
      padding-left: 10px;
    }
    .tree-node {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 7px 10px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      transition: all var(--transition-fast);
      margin-bottom: 2px;
    }
    .tree-node:hover {
      background: var(--bg-surface-elevated);
    }
    .org-node {
      font-weight: 600;
      background: rgba(99, 102, 241, 0.08);
      border: 1px solid rgba(99, 102, 241, 0.2);
    }
    .node-icon {
      font-size: 14px;
      width: 16px;
      text-align: center;
    }
    .text-indigo { color: var(--accent-indigo); }
    .text-cyan { color: var(--accent-cyan); }
    .text-purple { color: var(--accent-purple); }
    .text-emerald { color: var(--accent-emerald); }
    .node-name {
      flex: 1;
      font-size: 13px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .search-results-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .search-result-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px;
      cursor: pointer;
      transition: all var(--transition-fast);
    }
    .search-result-card:hover {
      border-color: rgba(255, 255, 255, 0.2);
      transform: translateX(2px);
    }
    .search-result-card.selected {
      border-color: var(--accent-cyan);
      background: rgba(6, 182, 212, 0.06);
    }
    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .result-title {
      font-weight: 600;
      font-size: 13px;
    }
    .result-path {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
      margin: 4px 0;
    }
    .result-footer {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 6px;
      flex-wrap: wrap;
    }
    .capacity-tag {
      font-size: 11px;
      color: var(--text-secondary);
      background: var(--bg-surface-elevated);
      padding: 2px 6px;
      border-radius: var(--radius-sm);
    }
    .scheduler-panel {
      padding: 24px;
      min-height: 500px;
    }
    .empty-scheduler {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      text-align: center;
      padding: 60px 20px;
      color: var(--text-muted);
    }
    .empty-icon-wrap {
      width: 70px;
      height: 70px;
      border-radius: 50%;
      background: rgba(99, 102, 241, 0.1);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 16px;
    }
    .empty-big-icon {
      font-size: 32px;
      color: var(--accent-indigo);
    }
    .host-banner {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding-bottom: 18px;
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 16px;
    }
    .host-pre {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--text-muted);
    }
    .host-name {
      font-size: 22px;
      font-weight: 700;
    }
    .host-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 4px;
    }
    .host-path {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
    }
    .guardrail-alert {
      display: flex;
      align-items: center;
      gap: 12px;
      background: rgba(244, 63, 94, 0.12);
      border: 1px solid rgba(244, 63, 94, 0.3);
      padding: 10px 14px;
      border-radius: var(--radius-md);
      color: #fecdd3;
      font-size: 12px;
    }
    .guardrail-icon {
      font-size: 22px;
      color: var(--accent-rose);
    }
    .date-picker-bar {
      display: flex;
      align-items: flex-end;
      gap: 20px;
      margin-bottom: 24px;
    }
    .tz-display-pill {
      font-size: 13px;
      color: var(--accent-cyan);
      background: rgba(6, 182, 212, 0.08);
      padding: 8px 14px;
      border-radius: var(--radius-md);
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .slots-sub {
      color: var(--text-muted);
      font-size: 13px;
      margin-bottom: 16px;
    }
    .slots-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }
    .slot-tile {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      transition: all var(--transition-fast);
      color: var(--text-primary);
    }
    .slot-tile:hover:not(:disabled) {
      border-color: var(--accent-cyan);
      background: rgba(6, 182, 212, 0.1);
      transform: translateY(-2px);
    }
    .slot-tile.selected {
      border-color: var(--accent-cyan);
      background: var(--accent-cyan);
      color: #04131f;
      font-weight: 600;
    }
    .slot-tile.unavailable {
      opacity: 0.35;
      cursor: not-allowed;
      border-style: dashed;
    }
    .slot-time {
      font-size: 14px;
      font-weight: 600;
    }
    .slot-status {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .booking-checkout-box {
      padding: 18px;
      border-color: var(--accent-cyan);
      background: rgba(6, 182, 212, 0.05);
    }
    .checkout-summary {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .summary-label {
      font-size: 12px;
      color: var(--text-muted);
    }
    .summary-val {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
    }
    .tracker-section {
      padding: 24px;
    }
    .tracker-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .tracker-item {
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .tracker-title {
      font-weight: 600;
      font-size: 14px;
    }
    .tracker-meta {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }
    .lifecycle-pipeline {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pipeline-step {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--text-muted);
    }
    .step-dot {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: var(--bg-surface-elevated);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
    }
    .pipeline-step.done {
      color: var(--accent-emerald);
    }
    .pipeline-step.done .step-dot {
      background: rgba(16, 185, 129, 0.2);
      color: var(--accent-emerald);
    }
    .pipeline-step.active {
      color: var(--accent-amber);
    }
    .pipeline-step.active .step-dot {
      background: rgba(245, 158, 11, 0.2);
      color: var(--accent-amber);
    }
    .pipeline-line {
      width: 30px;
      height: 2px;
      background: var(--border-subtle);
    }
    .pipeline-line.done {
      background: var(--accent-emerald);
    }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 20px;
    }
    .modal-dialog {
      width: 100%;
      max-width: 540px;
      background: var(--bg-secondary);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 24px;
      max-height: 90vh;
      overflow-y: auto;
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
    }
    .close-btn {
      background: transparent;
      border: 0;
      color: var(--text-muted);
      font-size: 18px;
      cursor: pointer;
    }
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 20px;
    }
    .error-banner {
      background: rgba(244, 63, 94, 0.15);
      color: #fb7185;
      padding: 10px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      margin-top: 10px;
    }
    .dynamic-schema-block {
      border-top: 1px solid var(--border-subtle);
      padding-top: 14px;
      margin-top: 14px;
    }
    .schema-heading {
      font-size: 14px;
      margin-bottom: 10px;
      color: var(--accent-cyan);
    }
  `]
})
export class BookerDashboardComponent implements OnInit {
  private nodeService = inject(NodeService);
  private searchService = inject(SearchService);
  private schedulingService = inject(SchedulingService);
  private intentService = inject(IntentService);
  private authService = inject(AuthService);
  private integrationsService = inject(IntegrationsService);

  activeDirectoryTab: 'tree' | 'search' = 'search';
  searchQuery = '';
  detectedTimezone = 'America/New_York';
  targetDate = new Date().toISOString().split('T')[0];

  rootOrgs = signal<NodeItem[]>([]);
  treeData = signal<NodeTreeItem | null>(null);
  searchResults = signal<SearchResultItem[]>([]);

  selectedResource = signal<NodeItem | SearchResultItem | null>(null);
  availableSlots = signal<AvailableSlot[]>([]);
  selectedSlot: AvailableSlot | null = null;

  userIntents = signal<BookingIntent[]>([]);
  intakeSchema: IntakeFormSchema | null = null;

  showBookingModal = false;
  submittingBooking = false;
  bookingError = '';

  bookerForm = {
    name: 'Sarah Lee',
    email: 'sarah.lee@stanford.edu',
    title: 'Advising Session',
    intakeResponses: {} as Record<string, any>,
  };

  ngOnInit(): void {
    this.detectedTimezone = this.schedulingService.detectLocalTimezone();
    this.loadRootOrgs();
    this.onSearchInput();
    this.refreshTracker();
  }

  loadRootOrgs(): void {
    this.nodeService.getRoots().subscribe({
      next: (roots) => {
        this.rootOrgs.set(roots);
        if (roots.length > 0) {
          this.loadTree(roots[0].id);
        }
      },
    });
  }

  loadTree(rootId: string): void {
    this.nodeService.getTree(rootId).subscribe({
      next: (tree) => this.treeData.set(tree),
    });
  }

  onSearchInput(): void {
    this.searchService.searchDirectory(this.searchQuery).subscribe({
      next: (res) => {
        this.searchResults.set(res);
        if (!this.selectedResource() && res.length > 0) {
          this.selectSearchResult(res[0]);
        }
      },
    });
  }

  selectSearchResult(item: SearchResultItem): void {
    this.selectedResource.set(item as any);
    this.selectedSlot = null;
    this.loadIntakeSchema(item.id);
    this.loadAvailableSlots();
  }

  selectNode(node: NodeItem): void {
    if (node.node_type === 'organization') {
      this.loadTree(node.id);
    }
    if (node.node_type === 'resource') {
      this.selectedResource.set(node);
      this.selectedSlot = null;
      this.loadIntakeSchema(node.id);
      this.loadAvailableSlots();
    }
  }

  loadIntakeSchema(nodeId: string): void {
    this.integrationsService.getIntakeSchema(nodeId).subscribe({
      next: (res) => (this.intakeSchema = res),
    });
  }

  loadAvailableSlots(): void {
    const res = this.selectedResource();
    if (!res) return;

    this.schedulingService.getAvailableSlots(res.id, this.targetDate, this.detectedTimezone).subscribe({
      next: (slots) => this.availableSlots.set(slots),
    });
  }

  onTimezoneChange(): void {
    this.loadAvailableSlots();
  }

  selectSlot(slot: AvailableSlot): void {
    this.selectedSlot = slot;
  }

  isTriageRequired(res: any): boolean {
    const tier = res.visibility_settings?.tier || res.visibility_tier;
    return tier === 'HIDDEN' || !!res.visibility_settings?.triage_project_id || !!res.triage_required;
  }

  openBookingModal(): void {
    this.bookingError = '';
    const user = this.authService.currentUser();
    if (user) {
      this.bookerForm.name = user.full_name;
      this.bookerForm.email = user.email;
    }
    this.showBookingModal = true;
  }

  submitBooking(): void {
    const res = this.selectedResource();
    const slot = this.selectedSlot;
    if (!res || !slot) return;

    this.submittingBooking = true;
    this.bookingError = '';

    if (this.isTriageRequired(res)) {
      // Route through indirect screening Intent Pipeline
      this.intentService.submitIntent({
        target_node_id: res.id,
        requested_start_time: slot.slot_start,
        requested_end_time: slot.slot_end,
        booker_name: this.bookerForm.name,
        booker_email: this.bookerForm.email,
        intake_responses: this.bookerForm.intakeResponses,
        intent_note: this.bookerForm.title,
      }).subscribe({
        next: (intent) => {
          this.submittingBooking = false;
          this.showBookingModal = false;
          this.refreshTracker();
          alert(`✓ Booking Intent submitted to screening pipeline. Status: ${intent.status}`);
        },
        error: (err) => {
          this.submittingBooking = false;
          this.bookingError = err.error?.message || 'Failed to submit booking intent.';
        },
      });
    } else {
      // Direct reservation with SELECT FOR UPDATE atomic concurrency lock
      this.schedulingService.bookSlot({
        resource_node_id: res.id,
        start_time: slot.slot_start,
        end_time: slot.slot_end,
        booker_name: this.bookerForm.name,
        booker_email: this.bookerForm.email,
        title: this.bookerForm.title,
      }).subscribe({
        next: () => {
          this.submittingBooking = false;
          this.showBookingModal = false;
          this.loadAvailableSlots();
          this.refreshTracker();
          alert('✓ Appointment confirmed successfully with atomic concurrency lock!');
        },
        error: (err) => {
          this.submittingBooking = false;
          this.bookingError = err.error?.detail || err.error?.message || 'Double-booking conflict or error.';
        },
      });
    }
  }

  confirmEscalated(intent: BookingIntent): void {
    if (!intent.escalation_token) return;
    this.intentService.confirmEscalatedBooking(intent.id, intent.escalation_token).subscribe({
      next: () => {
        alert('✓ Escalated appointment confirmed on executive calendar!');
        this.refreshTracker();
      },
    });
  }

  refreshTracker(): void {
    this.intentService.getTriageQueue().subscribe({
      next: (intents) => this.userIntents.set(intents),
    });
  }

  getNodeIcon(type: string): string {
    if (type === 'organization') return 'fa-solid fa-landmark text-indigo';
    if (type === 'folder') return 'fa-solid fa-folder text-cyan';
    if (type === 'project') return 'fa-solid fa-diagram-project text-purple';
    return 'fa-solid fa-id-badge text-emerald';
  }

  getNodeBadgeClass(type: string): string {
    if (type === 'organization') return 'badge-org';
    if (type === 'folder') return 'badge-folder';
    if (type === 'project') return 'badge-project';
    return 'badge-resource';
  }

  /** Normalises the visibility tier for the currently selected resource,
   *  handling both NodeItem (visibility_settings.tier) and SearchResultItem
   *  (flat visibility_tier) union members. */
  getSelectedTier(): VisibilityTier {
    const res = this.selectedResource();
    if (!res) return 'PUBLIC';
    if ('visibility_settings' in res) return res.visibility_settings.tier;
    return (res as SearchResultItem).visibility_tier;
  }

  getTierBadgeClass(tier?: string): string {
    if (tier === 'PUBLIC') return 'badge-public';
    if (tier === 'RESTRICTED') return 'badge-restricted';
    return 'badge-hidden';
  }

  getIntentBadgeClass(status: string): string {
    if (status === 'APPROVED') return 'badge-public';
    if (status === 'PENDING_REVIEW') return 'badge-restricted';
    return 'badge-hidden';
  }
}
