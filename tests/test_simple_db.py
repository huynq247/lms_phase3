"""
Simple database test with real database connection.
"""
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


@pytest.mark.asyncio
async def test_direct_database_connection():
    """Test direct database connection."""
    # Connect to real database
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    
    try:
        # Test ping
        result = await database.command("ping")
        assert result["ok"] == 1.0
        print(f"✅ Database ping successful to {settings.database_name}")
        
        # Test database info
        stats = await database.command("dbstats")
        print(f"📊 Database: {stats['db']}")
        print(f"📚 Collections: {stats.get('collections', 0)}")
        print(f"💾 Data size: {stats.get('dataSize', 0)} bytes")
        
        # Test listing collections
        collections = await database.list_collection_names()
        print(f"📋 Existing collections: {collections}")
        
        # Test creating a test document
        test_collection = database["test_simple"]
        test_doc = {"message": "Hello database!", "test": True}
        
        result = await test_collection.insert_one(test_doc)
        print(f"✅ Inserted test document: {result.inserted_id}")
        
        # Verify document
        found = await test_collection.find_one({"_id": result.inserted_id})
        assert found["message"] == "Hello database!"
        print("✅ Document verification successful")
        
        # Cleanup
        await test_collection.delete_one({"_id": result.inserted_id})
        print("🧹 Test document cleaned up")
        
    finally:
        client.close()


@pytest.mark.asyncio
async def test_database_operations():
    """Test basic database operations."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    collection = database["test_operations"]
    
    try:
        # Insert multiple documents
        docs = [
            {"name": "Test 1", "value": 100},
            {"name": "Test 2", "value": 200},
            {"name": "Test 3", "value": 300}
        ]
        
        result = await collection.insert_many(docs)
        assert len(result.inserted_ids) == 3
        print(f"✅ Inserted {len(result.inserted_ids)} documents")
        
        # Query documents
        found_docs = await collection.find({"value": {"$gte": 200}}).to_list(length=None)
        assert len(found_docs) == 2
        print(f"✅ Found {len(found_docs)} documents with value >= 200")
        
        # Update document
        update_result = await collection.update_one(
            {"name": "Test 1"},
            {"$set": {"value": 150}}
        )
        assert update_result.modified_count == 1
        print("✅ Document update successful")
        
        # Verify update
        updated = await collection.find_one({"name": "Test 1"})
        assert updated["value"] == 150
        print("✅ Update verification successful")
        
        # Count documents
        count = await collection.count_documents({})
        assert count == 3
        print(f"✅ Document count: {count}")
        
    finally:
        # Cleanup
        await collection.delete_many({})
        print("🧹 All test documents cleaned up")
        client.close()


@pytest.mark.asyncio 
async def test_database_configuration():
    """Test database configuration."""
    print(f"🔧 MongoDB URL: {settings.mongodb_url[:30]}...")
    print(f"🗄️ Database name: {settings.database_name}")
    print(f"🔐 Secret key length: {len(settings.secret_key)}")
    print(f"⚙️ Algorithm: {settings.algorithm}")
    
    assert settings.mongodb_url is not None
    assert settings.database_name is not None
    assert len(settings.secret_key) > 10
    print("✅ All configuration checks passed")
