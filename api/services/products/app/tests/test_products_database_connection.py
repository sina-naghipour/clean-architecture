import asyncio
import logging
from database.connection import MongoDBConnection, get_products_collection

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test basic connection functionality"""
    connection = MongoDBConnection()
    
    try:
        print("Testing MongoDB connection...")
        await connection.connect()
        print("✓ Connection successful")
        
        collection = connection.get_collection()
        print(f"✓ Collection retrieved: {collection}")
        
        result = await collection.find_one()
        print(f"✓ Basic find_one operation worked: {result is not None}")
        
        await connection.close()
        print("✓ Connection closed properly")
        
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False
    
    return True

async def test_get_products_collection():
    """Test the helper function"""
    try:
        print("\nTesting get_products_collection...")
        collection = await get_products_collection()
        print(f"✓ get_products_collection worked: {collection}")
        
        # Test count as a simple operation
        count = await collection.count_documents({})
        print(f"✓ Collection count: {count}")
        
        return True
    except Exception as e:
        print(f"✗ get_products_collection failed: {e}")
        return False

async def test_index_operations():
    """Test that indexes are working"""
    connection = MongoDBConnection()
    
    try:
        await connection.connect()
        collection = connection.get_collection()
        
        # List indexes to verify they were created
        indexes = await collection.list_indexes().to_list(length=None)
        print(f"\n✓ Indexes found: {len(indexes)}")
        for idx in indexes:
            print(f"  - {idx['name']}")
            
        await connection.close()
        return True
    except Exception as e:
        print(f"✗ Index test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Starting async MongoDB tests...")
    
    tests = [
        test_connection(),
        test_get_products_collection(),
        test_index_operations()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print(f"\n=== Test Results ===")
    for i, result in enumerate(results):
        test_name = ["Connection", "Get Collection", "Indexes"][i]
        status = "PASS" if result is True else "FAIL"
        print(f"{test_name}: {status}")
    
    if all(results):
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())