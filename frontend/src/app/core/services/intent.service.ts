import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Appointment, BookingIntent, IntentStatus } from '../models';

@Injectable({
  providedIn: 'root',
})
export class IntentService {
  private http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000/api/v1/booking';

  submitIntent(payload: {
    target_node_id: string;
    requested_start_time: string;
    requested_end_time: string;
    booker_name: string;
    booker_email: string;
    intake_responses: Record<string, any>;
    intent_note?: string;
  }): Observable<BookingIntent> {
    return this.http.post<BookingIntent>(`${this.baseUrl}/intent/submit`, payload, { withCredentials: true });
  }

  getTriageQueue(statusFilter?: IntentStatus): Observable<BookingIntent[]> {
    const url = statusFilter ? `${this.baseUrl}/intent/queue?status_filter=${statusFilter}` : `${this.baseUrl}/intent/queue`;
    return this.http.get<BookingIntent[]>(url, { withCredentials: true });
  }

  executeTriageAction(intentId: string, payload: {
    action: 'approve_and_escalate' | 'reject' | 'reschedule';
    reviewer_notes?: string;
    escalate_to_node_id?: string;
  }): Observable<BookingIntent> {
    return this.http.post<BookingIntent>(`${this.baseUrl}/intent/${intentId}/triage`, payload, { withCredentials: true });
  }

  confirmEscalatedBooking(intentId: string, escalationToken: string): Observable<Appointment> {
    return this.http.post<Appointment>(
      `${this.baseUrl}/intent/${intentId}/confirm?escalation_token=${encodeURIComponent(escalationToken)}`,
      {},
      { withCredentials: true }
    );
  }
}
