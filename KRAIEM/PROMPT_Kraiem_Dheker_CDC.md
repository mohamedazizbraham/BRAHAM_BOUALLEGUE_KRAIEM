Tu es expert en interopérabilité des systèmes d’information de santé, en HL7 FHIR, HL7 v2, architecture des SI de santé et modélisation sémantique.

Je travaille sur une évaluation universitaire d’interopérabilité en santé.

Je dois concevoir, avant développement, un cahier des charges suffisamment précis pour qu’il puisse ensuite être transmis tel quel à une autre IA chargée de développer le prototype.

============================================================
1. CONTEXTE DU PROJET
============================================================

Sujet choisi :
« Admission d’un patient »

Objectif général :
Créer un prototype d’application permettant à un agent hospitalier d’enregistrer l’admission d’un patient, d’interagir réellement avec un serveur FHIR et de convertir les informations pertinentes en un message HL7 v2 adapté à une admission.

Standard source :
HL7 FHIR R4, version 4.0.1.

Format cible :
HL7 v2.

Message cible envisagé :
ADT^A01 — Admit/Visit Notification.

Version HL7 v2 envisagée :
HL7 v2.5.1.

Ressources FHIR principales envisagées :
- Patient
- Encounter

Ressources complémentaires uniquement si réellement justifiées :
- Location
- Practitioner

Le prototype doit rester réalisable dans un temps de développement court d’environ 2 heures.

Il faut donc privilégier :
- une architecture simple ;
- le minimum de ressources FHIR nécessaires ;
- des fonctionnalités démontrables ;
- aucune complexité inutile.

Le serveur FHIR sera fourni ou défini ultérieurement.

Si une information dépend du serveur FHIR et n’est pas encore connue, NE L’INVENTE PAS.
Indique clairement :
« À vérifier selon le serveur FHIR fourni ».

Ne produis aucun code dans cette étape.
Il s’agit uniquement de la conception et du cahier des charges.

============================================================
2. OBJECTIF DU CAHIER DES CHARGES
============================================================

Produire un cahier des charges fonctionnel et technique précis couvrant exactement les éléments suivants :

1. Besoin métier
2. Utilisateur
3. Scénario métier
4. Critères d’acceptation
5. Choix des spécifications d’interopérabilité
6. Ressources FHIR et profils éventuels
7. Standard cible HL7 v2
8. Terminologies utilisées
9. Interactions prévues avec le serveur FHIR
10. Architecture du prototype
11. Lecture de l’architecture selon ReEIF
12. Règles de transformation FHIR → HL7 v2
13. Mapping sémantique
14. Alignements/changements de terminologie
15. Limites et pertes d’information
16. Gestion minimale des erreurs
17. Traçabilité
18. Hypothèses et contraintes
19. Définition précise du périmètre du prototype

Le résultat doit être suffisamment précis pour qu’une IA de développement puisse ensuite construire le prototype sans devoir réinterpréter les besoins fonctionnels.

============================================================
3. BESOIN MÉTIER
============================================================

Décris clairement le problème métier.

Le scénario général est le suivant :

Un patient arrive dans un établissement de santé afin d’être hospitalisé.

Un agent d’admission doit pouvoir :
- identifier le patient ;
- rechercher s’il existe déjà dans le serveur FHIR ;
- créer le patient s’il n’existe pas ;
- enregistrer son admission ;
- associer le patient à son séjour ;
- consulter le résultat de l’admission ;
- visualiser les ressources FHIR réellement utilisées ;
- visualiser la conversion des informations vers HL7 v2 ;
- visualiser au moins un mapping terminologique.

Explique la valeur métier de cette interopérabilité.

============================================================
4. UTILISATEUR
============================================================

Définis précisément l’acteur principal.

Acteur principal envisagé :
Agent d’admission / secrétaire hospitalier.

Précise :
- son rôle ;
- ses besoins ;
- les informations qu’il saisit ;
- les informations qu’il consulte ;
- les actions qu’il effectue ;
- ce qu’il ne doit pas avoir besoin de connaître techniquement.

L’utilisateur métier ne doit pas avoir besoin de connaître FHIR ni HL7.

============================================================
5. SCÉNARIO MÉTIER
============================================================

Construis un scénario nominal simple, cohérent et testable.

Exemple de données fictives pouvant être utilisées :

Identifiant patient : PAT001
Nom : Dupont
Prénom : Jean
Date de naissance : 2002-04-10
Sexe : male
Téléphone : 0612345678
Type de séjour : hospitalisation
Service : Cardiologie
Chambre : 101
Lit : A
Date d’admission : 2026-09-15T14:00:00+02:00

Le scénario doit décrire étape par étape :

1. ouverture de l’application ;
2. saisie ou recherche du patient ;
3. interrogation du serveur FHIR ;
4. patient trouvé ou non trouvé ;
5. création éventuelle du Patient ;
6. création de l’Encounter correspondant à l’admission ;
7. récupération des données créées ;
8. affichage métier ;
9. affichage des ressources FHIR ;
10. transformation vers HL7 v2 ;
11. affichage du message ADT^A01 ;
12. affichage du mapping terminologique ;
13. journalisation de l’échange.

Ajoute également au moins deux scénarios alternatifs simples :
- patient déjà existant ;
- erreur lors de la communication avec le serveur FHIR.

============================================================
6. CRITÈRES D’ACCEPTATION
============================================================

Définis des critères d’acceptation objectifs, vérifiables et numérotés.

Utilise la forme :

CA-01
CA-02
CA-03
etc.

Les critères doivent au minimum vérifier que :

- un patient peut être recherché ;
- un Patient FHIR peut être créé si nécessaire ;
- un Encounter peut être créé ;
- le Patient est correctement référencé dans l’Encounter ;
- les ressources FHIR utilisées sont visualisables ;
- le message HL7 v2 est généré ;
- le message est de type ADT^A01 ;
- les segments essentiels sont présents ;
- le mapping terminologique est visible ;
- les erreurs sont visibles ;
- les échanges sont tracés ;
- le prototype peut être testé avec plusieurs patients fictifs différents.

Rends chaque critère mesurable.

============================================================
7. SPÉCIFICATIONS FHIR
============================================================

Analyse et justifie les choix.

Standard :
HL7 FHIR R4 4.0.1.

Pour chaque ressource retenue, explique :
- sa fonction ;
- pourquoi elle est nécessaire ;
- les attributs FHIR utiles au prototype ;
- les attributs obligatoires ou fonctionnellement nécessaires.

Patient doit notamment permettre de gérer :
- identifier ;
- name ;
- gender ;
- birthDate ;
- telecom.

Encounter doit notamment permettre de gérer :
- identifier si nécessaire ;
- status ;
- class ;
- subject ;
- period ;
- location si elle est utilisée.

Ne rajoute pas de ressources qui n’apportent aucune valeur au scénario.

Pour les profils / Implementation Guides :
- indique s’il est nécessaire d’utiliser un profil particulier ;
- sinon explique pourquoi le prototype peut rester basé sur FHIR R4 standard ;
- si IPS n’est pas utile ici, précise explicitement qu’il n’est pas utilisé.

============================================================
8. STANDARD CIBLE HL7 v2
============================================================

Justifie le choix :

HL7 v2.5.1
Message ADT^A01.

Explique :
- pourquoi ADT est approprié ;
- ce que signifie A01 ;
- dans quel contexte ce message est normalement utilisé.

Définis les segments minimums nécessaires au prototype :

MSH
EVN
PID
PV1

Pour chaque segment, donne son rôle fonctionnel.

Ne génère pas encore tout le code du message.

============================================================
9. TERMINOLOGIES
============================================================

Identifier les terminologies réellement utiles.

Prévoir au minimum un mapping du sexe administratif :

FHIR :
male
female
other
unknown

vers HL7 v2 :

M
F
O
U

Étudier également le mapping de la classe de l’Encounter vers PV1-2, par exemple :

FHIR Encounter.class :
IMP

vers HL7 v2 :
I

Ne pas créer de terminologies artificielles.

Pour chaque terminologie ou CodeSystem utilisé :
- donner son nom ;
- expliquer son rôle ;
- préciser où il intervient.

============================================================
10. INTERACTIONS AVEC LE SERVEUR FHIR
============================================================

Décrire précisément les interactions REST prévues.

Prévoir notamment :

Recherche :
GET /Patient?identifier=...

Lecture :
GET /Patient/{id}

Création :
POST /Patient

Création d’une admission :
POST /Encounter

Lecture de l’admission :
GET /Encounter/{id}

Une mise à jour PUT /Encounter/{id} ne doit être intégrée que si elle apporte une réelle valeur au prototype.

Pour chaque interaction préciser :
- objectif ;
- données envoyées ;
- résultat attendu ;
- principaux codes HTTP possibles ;
- comportement du prototype en cas d’erreur.

============================================================
11. ARCHITECTURE
============================================================

Proposer une architecture volontairement simple.

Architecture envisagée :

Utilisateur
→ Interface Web
→ Backend / logique applicative
→ Client FHIR
→ Serveur FHIR

et en parallèle :

Patient + Encounter FHIR
→ moteur de mapping
→ message HL7 v2 ADT^A01.

Séparer conceptuellement :

- interface métier ;
- communication FHIR ;
- transformation FHIR → HL7 ;
- terminologies ;
- gestion des erreurs ;
- journalisation.

Le choix technologique définitif du développement pourra être par exemple :
Python + FastAPI + interface web simple.

Cependant le cahier des charges doit rester centré sur l’architecture et non sur le code.

============================================================
12. LECTURE ReEIF
============================================================

Analyser obligatoirement le projet selon les dimensions suivantes :

A. Infrastructure / sécurité
B. Application
C. Information
D. Métier
E. Organisation
F. Juridique

Pour chaque dimension :
- expliquer les éléments concernés ;
- expliquer les choix effectués ;
- expliquer les risques principaux ;
- expliquer les limites du prototype.

Pour la sécurité et le juridique :
- données fictives uniquement ;
- pas de données personnelles réelles ;
- pas de secrets dans le dépôt GitHub ;
- HTTPS si disponible ;
- authentification si imposée par le serveur ;
- respect du principe de minimisation des données ;
- mentionner le RGPD comme exigence d’un système réel sans transformer le projet en étude juridique complète.

============================================================
13. TRANSFORMATION FHIR → HL7 v2
============================================================

Créer un tableau de mapping précis comportant au minimum les colonnes :

Information métier
Champ FHIR source
Règle de transformation
Champ HL7 v2 cible
Perte éventuelle d’information

Prévoir notamment :

Patient.identifier.value
→ PID-3

Patient.name.family + Patient.name.given
→ PID-5

Patient.birthDate
→ PID-7

Patient.gender
→ PID-8

Patient.telecom
→ PID-13

Encounter.class
→ PV1-2

Encounter.location
→ PV1-3 si Location est retenue

Encounter.identifier
→ PV1-19 si pertinent

Encounter.period.start
→ PV1-44

Décrire précisément les transformations de format.

Exemples :

FHIR :
2002-04-10

devient HL7 :
20020410

FHIR :
2026-09-15T14:00:00+02:00

devient un timestamp HL7 compatible.

FHIR :
family = Dupont
given = Jean

devient une valeur HL7 adaptée au type XPN du champ PID-5.

============================================================
14. MAPPING SÉMANTIQUE
============================================================

Différencier clairement :

- transformation syntaxique ;
- transformation structurelle ;
- transformation sémantique ;
- mapping terminologique.

Par exemple :

Transformation syntaxique :
2002-04-10 → 20020410

Mapping terminologique :
male → M

Mapping de classe :
IMP → I

Explique pourquoi une simple copie de valeur n’est pas toujours possible entre FHIR et HL7 v2.

============================================================
15. LIMITES ET PERTES D’INFORMATION
============================================================

Identifier explicitement les pertes possibles lors de la conversion FHIR → HL7 v2.

Examiner notamment :

- plusieurs identifiants FHIR mais un identifiant principal choisi ;
- plusieurs noms ;
- plusieurs numéros de téléphone ;
- plusieurs adresses ;
- structure riche de FHIR simplifiée dans HL7 v2 ;
- références FHIR transformées en informations textuelles ou codées ;
- informations Encounter non reprises dans le message minimal ;
- extensions FHIR éventuelles non prises en charge.

Pour chacune, indiquer :
- information concernée ;
- stratégie choisie ;
- conséquence.

============================================================
16. GESTION DES ERREURS
============================================================

Définir une gestion minimale mais réelle.

Cas à prévoir :

- serveur FHIR indisponible ;
- erreur HTTP ;
- ressource invalide ;
- données obligatoires manquantes ;
- Patient introuvable ;
- création Patient refusée ;
- création Encounter refusée ;
- réponse OperationOutcome ;
- échec de transformation HL7.

Pour chaque erreur :
- comportement interne ;
- message utilisateur ;
- information conservée dans les logs.

============================================================
17. TRAÇABILITÉ
============================================================

Définir ce qui doit être journalisé.

Exemple :

date/heure
méthode HTTP
ressource FHIR
URL ou endpoint
code HTTP
succès/échec
identifiant de la ressource créée
résultat de la transformation HL7.

Ne jamais journaliser inutilement des informations sensibles.

============================================================
18. INTERFACE ATTENDUE
============================================================

Décrire une interface minimale permettant de démontrer les exigences de l’évaluation.

Prévoir au minimum :

Vue 1 — Admission
Formulaire métier.

Vue 2 — Résultat métier
Résumé du patient et de l’admission.

Vue 3 — FHIR
Affichage des ressources Patient et Encounter réellement envoyées/reçues.

Vue 4 — HL7 v2
Affichage du message ADT^A01 généré.

Vue 5 — Mapping / Terminologie
Affichage visuel d’au moins un mapping tel que :
FHIR male → HL7 M.

Vue 6 — Logs
Affichage de la traçabilité minimale des échanges.

Ne pas proposer d’écrans sans utilité pour l’évaluation.

============================================================
19. PÉRIMÈTRE
============================================================

Définir clairement ce qui EST dans le prototype et ce qui N’EST PAS dans le prototype.

Dans le périmètre :
- recherche patient ;
- création patient ;
- admission ;
- Patient ;
- Encounter ;
- affichage FHIR ;
- conversion ADT^A01 ;
- mapping terminologique ;
- logs ;
- gestion minimale des erreurs.

Hors périmètre sauf nécessité :
- authentification complexe ;
- gestion complète du dossier médical ;
- facturation ;
- prescriptions ;
- résultats biologiques ;
- gestion complète des lits ;
- sortie du patient ;
- transfert ;
- architecture microservices ;
- base de données métier supplémentaire ;
- systèmes de production.

============================================================
20. CONTRAINTES
============================================================

Le prototype doit être :

- simple ;
- démontrable ;
- réalisable rapidement ;
- connecté réellement au serveur FHIR ;
- indépendant des données codées en dur ;
- testable avec plusieurs jeux de données ;
- compréhensible par les membres du groupe ;
- suffisamment propre pour être publié dans un dépôt GitHub.

Les données métier importantes ne doivent pas être simulées lorsqu’elles sont censées provenir du serveur FHIR.

============================================================
21. FORMAT DE LA RÉPONSE ATTENDUE
============================================================

Produit le résultat sous la forme d’un véritable cahier des charges universitaire, propre et structuré.

Utilise exactement l’organisation suivante :

1. Présentation du projet
2. Objectifs
3. Besoin métier
4. Acteurs et utilisateurs
5. Scénario nominal
6. Scénarios alternatifs
7. Exigences fonctionnelles
8. Critères d’acceptation
9. Spécifications d’interopérabilité
   9.1 FHIR
   9.2 Ressources
   9.3 Profils / Implementation Guides
   9.4 HL7 v2
   9.5 Terminologies
10. Interactions avec le serveur FHIR
11. Architecture fonctionnelle et technique
12. Analyse ReEIF
   12.1 Infrastructure / sécurité
   12.2 Application
   12.3 Information
   12.4 Métier
   12.5 Organisation
   12.6 Juridique
13. Mapping FHIR → HL7 v2
14. Mapping sémantique et terminologique
15. Règles de transformation
16. Limites et pertes d’information
17. Gestion des erreurs
18. Traçabilité
19. Interface utilisateur attendue
20. Périmètre et hors périmètre
21. Contraintes et hypothèses
22. Tests et validation attendus
23. Synthèse destinée à l’IA de développement

Utilise :
- des paragraphes courts ;
- des tableaux quand cela améliore la compréhension ;
- des noms exacts des ressources et champs FHIR ;
- des noms exacts des segments/champs HL7 v2 ;
- un vocabulaire académique mais compréhensible.

Évite :
- les formulations vagues ;
- les fonctionnalités inutiles ;
- les architectures disproportionnées ;
- les informations non vérifiées ;
- l’invention de contraintes absentes du sujet.

============================================================
22. VÉRIFICATION FINALE OBLIGATOIRE
============================================================

Avant de terminer, effectue une auto-vérification du cahier des charges.

Crée à la fin une matrice :

Exigence de l’énoncé | Section du CDC | Couvert ? | Remarque

Elle doit vérifier explicitement :

- besoin métier ;
- utilisateur ;
- scénario ;
- critères d’acceptation ;
- FHIR + version ;
- ressources/profils/IG ;
- standard cible ;
- terminologies ;
- lecture FHIR ;
- recherche FHIR ;
- création/mise à jour si nécessaire ;
- infrastructure/sécurité ;
- application ;
- information ;
- métier ;
- organisation ;
- juridique ;
- règles de transformation ;
- mapping sémantique ;
- limites/pertes d’information ;
- précision suffisante pour transmission à l’IA de développement.

Si une exigence n’est pas couverte, corrige le cahier des charges avant de produire la réponse finale.

Enfin, termine par une section :

« Instructions techniques pour l’IA de développement »

Cette section doit résumer sans ambiguïté :
- ce qu’elle devra développer ;
- les endpoints FHIR à utiliser ;
- les ressources ;
- les champs nécessaires ;
- les mappings ;
- le résultat HL7 attendu ;
- les écrans attendus ;
- les erreurs à gérer ;
- les critères permettant de considérer le prototype terminé.

IMPORTANT :
Ne commence pas le développement.
Ne génère aucun fichier de code.
Cette étape concerne uniquement la conception.