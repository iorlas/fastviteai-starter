"""Tests for BaseRepository[T] generic CRUD operations.

These tests validate the BaseRepository pattern with a test model,
ensuring type safety, async operations, and pagination functionality.
"""

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.repository import BaseRepository

# Test model setup
Base = declarative_base()


class TestModel(Base):
    """Test model for repository testing."""

    __tablename__ = "test_models"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))


@pytest_asyncio.fixture
async def async_session():
    """Create an in-memory SQLite async session for testing."""
    # Create async engine with in-memory SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create and yield session
    async with async_session_factory() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def repository(async_session):
    """Create a BaseRepository instance for TestModel."""
    return BaseRepository[TestModel](TestModel, async_session)


@pytest.mark.asyncio()
async def test_repository_initialization(async_session):
    """Test BaseRepository can be initialized with model and session."""
    repo = BaseRepository[TestModel](TestModel, async_session)

    assert repo.model == TestModel
    assert repo.session == async_session


@pytest.mark.asyncio()
async def test_create(repository):
    """Test creating a new instance."""
    # AC#2: Test create commits and refreshes instance
    data = {"name": "Test Item", "description": "Test description"}

    instance = await repository.create(data)

    assert instance.id is not None
    assert instance.name == "Test Item"
    assert instance.description == "Test description"


@pytest.mark.asyncio()
async def test_get_by_id(repository):
    """Test retrieving an instance by ID."""
    # AC#2: Test get_by_id returns correct model instance
    # Create a test instance
    instance = await repository.create({"name": "Find Me", "description": "Searchable"})
    item_id = instance.id

    # Retrieve by ID
    found = await repository.get_by_id(item_id)

    assert found is not None
    assert found.id == item_id
    assert found.name == "Find Me"


@pytest.mark.asyncio()
async def test_get_by_id_not_found(repository):
    """Test get_by_id returns None when ID doesn't exist."""
    result = await repository.get_by_id(99999)
    assert result is None


@pytest.mark.asyncio()
async def test_list(repository):
    """Test listing instances with pagination."""
    # AC#2: Test list with pagination (offset, limit)
    # Create test data
    await repository.create({"name": "Item 1"})
    await repository.create({"name": "Item 2"})
    await repository.create({"name": "Item 3"})

    # Get all items
    all_items = await repository.list(offset=0, limit=10)
    assert len(all_items) == 3

    # Get first 2 items
    page1 = await repository.list(offset=0, limit=2)
    assert len(page1) == 2

    # Get last item (offset=2)
    page2 = await repository.list(offset=2, limit=2)
    assert len(page2) == 1


@pytest.mark.asyncio()
async def test_list_with_count(repository):
    """Test list_with_count returns items and total count."""
    # AC#5: Test list_with_count returns (items, total) tuple
    # Create test data
    for i in range(5):
        await repository.create({"name": f"Item {i + 1}"})

    # Get first page with count
    items, total = await repository.list_with_count(offset=0, limit=3)

    assert len(items) == 3
    assert total == 5
    assert items[0].name == "Item 1"

    # Get second page with count
    items_page2, total_page2 = await repository.list_with_count(offset=3, limit=3)

    assert len(items_page2) == 2  # Only 2 items remaining
    assert total_page2 == 5  # Total count remains the same


@pytest.mark.asyncio()
async def test_list_with_count_empty(repository):
    """Test list_with_count with no records."""
    items, total = await repository.list_with_count()

    assert items == []
    assert total == 0


@pytest.mark.asyncio()
async def test_update(repository):
    """Test updating an existing instance."""
    # AC#2: Test update modifies fields and commits
    # Create instance
    instance = await repository.create({"name": "Original", "description": "Old"})
    original_id = instance.id

    # Update instance
    updated = await repository.update(instance, {"name": "Updated", "description": "New"})

    assert updated.id == original_id
    assert updated.name == "Updated"
    assert updated.description == "New"

    # Verify update persisted
    found = await repository.get_by_id(original_id)
    assert found.name == "Updated"


@pytest.mark.asyncio()
async def test_delete(repository):
    """Test deleting an instance."""
    # AC#2: Test delete removes instance and commits
    # Create instance
    instance = await repository.create({"name": "To Delete"})
    item_id = instance.id

    # Verify it exists
    found = await repository.get_by_id(item_id)
    assert found is not None

    # Delete instance
    await repository.delete(instance)

    # Verify it's gone
    not_found = await repository.get_by_id(item_id)
    assert not_found is None


@pytest.mark.asyncio()
async def test_type_safety(repository):
    """Test that repository maintains type safety."""
    # AC#4: Test type hints work (IDE can infer T)
    # Create an instance
    instance = await repository.create({"name": "Type Test"})

    # Verify instance is of correct type
    assert isinstance(instance, TestModel)
    assert hasattr(instance, "id")
    assert hasattr(instance, "name")

    # List should return list of TestModel
    items = await repository.list()
    assert all(isinstance(item, TestModel) for item in items)


@pytest.mark.asyncio()
async def test_pagination_use_case(repository):
    """Test realistic pagination scenario."""
    # Create 25 items
    for i in range(25):
        await repository.create({"name": f"Item {i + 1:02d}"})

    # Page 1: items 1-10
    page1, total = await repository.list_with_count(offset=0, limit=10)
    assert len(page1) == 10
    assert total == 25
    assert page1[0].name == "Item 01"

    # Page 2: items 11-20
    page2, _ = await repository.list_with_count(offset=10, limit=10)
    assert len(page2) == 10
    assert page2[0].name == "Item 11"

    # Page 3: items 21-25 (partial page)
    page3, _ = await repository.list_with_count(offset=20, limit=10)
    assert len(page3) == 5
    assert page3[0].name == "Item 21"
