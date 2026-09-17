from fastapi import HTTPException



class InvalidCredentialsException(HTTPException):
    def __init__(self, detail: str = "Incorrect email or password"):
        super().__init__(
            status_code=401,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class AccountDisabledException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=403,
            detail="Your account has been deactivated."
        )
