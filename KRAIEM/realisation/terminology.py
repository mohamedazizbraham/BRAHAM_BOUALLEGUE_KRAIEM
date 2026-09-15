def gender_to_hl7(value):
    """CDC §10 : other et toute valeur non démontrable restent non mappés."""
    return {"male": "M", "female": "F", "unknown": "U"}.get(value, "")


def encounter_class_to_hl7(value):
    return "I" if value == "IMP" else ""

