# Vérification du prototype — 15 septembre 2026

## Résultats exécutés

- 35 tests unitaires et API réussis (`python -m pytest -q`).
- JavaScript : `node --check static/app.js` réussi.
- HAPI : GET /metadata HTTP 200, CapabilityStatement, FHIR 4.0.1.
- Capacités vérifiées : Patient read/search-type, recherches identifier/name, Encounter create/read.
- Smoke test HTTP réel : trois Patients fictifs existants, recherche vide, recherche par identifiant, création et relecture Encounter, référence Patient, champs HL7, mapping, traces, OperationOutcome réel 404.
- Test Edge réel : recherche vide, lecture Patient, saisie et admission, six vues, affichage mobile sans débordement, aucune erreur JavaScript, aucun appel HAPI direct du navigateur.
- Captures de l’interface initiale : [bureau](interface-desktop.png), [mobile](interface-mobile.png).

| Patient FHIR de test | Encounter réellement créé | Vérification |
|---|---|---|
| 137203486 | 138780779 | Smoke API ; relecture et mapping complet |
| 137204523 | 138780782 | Smoke API ; relecture et mapping complet |
| 137205841 | 138780784 | Smoke API ; relecture et mapping complet |
| 137203486 | 138781220 | Parcours complet Edge ; mapping complet |

Aucun Patient créé, modifié ou supprimé. Aucun Encounter préexistant modifié.
Ces IDs sont des preuves datées sur un serveur partagé, pas des constantes métier.

## Matrice des critères CDC

| Critère | Implémentation / preuve |
|---|---|
| CA-01 | /api/health et /metadata réels |
| CA-02 | Identité et JSON issus de GET Patient |
| CA-03 | Lecture / recherche, contrôle resourceType et id |
| CA-04 | POST Encounter réel, vérifié sur quatre admissions |
| CA-05 | subject.reference contrôlé côté backend et dans le smoke test |
| CA-06 | status=in-progress, class=IMP, subject et period.start |
| CA-07 | Résumé métier testé dans Edge |
| CA-08 | Patient réel et Encounter relu dans les deux blocs JSON |
| CA-09 | Noyau MSH/EVN/PID/PV1, MSH-9 ADT^A01^ADT_A01 ; tests par position |
| CA-10 | Tableau dynamique, source/règle/cible/destination/type/ambiguïté |
| CA-11 | Sexe et IMP ; tests explicites |
| CA-12 | Champs manquants laissés vides et signalés ; aucun identifiant FHIR substitué |
| CA-13 | Tests HTTP 400/401/403/404/5xx, timeout, OperationOutcome ; refus Encounter sans succès |
| CA-14 | Trois Patients différents, sans modification du code métier |
| CA-15 | Traces techniques contrôlées ; paramètres de recherche masqués |

## Corrections issues des vérifications

- Pagination HAPI réelle : le lien suivant utilise /baseR4?... ; contrôle ajusté et testé.
- Assertion API corrigée : une route de création Patient absente renvoie 404.
- Assertions navigateur ajustées aux contrôles HTML : bouton désactivé et format datetime-local accepté par Edge.

## Points de périmètre

CDC prioritaire : création Patient exclue ; other non mappé automatiquement.
Noyau pédagogique HL7, aucune revendication de conformité ADT complète en production.
Les tests isolés utilisent des transports simulés explicitement ; les essais ci-dessus utilisent réellement HAPI.
Deux avertissements de dépréciation de Starlette/TestClient sont présents ; aucun échec de test.
Publication GitHub, prompts individuels et vérification manuelle Postman restent des livrables de l’équipe.

## Reproduire le test navigateur (optionnel)

Le navigateur Edge est requis pour ce script. Playwright est une dépendance de validation,
pas une dépendance de l’application :

```sh
python -m pip install playwright
python tests/smoke_browser.py --patient-id ID_PATIENT_FICTIF
```

Ce script crée un Encounter réel et enregistre les captures de l’interface initiale.

