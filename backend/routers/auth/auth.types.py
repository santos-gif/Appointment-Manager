from pydantic import BaseModel


class LoginCredentials(BaseModel):
	email:str
	password:str


