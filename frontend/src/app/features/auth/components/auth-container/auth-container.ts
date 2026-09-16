import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { LoginForm } from '../login-form/login-form';
import { RegisterForm } from '../register-form/register-form';

@Component({
	imports: [CommonModule, LoginForm, RegisterForm],
	selector: 'app-auth-container',
	styleUrl: './auth-container.css',
	templateUrl: './auth-container.html',
})
export class AuthContainer {
	isRegisterSection = signal<boolean>(false)
}
