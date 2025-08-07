from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient | None = None
    database = None

db = Database()

async def get_database():
    """Get database instance."""
    return db.database

async def connect_to_mongo():
    """Create database connection."""
    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}...")
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        db.database = db.client[settings.database_name]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Initialize collections
        initialize_collections()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection."""
    try:
        logger.info("Closing MongoDB connection...")
        if db.client:
            db.client.close()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")

async def ping_database():
    """Health check for database connection."""
    try:
        await db.client.admin.command('ping')
        return True
    except Exception:
        return False

# Collections
def get_users_collection():
    """Get users collection."""
    return db.database.users

def get_flashcards_collection():
    """Get flashcards collection."""
    return db.database.flashcards

def get_decks_collection():
    """Get decks collection."""
    return db.database.decks

# Collection instances for easy import
users_collection = None
flashcards_collection = None
decks_collection = None

def initialize_collections():
    """Initialize collection instances after database connection."""
    global users_collection, flashcards_collection, decks_collection
    users_collection = get_users_collection()
    flashcards_collection = get_flashcards_collection()
    decks_collection = get_decks_collection()
