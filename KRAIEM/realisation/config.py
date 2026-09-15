import os

FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4").rstrip("/")
PATIENT_IDENTIFIER_SYSTEM = os.getenv(
    "PATIENT_IDENTIFIER_SYSTEM", "https://example.org/fhir/identifier/isis-admission-demo"
)
ENCOUNTER_IDENTIFIER_SYSTEM = os.getenv(
    "ENCOUNTER_IDENTIFIER_SYSTEM", PATIENT_IDENTIFIER_SYSTEM + "-encounter"
)
FHIR_TIMEOUT = 30.0

