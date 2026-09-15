from copy import deepcopy
import httpx
from fastapi.testclient import TestClient
import main
from fhir_client import FhirClient
from test_hl7_mapper import P

CAPABILITY = {"resourceType":"CapabilityStatement","fhirVersion":"4.0.1","rest":[{"mode":"server","resource":[
    {"type":"Patient","interaction":[{"code":"read"},{"code":"search-type"}],
     "searchParam":[{"name":"identifier"},{"name":"name"}]},
    {"type":"Encounter","interaction":[{"code":"create"},{"code":"read"}]}]}]}
PAYLOAD = {"patient_id":"test-p","admission_time":"2026-09-15T14:00:00+02:00",
           "identifier_system":"urn:test","identifier_value":"PAT-TEST-01"}


def setup_client(monkeypatch, patient=None, fail_create=False):
    calls, encounters = [], []
    def handler(request):
        calls.append((request.method,request.url.path))
        path = request.url.path
        if path.endswith("/metadata"):
            return httpx.Response(200,json=CAPABILITY)
        if path.endswith("/Patient/test-p"):
            return httpx.Response(200,json=patient or P)
        if request.method == "POST":
            if fail_create:
                return httpx.Response(400,json={"resourceType":"OperationOutcome","issue":[
                    {"severity":"error","code":"invalid","diagnostics":"Admission refusée"}]})
            import json
            saved = json.loads(request.content)
            saved["id"] = "enc-test"
            saved["meta"] = {"versionId":"1"}
            encounters.append(saved)
            return httpx.Response(201,json=saved)
        if path.endswith("/Encounter/enc-test"):
            return httpx.Response(200,json=encounters[-1])
        raise AssertionError(str(request.url))
    monkeypatch.setattr(main, "FhirClient", lambda trace:FhirClient(trace,httpx.MockTransport(handler)))
    return TestClient(main.app),calls


def test_admission_roundtrip(monkeypatch):
    client,calls = setup_client(monkeypatch)
    response = client.post("/api/admissions",json=PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert data["complete"] and data["admission_recorded"]
    assert data["encounter"]["meta"]["versionId"] == "1"
    assert data["encounter"]["subject"]["reference"] == "Patient/test-p"
    assert len([x for x in calls if x[0] == "POST"]) == 1
    assert calls[-1][1].endswith("/Encounter/enc-test")


def test_refused_encounter_is_error(monkeypatch):
    client,calls = setup_client(monkeypatch,fail_create=True)
    response = client.post("/api/admissions",json=PAYLOAD)
    assert response.status_code == 400
    assert not response.json()["ok"]
    assert response.json()["traces"][-1]["result"] == "ERREUR"


def test_other_does_not_prevent_admission(monkeypatch):
    p = deepcopy(P); p["gender"] = "other"
    client,calls = setup_client(monkeypatch,patient=p)
    data = client.post("/api/admissions",json=PAYLOAD).json()
    assert data["admission_recorded"] and not data["complete"]
    assert next(r for r in data["mapping"] if r["destination"] == "PID-8")["target"] == ""


def test_invalid_form_never_posts(monkeypatch):
    client,calls = setup_client(monkeypatch)
    response = client.post("/api/admissions",json={**PAYLOAD,"admission_time":"2026-09-15T14:00:00"})
    assert response.status_code == 422
    assert calls == []


def test_no_patient_creation_route(monkeypatch):
    client,_ = setup_client(monkeypatch)
    assert client.post("/api/patients",json={}).status_code == 404


