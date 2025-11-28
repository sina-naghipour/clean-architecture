import pytest
from datetime import datetime
from bson import ObjectId

from repositories.product_repository import ProductRepository
from database.database_models import ProductDB


class TestProductRepositoryInMemory:
    
    @pytest.fixture(scope="class")
    def in_memory_db(self):
        """Create an in-memory MongoDB connection using mongomock."""
        try:
            from mongomock import MongoClient
            client = MongoClient()
        except ImportError:
            pytest.skip("mongomock not installed. Run: pip install mongomock")
            return
        
        db = client.test_product_db
        self._setup_test_data(db)
        return db
    
    def _setup_test_data(self, db):
        """Setup initial test data."""
        products_collection = db.products
        
        # Clear any existing data
        products_collection.delete_many({})
        
        # Insert test products
        test_products = [
            {
                "_id": "product_1",
                "name": "Laptop",
                "price": 999.99,
                "stock": 10,
                "description": "High-performance laptop",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": "product_2", 
                "name": "Mouse",
                "price": 29.99,
                "stock": 50,
                "description": "Wireless mouse",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": "product_3",
                "name": "Keyboard",
                "price": 79.99,
                "stock": 25,
                "description": "Mechanical keyboard",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        products_collection.insert_many(test_products)
    
    def test_create_product_success(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        print('Repository type:', type(repository))
        
        new_product = ProductDB(
            name="New Product",
            price=49.99,
            stock=100,
            description="A brand new product"
        )
        result = repository.create_product(new_product)
        
        assert result is not None
        assert result.name == "New Product"
        assert result.price == 49.99
        
        # Verify it was actually saved to database
        saved_product = repository.get_product_by_name("New Product")
        assert saved_product is not None
        assert saved_product.name == "New Product"
    
    def test_create_product_duplicate_name(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        new_product = ProductDB(
            name="Laptop",  # This name already exists
            price=49.99,
            stock=100,
            description="Duplicate product"
        )
        
        result = repository.create_product(new_product)
        
        assert result is None
        
        # Verify no duplicate was created
        products = repository.list_products(search_query="Laptop")
        assert len(products) == 1  # Only the original laptop
    
    def test_get_product_by_id_found(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result = repository.get_product_by_id("product_1")
        
        assert result is not None
        assert result.id == "product_1"
        assert result.name == "Laptop"
        assert result.price == 999.99
    
    def test_get_product_by_id_not_found(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result = repository.get_product_by_id("nonexistent_id")
        
        assert result is None
    
    def test_get_product_by_name_found(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result = repository.get_product_by_name("Mouse")
        
        assert result is not None
        assert result.name == "Mouse"
        assert result.price == 29.99
        assert result.stock == 50
    
    def test_get_product_by_name_not_found(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result = repository.get_product_by_name("Nonexistent Product")
        
        assert result is None
    
    def test_list_products_no_search(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result = repository.list_products(skip=0, limit=10)
        
        assert len(result) == 4
        product_names = [product.name for product in result]
        assert "Laptop" in product_names
        assert "Mouse" in product_names
        assert "Keyboard" in product_names
    
    def test_list_products_with_search(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result = repository.list_products(search_query="wireless")
        
        assert len(result) == 1
        assert result[0].name == "Mouse"
        assert "wireless" in result[0].description.lower()
    
    def test_list_products_pagination(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result_page_1 = repository.list_products(skip=0, limit=2)
        result_page_2 = repository.list_products(skip=2, limit=2)
        
        assert len(result_page_1) == 2
        assert len(result_page_2) == 2
        
        # Verify different products
        page1_names = {product.name for product in result_page_1}
        page2_names = {product.name for product in result_page_2}
        
        assert not page1_names.intersection(page2_names)
    
    def test_count_products(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        count = repository.count_products()
        
        assert count == 4
    
    def test_count_products_with_search(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        count = repository.count_products(search_query="keyboard")
        
        assert count == 1
    
    def test_update_product_success(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        update_data = {
            "name": "Updated Laptop",
            "price": 1099.99,
            "stock": 5
        }
        
        result = repository.update_product("product_1", update_data)
        
        assert result is not None
        assert result.name == "Updated Laptop"
        assert result.price == 1099.99
        assert result.stock == 5
        
        # Verify the update persisted
        updated_product = repository.get_product_by_id("product_1")
        assert updated_product.name == "Updated Laptop"
    
    def test_update_product_name_conflict(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        update_data = {"name": "Mouse"}  # This name already exists for product_2
        
        result = repository.update_product("product_1", update_data)
        
        assert result is None
        
        # Verify product_1 wasn't changed
        product = repository.get_product_by_id("product_1")
        assert product.name != "Mouse"
    
    def test_patch_product(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        patch_data = {"price": 89.99}
        
        result = repository.patch_product("product_2", patch_data)
        
        assert result is not None
        assert result.name == "Mouse"  # Name unchanged
        assert result.price == 89.99   # Price updated
        
        # Verify the patch persisted
        patched_product = repository.get_product_by_id("product_2")
        assert patched_product.price == 89.99
    
    def test_delete_product_success(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        # First verify the product exists
        product = repository.get_product_by_id("product_3")
        assert product is not None
        
        # Delete the product
        result = repository.delete_product("product_3")
        
        assert result is True
        
        # Verify it's gone
        deleted_product = repository.get_product_by_id("product_3")
        assert deleted_product is None
        
        # Verify count decreased
        count = repository.count_products()
        assert count == 3
    
    def test_delete_product_not_found(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result = repository.delete_product("nonexistent_id")
        
        assert result is False
        
        # Verify count unchanged
        count = repository.count_products()
        assert count == 3
    
    def test_update_inventory_success(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        result = repository.update_inventory("product_1", 15)
        
        assert result is not None
        assert result.stock == 15
        
        # Verify the update persisted
        updated_product = repository.get_product_by_id("product_1")
        assert updated_product.stock == 15
    
    def test_update_inventory_no_change(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        # Get current stock
        product = repository.get_product_by_id("product_2")
        original_stock = product.stock
        
        # Update to same value
        result = repository.update_inventory("product_2", original_stock)
        
        assert result is not None
        assert result.stock == original_stock
    
    def test_integration_workflow(self, in_memory_db):
        # Create repository directly in test
        collection = in_memory_db.products
        repository = ProductRepository(collection=collection)
        
        """Test a complete workflow to verify everything works together."""
        # 1. Create a new product
        new_product = ProductDB(
            name="Tablet",
            price=299.99,
            stock=20,
            description="Portable tablet device"
        )
        created = repository.create_product(new_product)
        assert created is not None
        
        # 2. Verify it can be retrieved
        retrieved = repository.get_product_by_id(created.id)
        assert retrieved.name == "Tablet"
        
        # 3. Update the product
        update_result = repository.update_product(
            created.id, 
            {"price": 279.99, "stock": 15}
        )
        assert update_result.price == 279.99
        
        # 4. Search for the product
        search_results = repository.list_products(search_query="tablet")
        assert len(search_results) == 1
        
        # 5. Update inventory
        inventory_result = repository.update_inventory(created.id, 10)
        assert inventory_result.stock == 10
        
        # 6. Delete the product
        delete_result = repository.delete_product(created.id)
        assert delete_result is True
        
        # 7. Verify it's gone
        final_check = repository.get_product_by_id(created.id)
        assert final_check is None