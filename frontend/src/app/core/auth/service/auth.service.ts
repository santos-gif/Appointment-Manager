import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { environment } from '../../../../environments/environment';
import type { LoginCredentials } from '../interface/auth.interface';
import { Observable } from 'rxjs';


@Service()
export class AuthService {
	private http = inject(HttpClient)
	private apiUrl = environment.apiUrl;

	login(credentials: LoginCredentials):Observable<any> { // Should change the observable to be Observable<LoginResponse> type
		return this.http.post(`${this.apiUrl}/api/auth/login`, credentials)
	}
}
