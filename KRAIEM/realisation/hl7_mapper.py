import re
from datetime import date, datetime, timezone
from uuid import uuid4
from terminology import gender_to_hl7, encounter_class_to_hl7


def escape(value):
    codes = {"|": "F", "^": "S", "~": "R", "\\": "E", "&": "T"}
    return "".join("\\" + codes[c] + "\\" if c in codes else
                   "\\X" + format(ord(c), "02X") + "\\" if ord(c) < 32 else c
                   for c in str(value))


def date_to_hl7(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Date de naissance complète requise (YYYY-MM-DD).")
    return date.fromisoformat(value).strftime("%Y%m%d")


def datetime_to_hl7(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Fuseau horaire requis.")
    return parsed.strftime("%Y%m%d%H%M%S%z")


def segment(name, fields):
    parts = [""] * (max(fields, default=0) + 1)
    parts[0] = name
    for number, value in fields.items():
        parts[number] = value
    return "|".join(parts)


def select_identifier(patient, system="", value=""):
    identifiers = [x for x in patient.get("identifier", []) if x.get("value")]
    if value:
        matches = [x for x in identifiers if x.get("value") == value and x.get("system", "") == system]
        return matches[0] if len(matches) == 1 else None
    return identifiers[0] if len(identifiers) == 1 else None


def location_parts(encounter):
    locations = encounter.get("location", [])
    if len(locations) != 1:
        return None
    display = locations[0].get("location", {}).get("display", "")
    match = re.fullmatch(r"(.+) / Chambre (.+) / Lit (.+)", display)
    return match.groups() if match else None


def map_to_hl7(patient, encounter, identifier_system="", identifier_value=""):
    rows, warnings = [], []
    def row(concept, path, source, rule, target, destination, kind, issue=""):
        rows.append(dict(concept=concept, path=path, source=source, rule=rule, target=target,
                         destination=destination, kind=kind, issue=issue))
        if issue:
            warnings.append(destination + " : " + issue)
        return target

    ident = select_identifier(patient, identifier_system, identifier_value)
    pid3 = row("Identifiant patient", "Patient.identifier", ident or patient.get("identifier", []),
               "Identifiant unique ou sélection explicite ; CX.1", escape(ident["value"]) if ident else "",
               "PID-3", "Structurelle",
               "" if ident else "Identifiant absent ou sélection nécessaire ; identifiant FHIR non substitué.")
    names = patient.get("name", [])
    name = names[0] if names else {}
    family, given = name.get("family", ""), (name.get("given") or [""])[0]
    pid5 = row("Nom / prénom", "Patient.name[0]", name, "Premier nom et premier prénom → XPN.1 / XPN.2",
               escape(family) + "^" + escape(given) if family or given else "", "PID-5", "Structurelle",
               "" if family and given else "Nom ou prénom absent ; composante laissée vide.")
    birth = patient.get("birthDate", "")
    try:
        dob = date_to_hl7(birth)
        birth_issue = ""
    except (ValueError, TypeError):
        dob, birth_issue = "", "Date complète absente ou invalide ; transformation non effectuée."
    pid7 = row("Date de naissance", "Patient.birthDate", birth, "YYYY-MM-DD → YYYYMMDD", dob,
               "PID-7", "Syntaxique", birth_issue)
    gender = patient.get("gender", "")
    sex = gender_to_hl7(gender)
    pid8 = row("Sexe administratif", "Patient.gender", gender, "CDC §10 : male→M, female→F, unknown→U",
               sex, "PID-8", "Sémantique",
               "" if sex else "Correspondance non déterminée / ambiguë ; décision métier nécessaire.")
    phones = [x for x in patient.get("telecom", []) if x.get("system") == "phone" and x.get("value")]
    phone = phones[0].get("value", "") if phones else ""
    pid13 = row("Téléphone", "Patient.telecom", phones, "Premier téléphone → XTN.1 (optionnel)",
                escape(phone), "PID-13", "Structurelle")
    cls = encounter.get("class", {}).get("code", "")
    pv2 = row("Classe de séjour", "Encounter.class.code", cls, "IMP → I : hospitalisation",
              encounter_class_to_hl7(cls), "PV1-2", "Sémantique",
              "" if cls == "IMP" else "Classe source inattendue : correspondance non déterminée.")
    loc = location_parts(encounter)
    pv3 = row("Localisation", "Encounter.location", encounter.get("location", []),
              "Convention locale service / Chambre chambre / Lit lit → PL.1 / PL.2 / PL.3",
              "^".join(escape(x) for x in loc) if loc else "", "PV1-3", "Approximative / optionnelle",
              "Localisation non interprétable selon la convention locale." if encounter.get("location") and not loc else "")
    visits = [x for x in encounter.get("identifier", []) if x.get("value")]
    visit = visits[0]["value"] if len(visits) == 1 else ""
    pv19 = row("Identifiant séjour", "Encounter.identifier", visits, "Identifiant unique → CX.1",
               escape(visit), "PV1-19", "Structurelle",
               "Plusieurs identifiants de séjour ; sélection non déterminée." if len(visits) > 1 else "")
    start = encounter.get("period", {}).get("start", "")
    try:
        ts, ts_issue = datetime_to_hl7(start), ""
    except (ValueError, TypeError, AttributeError):
        ts, ts_issue = "", "Date/heure avec fuseau absente ou invalide."
    pv44 = row("Admission", "Encounter.period.start", start, "dateTime → TS avec fuseau",
               ts, "PV1-44", "Syntaxique", ts_issue)
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%z")
    message_id = uuid4().hex
    row("Création message", "Métadonnée technique", now, "Horloge au moment de la conversion", now, "MSH-7", "Technique")
    row("Type message", "Configuration", "ADT^A01^ADT_A01", "Notification d’admission", "ADT^A01^ADT_A01", "MSH-9", "Technique")
    row("Contrôle message", "Métadonnée technique", message_id, "UUID unique", message_id, "MSH-10", "Technique")
    row("Version", "Configuration", "2.5.1", "Version cible du CDC", "2.5.1", "MSH-12", "Technique")
    row("Événement", "Encounter.period.start", start, "Horodatage d’admission", ts, "EVN-2", "Syntaxique", ts_issue)
    msh = segment("MSH", {1: "^~\\&", 2: "ADMISSION_APP", 3: "ISIS_DEMO", 4: "SIH", 5: "HOSPITAL",
                           6: now, 8: "ADT^A01^ADT_A01", 9: message_id, 10: "P", 11: "2.5.1",
                           17: "UNICODE UTF-8"})
    message = "\r".join([msh, segment("EVN", {1: "A01", 2: ts}),
                           segment("PID", {1: "1", 3: pid3, 5: pid5, 7: pid7, 8: pid8, 13: pid13}),
                           segment("PV1", {1: "1", 2: pv2, 3: pv3, 19: pv19, 44: pv44})]) + "\r"
    if len(names) > 1 or len(name.get("given", [])) > 1:
        warnings.append("PID-5 : seuls le premier nom et le premier prénom sont représentés.")
    return {"message": message, "mapping": rows, "warnings": list(dict.fromkeys(warnings)),
            "complete": not any(r["issue"] for r in rows),
            "message_id": message_id}

