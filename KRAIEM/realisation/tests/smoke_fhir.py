"""Test réel explicite : crée uniquement des Encounter pour les Patients fictifs fournis."""
import argparse
import json
from datetime import datetime, timezone
from uuid import uuid4
import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patient-ids", nargs="+", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    with httpx.Client(base_url=args.base_url, timeout=180) as client:
        def call(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            data = response.json()
            if not response.is_success or not data.get("ok"):
                raise RuntimeError(json.dumps(data, ensure_ascii=True))
            return data
        health = call("GET", "/api/health")
        assert health["server"]["fhirVersion"] == "4.0.1"
        absent = call("GET", "/api/patients/search", params={"identifier":"ABSENT-" + uuid4().hex})
        assert absent["total"] == 0
        report = {"server":health["server"]["base_url"], "version":"4.0.1", "absent_search":True, "admissions":[]}
        for index, patient_id in enumerate(args.patient_ids, 1):
            patient = call("GET", "/api/patients/" + patient_id)["patient"]
            assert any("test" in str(name).lower() or "demo" in str(name).lower()
                       for name in patient.get("name", [])), "Utiliser un Patient explicitement fictif."
            identifier = next((x for x in patient.get("identifier", []) if x.get("value")), None)
            assert identifier, "Choisir un patient avec identifiant métier pour le scénario nominal."
            found = call("GET", "/api/patients/search", params={
                "identifier": identifier["value"], "system":identifier.get("system","")})
            assert patient_id in [p["id"] for p in found["patients"]]
            start = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            result = call("POST", "/api/admissions", json={
                "patient_id":patient_id, "identifier_system":identifier.get("system",""),
                "identifier_value":identifier["value"], "admission_time":start,
                "service":"Service démonstration " + str(index), "room":str(index), "bed":"TEST",
            })
            encounter = result["encounter"]
            assert encounter["subject"]["reference"] == "Patient/" + patient_id
            assert encounter["status"] == "in-progress"
            assert encounter["class"]["code"] == "IMP"
            reread = call("GET", "/api/encounters/" + encounter["id"])["encounter"]
            assert reread == encounter
            parts = {s.split("|")[0]:s.split("|") for s in result["message"].strip("\r").split("\r")}
            assert parts["MSH"][8] == "ADT^A01^ADT_A01"
            assert parts["PV1"][2] == "I"
            assert parts["PV1"][19] == encounter["identifier"][0]["value"]
            assert parts["PV1"][44] == parts["EVN"][2]
            assert result["complete"], result["warnings"]
            assert any(t["method"] == "POST" and t["status"] == 201 for t in result["traces"])
            assert not any(t["method"] in {"PUT","DELETE"} or
                           (t["method"] == "POST" and t["resource"] == "Patient") for t in result["traces"])
            report["admissions"].append({"patient_id":patient_id,"encounter_id":encounter["id"],
                                        "message_id":result["message_id"],"mapping_complete":result["complete"],
                                        "trace_count":len(result["traces"])})
            print(json.dumps(report["admissions"][-1]), flush=True)
        missing = client.get("/api/patients/absent-" + uuid4().hex)
        data = missing.json()
        assert missing.status_code == 404 and not data["ok"]
        assert data["issues"], "OperationOutcome réel attendu pour la lecture inexistante."
        report["operation_outcome_404"] = True
        print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()

