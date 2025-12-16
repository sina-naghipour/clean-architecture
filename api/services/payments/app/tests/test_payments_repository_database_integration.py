import pytest
import pytest_asyncio
from uuid import uuid4
from repositories.payments_repository import PaymentRepository
from database.database_models import PaymentDB, PaymentStatus
from database.connection import PostgreSQLConnection
from sqlalchemy import text

class TestPaymentRepositoryDatabaseIntegration:
    @pytest_asyncio.fixture(scope="function")
    async def db_connection(self):
        connection = PostgreSQLConnection()
        test_connection_string = "postgresql+asyncpg://postgres:toor@localhost:5432/test_payments_db"
        
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
        return PaymentRepository(db_session)

    @pytest_asyncio.fixture(autouse=True)
    async def clean_database(self, db_session):
        await db_session.execute(text("DELETE FROM payments"))
        await db_session.commit()
        yield
        await db_session.execute(text("DELETE FROM payments"))
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_create_and_retrieve_payment(self, repository):
        payment_data = PaymentDB(
            id=uuid4(),
            order_id="order_123",
            user_id="user_123",
            amount=150.50,
            status=PaymentStatus.CREATED,
            payment_method_token="pm_789",
            currency="usd",
            metadata={"product": "test"}
        )
        
        created_payment = await repository.create_payment(payment_data)
        assert created_payment is not None
        
        retrieved_payment = await repository.get_payment_by_id(payment_data.id)
        assert retrieved_payment is not None
        assert retrieved_payment.id == payment_data.id
        assert retrieved_payment.order_id == "order_123"
        assert retrieved_payment.amount == 150.50
        assert retrieved_payment.status == PaymentStatus.CREATED

    @pytest.mark.asyncio
    async def test_get_payment_by_order_id(self, repository):
        payment = PaymentDB(
            id=uuid4(),
            order_id="order_specific",
            user_id="user_123",
            amount=99.99,
            status=PaymentStatus.CREATED,
            payment_method_token="pm_123",
            currency="usd"
        )
        
        await repository.create_payment(payment)
        
        retrieved_payment = await repository.get_payment_by_order_id("order_specific")
        assert retrieved_payment is not None
        assert retrieved_payment.order_id == "order_specific"
        
        not_found = await repository.get_payment_by_order_id("non_existent")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_get_payment_by_stripe_id(self, repository):
        payment = PaymentDB(
            id=uuid4(),
            order_id="order_456",
            user_id="user_123",
            amount=50.0,
            status=PaymentStatus.CREATED,
            stripe_payment_intent_id="pi_123456",
            payment_method_token="pm_456",
            currency="usd"
        )
        
        await repository.create_payment(payment)
        
        retrieved_payment = await repository.get_payment_by_stripe_id("pi_123456")
        assert retrieved_payment is not None
        assert retrieved_payment.stripe_payment_intent_id == "pi_123456"
        
        not_found = await repository.get_payment_by_stripe_id("pi_999999")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_update_payment_status(self, repository):
        payment = PaymentDB(
            id=uuid4(),
            order_id="order_status",
            user_id="user_123",
            amount=75.0,
            status=PaymentStatus.CREATED,
            payment_method_token="pm_789",
            currency="usd"
        )
        
        created_payment = await repository.create_payment(payment)
        assert created_payment.status == PaymentStatus.CREATED
        
        updated_payment = await repository.update_payment_status(payment.id, PaymentStatus.SUCCEEDED)
        assert updated_payment is not None
        assert updated_payment.status == PaymentStatus.SUCCEEDED
        
        retrieved_payment = await repository.get_payment_by_id(payment.id)
        assert retrieved_payment.status == PaymentStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_update_payment_stripe_id(self, repository):
        payment = PaymentDB(
            id=uuid4(),
            order_id="order_stripe",
            user_id="user_123",
            amount=100.0,
            status=PaymentStatus.CREATED,
            payment_method_token="pm_111",
            currency="usd"
        )
        
        created_payment = await repository.create_payment(payment)
        assert created_payment.stripe_payment_intent_id is None
        
        updated_payment = await repository.update_payment_stripe_id(payment.id, "pi_updated")
        assert updated_payment is not None
        assert updated_payment.stripe_payment_intent_id == "pi_updated"

    @pytest.mark.asyncio
    async def test_update_payment_metadata(self, repository):
        payment = PaymentDB(
            id=uuid4(),
            order_id="order_meta",
            user_id="user_123",
            amount=25.0,
            status=PaymentStatus.CREATED,
            payment_method_token="pm_222",
            currency="usd",
            metadata={"old": "data"}
        )
        
        await repository.create_payment(payment)
        
        updated_payment = await repository.update_payment(payment.id, {"metadata": {"new": "data"}})
        assert updated_payment is not None
        assert updated_payment.metadata == {"new": "data"}

    @pytest.mark.asyncio
    async def test_list_payments_by_user(self, repository):
        user_id = "user_multi"
        
        for i in range(3):
            payment = PaymentDB(
                id=uuid4(),
                order_id=f"order_{i}",
                user_id=user_id,
                amount=10.0 * (i + 1),
                status=PaymentStatus.CREATED,
                payment_method_token=f"pm_{i}",
                currency="usd"
            )
            await repository.create_payment(payment)
        
        payments = await repository.list_payments_by_user(user_id, skip=0, limit=10)
        assert len(payments) == 3
        
        payments_paginated = await repository.list_payments_by_user(user_id, skip=1, limit=2)
        assert len(payments_paginated) == 2

    @pytest.mark.asyncio
    async def test_payment_not_found(self, repository):
        non_existent_id = uuid4()
        result = await repository.get_payment_by_id(non_existent_id)
        assert result is None
        
        result = await repository.update_payment_status(non_existent_id, PaymentStatus.SUCCEEDED)
        assert result is None

    @pytest.mark.asyncio
    async def test_payment_timestamps_auto_populated(self, repository):
        payment = PaymentDB(
            id=uuid4(),
            order_id="order_time",
            user_id="user_123",
            amount=99.99,
            status=PaymentStatus.CREATED,
            payment_method_token="pm_time",
            currency="usd"
        )
        
        created_payment = await repository.create_payment(payment)
        assert created_payment.created_at is not None
        assert created_payment.updated_at is not None
        
        await repository.update_payment_status(created_payment.id, PaymentStatus.SUCCEEDED)
        updated_payment = await repository.get_payment_by_id(created_payment.id)
        assert updated_payment.updated_at > created_payment.updated_at

    @pytest.mark.asyncio
    async def test_count_payments(self, repository):
        initial_count = await repository.count_payments()
        
        for i in range(2):
            payment = PaymentDB(
                id=uuid4(),
                order_id=f"order_count_{i}",
                user_id="user_count",
                amount=50.0,
                status=PaymentStatus.CREATED,
                payment_method_token=f"pm_count_{i}",
                currency="usd"
            )
            await repository.create_payment(payment)
        
        final_count = await repository.count_payments()
        assert final_count == initial_count + 2