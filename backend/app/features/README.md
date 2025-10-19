# Features Directory - Domain-Driven Architecture

This directory contains all application features organized by domain using the **Repository → Service → Router** pattern.

## Feature Structure Pattern

Each feature follows this standard structure:

```
features/
└── feature_name/
    ├── __init__.py          # Feature module exports
    ├── models.py            # SQLAlchemy ORM models
    ├── schemas.py           # Pydantic request/response DTOs
    ├── repository.py        # Data access layer (extends BaseRepository[T])
    ├── service.py           # Business logic layer
    ├── router.py            # FastAPI endpoints (uses service via DI)
    └── test_service.py      # Unit tests for service logic
```

## Architecture Layers

### 1. Models Layer (`models.py`)
- SQLAlchemy ORM models
- Database table definitions
- Relationships and constraints

**Example:**
```python
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
```

### 2. Schemas Layer (`schemas.py`)
- Pydantic models for request/response validation
- Data Transfer Objects (DTOs)
- Input validation and serialization

**Example:**
```python
from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
```

### 3. Repository Layer (`repository.py`)
- Extends `BaseRepository[T]` from `app.core.repository`
- Handles all database operations (CRUD)
- Domain-specific queries

**Example:**
```python
from app.core.repository import BaseRepository
from .models import User

class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> User | None:
        stmt = select(self.model).where(self.model.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()
```

### 4. Service Layer (`service.py`)
- Contains business logic
- Orchestrates repository operations
- Handles domain rules and validation
- **Generally uses repository** - but direct DB access is acceptable for simple cases (see below)

**Example (with repository - recommended for most features):**
```python
from .repository import UserRepository
from .schemas import UserResponse

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user_by_email(self, email: str) -> UserResponse | None:
        user = await self.repository.get_by_email(email)
        if not user:
            return None
        return UserResponse.model_validate(user)
```

**Example (direct DB access - for simple services):**
```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class HealthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_database(self) -> bool:
        await self.db.execute(text("SELECT 1"))
        return True
```

#### When to Use Repository vs Direct DB Access

**Use Repository Pattern when:**
- ✅ Performing CRUD operations on domain entities
- ✅ Need complex queries (filtering, sorting, pagination, joins)
- ✅ Multiple related database operations
- ✅ Query logic needs to be reused across services
- ✅ Need testing isolation (mock repository instead of DB)

**Use Direct DB Access when:**
- ✅ Simple diagnostic/health check queries (`SELECT 1`)
- ✅ One-off utility operations
- ✅ No domain entity involved
- ✅ Query is trivial and won't be reused

**Examples:**
- Repository: `TodoService` - CRUD on todos with filtering/sorting
- Direct DB: `HealthService` - simple `SELECT 1` for connectivity check

### 5. Router Layer (`router.py`)
- FastAPI route definitions
- Request/response handling
- **NO business logic** - delegates to service
- Uses dependency injection for service

**Example (with repository - most features):**
```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from .repository import UserRepository
from .service import UserService
from .schemas import UserResponse

router = APIRouter()

def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """Dependency injection for UserService.

    Pattern: Create repository, then inject into service.
    """
    repository = UserRepository(db)
    return UserService(repository)

@router.get("/users/{email}", response_model=UserResponse)
async def get_user(
    email: str,
    service: Annotated[UserService, Depends(get_user_service)],
):
    user = await service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Example (direct DB - simple services):**
```python
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from .service import HealthService

router = APIRouter()

def get_health_service(db: Annotated[AsyncSession, Depends(get_db)]) -> HealthService:
    """Dependency injection for HealthService.

    Pattern: Pass DB directly for simple services without repositories.
    """
    return HealthService(db)

@router.get("/health")
async def health_check(
    service: Annotated[HealthService, Depends(get_health_service)],
):
    return await service.check_basic_health()
```

#### Service Factory Pattern

Service factory functions (`get_*_service`) should:
- ✅ Take `db: Annotated[AsyncSession, Depends(get_db)]` as parameter
- ✅ Create repository if needed: `repository = TodoRepository(db)`
- ✅ Return service instance with dependencies injected
- ✅ Include docstring explaining the dependency pattern used

**Pattern:** Simple services get DB directly; complex ones get repositories.

## Existing Features

### Health (`health/`)
Health check endpoints for monitoring application and database status.
- Basic liveness check
- Database connectivity check
- Used by load balancers and orchestration systems

### Auth (`auth/`)
Authentication and user management (prepared for Epic 2).
- User model and schemas
- User repository for data access
- Placeholder service and router for future auth implementation

## Adding a New Feature

To add a new feature, follow these steps:

1. **Create feature directory:**
   ```bash
   mkdir -p app/features/your_feature
   ```

2. **Create `__init__.py`:**
   ```python
   """Brief description of your feature."""
   ```

3. **Create models, schemas, repository, service, router** following the pattern above

4. **Register router in `app/api/v1/router.py`:**
   ```python
   from app.features.your_feature.router import router as your_feature_router

   api_router.include_router(
       your_feature_router,
       prefix="/your-feature",
       tags=["your-feature"]
   )
   ```

5. **Write tests:**
   - Unit tests: `app/features/your_feature/test_service.py`
   - Integration tests: `tests/integration/test_your_feature.py`

## Benefits of This Architecture

✅ **Clear Separation of Concerns**: Each layer has a single responsibility
✅ **Testability**: Service layer can be unit tested without database
✅ **Maintainability**: All feature code is co-located in one directory
✅ **Scalability**: Easy to add new features without affecting existing ones
✅ **Type Safety**: Full type hints throughout with Python 3.12+ generics
✅ **DRY Principle**: `BaseRepository[T]` eliminates 60-70% of CRUD boilerplate
✅ **LLM-Friendly**: Clear patterns make it easy for LLMs to generate correct code

## Anti-Patterns to Avoid

❌ **Router accessing database directly** - Always use service layer
❌ **Service containing FastAPI dependencies** - Keep services framework-agnostic
❌ **Business logic in repository** - Repositories are for data access only
❌ **Multiple features sharing models** - Each feature owns its models
❌ **Circular imports between features** - Features should be independent

## References

- Architecture documentation: `docs/tech-spec-architecture.md`
- BaseRepository pattern: `app/core/repository.py`
- Example implementation: `app/features/health/`
