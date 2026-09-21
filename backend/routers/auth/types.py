from pydantic import BaseModel

class LoginCredentials(BaseModel):
	email:str
	password:str

class UserFrontend(BaseModel): pass
