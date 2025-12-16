import pytest
import pytest_asyncio
from uuid import uuid4
from repositories.orders_repository import OrderRepository
from database.database_models import OrderDB, OrderStatus
from database.connection import PostgreSQLConnection
from sqlalchemy import text

class TestOrderRepositoryDatabaseIntegration:
    @pytest_asyncio.fixture(scope="function")
    async def db_connection(self):
        connection = PostgreSQLConnection()
        test_connection_string = "postgresql+asyncpg://postgres:toor@localhost:5432/test_orders_db"
        
        try:
            await connection.connect(test_connection_string)
            await connection.create_tables()
            yield connection
        except Exception as e:
            pytest.skip(f"Could not connect to test database: {e}")
        finally:
            await connection.close()

    @pytest_asyncio.fixture
    async def db_session(self, db_connection):
        async with await db_connection.get_session() as session:
            try:
                yield session
            finally:
                await session.rollback()

    @pytest_asyncio.fixture
    async def repository(self, db_session):
        return OrderRepository(db_session)

    @pytest_asyncio.fixture(autouse=True)
    async def clean_database(self, db_session):
        await db_session.execute(text("DELETE FROM orders"))
        await db_session.commit()
        yield
        await db_session.execute(text("DELETE FROM orders"))
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_create_and_retrieve_order(self, repository):
        order_data = OrderDB(
            id=uuid4(),
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
        
        created_order = await repository.create_order(order_data)
        assert created_order is not None
        
        retrieved_order = await repository.get_order_by_id(order_data.id)
        assert retrieved_order is not None
        assert retrieved_order.id == order_data.id
        assert retrieved_order.status == OrderStatus.CREATED
        assert retrieved_order.total == 150.50
        assert retrieved_order.payment_id == "pay_999"

    @pytest.mark.asyncio
    async def test_update_order_payment_id(self, repository):
        order = OrderDB(
            id=uuid4(),
            status=OrderStatus.CREATED,
            total=99.99,
            items=[{"product_id": "prod_1", "name": "Test Product", "quantity": 1, "unit_price": 99.99}]
        )
        
        created_order = await repository.create_order(order)
        assert created_order.payment_id is None
        
        updated_order = await repository.update_order_payment_id(order.id, "pay_123")
        assert updated_order is not None
        assert updated_order.payment_id == "pay_123"
        
        retrieved_order = await repository.get_order_by_id(order.id)
        assert retrieved_order.payment_id == "pay_123"

    @pytest.mark.asyncio
    async def test_update_order_payment_id_not_found(self, repository):
        non_existent_id = uuid4()
        result = await repository.update_order_payment_id(non_existent_id, "pay_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, repository):
        non_existent_id = uuid4()
        result = await repository.get_order_by_id(non_existent_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_orders_with_pagination(self, repository):
        for i in range(3):
            order = OrderDB(
                id=uuid4(),
                status=OrderStatus.CREATED,
                total=100.00 + i,
                payment_id=f"pay_{i}",
                items=[{"product_id": f"prod_{i}", "name": f"Product {i}", "quantity": 1, "unit_price": 100.00 + i}]
            )
            await repository.create_order(order)
        
        first_page = await repository.list_orders(skip=0, limit=2)
        assert len(first_page) == 2
        assert first_page[0].payment_id == "pay_2"
        assert first_page[1].payment_id == "pay_1"
        
        second_page = await repository.list_orders(skip=2, limit=2)
        assert len(second_page) == 1
        assert second_page[0].payment_id == "pay_0"

    @pytest.mark.asyncio
    async def test_update_order_status(self, repository):
        order = OrderDB(
            id=uuid4(),
            status=OrderStatus.CREATED,
            total=99.99,
            payment_id="pay_initial",
            items=[{"product_id": "prod_1", "name": "Test Product", "quantity": 1, "unit_price": 99.99}]
        )
        
        created_order = await repository.create_order(order)
        assert created_order.status == OrderStatus.CREATED
        
        updated_order = await repository.update_order_status(order.id, OrderStatus.PAID)
        assert updated_order is not None
        assert updated_order.status == OrderStatus.PAID
        assert updated_order.payment_id == "pay_initial"

    @pytest.mark.asyncio
    async def test_update_order_status_not_found(self, repository):
        non_existent_id = uuid4()
        result = await repository.update_order_status(non_existent_id, OrderStatus.PAID)
        assert result is None

    @pytest.mark.asyncio
    async def test_count_orders(self, repository):
        initial_count = await repository.count_orders()
        
        for i in range(2):
            order = OrderDB(
                id=uuid4(),
                status=OrderStatus.CREATED,
                total=50.00,
                payment_id=f"pay_{i}",
                items=[{"product_id": f"prod_{i}", "name": f"Product {i}", "quantity": 1, "unit_price": 50.00}]
            )
            await repository.create_order(order)
        
        final_count = await repository.count_orders()
        assert final_count == initial_count + 2

    @pytest.mark.asyncio
    async def test_order_created_at_auto_populated(self, repository):
        order = OrderDB(
            id=uuid4(),
            status=OrderStatus.CREATED,
            total=75.00,
            payment_id="pay_time_test",
            items=[{"product_id": "prod_time", "name": "Time Test", "quantity": 1, "unit_price": 75.00}]
        )
        
        created_order = await repository.create_order(order)
        assert created_order.created_at is not None