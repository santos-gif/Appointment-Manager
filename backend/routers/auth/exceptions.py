from fastapi import HTTPException



class InvalidCredentialsException(HTTPException):
	def __init__(self, detail: str = "Incorrect email or password"):
		super().__init__(
		status_code=401,
		detail=detail
		)

class AccountDisabledException(HTTPException): #For banned cases
	def __init__(self):
		super().__init__(
		status_code=403,
		detail="Your account has been deactivated."
		)

class UserNotFoundException(HTTPException):
	def __init__(self, detail: str = "User not found") -> None:
		super().__init__(
			status_code=404,
			detail=detail
		)
