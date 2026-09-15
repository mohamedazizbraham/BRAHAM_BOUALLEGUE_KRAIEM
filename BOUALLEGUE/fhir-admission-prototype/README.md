# Admission d'un patient — FHIR R4 → HL7 v2.5.1 ADT^A01

Prototype pédagogique pour l'évaluation **Interopérabilité en santé — Sujet A**.

## Objectif

Démontrer une chaîne d'interopérabilité réelle :

`HAPI FHIR R4 → Patient réel → POST Encounter → vue métier → ressources FHIR → transformation HL7 v2.5.1 ADT^A01 → mapping terminologique → logs`

Aucune donnée métier Patient n'est codée en dur.

## Prérequis

- Node.js 18+ (Node 22 testé pour la syntaxe locale)
- Accès internet vers `https://hapi.fhir.org`

## Lancement

```bash
node server.mjs
```

Puis ouvrir :

```text
http://localhost:3000
```

Base FHIR par défaut :

```text
https://hapi.fhir.org/baseR4
```

Elle peut être remplacée sans modifier le code :

```bash
FHIR_BASE_URL=https://mon-serveur-fhir.example/fhir node server.mjs
```

## Pourquoi un petit proxy Node ?

Le navigateur appelle `/api/fhir/...`; `server.mjs` relaie ensuite vers le serveur FHIR réel. Cela :

- évite de dépendre des règles CORS du serveur public ;
- garde `FHIR_BASE_URL` configurable ;
- ne stocke aucune donnée métier ;
- n'ajoute aucune base de données ni dépendance externe.

## Parcours de démonstration

1. Vérifier `/metadata`.
2. Rechercher un Patient par nom, `identifier`, ou FHIR resource id.
3. Sélectionner un Patient réellement retourné par HAPI.
4. Cliquer **Admettre ce patient**.
5. L'application envoie réellement `POST /Encounter` avec :
   - `status = in-progress`
   - `class.code = IMP`
   - `subject.reference = Patient/{id}`
   - `period.start = date/heure de l'action`
6. Afficher les vues :
   - métier ;
   - FHIR réel ;
   - HL7 v2 ;
   - mapping ;
   - traçabilité.

## Ressources FHIR du MVP

- `Patient`
- `Encounter`

Aucun profil FR Core / US Core n'est revendiqué. Le prototype travaille sur FHIR R4 de base.

## Interactions FHIR

- `GET /metadata`
- `GET /Patient?name=...&_count=10`
- `GET /Patient?identifier=...&_count=10`
- `GET /Patient/{id}`
- `POST /Encounter`

Les réponses de recherche sont lues comme des `Bundle` et les ressources sont extraites de `Bundle.entry[].resource`.

## HL7 v2

Choix de conception : **HL7 v2.5.1 — ADT^A01**.

Segments générés :

- `MSH`
- `EVN`
- `PID`
- `PV1`

Principaux mappings :

- `Patient.identifier → PID-3`
- `Patient.name → PID-5`
- `Patient.birthDate → PID-7`
- `Patient.gender → PID-8`
- `Encounter.class → PV1-2`
- `Encounter.identifier/id → PV1-19`
- `Encounter.period.start → PV1-44`

### Mapping terminologique

- `male → M` : équivalent
- `female → F` : équivalent
- `unknown → U` : équivalent
- `other` : **ambigu**, non converti automatiquement dans ce prototype car le ConceptMap FHIR R4 indique plusieurs cibles v2 possibles (`A` et `O`).
- `Encounter.class=IMP → PV1-2=I`

## Gestion des erreurs

Le prototype gère notamment :

- erreur réseau / serveur FHIR indisponible ;
- HTTP non-2xx ;
- `OperationOutcome` ;
- recherche sans résultat ;
- `resourceType` inattendu ;
- `Encounter.subject.reference` incohérent ;
- champs manquants lors de la conversion ;
- mapping ambigu.

Une erreur ne produit jamais un faux message de succès.

## Traçabilité

La vue Logs conserve uniquement :

- heure ;
- méthode HTTP ;
- endpoint ;
- statut HTTP ;
- résultat technique.

Elle n'enregistre pas le nom ou les données personnelles du Patient.

## Tests manuels recommandés

1. `GET /metadata` doit retourner `CapabilityStatement`.
2. Recherche par nom → `Bundle`.
3. Lecture par FHIR id → `Patient`.
4. Critère sans résultat → message clair.
5. Admission → `Encounter` réel avec bonne référence Patient.
6. `male/female/unknown` → mapping PID-8.
7. `other` → avertissement d'ambiguïté, pas de traduction silencieuse.
8. Deux Patients différents → l'interface et le HL7 changent sans modification du code.
9. Base URL invalide → erreur visible, aucun faux succès.

## Limites

- Serveur public de test : données et identifiants non garantis dans le temps.
- Ne jamais saisir de vraies données personnelles ou de santé.
- Le message HL7 v2 est un MVP pédagogique ; aucune conformité à un profil national/établissement n'est revendiquée.
- La version HL7 v2.5.1 est un choix de conception à confirmer si l'enseignant impose une autre version.
