import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { map } from 'rxjs';


const convertKeysToSnake = (obj: any): any => {
	if (obj === null || typeof obj !== 'object' || obj instanceof Date)
		return obj;
	if (Array.isArray(obj))
		return obj.map(convertKeysToSnake);

	return Object.keys(obj).reduce((acc, key) => {
		const snakeKey = toSnakeCase(key);
		acc[snakeKey] = convertKeysToSnake(obj[key]);
		return acc;
	}, {} as any);
};

// 4. Incoming: Recursively turns a plain object into camelCase
const convertKeysToCamel = (obj: any): any => {
	if (obj === null || typeof obj !== 'object' || obj instanceof Date)
		return obj;
	if (Array.isArray(obj))
		return obj.map(convertKeysToCamel);

	return Object.keys(obj).reduce((acc, key) => {
		const camelKey = toCamelCase(key);
		acc[camelKey] = convertKeysToCamel(obj[key]);
		return acc;
	}, {} as any);
};

export const caseConverterInterceptor: HttpInterceptorFn = (req, next) => {
	let modifiedReq = req

	if (req.body && typeof req.body === 'object' && !Array.isArray(req.body)) {
		modifiedReq = req.clone({body: convertKeysToSnake(req.body)})
	}

	return next(modifiedReq).pipe(
		map(event => {
			if (event instanceof HttpResponse && event.body) {
				return event.clone({body:convertKeysToCamel(event.body)})
			}
			return event
		})
	);
};
