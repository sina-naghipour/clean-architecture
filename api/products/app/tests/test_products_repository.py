import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import uuid
from app.repositories.product_repository import ProductRepository
from app.database.database_models import ProductDB

class TestProductRepository:
    
    @pytest.fixture
    def mock_collection(self):
        return Mock()
    
    @pytest.fixture
    def repository(self, mock_collection):
        with patch('app.repositories.product_repository.get_products_collection', return_value=mock_collection):
            return ProductRepository()
    
    @pytest.fixture
    def sample_product(self):
        return ProductDB(
            name="Test Product",
            price=29.99,
            stock=100,
            description="Test Description"
        )
    
    @pytest.fixture
    def sample_product_dict(self):
        return {
            "_id": "test_id_123",
            "name": "Test Product",
            "price": 29.99,
            "stock": 100,
            "description": "Test Description",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @pytest.mark.asyncio
    async def test_create_product_success(self, repository, mock_collection, sample_product):
        mock_collection.find_one.return_value = None
        mock_collection.insert_one.return_value = Mock(inserted_id=sample_product.id)
        
        result = await repository.create_product(sample_product)
        
        assert result == sample_product
        mock_collection.find_one.assert_called_once()
        mock_collection.insert_one.assert_called_once_with(sample_product.to_dict())

    @pytest.mark.asyncio
    async def test_create_product_duplicate_name(self, repository, mock_collection, sample_product):
        mock_collection.find_one.return_value = {"_id": "existing_id", "name": "Test Product"}
        
        result = await repository.create_product(sample_product)
        
        assert result is None
        mock_collection.find_one.assert_called_once()
        mock_collection.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_product_by_id_found(self, repository, mock_collection, sample_product_dict):
        mock_collection.find_one.return_value = sample_product_dict
        
        result = await repository.get_product_by_id("test_id_123")
        
        assert result is not None
        assert result.id == "test_id_123"
        assert result.name == "Test Product"
        mock_collection.find_one.assert_called_once_with({"_id": "test_id_123"})

    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(self, repository, mock_collection):
        mock_collection.find_one.return_value = None
        
        result = await repository.get_product_by_id("nonexistent_id")
        
        assert result is None
        mock_collection.find_one.assert_called_once_with({"_id": "nonexistent_id"})

    @pytest.mark.asyncio
    async def test_get_product_by_name_found(self, repository, mock_collection, sample_product_dict):
        mock_collection.find_one.return_value = sample_product_dict
        
        result = await repository.get_product_by_name("Test Product")
        
        assert result is not None
        assert result.name == "Test Product"
        mock_collection.find_one.assert_called_once_with({
            "name": {"$regex": "^Test Product$", "$options": "i"}
        })

    @pytest.mark.asyncio
    async def test_get_product_by_name_not_found(self, repository, mock_collection):
        mock_collection.find_one.return_value = None
        
        result = await repository.get_product_by_name("Nonexistent Product")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_products_no_search(self, repository, mock_collection, sample_product_dict):
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [sample_product_dict]
        
        result = await repository.list_products(skip=0, limit=20)
        
        assert len(result) == 1
        assert result[0].name == "Test Product"
        mock_collection.find.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_list_products_with_search(self, repository, mock_collection, sample_product_dict):
        mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [sample_product_dict]
        
        result = await repository.list_products(skip=0, limit=20, search_query="test")
        
        assert len(result) == 1
        mock_collection.find.assert_called_once_with({
            "$or": [
                {"name": {"$regex": "test", "$options": "i"}},
                {"description": {"$regex": "test", "$options": "i"}}
            ]
        })

    @pytest.mark.asyncio
    async def test_count_products(self, repository, mock_collection):
        mock_collection.count_documents.return_value = 5
        
        result = await repository.count_products()
        
        assert result == 5
        mock_collection.count_documents.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_count_products_with_search(self, repository, mock_collection):
        mock_collection.count_documents.return_value = 2
        
        result = await repository.count_products(search_query="test")
        
        assert result == 2
        mock_collection.count_documents.assert_called_once_with({
            "$or": [
                {"name": {"$regex": "test", "$options": "i"}},
                {"description": {"$regex": "test", "$options": "i"}}
            ]
        })

    @pytest.mark.asyncio
    async def test_update_product_success(self, repository, mock_collection, sample_product_dict):
        mock_collection.find_one.side_effect = [None, sample_product_dict]
        mock_collection.update_one.return_value = Mock(modified_count=1)
        
        update_data = {"name": "Updated Product", "price": 39.99}
        result = await repository.update_product("test_id_123", update_data)
        
        assert result is not None
        assert result.id == "test_id_123"
        mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_product_name_conflict(self, repository, mock_collection):
        mock_collection.find_one.return_value = {"_id": "other_id", "name": "Existing Product"}
        
        update_data = {"name": "Existing Product"}
        result = await repository.update_product("test_id_123", update_data)
        
        assert result is None
        mock_collection.update_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_product_success(self, repository, mock_collection):
        mock_collection.delete_one.return_value = Mock(deleted_count=1)
        
        result = await repository.delete_product("test_id_123")
        
        assert result is True
        mock_collection.delete_one.assert_called_once_with({"_id": "test_id_123"})

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, repository, mock_collection):
        mock_collection.delete_one.return_value = Mock(deleted_count=0)
        
        result = await repository.delete_product("nonexistent_id")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_update_inventory_success(self, repository, mock_collection, sample_product_dict):
        mock_collection.update_one.return_value = Mock(modified_count=1)
        mock_collection.find_one.return_value = sample_product_dict
        
        result = await repository.update_inventory("test_id_123", 75)
        
        assert result is not None
        mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_inventory_no_change(self, repository, mock_collection, sample_product_dict):
        mock_collection.update_one.return_value = Mock(modified_count=0)
        mock_collection.find_one.return_value = sample_product_dict
        
        result = await repository.update_inventory("test_id_123", 100)
        
        assert result is not None
        mock_collection.update_one.assert_called_once()