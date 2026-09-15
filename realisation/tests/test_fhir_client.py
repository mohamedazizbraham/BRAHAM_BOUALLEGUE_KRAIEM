import asyncio
import httpx
import pytest
from fhir_client import FhirClient, FhirError
from trace_store import TraceStore


def run(handler, operation):
    trace = TraceStore()
    async def scenario():
        async with FhirClient(trace, httpx.MockTransport(handler)) as client:
            return await operation(client)
    return asyncio.run(scenario()), trace.entries


@pytest.mark.parametrize("status", [400,401,403,404,500,503])
def test_http_errors(status):
    def handler(request):
        return httpx.Response(status, json={"resourceType":"OperationOutcome","issue":[
            {"severity":"error","code":"invalid","details":{"text":"Ressource refusée"},"diagnostics":"Diagnostic fictif"}]})
    with pytest.raises(FhirError, match="Ressource refusée"):
        run(handler, lambda c:c.get_patient("test"))


def test_no_patient_is_normal():
    result, traces = run(lambda r:httpx.Response(200,json={"resourceType":"Bundle","type":"searchset","total":0}),
                         lambda c:c.search_patient("UNIQUE"))
    assert result == []
    assert traces[0]["result"] == "OK"
    assert "UNIQUE" not in str(traces)


def test_pagination_and_selection():
    def handler(request):
        i = "2" if "page=2" in str(request.url) else "1"
        bundle = {"resourceType":"Bundle","type":"searchset","entry":[{"resource":{"resourceType":"Patient","id":i}}]}
        if i == "1":
            bundle["link"] = [{"relation":"next","url":"https://hapi.fhir.org/baseR4?page=2"}]
        return httpx.Response(200,json=bundle)
    result, traces = run(handler, lambda c:c.search_patient("test"))
    assert [x["id"] for x in result] == ["1","2"]
    assert len(traces) == 2


def test_invalid_resource():
    with pytest.raises(FhirError, match="Patient attendu"):
        run(lambda r:httpx.Response(200,json={"resourceType":"Encounter","id":"x"}),lambda c:c.get_patient("p"))


def test_timeout():
    def handler(request):
        raise httpx.ReadTimeout("test", request=request)
    with pytest.raises(FhirError, match="Délai"):
        run(handler,lambda c:c.get_patient("p"))


def test_outcome_on_http_200_is_not_success():
    with pytest.raises(FhirError):
        run(lambda r:httpx.Response(200,json={"resourceType":"OperationOutcome","issue":[]}),lambda c:c.get_patient("p"))


def test_create_location_fallback():
    def handler(request):
        if request.method == "POST":
            assert request.headers["content-type"] == "application/fhir+json"
            return httpx.Response(201,headers={"Location":"https://hapi.fhir.org/baseR4/Encounter/123/_history/1"})
        return httpx.Response(200,json={"resourceType":"Encounter","id":"123"})
    result,traces = run(handler,lambda c:c.create_encounter({"resourceType":"Encounter"}))
    assert result["id"] == "123"
    assert [x["method"] for x in traces] == ["POST","GET"]


def test_external_pagination_refused():
    def handler(request):
        return httpx.Response(200,json={"resourceType":"Bundle","type":"searchset",
                                       "link":[{"relation":"next","url":"https://evil.example/Patient"}]})
    with pytest.raises(FhirError,match="externe"):
        run(handler,lambda c:c.search_patient("test"))


