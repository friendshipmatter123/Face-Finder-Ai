"""MongoDB client and database dependency."""
from pymongo import ASCENDING, DESCENDING, MongoClient
from config import MONGODB_URL, MONGODB_DATABASE


client = MongoClient(
    MONGODB_URL,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    appname="facefind-api",
)
database = client[MONGODB_DATABASE]


def get_db():
    """FastAPI dependency returning the shared MongoDB database."""
    yield database


def init_db():
    """Verify MongoDB and create indexes used by the API."""
    client.admin.command("ping")
    database.admins.create_index([("email", ASCENDING)], unique=True)
    database.events.create_index([("event_code", ASCENDING)], unique=True)
    database.events.create_index([("admin_id", ASCENDING), ("created_at", DESCENDING)])
    database.photos.create_index([("event_id", ASCENDING), ("created_at", DESCENDING)])
    database.face_encodings.create_index([("event_id", ASCENDING)])
    database.face_registrations.create_index([("registration_id", ASCENDING)], unique=True)
    database.face_registration_encodings.create_index([("registration_id", ASCENDING)])


def close_db():
    client.close()
