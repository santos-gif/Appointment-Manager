import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase): pass





class Database:
	def __init__(self, db_url: str | None) -> None:
		if not db_url:
			raise RuntimeError("Database URL is null")
		self.engine = create_async_engine(db_url, echo=True)
		self.async_session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

	async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
		async with self.async_session_factory() as session:
			yield session

	async def close(self):
		await self.engine.dispose()

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
db_instance = Database(DATABASE_URL)
