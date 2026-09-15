# PROMPTS_Nom_Prenom_REAL

Ce fichier sert de journal individuel de pilotage de l'IA. Les prompts ci-dessous ont pour logique : **spécifier → vérifier → tester → corriger → retester**.

## R01 — Cadrage de la réalisation

**Objectif :** fixer le MVP avant génération de code : HAPI FHIR R4 réel, Patient/Encounter, vues métier/FHIR/HL7/mapping, erreurs et logs, aucune donnée Patient codée en dur.

**Vérification attendue :** architecture minimale, hypothèses et risques (notamment CORS) explicités avant développement.

## R02 — Couche FHIR réelle

**Objectif :** implémenter `/metadata`, recherche/lecture Patient, interprétation `Bundle.entry[].resource`, `OperationOutcome` et erreurs HTTP.

**Vérification attendue :** endpoints réels, `resourceType`, recherche vide et erreur réseau.

## R03 — Admission Encounter

**Objectif :** créer réellement un `Encounter` pour le Patient sélectionné avec `status=in-progress`, `class=IMP`, `subject=Patient/{id}`, `period.start=now`.

**Vérification attendue :** réponse réelle, id Encounter et cohérence de `subject.reference`.

## R04 — Vues métier et FHIR

**Objectif :** séparer représentation métier lisible et JSON FHIR brut tout en utilisant les mêmes ressources réelles.

**Vérification attendue :** test avec au moins deux Patients différents, aucun champ absent inventé.

## R05 — Transformation HL7 v2

**Objectif :** construire `ADT^A01` avec `MSH`, `EVN`, `PID`, `PV1` et documenter chaque règle source → cible.

**Vérification attendue :** format des dates, PID-3/5/7/8, PV1-2/19/44, gestion des champs absents.

## R06 — Mapping terminologique

**Objectif :** rendre visible la différence entre transformation syntaxique et mapping sémantique ; ne pas traduire silencieusement `gender=other`.

**Vérification attendue :** système source, cible, conservation du sens, perte/ambiguïté.

## R07 — Audit final

**Objectif :** erreurs minimales, traçabilité, test multi-patient et matrice de conformité.

**Boucle :** problème → cause → correction → test de non-régression → GO/NO-GO.
