import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from sqlalchemy.exc import SQLAlchemyError
from repositories.payments_repository import PaymentRepository
from database.database_models import PaymentDB, PaymentStatus

class TestPaymentRepository:
    @pytest.fixture
    def mock_session(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_logger(self):
        return Mock()
    
    @pytest.fixture
    def repository(self, mock_session, mock_logger):
        return PaymentRepository(mock_session, mock_logger)
    
    @pytest.fixture
    def sample_payment(self):
        return PaymentDB(
            id=uuid4(),
            order_id="order_123",
            user_id="user_123",
            amount=99.99,
            status=PaymentStatus.CREATED,
            payment_method_token="pm_tok_abc",
            currency="usd"
        )

    @pytest.mark.asyncio
    async def test_create_payment_success(self, repository, mock_session, mock_logger, sample_payment):
        result = await repository.create_payment(sample_payment)
        
        assert result == sample_payment
        mock_session.add.assert_called_once_with(sample_payment)
        mock_session.refresh.assert_called_once_with(sample_payment)
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_create_payment_failure(self, repository, mock_session, mock_logger, sample_payment):
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.create_payment(sample_payment)
        
        mock_session.rollback.assert_called_once()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_payment_by_id_found(self, repository, mock_session, mock_logger, sample_payment):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_payment
        
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_payment_by_id(sample_payment.id)
        
        assert result == sample_payment
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_payment_by_id_not_found(self, repository, mock_session, mock_logger):
        payment_id = uuid4()
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_payment_by_id(payment_id)
        
        assert result is None
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_payment_by_order_id_found(self, repository, mock_session, mock_logger, sample_payment):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_payment
        
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_payment_by_order_id("order_123")
        
        assert result == sample_payment
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_payment_by_order_id_not_found(self, repository, mock_session, mock_logger):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_payment_by_order_id("order_999")
        
        assert result is None
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_payment_by_stripe_id_found(self, repository, mock_session, mock_logger, sample_payment):
        sample_payment.stripe_payment_intent_id = "pi_123"
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_payment
        
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_payment_by_stripe_id("pi_123")
        
        assert result == sample_payment
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_payment_by_stripe_id_not_found(self, repository, mock_session, mock_logger):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        result = await repository.get_payment_by_stripe_id("pi_999")
        
        assert result is None
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_payment_status_success(self, repository, mock_session, mock_logger, sample_payment):
        mock_update_result = Mock()
        mock_update_result.rowcount = 1
        
        updated_payment = PaymentDB(
            id=sample_payment.id,
            order_id=sample_payment.order_id,
            user_id=sample_payment.user_id,
            amount=sample_payment.amount,
            status=PaymentStatus.SUCCEEDED,
            payment_method_token=sample_payment.payment_method_token,
            currency=sample_payment.currency
        )
        
        mock_get_result = Mock()
        mock_get_result.scalar_one_or_none.return_value = updated_payment
        
        mock_session.execute.side_effect = [mock_update_result, mock_get_result]
        
        result = await repository.update_payment_status(sample_payment.id, PaymentStatus.SUCCEEDED)
        
        assert result.status == PaymentStatus.SUCCEEDED
        assert mock_session.execute.call_count == 2
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_payment_status_not_found(self, repository, mock_session, mock_logger):
        payment_id = uuid4()
        
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        result = await repository.update_payment_status(payment_id, PaymentStatus.SUCCEEDED)
        
        assert result is None
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_payment_status_failure(self, repository, mock_session, mock_logger):
        payment_id = uuid4()
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.update_payment_status(payment_id, PaymentStatus.SUCCEEDED)
        
        mock_session.rollback.assert_called_once()
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_payment_stripe_id_success(self, repository, mock_session, mock_logger, sample_payment):
        mock_update_result = Mock()
        mock_update_result.rowcount = 1
        
        updated_payment = PaymentDB(
            id=sample_payment.id,
            order_id=sample_payment.order_id,
            user_id=sample_payment.user_id,
            amount=sample_payment.amount,
            status=sample_payment.status,
            stripe_payment_intent_id="pi_123",
            payment_method_token=sample_payment.payment_method_token,
            currency=sample_payment.currency
        )
        
        mock_get_result = Mock()
        mock_get_result.scalar_one_or_none.return_value = updated_payment
        
        mock_session.execute.side_effect = [mock_update_result, mock_get_result]
        
        result = await repository.update_payment_stripe_id(sample_payment.id, "pi_123")
        
        assert result.stripe_payment_intent_id == "pi_123"
        assert mock_session.execute.call_count == 2
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_payment_stripe_id_not_found(self, repository, mock_session, mock_logger):
        payment_id = uuid4()
        
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        result = await repository.update_payment_stripe_id(payment_id, "pi_123")
        
        assert result is None
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_update_payment_stripe_id_failure(self, repository, mock_session, mock_logger):
        payment_id = uuid4()
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.update_payment_stripe_id(payment_id, "pi_123")
        
        mock_session.rollback.assert_called_once()
        mock_logger.error.assert_called_once()


    @pytest.mark.asyncio
    async def test_list_payments_by_user_success(self, repository, mock_session, mock_logger, sample_payment):
        mock_scalars = Mock()
        mock_scalars.all.return_value = [sample_payment]
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.list_payments_by_user("user_123", skip=0, limit=10)
        
        assert len(result) == 1
        assert result[0] == sample_payment
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_list_payments_by_user_empty(self, repository, mock_session, mock_logger):
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.list_payments_by_user("user_999")
        
        assert len(result) == 0
        mock_session.execute.assert_called_once()
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_count_payments_success(self, repository, mock_session, mock_logger, sample_payment):
        mock_scalars = Mock()
        mock_scalars.all.return_value = [sample_payment, sample_payment]
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.count_payments()
        
        assert result == 2
        mock_session.execute.assert_called_once()
        mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_count_payments_empty(self, repository, mock_session, mock_logger):
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result
        
        result = await repository.count_payments()
        
        assert result == 0
        mock_session.execute.assert_called_once()
        mock_logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_count_payments_failure(self, repository, mock_session, mock_logger):
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            await repository.count_payments()
        
        mock_logger.error.assert_called_once()