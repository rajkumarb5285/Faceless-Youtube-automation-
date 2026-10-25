import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Redis Client
try:
    import redis
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis successfully.")
except Exception as e:
    class SimpleMemoryRedis:
        def __init__(self):
            self.data = {}
        def get(self, k):
            return self.data.get(k)
        def set(self, k, v):
            self.data[k] = v
        def setex(self, k, ttl, v):
            self.data[k] = v
        def ping(self):
            return True
    redis_client = SimpleMemoryRedis()

# MongoDB Client
try:
    from pymongo import MongoClient
    mongo_client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
    mongo_client.server_info()
    db = mongo_client.get_database()
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    import json
    import os

    DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "local_db.json")

    def _load_store():
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_store(store):
        try:
            os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(store, f, indent=2)
        except Exception:
            pass

    class MemoryCollection:
        def __init__(self, name="coll"):
            self.name = name
            store = _load_store()
            self.docs = store.get(self.name, [])

        def _persist(self):
            store = _load_store()
            store[self.name] = self.docs
            _save_store(store)

        def find_one(self, q):
            for d in self.docs:
                if all(d.get(k) == v for k, v in q.items()):
                    return d
            return None

        def find(self, q=None):
            class Cursor:
                def __init__(self, items):
                    self.items = items
                def sort(self, *args, **kwargs):
                    return self
                def limit(self, n):
                    return self.items[:n]
                def __iter__(self):
                    return iter(self.items)
            return Cursor(self.docs)

        def insert_one(self, d):
            doc = dict(d)
            self.docs.append(doc)
            self._persist()
            return doc

        def update_one(self, q, u, upsert=False):
            doc = self.find_one(q)
            if doc:
                if "$set" in u:
                    doc.update(u["$set"])
                self._persist()
            elif upsert:
                new_doc = dict(q)
                if "$set" in u:
                    new_doc.update(u["$set"])
                self.docs.append(new_doc)
                self._persist()

    class MemoryDB:
        def __init__(self):
            self.channels = MemoryCollection("channels")
            self.topics = MemoryCollection("topics")
            self.jobs = MemoryCollection("jobs")
            self.research_notes = MemoryCollection("research_notes")
            self.claims = MemoryCollection("claims")
            self.scripts = MemoryCollection("scripts")
            self.renders = MemoryCollection("renders")
            self.publications = MemoryCollection("publications")
            self.metrics = MemoryCollection("metrics")
            self.analytics = MemoryCollection("analytics")
            self.settings = MemoryCollection("settings")

        def __getattr__(self, name):
            coll = MemoryCollection(name)
            setattr(self, name, coll)
            return coll

    db = MemoryDB()

    # Pre-seed existing completed job if found on disk
    if not db.jobs.find_one({"_id": "job_33e305001d"}):
        if os.path.exists(os.path.join(settings.STORAGE_DIR, "job_33e305001d", "final.mp4")):
            db.jobs.insert_one({
                "_id": "job_33e305001d",
                "channel_id": "default",
                "status": "completed",
                "current_node": "publisher",
                "custom_topic": "How One Accidental Bug Almost Destroyed Wall Street",
                "story_style": "cartoon_story"
            })

# Ensure default channel exists
if not db.channels.find_one({"_id": "default"}):
    from app.schemas import ChannelProfile
    default_chan = ChannelProfile().model_dump(by_alias=True)
    db.channels.insert_one(default_chan)

# Qdrant Client
try:
    from qdrant_client import QdrantClient
    qdrant_client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
except Exception:
    qdrant_client = None
