import re
from urllib.parse import urljoin, urlsplit
import httpx
from config import FHIR_BASE_URL, FHIR_TIMEOUT


class FhirError(Exception):
    def __init__(self, message, status=502, issues=None):
        super().__init__(message)
        self.status = status
        self.issues = issues or []


def operation_outcome(data):
    if not isinstance(data, dict) or data.get("resourceType") != "OperationOutcome":
        return None
    return [{
        "severity": x.get("severity", ""), "code": x.get("code", ""),
        "details": (x.get("details") or {}).get("text", ""),
        "diagnostics": x.get("diagnostics", ""),
    } for x in data.get("issue", []) if isinstance(x, dict)]


class FhirClient:
    def __init__(self, trace, transport=None):
        self.trace = trace
        self.http = httpx.AsyncClient(
            base_url=FHIR_BASE_URL + "/", timeout=FHIR_TIMEOUT, transport=transport,
            headers={"Accept": "application/fhir+json"},
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.http.aclose()

    @staticmethod
    def valid_id(value):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9.-]{1,64}", value):
            raise FhirError("Identifiant FHIR absent ou invalide.", 422)
        return value

    def safe_url(self, url):
        target = urljoin(FHIR_BASE_URL + "/", url)
        base, parsed = urlsplit(FHIR_BASE_URL), urlsplit(target)
        if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc) or not (parsed.path == base.path or parsed.path.startswith(base.path + "/")):
            raise FhirError("Lien FHIR externe refusé.")
        return target

    async def request(self, method, path, expected, **kwargs):
        resource = expected
        endpoint = urlsplit(str(path)).path
        if kwargs.get("params"):
            endpoint += "?" + "&".join(k + "=[masqué]" for k in kwargs["params"])
        try:
            response = await self.http.request(method, self.safe_url(path), **kwargs)
        except httpx.TimeoutException:
            self.trace.add(method, resource, endpoint, result="ERREUR", detail="Timeout")
            raise FhirError("Délai de réponse FHIR dépassé. Une écriture peut avoir abouti : vérifier avant de réessayer.", 504)
        except httpx.RequestError:
            self.trace.add(method, resource, endpoint, result="ERREUR", detail="Réseau inaccessible")
            raise FhirError("Serveur FHIR inaccessible.", 503)
        try:
            data = response.json()
        except ValueError:
            data = None
        issues = operation_outcome(data)
        valid = response.status_code in ({200} if method == "GET" else {200, 201})
        if not valid or issues is not None:
            # Les diagnostics libres peuvent contenir des données patient : seulement codes et sévérités dans les logs.
            detail = "OperationOutcome : " + ", ".join(
                x["severity"] + "/" + x["code"] for x in (issues or [])
            ) if issues is not None else "Réponse HTTP refusée"
            self.trace.add(method, resource, endpoint, response.status_code, "ERREUR", detail=detail)
            reasons = {400: "Requête FHIR invalide", 401: "Authentification FHIR requise",
                       403: "Accès FHIR interdit", 404: "Ressource FHIR introuvable",
                       412: "Condition de création non satisfaite"}
            message = reasons.get(response.status_code, "Opération FHIR refusée")
            if issues:
                message += " : " + "; ".join(x["details"] or x["diagnostics"] or x["code"] for x in issues)
            raise FhirError(f"{message} (HTTP {response.status_code}).",
                            response.status_code if 400 <= response.status_code < 500 else 502, issues)
        if method == "POST" and (not isinstance(data, dict) or not data.get("id")):
            location = response.headers.get("Location", "")
            match = re.search(r"/" + expected + r"/([A-Za-z0-9.-]+)(?:/_history/[^/]+)?$", urlsplit(location).path)
            if match:
                self.safe_url(location)
                self.trace.add(method, resource, endpoint, response.status_code, fhir_id=match[1])
                return await self.request("GET", expected + "/" + self.valid_id(match[1]), expected)
        if not isinstance(data, dict) or data.get("resourceType") != expected:
            self.trace.add(method, resource, endpoint, response.status_code, "ERREUR", detail="resourceType inattendu")
            raise FhirError("Réponse FHIR inattendue : " + expected + " attendu.")
        if expected in {"Patient", "Encounter"}:
            self.valid_id(data.get("id"))
        self.trace.add(method, resource, endpoint, response.status_code, fhir_id=data.get("id"))
        return data

    async def check_server(self):
        data = await self.request("GET", "metadata", "CapabilityStatement")
        resources = {r["type"]: r for rest in data.get("rest", []) if rest.get("mode") == "server"
                     for r in rest.get("resource", [])}
        for kind, required in {"Patient": {"read", "search-type"}, "Encounter": {"create", "read"}}.items():
            supported = {x["code"] for x in resources.get(kind, {}).get("interaction", [])}
            if not required <= supported:
                raise FhirError("Capacités FHIR insuffisantes pour " + kind)
        search = {x["name"] for x in resources["Patient"].get("searchParam", [])}
        if data.get("fhirVersion") != "4.0.1" or not {"identifier", "name"} <= search:
            raise FhirError("Version FHIR R4 ou paramètres de recherche non confirmés.")
        return {"resourceType": data["resourceType"], "fhirVersion": data["fhirVersion"],
                "base_url": FHIR_BASE_URL, "patient_search": sorted(search),
                "encounter_create": True}

    async def search_patient(self, identifier="", system="", name=""):
        params = {"_count": "50"}
        if identifier:
            params["identifier"] = (system + "|" if system else "") + identifier
        elif name:
            params["name"] = name
        else:
            raise FhirError("Saisir un identifiant ou un nom de patient fictif.", 422)
        patients, seen = {}, set()
        path = "Patient"
        for _ in range(20):
            bundle = await self.request("GET", path, "Bundle", params=params)
            if bundle.get("type") != "searchset":
                raise FhirError("Bundle de recherche searchset attendu.")
            for entry in bundle.get("entry", []):
                r = entry.get("resource", {})
                issues = operation_outcome(r)
                if issues is not None:
                    if any(x["severity"] in {"error", "fatal"} for x in issues):
                        raise FhirError("Erreur FHIR dans le Bundle de recherche.", issues=issues)
                    self.trace.add("GET", "Bundle", "Patient", result="AVERTISSEMENT",
                                   detail="OperationOutcome informatif dans le Bundle")
                if r.get("resourceType") == "Patient" and entry.get("search", {}).get("mode", "match") == "match":
                    patients[self.valid_id(r.get("id"))] = r
            next_url = next((x["url"] for x in bundle.get("link", []) if x.get("relation") == "next"), None)
            if not next_url:
                return list(patients.values())
            path = self.safe_url(next_url)
            if path in seen:
                raise FhirError("Boucle de pagination FHIR détectée.")
            seen.add(path)
            params = None
        raise FhirError("Trop de résultats : préciser la recherche.", 422)

    async def get_patient(self, fhir_id):
        return await self.request("GET", "Patient/" + self.valid_id(fhir_id), "Patient")

    async def get_encounter(self, fhir_id):
        return await self.request("GET", "Encounter/" + self.valid_id(fhir_id), "Encounter")

    async def create_encounter(self, encounter_data):
        return await self.request("POST", "Encounter", "Encounter", json=encounter_data,
                                  headers={"Content-Type": "application/fhir+json", "Prefer": "return=representation"})

