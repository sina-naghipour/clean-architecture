now the issue is that we have a working backend, but how do we store data and how do we track user activities to fill in the gap of `stateless HTTP`.

this is how each and every request is being processed.

```text
HTTP Request
    -> Routes (URL decoding, auth)
    -> Pydantic (Validation)
    -> Services (Business Logic)
```

```text
HTTP Response
    -> Services (Response based off static behavior)
    -> Pydantic (Serialization)
    -> Routes (HTTP Response)
```

the issue with this structure is the `static behavior`.

we have only one `scheme` of response for any user that sends variable requests.

how do we convert `static behavior` into `dynamic behavior` is : adding `DATABASE`.

so for now, these layers do work, they are tested so each of them are valid, but we should inject a DATABASE layer into our system.

```text
HTTP Request
    -> Routes (URL decoding, auth)
    -> Pydantic (Validation)
    -> Services (Business Logic)
    -> Repository (Data Access)
    -> SQLAlchemy (ORM)
    -> Database (Persistence)
```

```text
HTTP Response
    -> SQLAchemy (object mapping)
    -> Repositories (Data Assembly)
    -> Services (Enrichment)
    -> Pydantic (Serialization)
    -> Routes (HTTP Response)
```

so the first step of injecting these layers, is building the database itself, but `Database` should follow the semantic of our `Pydantic` data definition.

```python
from connection import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserModel(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
```

but to track and add a safety layer to our database we should use alembic.

we add our `Base` in env.py of alembic.

```python
from database.connection import Base
target_metadata = Base.metadata
```

in `alembic.ini`:
```text
sqlalchemy.url = postgresql://postgres:toor@localhost:5432/auth
```

now we have a database with `users` table in it, and alembic watching every database strcutural change and saving it as a history tree.

now we want to be able to do `CRUD` on this database, in layer view, `Repository (Data Access)`.

now that we created this Repository of users where we can access data through it, we need to change our `AuthService` so that instead of static behavior, work with this `Repository` and do `dynamic` interaction with it based on user's request.


important to note that we should separate error handling logic from our business logic.

