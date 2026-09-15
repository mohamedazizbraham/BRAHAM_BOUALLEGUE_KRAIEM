AVANT DE COMMENCER :
Le cahier des charges officiel du projet se trouve ici :
docs\Cahier_des_charges_CONSOLIDE_Admission_Patient_FHIR_HL7v2.pdf
Lis-le entièrement avant de créer ou modifier du code.
Ce document constitue la source principale de vérité concernant :
- le besoin métier ;
- le périmètre ;
- les ressources FHIR ;
- les critères d’acceptation ;
- les mappings FHIR → HL7 v2 ;
- les règles de transformation ;
- les vues attendues ;
- les tests ;
- la gestion des erreurs ;
- la traçabilité.
Le prompt de réalisation précise l’implémentation à produire.
En cas de contradiction entre une supposition de ta part et le CDC,
suis le CDC.
MISE À JOUR DEPUIS LA RÉDACTION DU CDC :
Le serveur FHIR est maintenant connu.
Utiliser :
FHIR_BASE_URL=https://hapi.fhir.org/baseR4
Il s’agit du serveur HAPI FHIR R4.
Toute mention dans le CDC de :
« À vérifier selon le serveur FHIR fourni »
concernant l’URL du serveur doit donc être considérée comme résolue
par cette configuration.


Tu es un ingénieur logiciel senior spécialisé en :
- interopérabilité en santé ;
- HL7 FHIR R4 ;
- HL7 v2.5.1 ;
- Python ;
- FastAPI ;
- APIs REST ;
- développement web frontend simple ;
- tests et validation.

Tu dois maintenant DÉVELOPPER un prototype fonctionnel d’interopérabilité en santé.

IMPORTANT :
Un cahier des charges intitulé :

« Cahier des charges fonctionnel et technique —
Prototype d’interopérabilité — Admission d’un patient —
HL7 FHIR R4 → HL7 v2.5.1 ADT^A01 »

est fourni avec cette demande.

CE CAHIER DES CHARGES EST LA SOURCE DE VÉRITÉ.

Lis-le entièrement avant de commencer.

Ne modifie pas arbitrairement :
- le périmètre ;
- les ressources FHIR ;
- les mappings ;
- le message HL7 ;
- les critères d’acceptation.

Si le cahier des charges et une hypothèse de ta part sont en conflit,
LE CAHIER DES CHARGES EST PRIORITAIRE.

============================================================
1. OBJECTIF
============================================================

Développer une application web minimale permettant de gérer
l’admission d’un patient.

Le workflow doit être réellement fonctionnel :

Utilisateur
   ↓
Recherche patient
   ↓
Serveur FHIR réel
   ↓
Patient existant ?
   ├── Oui → utiliser le Patient existant
   └── Non → créer le Patient
   ↓
Créer Encounter
   ↓
Relire / récupérer les ressources réellement enregistrées
   ↓
Afficher résultat métier
   ↓
Afficher Patient + Encounter FHIR
   ↓
Transformer les données
   ↓
Générer HL7 v2.5.1 ADT^A01
   ↓
Afficher mappings
   ↓
Afficher logs techniques

Il ne s’agit PAS d’une maquette.

Les appels au serveur FHIR doivent être RÉELS.

============================================================
2. SERVEUR FHIR
============================================================

Utiliser exactement :

FHIR_BASE_URL=https://hapi.fhir.org/baseR4

Version :

HL7 FHIR R4 — 4.0.1

Le serveur est un serveur public HAPI FHIR de test.

Ne jamais utiliser de données médicales ou personnelles réelles.

Toutes les données doivent être fictives.

Avant de commencer les interactions métier, vérifier le serveur avec :

GET https://hapi.fhir.org/baseR4/metadata

Vérifier que la réponse est un CapabilityStatement.

Ne jamais simuler une réponse FHIR lorsque le serveur est supposé
être interrogé.

============================================================
3. CONTRAINTE DE TEMPS
============================================================

Le prototype doit être réalisable rapidement.

Privilégier systématiquement :
- simplicité ;
- lisibilité ;
- fonctionnement de bout en bout ;
- conformité au CDC.

Ne pas créer :
- microservices ;
- Docker complexe ;
- base de données ;
- React ;
- authentification applicative ;
- architecture distribuée ;
- fonctionnalités non demandées.

Le fonctionnement prime sur les améliorations esthétiques.

============================================================
4. STACK À UTILISER
============================================================

Backend :

Python 3
FastAPI
httpx
Pydantic
Uvicorn

Frontend :

HTML5
CSS3
JavaScript vanilla

Utiliser éventuellement Jinja2 pour servir l’interface depuis FastAPI.

IMPORTANT :

Le navigateur ne doit pas communiquer directement avec HAPI FHIR.

Architecture :

Navigateur
    ↓
FastAPI
    ↓
httpx
    ↓
https://hapi.fhir.org/baseR4

Cela permet :
- de centraliser les appels FHIR ;
- de gérer les erreurs ;
- de gérer les logs ;
- d’éviter les problèmes CORS ;
- de garder la logique FHIR côté backend.

============================================================
5. STRUCTURE DU PROJET
============================================================

Créer une structure simple de ce type :

admission-fhir/
│
├── main.py
├── config.py
├── fhir_client.py
├── hl7_mapper.py
├── terminology.py
├── schemas.py
├── trace_store.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── app.js
│
├── tests/
│   └── test_hl7_mapper.py
│
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore

Ne complexifie pas davantage cette architecture.

============================================================
6. CONFIGURATION
============================================================

La Base URL doit être configurable.

Dans config.py :

FHIR_BASE_URL

Valeur par défaut :

https://hapi.fhir.org/baseR4

Prévoir également un namespace d’identifiant pour éviter les
collisions sur le serveur public.

Par exemple :

PATIENT_IDENTIFIER_SYSTEM =
https://example.org/fhir/identifier/isis-admission-demo

Ce namespace est uniquement technique et destiné au prototype.

L’identifiant métier reste saisi par l’utilisateur.

Exemple :

PAT001
PAT002
PAT003

Dans FHIR :

identifier.system =
https://example.org/fhir/identifier/isis-admission-demo

identifier.value =
PAT001

============================================================
7. HEADERS FHIR
============================================================

Pour les appels FHIR utiliser :

Accept: application/fhir+json

Pour POST :

Content-Type: application/fhir+json

Ajouter si possible :

Prefer: return=representation

Ne jamais considérer un POST comme réussi uniquement parce que la
requête a été envoyée.

Vérifier réellement le code HTTP.

============================================================
8. CLIENT FHIR
============================================================

Créer un module fhir_client.py responsable exclusivement des
interactions avec HAPI FHIR.

Implémenter :

check_server()

search_patient(identifier)

get_patient(fhir_id)

create_patient(patient_data)

create_encounter(encounter_data)

get_encounter(fhir_id)

Chaque méthode doit :

1. effectuer un vrai appel HTTP ;
2. définir un timeout raisonnable ;
3. enregistrer une trace technique ;
4. vérifier le code HTTP ;
5. détecter OperationOutcome ;
6. retourner une structure exploitable au reste de l’application.

Ne PAS implémenter PUT /Encounter pour ce MVP.

============================================================
9. RECHERCHE PATIENT
============================================================

La recherche doit être réellement effectuée sur le serveur FHIR.

Utiliser préférentiellement :

GET /Patient?identifier={system}|{value}

avec httpx params afin d’encoder correctement les paramètres.

Conceptuellement :

identifier =
https://example.org/fhir/identifier/isis-admission-demo|PAT001

Le serveur doit retourner un Bundle.

Traiter trois situations.

CAS 1 — total = 0

Afficher :

« Aucun patient trouvé. Vous pouvez créer ce patient. »

CAS 2 — un résultat

Afficher le patient trouvé.

Ne PAS recréer ce Patient.

CAS 3 — plusieurs résultats

Ne jamais choisir silencieusement le premier.

Afficher la liste des résultats permettant de sélectionner le bon
Patient.

============================================================
10. DONNÉES DU FORMULAIRE
============================================================

Créer un formulaire comprenant :

Identifiant patient
Nom
Prénom
Date de naissance
Sexe
Téléphone
Service
Chambre
Lit
Date et heure d’admission

Sexe disponible :

male
female
other
unknown

Le type de séjour du MVP est :

Hospitalisation

Les valeurs métier doivent venir du formulaire.

IMPORTANT :

Aucun patient ne doit être codé en dur dans la logique.

PAT001 / Jean Dupont peuvent éventuellement être utilisés comme
exemple de démonstration dans le README ou comme placeholders,
mais l’application doit fonctionner avec :

PAT002
PAT003
XYZ123
etc.

sans modification du code.

============================================================
11. CRÉATION PATIENT FHIR
============================================================

Lorsqu’aucun Patient n’existe, construire une vraie ressource
FHIR R4 Patient.

Structure minimale :

{
  "resourceType": "Patient",
  "identifier": [
    {
      "system": "...",
      "value": "..."
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "...",
      "given": ["..."]
    }
  ],
  "gender": "...",
  "birthDate": "...",
  "telecom": [
    {
      "system": "phone",
      "value": "...",
      "use": "mobile"
    }
  ]
}

Envoyer :

POST /Patient

Ne pas inventer l’id FHIR.

L’id doit provenir de la réponse réelle du serveur.

Après création, récupérer :

Patient.id

et, si nécessaire, relire :

GET /Patient/{id}

La ressource réellement enregistrée doit être conservée pour la vue
FHIR.

============================================================
12. CRÉATION ENCOUNTER
============================================================

Après récupération ou création du Patient, construire Encounter.

Utiliser :

resourceType = Encounter

status = in-progress

class.system =
http://terminology.hl7.org/CodeSystem/v3-ActCode

class.code =
IMP

class.display =
inpatient encounter

subject.reference =
Patient/{FHIR_PATIENT_ID}

period.start =
date d’admission fournie par l’utilisateur.

Créer un identifiant de séjour UNIQUE à chaque admission.

Par exemple :

ADM-{UUID}

Ne pas utiliser toujours la même valeur.

Utiliser un Identifier.system propre au prototype.

============================================================
13. LOCALISATION
============================================================

Conformément au CDC :

NE PAS créer de ressources Location séparées.

Représenter la localisation dans Encounter.location.

Exemple conceptuel :

"location": [
  {
    "location": {
      "display": "Cardiologie / Chambre 101 / Lit A"
    }
  }
]

La valeur doit être construite à partir des données réellement saisies :

service
chambre
lit

Ne pas coder :

Cardiologie
101
A

en dur.

============================================================
14. CRÉATION ENCOUNTER SUR FHIR
============================================================

Envoyer réellement :

POST /Encounter

Vérifier la réponse.

Récupérer :

Encounter.id

Puis effectuer si nécessaire :

GET /Encounter/{id}

pour afficher exactement la ressource enregistrée par le serveur.

Si la création échoue :

NE PAS afficher
« Admission réussie ».

Afficher l’erreur.

============================================================
15. VUE MÉTIER
============================================================

La première exigence de l’évaluation est une vue réellement
exploitable par l’utilisateur.

Créer une interface claire avec en haut :

« Admission d’un patient »

La vue métier doit permettre :

1. saisir l’identifiant ;
2. rechercher ;
3. voir si le patient existe ;
4. renseigner les informations ;
5. enregistrer l’admission ;
6. voir la confirmation.

Après admission réussie afficher une carte :

ADMISSION ENREGISTRÉE

Patient :
Jean DUPONT

Identifiant métier :
PAT001

Identifiant FHIR Patient :
...

Identifiant FHIR Encounter :
...

Admission :
...

Service :
...

Chambre :
...

Lit :
...

Toutes les informations doivent provenir du workflow courant.

============================================================
16. ORGANISATION DE L’INTERFACE
============================================================

Créer une interface unique avec six onglets ou sections :

1 — Admission

2 — Résultat métier

3 — Ressources FHIR

4 — HL7 v2

5 — Mapping / Terminologie

6 — Logs

Ces six parties doivent être clairement visibles pendant la
démonstration.

L’interface doit être moderne, lisible et sobre.

Ne pas passer trop de temps sur le design.

============================================================
17. VUE FHIR
============================================================

La vue FHIR doit afficher les ressources RÉELLEMENT utilisées.

Afficher deux blocs JSON formatés :

PATIENT FHIR

{ vrai JSON Patient }

ENCOUNTER FHIR

{ vrai JSON Encounter }

Utiliser une police monospace.

Ajouter une coloration légère si simple à réaliser.

Les ressources affichées doivent correspondre aux réponses réelles
du serveur, pas à des objets fictifs préparés uniquement pour
l’interface.

============================================================
18. CONVERSION FHIR → HL7 v2
============================================================

Créer hl7_mapper.py.

Ce module reçoit :

Patient FHIR
+
Encounter FHIR

et génère :

HL7 v2.5.1 ADT^A01

Le message doit contenir au minimum :

MSH
EVN
PID
PV1

============================================================
19. STRUCTURE HL7 ATTENDUE
============================================================

Construire quelque chose conceptuellement équivalent à :

MSH|^~\&|ADMISSION_APP|ISIS_DEMO|SIH|HOSPITAL|{timestamp}||ADT^A01^ADT_A01|{message_id}|P|2.5.1
EVN|A01|{admission_timestamp}
PID|...
PV1|...

IMPORTANT :

Ne pas simplement concaténer arbitrairement des séparateurs.

Construire correctement les champs afin que les positions HL7 soient
respectées.

Vérifier particulièrement :

PID-3
PID-5
PID-7
PID-8
PID-13

PV1-2
PV1-3
PV1-19
PV1-44

============================================================
20. MAPPING FHIR → HL7
============================================================

Implémenter exactement le mapping fonctionnel suivant.

Patient.identifier.value
→ PID-3

Patient.name[0].family
+
Patient.name[0].given[0]
→ PID-5

Patient.birthDate
→ PID-7

Patient.gender
→ PID-8

Patient.telecom
→ PID-13

Encounter.class.code
→ PV1-2

Encounter.location
→ PV1-3

Encounter.identifier.value
→ PV1-19

Encounter.period.start
→ PV1-44

============================================================
21. MAPPING TERMINOLOGIQUE SEXE
============================================================

Créer terminology.py.

Implémenter exactement :

male    → M
female  → F
other   → O
unknown → U

Pour toute valeur inattendue :

→ U

et créer un warning dans les logs.

Ne pas copier directement :

male

dans PID-8.

============================================================
22. MAPPING CLASSE D’ENCOUNTER
============================================================

Implémenter :

FHIR :

IMP

→ HL7 v2 PV1-2 :

I

Si une autre classe inattendue est rencontrée :

- ne pas planter silencieusement ;
- créer une erreur ou un warning explicite ;
- afficher la valeur source.

============================================================
23. TRANSFORMATION DATE DE NAISSANCE
============================================================

FHIR :

2002-04-10

doit devenir :

20020410

dans :

PID-7

Créer une fonction dédiée et testable.

============================================================
24. TRANSFORMATION TIMESTAMP
============================================================

FHIR :

2026-09-15T14:00:00+02:00

doit devenir :

20260915140000+0200

pour HL7.

La fonction doit fonctionner avec d’autres dates.

Ne jamais faire uniquement un remplacement spécifique à cet exemple.

Utiliser une vraie conversion de datetime.

============================================================
25. NOM
============================================================

FHIR :

family = Dupont
given = Jean

doit devenir conceptuellement :

Dupont^Jean

dans PID-5.

Respecter la structure :

PID-5.1 = nom
PID-5.2 = prénom

============================================================
26. LOCALISATION HL7
============================================================

FHIR :

service = Cardiologie
chambre = 101
lit = A

doit devenir conceptuellement :

Cardiologie^101^A

dans :

PV1-3

Les valeurs doivent provenir de l’Encounter réellement utilisé.

============================================================
27. MESSAGE CONTROL ID
============================================================

MSH-10 doit être unique.

Utiliser par exemple UUID.

Ne pas coder :

MSG000001

en permanence.

============================================================
28. TIMESTAMPS
============================================================

Le timestamp du message MSH doit être généré au moment de la
conversion.

L’heure d’admission de EVN et PV1 doit provenir de :

Encounter.period.start

Ne pas confondre :

date de création du message

et :

date d’admission.

============================================================
29. VUE HL7 v2
============================================================

Afficher le message généré dans une zone dédiée.

Exemple visuel :

HL7 v2.5.1 — ADT^A01

MSH|...
EVN|...
PID|...
PV1|...

Police monospace.

Chaque segment sur une ligne.

Ajouter un bouton :

Copier

uniquement si cela reste simple.

============================================================
30. VUE MAPPING / TERMINOLOGIE
============================================================

Cette vue est OBLIGATOIRE.

Afficher un tableau présentant réellement les valeurs utilisées.

Colonnes :

Concept
FHIR source
Transformation
HL7 cible
Destination

Exemple dynamique :

Sexe
male
male → M
M
PID-8

Classe de séjour
IMP
IMP → I
I
PV1-2

Date de naissance
2002-04-10
suppression syntaxique / conversion
20020410
PID-7

Date d’admission
2026-09-15T14:00:00+02:00
conversion timestamp
20260915140000+0200
PV1-44

Les valeurs doivent changer lorsque l’on utilise un autre patient.

============================================================
31. LOGS / TRAÇABILITÉ
============================================================

Créer une traçabilité technique minimale.

Pour chaque interaction enregistrer :

timestamp
méthode HTTP
ressource
endpoint
code HTTP
succès / erreur
id FHIR éventuellement retourné

Exemple :

14:03:02 | GET  | Patient   | /Patient?identifier=... | 200 | OK
14:03:08 | POST | Patient   | /Patient                | 201 | OK
14:03:10 | POST | Encounter | /Encounter              | 201 | OK
14:03:11 | MAP  | ADT^A01   | FHIR → HL7             | --- | OK

IMPORTANT :

Ne pas mettre dans les logs :
- nom complet ;
- téléphone ;
- date de naissance ;
- JSON Patient complet.

La vue FHIR est là pour la démonstration des ressources.

Les logs doivent rester techniques.

============================================================
32. OPERATIONOUTCOME
============================================================

Créer une fonction capable de reconnaître :

{
  "resourceType": "OperationOutcome",
  ...
}

Lorsque cette ressource est reçue :

examiner :

issue[].severity
issue[].code
issue[].details.text
issue[].diagnostics

Construire un message utilisateur compréhensible.

Conserver le détail technique utile dans les logs.

Ne pas afficher simplement :

HTTP Error.

============================================================
33. ERREURS À GÉRER
============================================================

Gérer au minimum :

serveur FHIR inaccessible ;

timeout ;

HTTP 400 ;

HTTP 401 ;

HTTP 403 ;

HTTP 404 ;

HTTP 5xx ;

Patient invalide ;

création Patient refusée ;

création Encounter refusée ;

OperationOutcome ;

champ nécessaire à la transformation absent ;

mapping inconnu.

Règle absolue :

UNE ERREUR NE DOIT JAMAIS ÊTRE AFFICHÉE COMME UN SUCCÈS.

============================================================
34. PATIENT ABSENT N’EST PAS UNE ERREUR
============================================================

Attention :

Un Bundle de recherche avec 0 Patient n’est PAS une erreur.

C’est un état métier normal.

Afficher :

« Aucun patient trouvé. Vous pouvez créer ce patient. »

============================================================
35. PAS DE DONNÉES MÉTIER CODÉES EN DUR
============================================================

C’est une exigence majeure de l’évaluation.

Interdit :

if patient == "PAT001":
    utiliser Jean Dupont

Interdit :

service = "Cardiologie"

Interdit :

chambre = "101"

Interdit :

lit = "A"

Toutes ces valeurs doivent venir :

- du formulaire ;
- ou des vraies ressources FHIR.

Les seules constantes autorisées concernent les standards :

FHIR R4
IMP
in-progress
HL7 v2.5.1
ADT^A01
mappings terminologiques.

============================================================
36. TEST AVEC PLUSIEURS PATIENTS
============================================================

Le prototype doit fonctionner sans modification de code avec au
moins trois patients fictifs différents.

Préparer par exemple les tests manuels avec :

PAT-TEST-{suffixe unique}-01
PAT-TEST-{suffixe unique}-02
PAT-TEST-{suffixe unique}-03

Ne pas supposer que PAT001 est disponible sur un serveur public.

Ajouter un suffixe unique si nécessaire afin d’éviter les collisions
avec les autres utilisateurs du serveur HAPI.

============================================================
37. TESTS UNITAIRES
============================================================

Créer au minimum des tests pour :

gender_to_hl7("male") == "M"

gender_to_hl7("female") == "F"

gender_to_hl7("other") == "O"

gender_to_hl7("unknown") == "U"

encounter_class_to_hl7("IMP") == "I"

FHIR date :
2002-04-10

→

20020410

FHIR datetime :
2026-09-15T14:00:00+02:00

→

20260915140000+0200

Tester également que le message contient :

MSH
EVN
PID
PV1

et :

ADT^A01

============================================================
38. TEST RÉEL FHIR
============================================================

Effectuer un smoke test réel :

1. GET /metadata

2. rechercher un identifiant fictif unique ;

3. constater 0 résultat ;

4. POST Patient ;

5. récupérer son vrai id ;

6. rechercher à nouveau le même identifiant ;

7. constater que le Patient existe ;

8. POST Encounter ;

9. vérifier :

Encounter.subject.reference =
Patient/{id}

10. relire Patient ;

11. relire Encounter ;

12. générer ADT^A01.

Ne jamais supprimer ou modifier arbitrairement les ressources
appartenant à d’autres utilisateurs du serveur public.

============================================================
39. UX MINIMALE
============================================================

Créer une interface agréable mais simple.

Prévoir :

- header avec titre du projet ;
- indicateur serveur FHIR connecté / erreur ;
- formulaire sous forme de carte ;
- boutons clairement visibles ;
- messages succès en vert ;
- messages erreur en rouge ;
- onglets ou navigation interne ;
- blocs JSON monospace ;
- bloc HL7 monospace ;
- tableau mapping ;
- tableau logs ;
- responsive simple.

Aucune bibliothèque frontend lourde.

============================================================
40. API INTERNE FASTAPI
============================================================

Tu peux créer des routes internes simples telles que :

GET /
→ interface

GET /api/health
→ vérification du serveur FHIR

GET /api/patients/search?identifier=...

POST /api/patients

POST /api/admissions

GET /api/patients/{id}

GET /api/encounters/{id}

La structure exacte peut être adaptée si elle reste simple.

IMPORTANT :

Les routes FastAPI ne remplacent pas FHIR.

Elles servent d’intermédiaire vers le véritable serveur :

https://hapi.fhir.org/baseR4

============================================================
41. README
============================================================

Créer un README.md contenant :

titre du projet ;

objectif ;

architecture ;

stack ;

prérequis ;

installation ;

commande de lancement ;

URL locale ;

FHIR Base URL ;

workflow de démonstration ;

description des six vues ;

mapping FHIR → HL7 ;

scénario de test ;

limites ;

rappel :

« Données fictives uniquement ».

Ajouter les commandes exactes :

python -m venv .venv

puis activation environnement adaptée au système.

pip install -r requirements.txt

uvicorn main:app --reload

et indiquer l’URL :

http://127.0.0.1:8000

============================================================
42. .gitignore
============================================================

Exclure au minimum :

.venv/
__pycache__/
*.pyc
.env
.pytest_cache/
.idea/
.vscode/

Ne jamais pousser un secret.

============================================================
43. IMPORTANT POUR LE DÉPÔT GITHUB
============================================================

Le code commun sera placé sur GitHub.

Donc :

- code lisible ;
- noms explicites ;
- commentaires seulement lorsque nécessaires ;
- aucune donnée personnelle ;
- aucun secret ;
- aucune dépendance inutile ;
- README fonctionnel.

============================================================
44. ORDRE DE DÉVELOPPEMENT OBLIGATOIRE
============================================================

Travaille dans cet ordre.

ÉTAPE A
Lire le CDC.

ÉTAPE B
Créer l’architecture minimale.

ÉTAPE C
Tester :

GET https://hapi.fhir.org/baseR4/metadata

ÉTAPE D
Implémenter fhir_client.

ÉTAPE E
Tester recherche Patient réelle.

ÉTAPE F
Tester création Patient réelle.

ÉTAPE G
Tester création Encounter réelle.

ÉTAPE H
Implémenter transformations HL7.

ÉTAPE I
Écrire les tests des mappings.

ÉTAPE J
Créer l’interface.

ÉTAPE K
Connecter l’interface aux vraies opérations.

ÉTAPE L
Tester le scénario complet.

ÉTAPE M
Corriger les erreurs.

ÉTAPE N
Faire seulement ensuite les améliorations visuelles.

NE COMMENCE PAS par passer du temps sur le CSS.

============================================================
45. CRITÈRES DE TERMINAISON
============================================================

Ne considère pas le projet terminé tant que tous ces points ne sont
pas vrais :

[ ] https://hapi.fhir.org/baseR4/metadata répond

[ ] Patient est réellement recherché sur HAPI FHIR

[ ] un Patient absent peut être créé

[ ] l’id FHIR réel est récupéré

[ ] le même Patient recherché ensuite est retrouvé

[ ] un Patient existant n’est pas recréé

[ ] Encounter est réellement créé

[ ] Encounter.subject référence le vrai Patient

[ ] Patient réel est affiché

[ ] Encounter réel est affiché

[ ] ADT^A01 est généré

[ ] MSH est présent

[ ] EVN est présent

[ ] PID est présent

[ ] PV1 est présent

[ ] PID-3 contient l’identifiant métier

[ ] PID-5 contient nom/prénom

[ ] PID-7 contient la date transformée

[ ] PID-8 contient le code HL7 correspondant

[ ] PV1-2 vaut I pour IMP

[ ] PV1-3 contient service/chambre/lit

[ ] PV1-19 contient l’identifiant de séjour

[ ] PV1-44 contient l’heure d’admission

[ ] vue Admission fonctionne

[ ] vue Résultat métier fonctionne

[ ] vue FHIR fonctionne

[ ] vue HL7 fonctionne

[ ] vue Mapping fonctionne

[ ] vue Logs fonctionne

[ ] une erreur FHIR est correctement affichée

[ ] OperationOutcome est géré

[ ] les logs montrent les vrais échanges

[ ] trois patients fictifs différents peuvent être utilisés sans
modifier le code

[ ] aucune donnée métier censée provenir du workflow n’est simulée

============================================================
46. VÉRIFICATION FINALE
============================================================

Une fois le développement terminé :

1. lancer les tests ;

2. lancer le serveur ;

3. vérifier /api/health ;

4. exécuter réellement un scénario complet ;

5. vérifier les ressources sur HAPI ;

6. vérifier le message HL7 ;

7. contrôler les positions PID/PV1 ;

8. contrôler le mapping terminologique ;

9. contrôler les logs ;

10. comparer chaque fonctionnalité avec les critères du CDC.

Si une fonctionnalité du CDC n’est pas implémentée, corrige-la avant
de considérer le projet terminé.

============================================================
47. MODE DE TRAVAIL ATTENDU
============================================================

Tu es chargé de RÉALISER le projet, pas uniquement d’expliquer ce
qu’il faudrait faire.

Commence par :

1. résumer en quelques lignes ce que tu vas construire ;

2. afficher l’arborescence retenue ;

3. vérifier le serveur FHIR ;

4. créer les fichiers ;

5. implémenter le projet ;

6. lancer les tests ;

7. corriger les erreurs rencontrées ;

8. donner à la fin les commandes exactes permettant de lancer
l’application.

Lorsque tu rencontres une erreur réelle du serveur ou de
l’application :

NE L’IGNORE PAS.

Analyse-la et corrige l’implémentation.

Ne remplace jamais une interaction qui échoue par une fausse donnée
pour faire fonctionner la démonstration.

============================================================
48. PRIORITÉ ABSOLUE
============================================================

La priorité absolue est :

FORMULAIRE
→ VRAI SERVEUR FHIR
→ PATIENT
→ ENCOUNTER
→ VRAIES RESSOURCES FHIR
→ MAPPING
→ HL7 ADT^A01
→ TERMINOLOGIE
→ LOGS

avant toute fonctionnalité supplémentaire.

Commence maintenant la réalisation.