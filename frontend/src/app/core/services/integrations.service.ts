import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CalendarIntegration, IntakeFormSchema, PaymentEscrowConfig } from '../models';

@Injectable({
  providedIn: 'root',
})
export class IntegrationsService {
  private http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000/api/v1/integrations';

  getCalendarSync(resourceNodeId: string): Observable<CalendarIntegration[]> {
    return this.http.get<CalendarIntegration[]>(`${this.baseUrl}/calendar/${resourceNodeId}`, { withCredentials: true });
  }

  connectCalendar(resourceNodeId: string, provider: 'google' | 'outlook'): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/calendar/${resourceNodeId}/connect?provider=${provider}`, {}, { withCredentials: true });
  }

  getEscrowConfig(nodeId: string): Observable<PaymentEscrowConfig> {
    return this.http.get<PaymentEscrowConfig>(`${this.baseUrl}/escrow/${nodeId}`, { withCredentials: true });
  }

  updateEscrowConfig(nodeId: string, payload: PaymentEscrowConfig): Observable<PaymentEscrowConfig> {
    return this.http.put<PaymentEscrowConfig>(`${this.baseUrl}/escrow/${nodeId}`, payload, { withCredentials: true });
  }

  getIntakeSchema(nodeId: string): Observable<IntakeFormSchema> {
    return this.http.get<IntakeFormSchema>(`${this.baseUrl}/intake-schema/${nodeId}`, { withCredentials: true });
  }

  saveIntakeSchema(nodeId: string, payload: IntakeFormSchema): Observable<IntakeFormSchema> {
    return this.http.put<IntakeFormSchema>(`${this.baseUrl}/intake-schema/${nodeId}`, payload, { withCredentials: true });
  }
}
