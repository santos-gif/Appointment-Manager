import { Component, model } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';

@Component({
	imports: [ReactiveFormsModule],
	selector: 'app-register-form',
	styleUrl: './register-form.css',
	templateUrl: './register-form.html',
})
export class RegisterForm {
	isRegisterSection = model<boolean>(false)
	registerForm = new FormGroup({
		email:new FormControl(''),
		username:new FormControl(''),
		name: new FormControl(''),
		password:new FormControl(''),
		confirmPassword: new FormControl('')
	})

	submitRegister() {}
	gotoLoginForm() {
		this.isRegisterSection.set(false)
	}
}
