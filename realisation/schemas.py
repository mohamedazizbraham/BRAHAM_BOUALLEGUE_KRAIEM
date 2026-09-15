from typing import Annotated
from pydantic import BaseModel, Field, AwareDatetime, ConfigDict, model_validator

FhirId = Annotated[str, Field(pattern=r"^[A-Za-z0-9.-]{1,64}$")]
ShortText = Annotated[str, Field(max_length=120)]


class AdmissionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    patient_id: FhirId
    identifier_system: str = Field(default="", max_length=500)
    identifier_value: str = Field(default="", max_length=200)
    admission_time: AwareDatetime
    service: ShortText = ""
    room: ShortText = ""
    bed: ShortText = ""

    @model_validator(mode="after")
    def location_consistency(self):
        values = (self.service, self.room, self.bed)
        if any(values) and not all(values):
            raise ValueError("Renseigner service, chambre et lit ensemble, ou laisser les trois vides.")
        if any(" / " in x or any(ord(c) < 32 for c in x) for x in values):
            raise ValueError("La localisation ne peut contenir de contrôle ni le séparateur ' / '.")
        return self

