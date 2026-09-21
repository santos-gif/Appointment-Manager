import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { NodeItem, NodeTreeItem } from '../models';

@Injectable({
  providedIn: 'root',
})
export class NodeService {
  private http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000/api/v1/nodes';

  getRoots(): Observable<NodeItem[]> {
    return this.http.get<NodeItem[]>(`${this.baseUrl}/roots`, { withCredentials: true });
  }

  getTree(rootId: string): Observable<NodeTreeItem> {
    return this.http.get<NodeTreeItem>(`${this.baseUrl}/tree/${rootId}`, { withCredentials: true });
  }

  getNode(nodeId: string): Observable<NodeItem> {
    return this.http.get<NodeItem>(`${this.baseUrl}/${nodeId}`, { withCredentials: true });
  }
}
