import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { ResourceCapacity, User } from '../models';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000/api/v1/auth';

  // Angular Signals for Reactive State
  readonly currentUser = signal<User | null>(null);
  readonly activeCapacities = signal<ResourceCapacity[]>([]);
  readonly activeContextNode = signal<ResourceCapacity | null>(null);

  readonly isAuthenticated = computed(() => this.currentUser() !== null);
  readonly isSuperuser = computed(() => this.currentUser()?.is_superuser ?? false);
  readonly userRoles = computed(() => this.currentUser()?.roles ?? []);

  constructor() {
    this.checkInitialSession();
  }

  checkInitialSession(): void {
    this.http.get<{ user: User; active_capacities: ResourceCapacity[] }>(`${this.baseUrl}/me`, { withCredentials: true })
      .subscribe({
        next: (res) => {
          this.currentUser.set(res.user);
          this.activeCapacities.set(res.active_capacities);
          if (res.active_capacities.length > 0 && !this.activeContextNode()) {
            this.activeContextNode.set(res.active_capacities[0]);
          }
        },
        error: () => {
          // Unauthenticated or cookies expired
          this.currentUser.set(null);
          this.activeCapacities.set([]);
        },
      });
  }

  login(email: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/login`, { email, password }, { withCredentials: true })
      .pipe(
        tap((res) => {
          this.currentUser.set(res.user);
          this.fetchMe();
        })
      );
  }

  mockSSO(preset: 'stanford_faculty' | 'acme_executive' | 'student'): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/mock-sso?preset=${preset}`, {}, { withCredentials: true })
      .pipe(
        tap((res) => {
          this.currentUser.set(res.user);
          this.fetchMe();
        })
      );
  }

  fetchMe(): void {
    this.http.get<{ user: User; active_capacities: ResourceCapacity[] }>(`${this.baseUrl}/me`, { withCredentials: true })
      .subscribe({
        next: (res) => {
          this.currentUser.set(res.user);
          this.activeCapacities.set(res.active_capacities);
          if (res.active_capacities.length > 0) {
            this.activeContextNode.set(res.active_capacities[0]);
          }
        },
      });
  }

  logout(): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/logout`, {}, { withCredentials: true })
      .pipe(
        tap(() => {
          this.currentUser.set(null);
          this.activeCapacities.set([]);
          this.activeContextNode.set(null);
        })
      );
  }

  setActiveContext(capacity: ResourceCapacity): void {
    this.activeContextNode.set(capacity);
  }
}
