import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL","postgresql+asyncpg://postgres:toor@localhost:5432/auth")

engine = create_async_engine(DATABASE_URL, echo=False, future=True, poolclass=NullPool)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, future=True,)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()