import os, uuid, logging, json
from datetime import datetime, timezone
from flask import Flask, jsonify, request

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("cit")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_STATUSES = {"open", "in_progress", "resolved", "closed"}
INCIDENTS = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def validate(payload, partial=False):
    if not isinstance(payload, dict):
        return "JSON request body must be an object."
    if not partial:
        for field in ("title", "description"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                return f"'{field}' is required and must be a non-empty string."
    for field in ("title", "description"):
        if field in payload and (not isinstance(payload[field], str) or not payload[field].strip()):
            return f"'{field}' must be a non-empty string."
    if "severity" in payload and payload["severity"] not in VALID_SEVERITIES:
        return "Invalid severity. Use low, medium, high, or critical."
    if "status" in payload and payload["status"] not in VALID_STATUSES:
        return "Invalid status. Use open, in_progress, resolved, or closed."
    return None

class MemoryStore:
    def get(self, key): return INCIDENTS.get(key)
    def list(self): return list(INCIDENTS.values())
    def put(self, key, value): INCIDENTS[key] = value
    def delete(self, key): INCIDENTS.pop(key, None)

class FirestoreStore:
    def __init__(self):
        from google.cloud import firestore
        self.collection = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT")).collection(os.getenv("FIRESTORE_COLLECTION", "incidents"))
    def get(self, key):
        snap = self.collection.document(key).get()
        return snap.to_dict() if snap.exists else None
    def list(self): return [doc.to_dict() for doc in self.collection.stream()]
    def put(self, key, value): self.collection.document(key).set(value)
    def delete(self, key): self.collection.document(key).delete()

def get_store():
    return FirestoreStore() if os.getenv("USE_FIRESTORE", "false").lower() == "true" else MemoryStore()

def publish_event(event):
    topic, project = os.getenv("PUBSUB_TOPIC"), os.getenv("GOOGLE_CLOUD_PROJECT")
    if not topic or not project: return
    try:
        from google.cloud import pubsub_v1
        publisher = pubsub_v1.PublisherClient()
        publisher.publish(publisher.topic_path(project, topic), json.dumps(event).encode("utf-8"))
    except Exception:
        logger.exception("Pub/Sub publish failed; incident operation remains saved")

@app.get("/health")
def health():
    return jsonify({"status":"ok", "service":"cloud-incident-tracker"}), 200

@app.post("/incidents")
def create_incident():
    payload = request.get_json(silent=True)
    error = validate(payload)
    if error: return jsonify({"error":error}), 400
    store, incident_id = get_store(), str(uuid.uuid4())
    incident = {"id":incident_id, "title":payload["title"].strip(), "description":payload["description"].strip(),
                "severity":payload.get("severity","medium"), "status":payload.get("status","open"),
                "reported_by":payload.get("reported_by","unknown"), "created_at":now_iso(), "updated_at":now_iso()}
    store.put(incident_id, incident)
    publish_event({"event":"incident.created", "incident":incident})
    logger.info("incident_created id=%s severity=%s", incident_id, incident["severity"])
    return jsonify(incident), 201

@app.get("/incidents")
def list_incidents():
    return jsonify({"incidents":get_store().list()}), 200

@app.get("/incidents/<incident_id>")
def get_incident(incident_id):
    incident = get_store().get(incident_id)
    if not incident: return jsonify({"error":"Incident not found."}), 404
    return jsonify(incident), 200

@app.patch("/incidents/<incident_id>")
def update_incident(incident_id):
    payload = request.get_json(silent=True)
    error = validate(payload, partial=True)
    if error: return jsonify({"error":error}), 400
    store, incident = get_store(), get_store().get(incident_id)
    if not incident: return jsonify({"error":"Incident not found."}), 404
    for field in ("title","description","severity","status","reported_by"):
        if field in payload: incident[field] = payload[field].strip() if isinstance(payload[field], str) else payload[field]
    incident["updated_at"] = now_iso()
    store.put(incident_id, incident)
    publish_event({"event":"incident.updated","incident":incident})
    logger.info("incident_updated id=%s status=%s", incident_id, incident["status"])
    return jsonify(incident), 200

@app.delete("/incidents/<incident_id>")
def delete_incident(incident_id):
    store = get_store()
    if not store.get(incident_id): return jsonify({"error":"Incident not found."}), 404
    store.delete(incident_id)
    publish_event({"event":"incident.deleted","incident_id":incident_id})
    logger.info("incident_deleted id=%s", incident_id)
    return jsonify({"message":"Incident deleted.","id":incident_id}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","8080")), debug=False)
