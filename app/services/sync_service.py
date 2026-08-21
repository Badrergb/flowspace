import logging

logger = logging.getLogger(__name__)


class SyncService:
    """
    With Firestore, real-time sync is handled natively by the client SDK.
    This service is kept as a stub for backward compatibility.
    The actual sync logic lives in app/api/v1/sync.py.
    """

    def __init__(self, db):
        self.db = db

    def process_upload(self, user_id: str, device_id: str, operations: list) -> dict:
        applied = 0
        for op in operations:
            try:
                ref = (
                    self.db.collection("users")
                    .document(user_id)
                    .collection(op.get("collection", "unknown"))
                    .document(op.get("document_id", "unknown"))
                )
                operation = op.get("operation", "set")
                data = op.get("data", {})

                if operation == "delete":
                    ref.delete()
                elif operation == "update":
                    ref.set(data, merge=True)
                else:
                    ref.set(data)

                applied += 1
            except Exception as e:
                logger.error(f"Failed to apply sync op: {e}")

        return {"applied": applied, "total": len(operations)}

    def get_downloads(self, user_id: str, device_id: str, last_sync_version: str) -> dict:
        collections = ["tasks", "habits", "goals", "notes", "journals",
                       "calendar_events", "transactions", "categories"]
        result = {}
        for col in collections:
            try:
                docs = self.db.collection("users").document(user_id).collection(col).stream()
                result[col] = [{**doc.to_dict(), "id": doc.id} for doc in docs]
            except Exception:
                result[col] = []
        return result
