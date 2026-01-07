import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError
from repositories.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus

class TestOrderRepository:
    @pytest.fixture
    def mock_session(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_logger(self):
        return Mock()
    
    @pytest.fixture
    def repository(self, mock_session, mock_logger):
        return OrderRepository(mock_session, mock_logger)
    
    @pytest.fixture
    def sample_order(self):
        return OrderDB(
            id=uuid4(),
            status=OrderStatus.CREATED,
            total=99.99,
            payment_id="pay_123",
            user_id="test_user_1",
            items=[{"product_id": "prod1", "name": "Test Product", "quantity": 2, "unit_price": 49.99}]
        )

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'create_order')
    async def test_create_order_success(self, mock_method, repository, mock_session, mock_logger, sample_order):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = sample_order
        
        result = await repository.create_order(sample_order)
        
        assert result == sample_order

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'create_order')
    async def test_create_order_failure(self, mock_method, repository, mock_session, mock_logger, sample_order):
        mock_method.__wrapped__ = mock_method
        mock_method.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.create_order(sample_order)

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'get_order_by_id')
    async def test_get_order_by_id_found(self, mock_method, repository, mock_session, mock_logger, sample_order):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = sample_order
        
        result = await repository.get_order_by_id(sample_order.id)
        
        assert result == sample_order

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'get_order_by_id')
    async def test_get_order_by_id_not_found(self, mock_method, repository, mock_session, mock_logger):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = None
        
        result = await repository.get_order_by_id(uuid4())
        
        assert result is None

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'list_orders')
    async def test_list_orders_success(self, mock_method, repository, mock_session, mock_logger, sample_order):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = [sample_order.to_dict()]
        
        result = await repository.list_orders(user_id="test_user_1", skip=0, limit=10)
        
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["payment_id"] == "pay_123"

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'list_orders')
    async def test_list_orders_empty(self, mock_method, repository, mock_session, mock_logger):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = []
        
        result = await repository.list_orders(user_id="test_user_1")
        
        assert len(result) == 0

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'update_order_payment_id')
    async def test_update_order_payment_id_success(self, mock_method, repository, mock_session, mock_logger, sample_order):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = sample_order
        
        result = await repository.update_order_payment_id(sample_order.id, "pay_new")
        
        assert result == sample_order

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'update_order_payment_id')
    async def test_update_order_payment_id_not_found(self, mock_method, repository, mock_session, mock_logger):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = None
        
        result = await repository.update_order_payment_id(uuid4(), "pay_new")
        
        assert result is None

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'update_order_payment_id')
    async def test_update_order_payment_id_failure(self, mock_method, repository, mock_session, mock_logger):
        mock_method.__wrapped__ = mock_method
        mock_method.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.update_order_payment_id(uuid4(), "pay_new")

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'update_order_status')
    async def test_update_order_status_success(self, mock_method, repository, mock_session, mock_logger, sample_order):
        mock_method.__wrapped__ = mock_method
        updated_order = OrderDB(
            id=sample_order.id,
            status=OrderStatus.PAID,
            total=sample_order.total,
            payment_id=sample_order.payment_id,
            user_id=sample_order.user_id,
            items=sample_order.items
        )
        mock_method.return_value = updated_order
        
        result = await repository.update_order_status(sample_order.id, OrderStatus.PAID)
        
        assert result.status == OrderStatus.PAID
        assert result.id == sample_order.id

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'update_order_status')
    async def test_update_order_status_not_found(self, mock_method, repository, mock_session, mock_logger):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = None
        
        result = await repository.update_order_status(uuid4(), OrderStatus.PAID)
        
        assert result is None

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'update_order_status')
    async def test_update_order_status_failure(self, mock_method, repository, mock_session, mock_logger):
        mock_method.__wrapped__ = mock_method
        mock_method.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.update_order_status(uuid4(), OrderStatus.PAID)

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'count_orders')
    async def test_count_orders_success(self, mock_method, repository, mock_session, mock_logger, sample_order):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = 2
        
        result = await repository.count_orders(user_id="test_user_1")
        
        assert result == 2

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'count_orders')
    async def test_count_orders_empty(self, mock_method, repository, mock_session, mock_logger):
        mock_method.__wrapped__ = mock_method
        mock_method.return_value = 0
        
        result = await repository.count_orders()
        
        assert result == 0

    @pytest.mark.asyncio
    @patch.object(OrderRepository, 'count_orders')
    async def test_count_orders_failure(self, mock_method, repository, mock_session, mock_logger):
        mock_method.__wrapped__ = mock_method
        mock_method.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.count_orders()