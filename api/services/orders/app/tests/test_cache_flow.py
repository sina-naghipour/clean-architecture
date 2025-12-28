import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call
from uuid import uuid4
from datetime import datetime
import json
import os

# Mock environment before imports
os.environ['CACHE_ENABLED'] = 'true'
os.environ['CACHE_TTL'] = '300'

from cache.redis_client import redis_client
from cache.cache_service import cache_service, CacheService
from cache.cache_strategy import CacheStrategy
from repositories.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus


@pytest.fixture(autouse=True)
def clear_env():
    os.environ['CACHE_ENABLED'] = 'true'
    yield
    redis_client._pool = None
    redis_client._initialized = False


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.get = AsyncMock()
    mock.setex = AsyncMock()
    mock.delete = AsyncMock()
    mock.keys = AsyncMock()
    mock.ping = AsyncMock()
    return mock


@pytest.fixture
def order_data():
    order_id = uuid4()
    return {
        "id": str(order_id),
        "status": "pending",
        "total": 99.99,
        "user_id": "user_123",
        "items": [{"product_id": "prod_1", "name": "Product 1", "quantity": 2, "unit_price": 49.99}],
        "created_at": datetime.utcnow().isoformat()
    }


class TestRedisClient:
    @pytest.mark.asyncio
    async def test_ping_success(self, mock_redis):
        with patch.object(redis_client, 'get_client', return_value=mock_redis):
            mock_redis.ping.return_value = True
            result = await redis_client.ping()
            assert result is True


class TestCacheService:
    @pytest.mark.asyncio
    async def test_get_order_cache_hit(self, mock_redis, order_data):
        cache_service.enabled = True
        redis_client._pool = True
        redis_client.is_connected = True
        
        with patch.object(redis_client, 'get_client', return_value=mock_redis):
            mock_redis.get.return_value = json.dumps(order_data)
            
            cached = await cache_service.get_order(order_data["id"])
            
            assert cached == order_data
            mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_order_cache_miss(self, mock_redis, order_data):
        cache_service.enabled = True
        redis_client._pool = True
        redis_client.is_connected = True
        
        with patch.object(redis_client, 'get_client', return_value=mock_redis):
            mock_redis.get.return_value = None
            
            cached = await cache_service.get_order(order_data["id"])
            
            assert cached is None
            mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_order_cache_disabled(self, mock_redis, order_data):
        cache_service.enabled = False
        
        cached = await cache_service.get_order(order_data["id"])
        
        assert cached is None
        mock_redis.get.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_set_order(self, mock_redis, order_data):
        cache_service.enabled = True
        redis_client._pool = True
        redis_client.is_connected = True
        
        with patch.object(redis_client, 'get_client', return_value=mock_redis):
            mock_redis.setex.return_value = True
            
            result = await cache_service.set_order(order_data["id"], order_data)
            
            assert result is True
            mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_order(self, mock_redis, order_data):
        cache_service.enabled = True
        redis_client._pool = True
        redis_client.is_connected = True
        
        with patch.object(redis_client, 'get_client', return_value=mock_redis):
            mock_redis.delete.return_value = 1
            
            result = await cache_service.delete_order(order_data["id"])
            
            assert result is True
            mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_user_orders_pattern(self, mock_redis):
        cache_service.enabled = True
        redis_client._pool = True
        redis_client.is_connected = True
        
        with patch.object(redis_client, 'get_client', return_value=mock_redis):
            mock_redis.keys.return_value = [
                "orders:abc123:user_orders:user_123:1:10",
                "orders:def456:user_orders:user_123:2:10"
            ]
            mock_redis.delete.return_value = 2
            
            deleted = await cache_service.delete_user_orders("user_123")
            
            assert deleted == 2
            mock_redis.keys.assert_called_once()
            mock_redis.delete.assert_called_once_with(
                "orders:abc123:user_orders:user_123:1:10",
                "orders:def456:user_orders:user_123:2:10"
            )
    
    @pytest.mark.asyncio
    async def test_key_generation(self):
        cache_service = CacheService()
        key = cache_service._generate_key('order', '123')
        assert key.startswith('orders:')
        assert len(key) == len('orders:') + 12


class TestOrderRepositoryCache:
    @pytest.fixture
    def mock_session(self):
        return AsyncMock()
    
    @pytest.fixture
    def repository(self, mock_session):
        repo = OrderRepository(mock_session)
        repo.logger = MagicMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_get_order_by_id_cache_hit(self, repository, mock_session, order_data):
        with patch.object(cache_service, 'enabled', True):
            with patch.object(cache_service, 'get_order', AsyncMock(return_value=order_data)):
                result = await repository.get_order_by_id(uuid4())
                
                assert result == order_data
                mock_session.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_order_by_id_cache_miss(self, repository, mock_session):
        order_id = uuid4()
        order_db = OrderDB(
            id=order_id,
            status=OrderStatus.PENDING,
            total=99.99,
            user_id="user_123",
            items=[]
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = order_db
        mock_session.execute.return_value = mock_result
        
        with patch.object(cache_service, 'enabled', True):
            with patch.object(cache_service, 'get_order', AsyncMock(return_value=None)):
                with patch.object(cache_service, 'set_order', AsyncMock(return_value=True)) as mock_set:
                    result = await repository.get_order_by_id(order_id)
                    
                    mock_session.execute.assert_called_once()
                    mock_set.assert_called_once()
                    assert result is not None
    
    @pytest.mark.asyncio
    async def test_create_order_invalidates_cache(self, repository, mock_session):
        order_db = OrderDB(
            id=uuid4(),
            status=OrderStatus.CREATED,
            total=99.99,
            user_id="user_123",
            items=[]
        )
        
        with patch.object(cache_service, 'enabled', True):
            with patch.object(cache_service, 'delete_user_orders', AsyncMock()) as mock_delete:
                await repository.create_order(order_db)
                
                mock_delete.assert_called_once_with("user_123")
                mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_order_status_invalidates_cache(self, repository, mock_session):
        order_id = uuid4()
        
        mock_execute_result = MagicMock()
        mock_execute_result.rowcount = 1
        mock_session.execute.return_value = mock_execute_result
        
        with patch.object(cache_service, 'enabled', True):
            with patch.object(repository, 'get_order_by_id', AsyncMock(return_value={"id": str(order_id), "user_id": "user_123"})):
                with patch.object(cache_service, 'delete_order', AsyncMock()) as mock_delete:
                    result = await repository.update_order_status(order_id, OrderStatus.PAID)
                    
                    mock_delete.assert_called_once_with(str(order_id))
    
    @pytest.mark.asyncio
    async def test_list_orders_cache_hit(self, repository, mock_session):
        user_id = "user_123"
        page = 1
        page_size = 10
        
        cached_data = {
            "orders": [{"id": str(uuid4()), "status": "paid", "total": 99.99}],
            "_cached_at": datetime.utcnow().isoformat()
        }
        
        with patch.object(cache_service, 'enabled', True):
            with patch.object(cache_service, 'get_user_orders', AsyncMock(return_value=cached_data)):
                result = await repository.list_orders(user_id, 0, page_size)
                
                assert result == cached_data["orders"]
                mock_session.execute.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_list_orders_cache_miss(self, repository, mock_session):
        user_id = "user_123"
        page_size = 10
        
        order_db = OrderDB(
            id=uuid4(),
            status=OrderStatus.PAID,
            total=99.99,
            user_id=user_id,
            items=[]
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [order_db]
        mock_session.execute.return_value = mock_result
        
        with patch.object(cache_service, 'enabled', True):
            with patch.object(cache_service, 'get_user_orders', AsyncMock(return_value=None)):
                with patch.object(cache_service, 'set_user_orders', AsyncMock()) as mock_set:
                    result = await repository.list_orders(user_id, 0, page_size)
                    
                    mock_session.execute.assert_called_once()
                    mock_set.assert_called_once()
                    assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_cache_disabled_still_works(self, repository, mock_session):
        order_id = uuid4()
        order_db = OrderDB(
            id=order_id,
            status=OrderStatus.PENDING,
            total=99.99,
            user_id="user_123",
            items=[]
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = order_db
        mock_session.execute.return_value = mock_result
        
        cache_service.enabled = False
        
        result = await repository.get_order_by_id(order_id)
        
        mock_session.execute.assert_called_once()
        assert result is not None


class TestCacheStrategy:
    def test_should_cache_order(self):
        strategy = CacheStrategy()
        strategy.enabled = True
        
        assert strategy.should_cache_order({"status": "pending", "total": 50}) is True
        assert strategy.should_cache_order({"status": "failed", "total": 50}) is False
        assert strategy.should_cache_order({"status": "canceled", "total": 50}) is False
        assert strategy.should_cache_order({"status": "paid", "total": 15000}) is True
    
    def test_get_order_ttl(self):
        strategy = CacheStrategy()
        
        assert strategy.get_order_ttl({"status": "pending"}) == 60
        assert strategy.get_order_ttl({"status": "paid"}) == 1800
        assert strategy.get_order_ttl({"status": "created"}) == 300
        assert strategy.get_order_ttl({"status": "unknown"}) == 300


class TestCompleteCacheFlow:
    @pytest.mark.asyncio
    async def test_end_to_end_cache_flow(self, mock_redis):
        cache_service.enabled = True
        redis_client._pool = True
        redis_client.is_connected = True
        
        with patch.object(redis_client, 'get_client', return_value=mock_redis):
            order_id = str(uuid4())
            order_data = {
                "id": order_id,
                "status": "pending",
                "total": 100.0
            }
            
            key = cache_service._generate_key('order', order_id)
            
            mock_redis.get.side_effect = [None, json.dumps(order_data), None]
            mock_redis.setex.return_value = True
            mock_redis.delete.return_value = 1
            
            cached = await cache_service.get_order(order_id)
            assert cached is None
            
            await cache_service.set_order(order_id, order_data)
            
            cached = await cache_service.get_order(order_id)
            assert cached == order_data
            
            await cache_service.delete_order(order_id)
            
            cached = await cache_service.get_order(order_id)
            assert cached is None
            
            calls = mock_redis.get.call_args_list
            assert len(calls) == 3
            assert calls[0][0][0] == key
            assert calls[1][0][0] == key
            assert calls[2][0][0] == key


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])