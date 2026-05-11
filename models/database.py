from pymongo import MongoClient
from config.settings import Config
from datetime import datetime, timezone
import json

# Global client
client = None
db = None

def get_db():
    global client, db
    if client is None:
        client = MongoClient(Config.MONGO_URI)
        db = client[Config.MONGO_DB_NAME]
    return db

def init_db():
    get_db()
    # Create indexes if necessary
    db.users.create_index("username", unique=True)
    db.evaluations.create_index("created_at")

def close_db():
    global client
    if client:
        client.close()
        client = None

# Helper classes to simulate the ORM-like structure for the services
class EvaluationModel:
    def __init__(self, **kwargs):
        self._data = kwargs
        if "created_at" not in self._data:
            self._data["created_at"] = datetime.now(timezone.utc).isoformat()
        if "updated_at" not in self._data:
            self._data["updated_at"] = self._data["created_at"]
        if "version" not in self._data:
            self._data["version"] = 1
            
    def save(self):
        db = get_db()
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if "_id" in self._data:
            db.evaluations.update_one({"_id": self._data["_id"]}, {"$set": self._data})
        else:
            result = db.evaluations.insert_one(self._data)
            self._data["_id"] = result.inserted_id
        return str(self._data["_id"])
        
    def to_dict(self):
        d = dict(self._data)
        if "_id" in d:
            d["id"] = str(d["_id"])
            del d["_id"]
        return d
        
    def to_summary(self):
        d = self.to_dict()
        return {
            "id": d.get("id"),
            "candidate_filename": d.get("candidate_filename"),
            "ats_score": d.get("ats_score"),
            "version": d.get("version"),
            "has_optimized_resume": d.get("optimized_resume_text") is not None,
            "created_at": d.get("created_at"),
            "updated_at": d.get("updated_at"),
        }
        
    def to_full(self):
        d = self.to_summary()
        d["evaluation"] = json.loads(self._data.get("raw_json_data", "{}"))
        d["job_description"] = self._data.get("job_description")
        return d

    @classmethod
    def get_by_id(cls, eval_id):
        from bson.objectid import ObjectId
        db = get_db()
        try:
            doc = db.evaluations.find_one({"_id": ObjectId(eval_id)})
            if doc:
                return cls(**doc)
        except Exception:
            pass
        return None

class EvaluationVersionModel:
    def __init__(self, **kwargs):
        self._data = kwargs
        if "created_at" not in self._data:
            self._data["created_at"] = datetime.now(timezone.utc).isoformat()
            
    def save(self):
        db = get_db()
        result = db.evaluation_versions.insert_one(self._data)
        self._data["_id"] = result.inserted_id
        return str(self._data["_id"])
        
    def to_dict(self):
        d = dict(self._data)
        if "_id" in d:
            d["id"] = str(d["_id"])
            del d["_id"]
        if "evaluation_id" in d and not isinstance(d["evaluation_id"], str):
            d["evaluation_id"] = str(d["evaluation_id"])
            
        return {
            "id": d.get("id"),
            "evaluation_id": d.get("evaluation_id"),
            "version": d.get("version"),
            "candidate_filename": d.get("candidate_filename"),
            "ats_score": d.get("ats_score"),
            "evaluation": json.loads(d.get("raw_json_data", "{}")),
            "job_description": d.get("job_description"),
            "created_at": d.get("created_at"),
        }
