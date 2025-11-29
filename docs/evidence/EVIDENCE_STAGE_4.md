# Evidence: Stage 2 - Python Backend Development


## 1. Feature Implementation / Calculation

**File**: `./api/products/database/connection.py`
### MongoDB Asynchronous Connection.
```python
class MongoDBConnection:
    def __init__(self):
        self.client = None
        self.db = None
        self.logger = logger.getChild("MongoDBConnection")
        
    async def connect(self, connection_string: str = None, db_name: str = None):
        try:
            connection_string = connection_string or os.getenv(
                "MONGODB_URI", "mongodb://mongodb:27017/"
            )
            db_name = db_name or os.getenv("MONGODB_DB_NAME", "product_db")
            
            self.logger.info(f"Connecting to MongoDB: {db_name}")
            self.logger.debug(f"Connection string: {self._mask_connection_string(connection_string)}")
            
            self.client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
            self.db = self.client[db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            self.logger.info("Successfully connected to MongoDB")
            
            await self._setup_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self.logger.error(f"MongoDB connection failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during MongoDB connection: {e}")
            raise
    ### rest of the class.

db_connection = MongoDBConnection()

async def get_db():
    if db_connection.db is None:
        await db_connection.connect()
    return db_connection.db

async def get_products_collection():
    db = await get_db()
    collection = db[ProductDB.COLLECTION_NAME]
    logger.debug("Products collection retrieved")
    return collection
```

### Postgres Asynchronous Connection.
**File**: `./api/orders/database/connection.py`

```python
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
                "postgresql+asyncpg://user:password@localhost:5432/orders_db"
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

    ### rest of the class.

db_connection = PostgreSQLConnection()

async def get_db():
    if not db_connection.async_session_local:
        await db_connection.connect()
    return await db_connection.get_session()

async def init_db():
    if not db_connection.engine:
        await db_connection.connect()
    await db_connection.create_tables()
```

### Neat and isolated data access layer:
**File**: `./api/auth/repository/user_repository.py`

```python
class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(UserModel, db_session)
        self.logger = logger

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        result = await self.db_session.execute(
            select(UserModel).where(UserModel.email.ilike(email))
        )
        return result.scalar_one_or_none()

    async def get_active_user_by_email(self, email: str) -> Optional[UserModel]:
        result = await self.db_session.execute(
            select(UserModel).where(
                and_(
                    UserModel.email.ilike(email),
                    UserModel.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        user = await self.get_by_email(email)
        return user is not None

    async def create_user(self, user_data: UserCreate) -> Optional[UserModel]:
        ...

    async def update_last_login(self, user_id: uuid.UUID) -> bool:
        ...

    async def update_password(self, user_id: uuid.UUID, new_password_hash: str) -> bool:
        ...

    async def activate_user(self, user_id: uuid.UUID) -> bool:
        ...

    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        ...

    async def update_profile(self, user_id: uuid.UUID, profile_data: ProfileUpdateRequest) -> Optional[UserModel]:
        update_data = profile_data.model_dump(exclude_unset=True)
        return await self.update(user_id, update_data)

    async def search_users(self, query: str, skip: int = 0, limit: int = 50) -> List[UserModel]:
        ...

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        ...

    async def get_users_created_after(self, date: datetime) -> List[UserModel]:
        ...
```
---

## 2. Clear and Easy to Understand Error Handling Decorators

**File**: `./api/auth/decorators/auth_service_decorators.py`
```python
def handle_database_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            self = args[0]
            request = next((arg for arg in args if hasattr(arg, 'url')), None)
            
            self.logger.error(f"Database integrity error in {func.__name__}: {e}")
            return create_problem_response(
                status_code=409,
                error_type="conflict",
                title="Conflict",
                detail="Resource conflict occurred",
                instance=str(request.url) if request else ""
            )
        except SQLAlchemyError as e:
            self = args[0]
            request = next((arg for arg in args if hasattr(arg, 'url')), None)
            
            self.logger.error(f"Database error in {func.__name__}: {e}")
            return create_problem_response(
                status_code=500,
                error_type="internal_error",
                title="Internal Server Error",
                detail="Database operation failed",
                instance=str(request.url) if request else ""
            )
    return wrapper
```


---

## 3. Faster reading using indexes.

in small databases, it is actually worse, but after generating dummy data to increase our database size, we can see that using indexes actually help us read much more faster.

```bash
tests/test_products_repository.py::test_index_effectiveness Without index: 0.0270s, With index: 0.0230s, Improvement: 14.7%
PASSED
```

## 4. Key Improvements / Notes

* **Clean Architecture / Modularization**: data access layer in between database and service layer.
* **Database Safe Migrations**: using alembic to safely move migrations up/down.
---
