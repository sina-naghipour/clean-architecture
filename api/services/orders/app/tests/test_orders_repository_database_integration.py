import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from repositories.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class TestOrderRepositoryDatabaseIntegration:
    @pytest_asyncio.fixture
    async def mock_session(self):
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        session.scalar = AsyncMock()
        return session

    @pytest_asyncio.fixture
    async def repository(self, mock_session):
        return OrderRepository(mock_session)

    @pytest.mark.asyncio
    async def test_create_and_retrieve_order(self, repository, mock_session):
        order_id = uuid4()
        order_data = OrderDB(
            id=order_id,
            status=OrderStatus.CREATED,
            total=150.50,
            billing_address_id="addr_123",
            shipping_address_id="addr_456",
            payment_method_token="pm_789",
            payment_id="pay_999",
            items=[
                {
                    "product_id": "prod_1",
                    "name": "Test Product 1",
                    "quantity": 2,
                    "unit_price": 50.00
                },
                {
                    "product_id": "prod_2",
                    "name": "Test Product 2",
                    "quantity": 1,
                    "unit_price": 50.50
                }
            ]
        )

        def mock_refresh(obj):
            obj.created_at = datetime.utcnow()

        mock_session.refresh.side_effect = mock_refresh

        created_order = await repository.create_order(order_data)

        assert created_order == order_data
        mock_session.add.assert_called_once_with(order_data)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(order_data)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = order_data
        mock_session.execute.return_value = mock_result

        retrieved_order = await repository.get_order_by_id(order_id)
        assert retrieved_order == order_data

    @pytest.mark.asyncio
    async def test_update_order_payment_id(self, repository, mock_session):
        order_id = uuid4()

        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1
        mock_session.execute.return_value = mock_update_result

        mock_order = MagicMock()
        mock_order.id = order_id
        mock_order.payment_id = "pay_123"

        mock_select_result = MagicMock()
        mock_select_result.scalar_one_or_none.return_value = mock_order

        mock_session.execute.side_effect = [mock_update_result, mock_select_result]

        updated_order = await repository.update_order_payment_id(order_id, "pay_123")
        assert updated_order == mock_order

    @pytest.mark.asyncio
    async def test_update_order_payment_id_not_found(self, repository, mock_session):
        order_id = uuid4()
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 0
        mock_session.execute.return_value = mock_update_result

        result = await repository.update_order_payment_id(order_id, "pay_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, repository, mock_session):
        order_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_order_by_id(order_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_orders_with_pagination(self, repository, mock_session):
        mock_orders = []
        for i in range(3):
            order = MagicMock()
            order.payment_id = f"pay_{i}"
            mock_orders.append(order)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_orders
        mock_session.execute.return_value = mock_result

        result = await repository.list_orders(skip=0, limit=2)
        assert len(result) == 3
        assert result[0].payment_id == "pay_0"
        assert result[1].payment_id == "pay_1"

    @pytest.mark.asyncio
    async def test_update_order_status(self, repository, mock_session):
        order_id = uuid4()
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 1
        mock_session.execute.return_value = mock_update_result

        mock_order = MagicMock()
        mock_order.id = order_id
        mock_order.status = OrderStatus.PAID
        mock_order.payment_id = "pay_initial"

        mock_select_result = MagicMock()
        mock_select_result.scalar_one_or_none.return_value = mock_order

        mock_session.execute.side_effect = [mock_update_result, mock_select_result]

        updated_order = await repository.update_order_status(order_id, OrderStatus.PAID)
        assert updated_order == mock_order
        assert updated_order.status == OrderStatus.PAID

    @pytest.mark.asyncio
    async def test_update_order_status_not_found(self, repository, mock_session):
        order_id = uuid4()
        mock_update_result = MagicMock()
        mock_update_result.rowcount = 0
        mock_session.execute.return_value = mock_update_result

        result = await repository.update_order_status(order_id, OrderStatus.PAID)
        assert result is None

    @pytest.mark.asyncio
    async def test_count_orders(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
        mock_session.execute.return_value = mock_result

        count = await repository.count_orders()
        assert count == 2

    @pytest.mark.asyncio
    async def test_order_created_at_auto_populated(self, repository, mock_session):
        order_id = uuid4()
        order_data = OrderDB(
            id=order_id,
            status=OrderStatus.CREATED,
            total=75.00,
            payment_id="pay_time_test",
            items=[{"product_id": "prod_time", "name": "Time Test", "quantity": 1, "unit_price": 75.00}]
        )

        created_at_time = datetime.utcnow()
        def mock_refresh(obj):
            obj.created_at = created_at_time

        mock_session.refresh.side_effect = mock_refresh

        created_order = await repository.create_order(order_data)
        assert created_order.created_at == created_at_time

    @pytest.mark.asyncio
    async def test_create_order_database_error(self, repository, mock_session):
        order_data = OrderDB(
            id=uuid4(),
            status=OrderStatus.CREATED,
            total=100.00,
            items=[]
        )

        mock_session.commit.side_effect = SQLAlchemyError("DB Error")

        with pytest.raises(SQLAlchemyError):
            await repository.create_order(order_data)

        mock_session.rollback.assert_called_once()