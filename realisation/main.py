from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from config import ENCOUNTER_IDENTIFIER_SYSTEM
from fhir_client import FhirClient, FhirError
from hl7_mapper import map_to_hl7, location_parts, select_identifier
from schemas import AdmissionRequest
from trace_store import TraceStore

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="Admission patient — FHIR R4 → HL7 v2.5.1")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.middleware("http")
async def trace_request(request: Request, call_next):
    request.state.trace = TraceStore()
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(FhirError)
async def fhir_error(request, exc):
    return JSONResponse(status_code=exc.status, content={
        "ok": False, "message": str(exc), "issues": exc.issues,
        "traces": request.state.trace.entries,
    })


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(status_code=422, content={
        "ok": False, "message": "Saisie invalide : " + "; ".join(
            ".".join(str(x) for x in e["loc"]) + " — " + e["msg"] for e in exc.errors()),
        "traces": request.state.trace.entries,
    })


@app.get("/")
async def index():
    return FileResponse(ROOT / "templates" / "index.html")


@app.get("/api/health")
async def health(request: Request):
    async with FhirClient(request.state.trace) as client:
        server = await client.check_server()
    return {"ok": True, "server": server, "traces": request.state.trace.entries}


@app.get("/api/patients/search")
async def search(request: Request, identifier: str = Query("", max_length=200),
                 system: str = Query("", max_length=500), name: str = Query("", max_length=120)):
    async with FhirClient(request.state.trace) as client:
        await client.check_server()
        patients = await client.search_patient(identifier.strip(), system.strip(), name.strip())
    return {"ok": True, "patients": patients, "total": len(patients), "traces": request.state.trace.entries}


@app.get("/api/patients/{fhir_id}")
async def patient(request: Request, fhir_id: str):
    async with FhirClient(request.state.trace) as client:
        await client.check_server()
        data = await client.get_patient(fhir_id)
    return {"ok": True, "patient": data, "traces": request.state.trace.entries}


@app.get("/api/encounters/{fhir_id}")
async def encounter(request: Request, fhir_id: str):
    async with FhirClient(request.state.trace) as client:
        await client.check_server()
        data = await client.get_encounter(fhir_id)
    return {"ok": True, "encounter": data, "traces": request.state.trace.entries}


@app.post("/api/admissions")
async def admit(request: Request, data: AdmissionRequest):
    trace = request.state.trace
    async with FhirClient(trace) as client:
        await client.check_server()
        p = await client.get_patient(data.patient_id)
        if data.identifier_value and not select_identifier(p, data.identifier_system, data.identifier_value):
            raise FhirError("L’identifiant sélectionné ne correspond plus au Patient relu.", 409)
        payload = {
            "resourceType": "Encounter", "status": "in-progress",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                      "code": "IMP", "display": "inpatient encounter"},
            "subject": {"reference": "Patient/" + p["id"]},
            "period": {"start": data.admission_time.isoformat()},
            "identifier": [{"system": ENCOUNTER_IDENTIFIER_SYSTEM, "value": "ADM-" + str(uuid4())}],
        }
        if data.service:
            payload["location"] = [{"location": {"display":
                f"{data.service} / Chambre {data.room} / Lit {data.bed}"}}]
        e = await client.create_encounter(payload)
        try:
            e = await client.get_encounter(e["id"])
        except FhirError as exc:
            raise FhirError(f"Encounter/{e['id']} a été créé, mais la relecture a échoué. "
                            "Vérifier cet identifiant avant toute nouvelle admission. " + str(exc),
                            exc.status, exc.issues)
        if e.get("subject", {}).get("reference") != "Patient/" + p["id"] or e.get("status") != "in-progress":
            raise FhirError("Encounter créé mais référence ou statut inattendu ; vérifier Encounter/" + e["id"])
    mapped = map_to_hl7(p, e, data.identifier_system, data.identifier_value)
    for item in mapped["mapping"]:
        if item["issue"]:
            trace.add("MAP", "ADT^A01", item["destination"], result="AVERTISSEMENT",
                      detail=item["issue"])
    trace.add("MAP", "ADT^A01", "FHIR → HL7", result="OK" if mapped["complete"] else "INCOMPLET",
              detail="Message " + mapped["message_id"])
    selected = select_identifier(p, data.identifier_system, data.identifier_value)
    return {"ok": True, "admission_recorded": True, "patient": p, "encounter": e, **mapped,
            "summary": {"patient_id": p["id"], "encounter_id": e["id"],
                        "identifier": selected["value"] if selected else "",
                        "name": (p.get("name") or [{}])[0], "admission": e.get("period", {}).get("start", ""),
                        "location": location_parts(e)}, "traces": trace.entries}

