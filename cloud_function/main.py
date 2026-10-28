import base64, json, logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cit-event-consumer")

def handle_incident_event(cloud_event):
    """Cloud Functions event handler for Pub/Sub messages."""
    message = (cloud_event.data or {}).get("message", {})
    encoded = message.get("data")
    if not encoded:
        logger.warning("Pub/Sub event has no data")
        return
    try:
        event = json.loads(base64.b64decode(encoded).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        logger.exception("Could not decode incident event payload")
        return
    logger.info("received_incident_event type=%s", event.get("event","unknown"))
