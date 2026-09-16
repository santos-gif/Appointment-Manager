from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()
class Configs(BaseSettings):
	jwt_secret_key: str = ""
	database_url:str = ""
	algorithm: str = "HS256"
	access_token_expire_minutes: int = 30
	refresh_token_expire_days: int = 2

configs = Configs()
