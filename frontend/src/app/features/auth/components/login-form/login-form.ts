import { Component, model } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';

@Component({
	imports: [ReactiveFormsModule],
	selector: 'app-login-form',
	styleUrl: './login-form.css',
	templateUrl: './login-form.html',
})
export class LoginForm {
	isRegisterSection = model<boolean>(false)
	loginForm = new FormGroup({
		email: new FormControl(''),
		password: new FormControl('')
	})
	submitLogin() {}
	gotoRegisterForm() {
		this.isRegisterSection.set(true)
	}
}
