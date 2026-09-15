from copy import deepcopy
import pytest
from hl7_mapper import map_to_hl7, date_to_hl7, datetime_to_hl7, escape
from terminology import gender_to_hl7, encounter_class_to_hl7
from schemas import AdmissionRequest

P = {"resourceType": "Patient", "id": "test-p", "identifier": [{"system": "urn:test", "value": "PAT-TEST-01"}],
     "name": [{"family": "Exemple", "given": ["Fictif"]}], "birthDate": "2002-04-10", "gender": "male",
     "telecom": [{"system": "phone", "value": "0000000000"}]}
E = {"resourceType": "Encounter", "id": "test-e", "class": {"code": "IMP"},
     "subject": {"reference": "Patient/test-p"}, "identifier": [{"value": "ADM-TEST"}],
     "period": {"start": "2026-09-15T14:00:00+02:00"},
     "location": [{"location": {"display": "Service fictif / Chambre 12 / Lit B"}}]}


@pytest.mark.parametrize("source,target", [("male","M"),("female","F"),("unknown","U"),("other",""),("unexpected",""),(None,"")])
def test_gender(source, target):
    assert gender_to_hl7(source) == target


def test_dates_and_class():
    assert encounter_class_to_hl7("IMP") == "I"
    assert encounter_class_to_hl7("AMB") == ""
    assert date_to_hl7("2002-04-10") == "20020410"
    assert datetime_to_hl7("2026-09-15T14:00:00+02:00") == "20260915140000+0200"
    assert datetime_to_hl7("2024-02-29T01:02:03Z") == "20240229010203+0000"
    assert datetime_to_hl7("2025-01-01T01:02:03-05:30") == "20250101010203-0530"


@pytest.mark.parametrize("value", ["2002", "2002-04", "2025-02-29", "bad"])
def test_invalid_birth(value):
    with pytest.raises(ValueError):
        date_to_hl7(value)


def test_no_timezone():
    with pytest.raises(ValueError):
        datetime_to_hl7("2026-09-15T14:00:00")


def test_fields_and_ids():
    mapped = map_to_hl7(P, E)
    segments = {x.split("|")[0]: x.split("|") for x in mapped["message"].strip("\r").split("\r")}
    assert list(segments) == ["MSH", "EVN", "PID", "PV1"]
    assert segments["MSH"][8] == "ADT^A01^ADT_A01"
    assert segments["MSH"][11] == "2.5.1"
    assert segments["MSH"][17] == "UNICODE UTF-8"
    assert segments["EVN"][2] == "20260915140000+0200"
    for position, expected in {3:"PAT-TEST-01",5:"Exemple^Fictif",7:"20020410",8:"M",13:"0000000000"}.items():
        assert segments["PID"][position] == expected
    for position, expected in {2:"I",3:"Service fictif^12^B",19:"ADM-TEST",44:"20260915140000+0200"}.items():
        assert segments["PV1"][position] == expected
    assert mapped["complete"]
    assert mapped["message_id"] != map_to_hl7(P,E)["message_id"]


def test_ambiguity_and_missing_data():
    p = deepcopy(P); p["gender"] = "other"; del p["birthDate"]
    mapped = map_to_hl7(p, E)
    assert not mapped["complete"]
    rows = {r["destination"]: r for r in mapped["mapping"]}
    assert rows["PID-8"]["target"] == ""
    assert "ambigu" in rows["PID-8"]["issue"]
    assert rows["PID-7"]["target"] == ""
    assert rows["PV1-2"]["target"] == "I"


def test_identifier_selection():
    p = deepcopy(P); p["identifier"].append({"system":"urn:other", "value":"SECOND"})
    assert not map_to_hl7(p,E)["complete"]
    result = map_to_hl7(p,E,"urn:other","SECOND")
    assert next(r for r in result["mapping"] if r["destination"] == "PID-3")["target"] == "SECOND"


def test_escape_and_optional_location():
    assert escape("|^~\\&\r") == "\\F\\\\S\\\\R\\\\E\\\\T\\\\X0D\\"
    p = deepcopy(P); p["name"][0]["family"] = "Test|A^B"
    e = deepcopy(E); del e["location"]; del p["telecom"]
    mapped = map_to_hl7(p,e)
    assert len(mapped["message"].strip("\r").split("\r")) == 4
    assert "Test\\F\\A\\S\\B^Fictif" in mapped["message"]
    assert mapped["complete"]


def test_schema_rejects_partial_location():
    with pytest.raises(ValueError):
        AdmissionRequest(patient_id="p", admission_time="2026-09-15T14:00:00+02:00",service="Test")

