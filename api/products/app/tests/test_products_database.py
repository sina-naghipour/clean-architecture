import pytest
import datetime
from database.database_models import ProductDB

class TestProductDBModel:
    
    def test_product_creation(self):
        product = ProductDB(
            name="Test Product",
            price=29.99,
            stock=100,
            description="Test description"
        )

        assert product.name == "Test Product"
        assert product.price == 29.99
        assert product.stock == 100
        assert product.description == "Test description"
        assert product.id is not None
    
    def test_product_to_dict(self):
        product = ProductDB(
            name="Test Product",
            price=29.99,
            stock=100
        )
        
        product_dict = product.to_dict()
        
        assert product_dict["_id"] == product.id
        assert product_dict["name"] == "Test Product"
        assert product_dict["price"] == 29.99
        assert product_dict["stock"] == 100
    
    def test_product_from_dict(self):
        product_data = {
            "_id": "test-id-123",
            "name": "Test Product",
            "price": 29.99,
            "stock": 100,
            "description": "Test description"
        }
        
        product = ProductDB.from_dict(product_data)
        
        assert product.id == "test-id-123"
        assert product.name == "Test Product"
        assert product.price == 29.99
        assert product.stock == 100

    def test_product_with_minimal_data(self):
        product = ProductDB(
            name="Minimal Product",
            price=10.0,
            stock=0
        )
        
        assert product.name == "Minimal Product"
        assert product.price == 10.0
        assert product.stock == 0
        assert product.description is None

    def test_product_dict_round_trip(self):
        original = ProductDB(
            name="Round Trip Product",
            price=15.50,
            stock=25,
            description="Test round trip"
        )
        
        data = original.to_dict()
        
        restored = ProductDB.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.price == original.price
        assert restored.stock == original.stock

    def test_product_collection_name(self):
        assert ProductDB.COLLECTION_NAME == "products"
        assert isinstance(ProductDB.COLLECTION_NAME, str)

def test_basic_connection_import():
    from database.connection import MongoDBConnection
    connection = MongoDBConnection()
    assert connection.client is None
    assert connection.db is None