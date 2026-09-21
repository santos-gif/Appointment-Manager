import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Appointment, AvailabilityRule, AvailableSlot } from '../models';

@Injectable({
  providedIn: 'root',
})
export class SchedulingService {
  private http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  /**
   * Global Time-Zone Engine: Automatically detects client system timezone.
   */
  detectLocalTimezone(): string {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    } catch {
      return 'UTC';
    }
  }

  getAvailableSlots(nodeId: string, targetDate: string, timezone?: string): Observable<AvailableSlot[]> {
    const tz = timezone || this.detectLocalTimezone();
    return this.http.get<AvailableSlot[]>(
      `${this.baseUrl}/availability/${nodeId}/slots?target_date=${targetDate}&timezone=${encodeURIComponent(tz)}`,
      { withCredentials: true }
    );
  }

  getAvailabilityMatrix(nodeId: string): Observable<{ node_id: string; rules: AvailabilityRule[] }> {
    return this.http.get<{ node_id: string; rules: AvailabilityRule[] }>(
      `${this.baseUrl}/availability/${nodeId}`,
      { withCredentials: true }
    );
  }

  updateAvailabilityMatrix(nodeId: string, rules: AvailabilityRule[]): Observable<{ node_id: string; rules: AvailabilityRule[] }> {
    return this.http.put<{ node_id: string; rules: AvailabilityRule[] }>(
      `${this.baseUrl}/availability/${nodeId}`,
      rules,
      { withCredentials: true }
    );
  }

  bookSlot(payload: {
    resource_node_id: string;
    start_time: string;
    end_time: string;
    booker_name: string;
    booker_email: string;
    title?: string;
    notes?: string;
    escalation_token?: string;
  }): Observable<Appointment> {
    return this.http.post<Appointment>(
      `${this.baseUrl}/booking/book`,
      payload,
      { withCredentials: true }
    );
  }

  getMyAppointments(): Observable<Appointment[]> {
    return this.http.get<Appointment[]>(
      `${this.baseUrl}/booking/appointments/my`,
      { withCredentials: true }
    );
  }
}
