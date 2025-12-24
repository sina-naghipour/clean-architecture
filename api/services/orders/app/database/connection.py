import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, event
from sqlalchemy.pool import QueuePool
import asyncpg

Base = declarative_base()

class PostgreSQLConnection:
    def __init__(self, logger: logging.Logger = None):
        self.engine = None
        self.async_session_local = None
        self.Base = Base
        self.logger = logger or logging.getLogger(__name__).getChild("PostgreSQLConnection")
        self._pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self._max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self._pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self._pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        self._pool_pre_ping = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
        
    async def connect(self, connection_string: str = None):
        try:
            connection_string = connection_string or os.getenv(
                "DATABASE_URL", 
                "postgresql+asyncpg://user:password@localhost:5432/orders_db"
            )
            
            self.logger.info("Connecting to PostgreSQL database")
            
            self.engine = create_async_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_timeout=self._pool_timeout,
                pool_recycle=self._pool_recycle,
                pool_pre_ping=self._pool_pre_ping,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
                connect_args={
                    "server_settings": {
                        "application_name": "orders_service",
                        "jit": "off",
                    },
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 500,
                }
            )
            
            @event.listens_for(self.engine.sync_engine, "connect")
            def connect(dbapi_connection, connection_record):
                self.logger.debug("New database connection created")
                
            @event.listens_for(self.engine.sync_engine, "checkout")
            def checkout(dbapi_connection, connection_record, connection_proxy):
                self.logger.debug("Connection checked out from pool")
                
            @event.listens_for(self.engine.sync_engine, "checkin")
            def checkin(dbapi_connection, connection_record):
                self.logger.debug("Connection checked in to pool")
            
            self.async_session_local = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            
            await self._test_connection()
            await self._check_pool_status()
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
                await conn.execute(text("SET statement_timeout = 30000"))
                await conn.execute(text("SET lock_timeout = 10000"))
        except SQLAlchemyError as e:
            self.logger.error(f"Database connection test failed: {e}")
            raise

    async def _check_pool_status(self):
        try:
            pool = self.engine.pool
            if pool:
                self.logger.info(f"Pool status: {pool.status()}")
        except Exception as e:
            self.logger.warning(f"Could not check pool status: {e}")

    async def get_session(self):
        if not self.async_session_local:
            self.logger.error("Attempted to get session without active database connection")
            raise Exception("Database not connected. Call connect() first.")
        
        self.logger.debug("Creating new async database session")
        return self.async_session_local()

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self.logger.info("PostgreSQL connection pool closed")
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
    
    async def get_pool_stats(self) -> dict:
        if not self.engine:
            return {"error": "Engine not initialized"}
        
        pool = self.engine.pool
        if not pool:
            return {"error": "Pool not available"}
        
        return {
            "size": pool.size() if hasattr(pool, 'size') else None,
            "checkedout": pool.checkedout() if hasattr(pool, 'checkedout') else None,
            "overflow": pool.overflow() if hasattr(pool, 'overflow') else None,
            "checkedin": pool.checkedin() if hasattr(pool, 'checkedin') else None,
            "status": pool.status() if hasattr(pool, 'status') else None,
        }

db_connection = PostgreSQLConnection()

@asynccontextmanager
async def get_db():
    session = None
    try:
        if not db_connection.async_session_local:
            await db_connection.connect()
        
        session = await db_connection.get_session()
        yield session
        await session.commit()
    except Exception as e:
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()

async def init_db():
    if not db_connection.engine:
        await db_connection.connect()
    await db_connection.create_tables()

async def health_check_db() -> dict:
    try:
        async with db_connection.engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                pool_stats = await db_connection.get_pool_stats()
                return {
                    "status": "healthy",
                    "pool_stats": pool_stats
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
    return {"status": "unhealthy"}