import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SearchResultItem } from '../models';

@Injectable({
  providedIn: 'root',
})
export class SearchService {
  private http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000/api/v1/search';

  searchDirectory(query?: string, nodeType?: string, tenantId?: string): Observable<SearchResultItem[]> {
    let params: string[] = [];
    if (query) params.push(`query=${encodeURIComponent(query)}`);
    if (nodeType) params.push(`node_type=${encodeURIComponent(nodeType)}`);
    if (tenantId) params.push(`tenant_id=${encodeURIComponent(tenantId)}`);

    const queryString = params.length > 0 ? `?${params.join('&')}` : '';
    return this.http.get<SearchResultItem[]>(`${this.baseUrl}/discovery${queryString}`, { withCredentials: true });
  }
}
