export type NodeType = 'organization' | 'folder' | 'project' | 'resource';
export type VisibilityTier = 'PUBLIC' | 'RESTRICTED' | 'HIDDEN';
export type IntentStatus = 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'RESCHEDULED' | 'COMPLETED';

export interface VisibilitySettings {
  tier: VisibilityTier;
  allowed_roles?: string[];
  inherit?: boolean;
  triage_project_id?: string | null;
}

export interface NodeItem {
  id: string;
  tenant_id: string;
  node_type: NodeType;
  parent_id?: string | null;
  path: string;
  name: string;
  slug: string;
  description?: string | null;
  metadata_json: Record<string, any>;
  visibility_settings: VisibilitySettings;
  created_at: string;
  updated_at: string;
}

export interface NodeTreeItem extends NodeItem {
  children?: NodeTreeItem[];
  expanded?: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  is_superuser: boolean;
}

export interface ResourceCapacity {
  node_id: string;
  tenant_id: string;
  name: string;
  path: string;
  capacity_title: string;
  tier: VisibilityTier;
}

export interface AvailabilityRule {
  id?: string;
  node_id?: string;
  day_of_week?: number | null;
  specific_date?: string | null;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  buffer_minutes: number;
  is_active: boolean;
}

export interface AvailableSlot {
  slot_start: string;
  slot_end: string;
  formatted_start: string;
  formatted_end: string;
  timezone: string;
  is_available: boolean;
}

export interface BookingIntent {
  id: string;
  tenant_id: string;
  target_node_id: string;
  triage_project_id?: string | null;
  escalated_node_id?: string | null;
  booker_name: string;
  booker_email: string;
  requested_start_time: string;
  requested_end_time: string;
  status: IntentStatus;
  intake_responses: Record<string, any>;
  triage_notes?: string | null;
  escalation_token?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Appointment {
  id: string;
  tenant_id: string;
  resource_node_id: string;
  booker_name: string;
  booker_email: string;
  title: string;
  notes?: string | null;
  start_time: string;
  end_time: string;
  status: 'CONFIRMED' | 'CANCELLED' | 'COMPLETED';
  payment_status: string;
  payment_amount_cents: number;
  created_at: string;
}

export interface CalendarIntegration {
  id: string;
  resource_node_id: string;
  provider: 'google' | 'outlook';
  account_email: string;
  sync_active: boolean;
  last_synced_at?: string | null;
  sync_status_message: string;
}

export interface PaymentEscrowConfig {
  id?: string;
  node_id: string;
  provider: 'stripe' | 'paypal';
  is_enabled: boolean;
  amount_cents: number;
  currency: string;
  escrow_policy: string;
  account_connected_id?: string | null;
}

export interface IntakeField {
  id: string;
  type: 'text' | 'textarea' | 'select' | 'number' | 'checkbox';
  label: string;
  placeholder?: string;
  required: boolean;
  options?: string[];
}

export interface IntakeFormSchema {
  id?: string;
  node_id: string;
  title: string;
  description?: string | null;
  fields_json: IntakeField[];
}

export interface SearchResultItem {
  id: string;
  tenant_id: string;
  node_type: NodeType;
  name: string;
  slug: string;
  path: string;
  description?: string;
  metadata_json: Record<string, any>;
  visibility_tier: VisibilityTier;
  capacity_title?: string;
  direct_booking_allowed: boolean;
  triage_required: boolean;
}
