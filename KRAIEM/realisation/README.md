# Admission d’un patient — FHIR R4 → HL7 v2.5.1

Prototype pédagogique connecté à **https://hapi.fhir.org/baseR4**.
**Données fictives uniquement.** Aucune base de données locale, aucun compte applicatif.

## Source de vérité et arbitrages

Le [CDC consolidé](docs/Cahier_des_charges_CONSOLIDE_Admission_Patient_FHIR_HL7v2.pdf), lu intégralement (12 pages), prime sur le prompt de réalisation :

- §3 et §13 : Patient existant uniquement. Aucun POST Patient ni modification de Patient.
- §10 et T08 : `other` reste non mappé ; ambiguïté visible, aucune conversion automatique vers O.
- Les valeurs inattendues ou absentes restent non déterminées, sans substitution par U.
- Téléphone et localisation sont optionnels. Le formulaire permet la localisation si ses trois composantes sont renseignées.
- Les quatre vues du CDC sont présentées en six sections conformément au prompt : Admission, Résultat métier, Ressources FHIR, HL7 v2, Mapping / Terminologie, Logs.

## Architecture et stack

Navigateur HTML/CSS/JavaScript vanilla → FastAPI → httpx → serveur HAPI réel.
Patient + Encounter relus → mapper Python → noyau ADT^A01.
Pydantic valide la saisie ; Uvicorn sert l’application. Aucun appel HAPI direct depuis le navigateur.

```text
main.py                 Routes et orchestration
config.py               Variables d’environnement
fhir_client.py          HTTP FHIR, capacités, pagination et erreurs
schemas.py              Validation des admissions
hl7_mapper.py           Champs HL7 et tableau dynamique de mapping
terminology.py          Mappings retenus par le CDC
trace_store.py          Traces techniques par requête
templates/index.html    Six vues
static/app.js           Parcours utilisateur
static/style.css        Présentation responsive
tests/                  Tests isolés et smoke test réel explicite
```

## Installation

Prérequis : Python 3.11 ou ultérieur, accès HTTPS à HAPI. Vérifié avec Python 3.14.

PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --no-access-log
```

Si l’activation PowerShell est interdite :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --no-access-log
```

Linux / macOS :

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --no-access-log
```

Interface : **http://127.0.0.1:8000**. API : http://127.0.0.1:8000/docs.

La commande minimale demandée `uvicorn main:app --reload` fonctionne également.
L’option `--no-access-log` évite que le journal d’accès Uvicorn conserve les noms recherchés dans les URL.

## Configuration

Valeurs par défaut dans `config.py` et exemple dans `.env.example`.
Le fichier `.env` n’est pas chargé automatiquement : exporter les variables avant lancement.

```powershell
$env:FHIR_BASE_URL = "https://hapi.fhir.org/baseR4"
$env:PATIENT_IDENTIFIER_SYSTEM = "https://example.org/fhir/identifier/isis-admission-demo"
$env:ENCOUNTER_IDENTIFIER_SYSTEM = "https://example.org/fhir/identifier/isis-admission-demo-encounter"
```

Le système Patient est une référence de configuration du prototype, pas un filtre imposé :
les Patients préexistants peuvent utiliser un autre namespace. La recherche permet de saisir
explicitement le système, ou uniquement la valeur. Le séjour reçoit un identifiant ADM-UUID unique.

## Démonstration

1. Ouvrir l’interface ; le contrôle réel /metadata valide resourceType, version 4.0.1, lecture/recherche Patient et création/lecture Encounter.
2. Rechercher un identifiant métier fictif, éventuellement avec son système. Autre possibilité : nom fictif ou identifiant technique FHIR connu.
3. Zéro résultat est un état normal ; aucune création Patient n’est proposée.
4. Un résultat est affiché et sélectionné ; plusieurs résultats exigent un choix visible.
5. Choisir l’identifiant métier si le Patient en possède plusieurs. L’identité est issue de HAPI et n’est pas éditée.
6. Saisir date/heure d’admission ; le fuseau du navigateur est explicite. Service/chambre/lit sont facultatifs, à saisir ensemble.
7. Enregistrer : relecture Patient → POST Encounter → GET Encounter → contrôle référence/statut → mapping.
8. Vérifier la confirmation et les deux JSON réellement reçus, puis le message, les règles et les traces.
9. Répéter avec deux autres Patients fictifs existants, sans changer le code.

Les champs FHIR nécessaires au mapping peuvent manquer : l’admission reste possible,
la transformation concernée reste vide avec explication, et le message est marqué incomplet.
Après toute tentative d’écriture, le bouton est désactivé pour ce choix de patient.
En cas de timeout, vérifier les traces et HAPI avant de sélectionner à nouveau le patient :
le serveur pourrait avoir enregistré l’Encounter malgré l’absence de réponse.

## Mapping et pertes d’information

| Source | Cible | Règle |
|---|---|---|
| Patient.identifier | PID-3 | Identifiant unique ou sélection explicite ; valeur dans CX.1, jamais Patient.id |
| Patient.name[0] | PID-5 | family → XPN.1 ; given[0] → XPN.2 |
| Patient.birthDate | PID-7 | Date complète YYYY-MM-DD → YYYYMMDD |
| Patient.gender | PID-8 | male→M, female→F, unknown→U ; autre valeur non mappée |
| Premier Patient.telecom de type phone | PID-13 | Valeur dans XTN.1, optionnelle |
| Encounter.class.code | PV1-2 | IMP→I |
| Encounter.location[0].location.display | PV1-3 | Convention locale « service / Chambre chambre / Lit lit » → service^chambre^lit |
| Encounter.identifier unique | PV1-19 | Valeur dans CX.1 |
| Encounter.period.start | PV1-44 et EVN-2 | TS avec fuseau |
| Horloge de conversion | MSH-7 | Horodatage du message, distinct de l’admission |
| UUID généré | MSH-10 | Identifiant de message unique |

MSH-9 = ADT^A01^ADT_A01 ; MSH-12 = 2.5.1 ; MSH-18 = UNICODE UTF-8.
Les segments sont séparés par CR ; l’interface les présente sur des lignes.
Les délimiteurs HL7 présents dans les valeurs sont échappés.

Les autres noms/prénoms, identifiants, téléphones, extensions et métadonnées ne sont
pas tous représentés dans le message. Le namespace d’identifiant n’est pas transmis dans
CX.4 : perte documentée, à résoudre avec le SIH destinataire avant usage réel.
La localisation est une convention locale approximative, pas une hiérarchie Location complète.
Une localisation non interprétable reste vide et signalée.
Les dates de naissance partielles ne sont pas complétées arbitrairement.

## Erreurs et traçabilité

Gestion des timeouts, réseau inaccessible, HTTP 400/401/403/404/5xx,
resourceType inattendu et OperationOutcome, y compris sous HTTP 200.
Les diagnostics et details de l’OperationOutcome sont présentés à l’utilisateur.
Les traces gardent seulement les codes et sévérités, car les diagnostics libres peuvent contenir des données personnelles.

Traces : horodatage UTC, méthode, endpoint avec paramètres masqués, statut HTTP, résultat, ID FHIR.
Aucun nom, téléphone, date de naissance ou JSON Patient dans les traces.
La page conserve 500 traces en mémoire ; recharger la page les efface. Pas d’audit durable.
La pagination est suivie sur le même serveur ; au-delà de 20 pages, préciser la recherche.

## Tests

```sh
python -m pytest -q
```

Les tests isolés utilisent explicitement httpx.MockTransport et TestClient.
Ils ne remplacent jamais les appels réels de l’application.

Le smoke test nécessite le serveur local lancé et **crée de vrais Encounter**.
Fournir les IDs actuels de trois Patients explicitement fictifs existants (nom contenant Test ou Demo),
avec identifiant métier, nom/prénom, date complète et sexe mappable :

```sh
python tests/smoke_fhir.py --patient-ids ID_FICTIF_1 ID_FICTIF_2 ID_FICTIF_3
```

Il contrôle /metadata, recherche vide, lecture, recherche par identifiant, création
et relecture Encounter, référence Patient, champs HL7, traces et un OperationOutcome réel 404.
Aucune ressource existante n’est modifiée ni supprimée. Aucun Patient n’est créé.
Les IDs sur le serveur public ne sont pas garantis permanents.

## Références de vérification

- CDC local : décision fonctionnelle et mapping sémantique.
- [FHIR R4 Patient](https://hl7.org/fhir/R4/patient.html)
- [FHIR R4 Encounter](https://hl7.org/fhir/R4/encounter.html)
- [HL7 v2.5.1 chapitre 3](https://hl7.eu/HL7v2x/v251/std251/ch03.html)
- [CapabilityStatement HAPI](https://hapi.fhir.org/baseR4/metadata)
- [Swagger HAPI](https://hapi.fhir.org/baseR4/swagger-ui/)

## Limites et gouvernance

Prototype local pédagogique ; aucune conformité FR Core, US Core ou profil national revendiquée.
Le message couvre le noyau MSH/EVN/PID/PV1 du CDC, pas toutes les obligations d’un message
ADT complet en production. Aucun transport MLLP, ACK ou envoi vers un SIH.
Pas de PUT Encounter, création Patient, transaction atomique Patient/Encounter,
authentification applicative ni gestion de lits.

ReEIF : données fictives et minimisation (juridique), règles documentées par le CDC
(gouvernance), séparation personne/séjour (processus), ambiguïtés explicites (information),
validation FHIR/HL7 (applications), HTTPS et gestion d’indisponibilité (infrastructure).

Les essais HTTP sont exécutés depuis Python et l’application ; une exécution manuelle Postman
reste à faire si elle est exigée séparément par l’évaluation.
La publication du dépôt GitHub et les prompts individuels des membres du groupe
restent des livrables de l’équipe.


## Résultats de validation

Voir [le rapport de vérification](docs/VERIFICATION.md) : 35 tests réussis, trois patients testés sur HAPI et parcours Edge complet validé.
