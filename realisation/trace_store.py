from datetime import datetime, timezone


class TraceStore:
    """Traces limitées à une requête ; aucune persistance des données patient."""

    def __init__(self):
        self.entries = []

    def add(self, method, resource, endpoint, status=None, result="OK", fhir_id=None, detail=""):
        self.entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method, "resource": resource, "endpoint": endpoint,
            "status": status, "result": result, "fhir_id": fhir_id, "detail": detail,
        })

