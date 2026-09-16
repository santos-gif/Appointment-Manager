import { Component } from '@angular/core';
import { AuthContainer } from '../../components/auth-container/auth-container';

@Component({
	imports: [AuthContainer],
	selector: 'app-auth-page',
	styleUrl: './auth-page.css',
	templateUrl: './auth-page.html',
})
export class AuthPage {}
