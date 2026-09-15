# Prototype — Admission patient FHIR R4 → HL7 v2

Prototype d'évaluation d'interopérabilité en santé.

## Serveur utilisé

- HAPI FHIR R4
- Base URL : `https://hapi.fhir.org/baseR4`
- Version ciblée : FHIR R4 / 4.0.1
- Swagger : `https://hapi.fhir.org/baseR4/swagger-ui/`

## Fonctionnalités

- Vérification du serveur via `/metadata`
- Recherche réelle de `Patient`
- Traitement des réponses de recherche sous forme de `Bundle` `searchset`
- Sélection d'un patient et récupération de sa ressource complète
- Recherche des `Encounter` avec `Encounter?subject=Patient/{id}`
- Récupération des ressources référencées lorsque nécessaire (`Organization`, `Practitioner`, `Location`)
- Vue métier de l'identité et de l'admission
- Vue JSON des ressources FHIR réellement utilisées
- Génération dynamique d'une représentation `ADT^A01`
- Vue détaillée du mapping FHIR → HL7 v2
- Démonstration d'alignement de terminologie `Patient.gender` → HL7 v2 Table 0001
- Gestion minimale des erreurs HTTP et FHIR
- Journal de traçabilité des appels
- Aucun patient métier codé en dur

## Données réelles du serveur

La réponse de recherche fournie pour le prototype montre par exemple un patient avec :

- `Patient.id` : `sindhu-syn-000007`
- `Patient.identifier.value` : `SYN-000007`
- `Patient.name.text` : `Synthetic Patient SYN-000007`
- `Patient.gender` : `male`
- `Patient.birthDate` : `1967-01-01`

Ces valeurs servent uniquement de données observées lors du test manuel. Elles ne sont pas inscrites dans le code : l'application les récupère dynamiquement depuis le serveur.

## Lancement

```bash
npm install
npm run dev
```

Puis ouvrir l'URL affichée par Vite, généralement `http://localhost:5173`.

## Note sur la validation

La structure du message HL7 v2 et certains choix de mapping doivent être comparés à la version HL7 v2 exacte demandée par l'évaluation avant validation finale.
