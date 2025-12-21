import pytest
from unittest.mock import Mock, AsyncMock
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
    async def test_create_order_success(self, repository, mock_session, mock_logger, sample_order):
        result = await repository.create_order(sample_order)
        
        assert result == sample_order
        mock_session.add.assert_called_once_with(sample_order)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(sample_order)
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_create_order_failure(self, repository, mock_session, mock_logger, sample_order):
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.create_order(sample_order)
        
        mock_session.rollback.assert_called_once()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_order_by_id_found(self, repository, mock_session, mock_logger, sample_order):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_order
        
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_order_by_id(sample_order.id)
        
        assert result == sample_order
        assert result.payment_id == "pay_123"
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_order_by_id_not_found(self, repository, mock_session, mock_logger):
        order_id = uuid4()
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_order_by_id(order_id)
        
        assert result is None
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_list_orders_success(self, repository, mock_session, mock_logger, sample_order):
        mock_scalars = Mock()
        mock_scalars.all.return_value = [sample_order]
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.list_orders(skip=0, limit=10)
        
        assert len(result) == 1
        assert result[0] == sample_order
        assert result[0].payment_id == "pay_123"
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_list_orders_empty(self, repository, mock_session, mock_logger):
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.list_orders()
        
        assert len(result) == 0
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_order_payment_id_success(self, repository, mock_session, mock_logger, sample_order):
        mock_update_result = Mock()
        mock_update_result.rowcount = 1
        
        mock_get_result = Mock()
        mock_get_result.scalar_one_or_none.return_value = sample_order
        
        mock_session.execute.side_effect = [mock_update_result, mock_get_result]
        
        result = await repository.update_order_payment_id(sample_order.id, "pay_new")
        
        assert result == sample_order
        assert mock_session.execute.call_count == 2
        mock_session.commit.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_order_payment_id_not_found(self, repository, mock_session, mock_logger):
        order_id = uuid4()
        
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        result = await repository.update_order_payment_id(order_id, "pay_new")
        
        assert result is None
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_order_payment_id_failure(self, repository, mock_session, mock_logger):
        order_id = uuid4()
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.update_order_payment_id(order_id, "pay_new")
        
        mock_session.rollback.assert_called_once()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_order_status_success(self, repository, mock_session, mock_logger, sample_order):
        # First call: update statement
        mock_update_result = Mock()
        mock_update_result.rowcount = 1
        
        updated_order = OrderDB(
            id=sample_order.id,
            status=OrderStatus.PAID,
            total=sample_order.total,
            payment_id=sample_order.payment_id,
            user_id=sample_order.user_id,
            items=sample_order.items
        )
        
        mock_get_result = Mock()
        mock_get_result.scalar_one_or_none.return_value = updated_order
        
        mock_session.execute.side_effect = [mock_update_result, mock_get_result]
        
        result = await repository.update_order_status(sample_order.id, OrderStatus.PAID)
        
        assert result.status == OrderStatus.PAID
        assert result.id == sample_order.id
        assert mock_session.execute.call_count == 2
        mock_session.commit.assert_called_once()
        mock_logger.info.assert_called()
        
    @pytest.mark.asyncio
    async def test_update_order_status_not_found(self, repository, mock_session, mock_logger):
        order_id = uuid4()
        
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        result = await repository.update_order_status(order_id, OrderStatus.PAID)
        
        assert result is None
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_order_status_failure(self, repository, mock_session, mock_logger):
        order_id = uuid4()
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.update_order_status(order_id, OrderStatus.PAID)
        
        mock_session.rollback.assert_called_once()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_orders_success(self, repository, mock_session, mock_logger, sample_order):
        mock_scalars = Mock()
        mock_scalars.all.return_value = [sample_order, sample_order]
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.count_orders()
        
        assert result == 2
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_count_orders_empty(self, repository, mock_session, mock_logger):
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.count_orders()
        
        assert result == 0
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_count_orders_failure(self, repository, mock_session, mock_logger):
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.count_orders()
        
        mock_logger.error.assert_called_once()