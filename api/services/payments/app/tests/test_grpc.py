import pytest
import grpc
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from protos import payments_pb2
from protos import payments_pb2_grpc

class TestPaymentGRPC:
    @pytest.fixture
    def mock_channel(self):
        return Mock(spec=grpc.Channel)
    
    @pytest.fixture
    def mock_stub(self, mock_channel):
        return payments_pb2_grpc.PaymentServiceStub(mock_channel)
    
    @pytest.fixture
    def create_payment_request(self):
        request = payments_pb2.CreatePaymentRequest(
            order_id="test_order_123",
            user_id="test_user_123",
            amount=99.99,
            payment_method_token="pm_test_123",
            currency="usd"
        )
        return request
    
    @pytest.fixture
    def get_payment_request(self):
        return payments_pb2.GetPaymentRequest(
            payment_id="123e4567-e89b-12d3-a456-426614174000"
        )
    
    @pytest.fixture
    def refund_request(self):
        return payments_pb2.RefundRequest(
            payment_id="123e4567-e89b-12d3-a456-426614174000",
            amount=50.0,
            reason="customer_request"
        )
    
    def test_create_payment_success(self, mock_stub, create_payment_request):
        mock_response = payments_pb2.PaymentResponse(
            payment_id="payment_123",
            order_id="test_order_123",
            user_id="test_user_123",
            amount=99.99,
            status="created",
            stripe_payment_intent_id="pi_123",
            payment_method_token="pm_test_123",
            currency="usd",
            client_secret="cs_test_123"
        )
        
        mock_stub.CreatePayment = Mock(return_value=mock_response)
        
        response = mock_stub.CreatePayment(create_payment_request, timeout=5)
        
        assert response.payment_id == "payment_123"
        assert response.order_id == "test_order_123"
        assert response.status == "created"
        assert response.client_secret == "cs_test_123"
    
    def test_create_payment_failure(self, mock_stub, create_payment_request):
        class MockRpcError(Exception):
            def __init__(self):
                super().__init__("Mock RPC Error")
            
            def code(self):
                return grpc.StatusCode.INTERNAL
            
            def details(self):
                return "Payment creation failed"
        
        mock_stub.CreatePayment = Mock(side_effect=MockRpcError())
        
        with pytest.raises(Exception) as exc_info:
            mock_stub.CreatePayment(create_payment_request, timeout=5)
        
        assert isinstance(exc_info.value, MockRpcError)
        assert exc_info.value.code() == grpc.StatusCode.INTERNAL
        assert "Payment creation failed" in exc_info.value.details()
    
    def test_get_payment_success(self, mock_stub, get_payment_request):
        mock_response = payments_pb2.PaymentResponse(
            payment_id="123e4567-e89b-12d3-a456-426614174000",
            order_id="test_order_123",
            user_id="test_user_123",
            amount=99.99,
            status="succeeded",
            stripe_payment_intent_id="pi_123",
            payment_method_token="pm_test_123",
            currency="usd",
            client_secret="cs_test_123"
        )
        
        mock_stub.GetPayment = Mock(return_value=mock_response)
        
        response = mock_stub.GetPayment(get_payment_request, timeout=5)
        
        assert response.payment_id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.status == "succeeded"
    
    def test_get_payment_not_found(self, mock_stub, get_payment_request):
        class MockRpcError(Exception):
            def __init__(self):
                super().__init__("Mock RPC Error")
            
            def code(self):
                return grpc.StatusCode.NOT_FOUND
            
            def details(self):
                return "Payment not found"
        
        mock_stub.GetPayment = Mock(side_effect=MockRpcError())
        
        with pytest.raises(Exception) as exc_info:
            mock_stub.GetPayment(get_payment_request, timeout=5)
        
        assert isinstance(exc_info.value, MockRpcError)
        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND
        assert "Payment not found" in exc_info.value.details()
    
    def test_process_refund_success(self, mock_stub, refund_request):
        mock_response = payments_pb2.RefundResponse(
            refund_id="re_123",
            status="succeeded",
            amount=50.0,
            currency="usd",
            reason="customer_request"
        )
        
        mock_stub.ProcessRefund = Mock(return_value=mock_response)
        
        response = mock_stub.ProcessRefund(refund_request, timeout=5)
        
        assert response.refund_id == "re_123"
        assert response.status == "succeeded"
        assert response.amount == 50.0
        assert response.reason == "customer_request"
    
    def test_process_refund_failure(self, mock_stub, refund_request):
        class MockRpcError(Exception):
            def __init__(self):
                super().__init__("Mock RPC Error")
            
            def code(self):
                return grpc.StatusCode.INTERNAL
            
            def details(self):
                return "Refund creation failed"
        
        mock_stub.ProcessRefund = Mock(side_effect=MockRpcError())
        
        with pytest.raises(Exception) as exc_info:
            mock_stub.ProcessRefund(refund_request, timeout=5)
        
        assert isinstance(exc_info.value, MockRpcError)
        assert exc_info.value.code() == grpc.StatusCode.INTERNAL
        assert "Refund creation failed" in exc_info.value.details()
    
    def test_create_payment_with_metadata(self, mock_stub):
        request = payments_pb2.CreatePaymentRequest(
            order_id="order_123",
            user_id="user_123",
            amount=100.0,
            payment_method_token="pm_123",
            currency="usd"
        )
        
        mock_response = payments_pb2.PaymentResponse(
            payment_id="payment_123",
            order_id="order_123",
            status="created"
        )
        
        mock_stub.CreatePayment = Mock(return_value=mock_response)
        
        response = mock_stub.CreatePayment(request, timeout=5)
        
        assert response.payment_id == "payment_123"
        assert response.order_id == "order_123"
    
    def test_create_payment_invalid_amount(self, mock_stub):
        request = payments_pb2.CreatePaymentRequest(
            order_id="order_123",
            user_id="user_123",
            amount=0.0,
            payment_method_token="pm_123",
            currency="usd"
        )
        
        class MockRpcError(Exception):
            def __init__(self):
                super().__init__("Mock RPC Error")
            
            def code(self):
                return grpc.StatusCode.INVALID_ARGUMENT
            
            def details(self):
                return "Amount must be greater than 0"
        
        mock_stub.CreatePayment = Mock(side_effect=MockRpcError())
        
        with pytest.raises(Exception) as exc_info:
            mock_stub.CreatePayment(request, timeout=5)
        
        assert isinstance(exc_info.value, MockRpcError)
        assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    
    def test_get_payment_invalid_uuid(self, mock_stub):
        request = payments_pb2.GetPaymentRequest(
            payment_id="invalid-uuid-format"
        )
        
        class MockRpcError(Exception):
            def __init__(self):
                super().__init__("Mock RPC Error")
            
            def code(self):
                return grpc.StatusCode.INVALID_ARGUMENT
            
            def details(self):
                return "Invalid payment ID format"
        
        mock_stub.GetPayment = Mock(side_effect=MockRpcError())
        
        with pytest.raises(Exception) as exc_info:
            mock_stub.GetPayment(request, timeout=5)
        
        assert isinstance(exc_info.value, MockRpcError)
        assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    
    def test_refund_without_amount(self, mock_stub):
        request = payments_pb2.RefundRequest(
            payment_id="123e4567-e89b-12d3-a456-426614174000",
            reason="customer_request"
        )
        
        mock_response = payments_pb2.RefundResponse(
            refund_id="re_123",
            status="succeeded",
            amount=99.99,
            currency="usd",
            reason="customer_request"
        )
        
        mock_stub.ProcessRefund = Mock(return_value=mock_response)
        
        response = mock_stub.ProcessRefund(request, timeout=5)
        
        assert response.refund_id == "re_123"
        assert response.status == "succeeded"
    
    def test_refund_without_reason(self, mock_stub):
        request = payments_pb2.RefundRequest(
            payment_id="123e4567-e89b-12d3-a456-426614174000",
            amount=50.0
        )
        
        mock_response = payments_pb2.RefundResponse(
            refund_id="re_123",
            status="succeeded",
            amount=50.0,
            currency="usd",
            reason=""
        )
        
        mock_stub.ProcessRefund = Mock(return_value=mock_response)
        
        response = mock_stub.ProcessRefund(request, timeout=5)
        
        assert response.refund_id == "re_123"
        assert response.reason == ""