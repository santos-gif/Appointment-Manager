import { TestBed } from '@angular/core/testing';
import { HttpInterceptorFn } from '@angular/common/http';
import { caseConverterInterceptor } from './case-converter-interceptor';

describe('caseConverterInterceptor', () => {
	const interceptor: HttpInterceptorFn = (req, next) =>
		TestBed.runInInjectionContext(() => caseConverterInterceptor(req, next));

	beforeEach(() => {
		TestBed.configureTestingModule({});
	});

	it('should be created', () => {
		expect(interceptor).toBeTruthy();
	});
});
