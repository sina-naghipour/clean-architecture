import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from repository.user_repository import UserRepository
from database.pydantic_models import UserCreate, ProfileUpdateRequest

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.delete = MagicMock()
    return session

@pytest.fixture
def user_repository(mock_db_session):
    return UserRepository(mock_db_session)

@pytest.fixture
def sample_user_data():
    return {
        "email": "test@example.com",
        "password_hash": "hashed_password_123",
        "name": "Test User"
    }

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.password = "hashed_password_123"
    user.name = "Test User"
    user.is_active = True
    user.last_login = None
    user.created_at = datetime.now()
    user.updated_at = datetime.now()
    return user

@pytest.mark.asyncio
class TestUserRepositoryClass:
    async def test_get_by_id_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_id(mock_user.id)

        assert result == mock_user
        mock_db_session.execute.assert_called_once()

    async def test_get_by_id_not_found(self, user_repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_id(uuid.uuid4())

        assert result is None
        mock_db_session.execute.assert_called_once()

    async def test_get_by_email_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_email("test@example.com")

        assert result == mock_user
        mock_db_session.execute.assert_called_once()

    async def test_get_by_email_not_found(self, user_repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_email("nonexistent@example.com")

        assert result is None
        mock_db_session.execute.assert_called_once()

    async def test_get_active_user_by_email_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_active_user_by_email("test@example.com")

        assert result == mock_user
        mock_db_session.execute.assert_called_once()

    async def test_get_active_user_by_email_inactive(self, user_repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_active_user_by_email("test@example.com")

        assert result is None
        mock_db_session.execute.assert_called_once()

    async def test_email_exists_true(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.email_exists("test@example.com")

        assert result is True
        mock_db_session.execute.assert_called_once()

    async def test_email_exists_false(self, user_repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.email_exists("nonexistent@example.com")

        assert result is False
        mock_db_session.execute.assert_called_once()

    async def test_create_user_success(self, user_repository, mock_db_session, sample_user_data):
        mock_user = MagicMock()
        user_repository.create = AsyncMock(return_value=mock_user)

        result = await user_repository.create_user(UserCreate(**sample_user_data))

        assert result == mock_user
        user_repository.create.assert_called_once()

    async def test_create_user_duplicate_email(self, user_repository, sample_user_data):
        from sqlalchemy.exc import IntegrityError
        user_repository.create = AsyncMock(side_effect=IntegrityError("Duplicate email", None, None))

        with pytest.raises(ValueError, match="User with this email already exists"):
            await user_repository.create_user(UserCreate(**sample_user_data))

        user_repository.db_session.rollback.assert_called_once()

    async def test_update_last_login_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.update_last_login(mock_user.id)

        assert result is True
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_update_last_login_user_not_found(self, user_repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.update_last_login(uuid.uuid4())

        assert result is False
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_update_password_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.update_password(mock_user.id, "new_hash")

        assert result is True
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_update_password_user_not_found(self, user_repository, mock_db_session):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.update_password(uuid.uuid4(), "new_hash")

        assert result is False
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_activate_user_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.activate_user(mock_user.id)

        assert result is True
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_deactivate_user_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.deactivate_user(mock_user.id)

        assert result is True
        mock_db_session.execute.assert_called_once()
        mock_db_session.commit.assert_called_once()

    async def test_update_profile_success(self, user_repository, mock_user):
        profile_data = ProfileUpdateRequest(name="Updated Name")
        user_repository.update = AsyncMock(return_value=mock_user)

        result = await user_repository.update_profile(mock_user.id, profile_data)

        assert result == mock_user
        user_repository.update.assert_called_once()

    async def test_search_users_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        mock_db_session.execute.return_value = mock_result

        results = await user_repository.search_users("test")

        assert len(results) == 1
        assert results[0] == mock_user
        mock_db_session.execute.assert_called_once()

    async def test_get_active_users_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        mock_db_session.execute.return_value = mock_result

        results = await user_repository.get_active_users()

        assert len(results) == 1
        assert results[0] == mock_user
        mock_db_session.execute.assert_called_once()

    async def test_get_users_created_after_success(self, user_repository, mock_db_session, mock_user):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        mock_db_session.execute.return_value = mock_result

        results = await user_repository.get_users_created_after(datetime(2020, 1, 1))

        assert len(results) == 1
        assert results[0] == mock_user
        mock_db_session.execute.assert_called_once()

    async def test_delete_user_success(self, user_repository, mock_db_session, mock_user):
        user_repository.get_by_id = AsyncMock(return_value=mock_user)
        mock_db_session.delete = AsyncMock()
        mock_db_session.commit = AsyncMock()
        
        result = await user_repository.delete(mock_user.id)
        
        assert result is True
        user_repository.get_by_id.assert_called_once_with(mock_user.id)
        mock_db_session.delete.assert_called_once_with(mock_user)
        mock_db_session.commit.assert_called_once()

    async def test_delete_user_not_found(self, user_repository, mock_db_session):
        user_repository.get_by_id = AsyncMock(return_value=None)

        result = await user_repository.delete(uuid.uuid4())

        assert result is False
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()