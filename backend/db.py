import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase



load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
	def __init__(self) -> None:
		if not DATABASE_URL:
			raise RuntimeError("Database URL is null")
		self.engine = create_async_engine(DATABASE_URL, echo=True)
		self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase): pass
