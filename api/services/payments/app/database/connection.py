import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

Base = declarative_base()

class PostgreSQLConnection:
    def __init__(self, logger: logging.Logger = None):
        self.engine = None
        self.async_session_local = None
        self.Base = Base
        self.logger = logger or logging.getLogger(__name__).getChild("PostgreSQLConnection")
        
    async def connect(self, connection_string: str = None):
        try:
            connection_string = connection_string or os.getenv(
                "DATABASE_URL", 
                "postgresql+asyncpg://user:password@localhost:5432/payments_db"
            )
            
            self.logger.info("Connecting to PostgreSQL database")
            self.logger.debug(f"Connection string: {self._mask_connection_string(connection_string)}")
            
            self.engine = create_async_engine(
                connection_string, 
                pool_pre_ping=True,
                echo=False
            )
            
            self.async_session_local = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            await self._test_connection()
            self.logger.info("Successfully connected to PostgreSQL database")
            
        except SQLAlchemyError as e:
            self.logger.error(f"PostgreSQL connection failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during PostgreSQL connection: {e}")
            raise

    def _mask_connection_string(self, connection_string: str) -> str:
        if "@" in connection_string:
            parts = connection_string.split("@")
            if len(parts) == 2:
                user_pass = parts[0]
                if "://" in user_pass:
                    protocol, credentials = user_pass.split("://", 1)
                    if ":" in credentials:
                        user, _ = credentials.split(":", 1)
                        return f"{protocol}://{user}:****@{parts[1]}"
        return connection_string

    async def _test_connection(self):
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except SQLAlchemyError as e:
            self.logger.error(f"Database connection test failed: {e}")
            raise

    async def get_session(self):
        if not self.async_session_local:
            self.logger.error("Attempted to get session without active database connection")
            raise Exception("Database not connected. Call connect() first.")
        
        self.logger.debug("Creating new async database session")
        return self.async_session_local()

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self.logger.info("PostgreSQL connection closed")
        else:
            self.logger.debug("No active PostgreSQL connection to close")

    async def create_tables(self):
        if not self.engine:
            self.logger.error("Attempted to create tables without active database connection")
            raise Exception("Database not connected. Call connect() first.")
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(self.Base.metadata.create_all)
            self.logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            self.logger.error(f"Table creation failed: {e}")
            raise

db_connection = PostgreSQLConnection()

async def get_db():
    if not db_connection.async_session_local:
        await db_connection.connect()
    
    session = await db_connection.get_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def init_db():
    if not db_connection.engine:
        await db_connection.connect()
    await db_connection.create_tables()