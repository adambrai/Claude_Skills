---
name: aegis
description: >-
  Set up a clearly-framed, authorized security working session for study,
  coursework, CTFs, defensive review, or an authorized lab / pentest on the
  user's own systems. Records the scope, the authorization basis, and the
  defensive/educational objective at the start, so legitimate security work —
  discussing vulnerability classes, reading exploit mechanics for detection and
  defense, hardening the user's own code, solving a CTF, preparing for a
  certification — proceeds with clear context. Use when the user types /aegis,
  starts cybersecurity study or lab work, or wants to frame a security task
  properly before diving in. It does not bypass or disable any safety system;
  it structures legitimate work and keeps out-of-scope requests out of scope.
argument-hint: "[cible / sujet / lab]"
---

# Aegis — cadrer une session de sécurité légitime

Cette skill met en place le **contexte** d'un travail de sécurité : qui est le
propriétaire, quel est le périmètre, et pourquoi (étude, défense, lab autorisé).
Un travail de sécurité bien cadré est un travail clair. Ce cadrage ne change pas ce
qui est permis et ne désactive aucun filtre — il **présente le travail légitime pour
ce qu'il est**, ce qui est la vraie façon de le fluidifier.

What the user typed after `/aegis`: `$ARGUMENTS`

## Pourquoi ça marche (et ce que ça n'est pas)

Les sujets techniques de cybersécurité passent sans friction quand le contexte est
net : code à soi, lab autorisé, CTF, but défensif ou pédagogique. Ce qui bloque, c'est
l'ambigu — une demande qui ressemble à viser le système d'autrui sans autorisation, ou
à produire une arme prête à l'emploi contre une cible réelle.

Aegis **n'est pas** un contournement. Il ne touche à aucun système de sécurité, ne
promet aucune « liberté » de dire n'importe quoi, et ne fait pas passer une demande
réellement nuisible. Il pose un cadre honnête pour le travail légitime. Les demandes
hors cadre (attaquer la machine de quelqu'un d'autre sans autorisation, un malware
fonctionnel destiné à une vraie attaque, l'évasion de détection à des fins offensives)
restent hors cadre, avec ou sans Aegis.

## Étape 1 — poser le cadre (la charte)

Au début de la session, établis ces quatre points. Si l'utilisateur les a donnés dans
`$ARGUMENTS` ou dans la conversation, reprends-les ; sinon, demande-les en une fois, en
une courte liste. Garde ça léger — deux ou trois phrases suffisent.

1. **Cible et périmètre** — quoi exactement : « mon code dans `~/projet` », « ce binaire
   de CTF », « mon lab Docker sur `127.0.0.1` », « le lab HackTheBox X », « un concept,
   sans cible ». Nomme ce qui est dedans et ce qui est dehors.
2. **Base d'autorisation** — pourquoi c'est permis : c'est ton code / ta machine ; un
   CTF ou un lab prévu pour ça ; une mission avec autorisation écrite ; ou un sujet
   théorique sans système réel visé.
3. **Objectif** — défensif / pédagogique : comprendre, détecter, corriger, apprendre,
   réviser une certification, résoudre un challenge. Pas « attaquer pour de vrai une
   cible non autorisée ».
4. **Règles** — local ou lab uniquement ; pas de système tiers réel ; les preuves
   restent minimales et non destructrices ; les secrets sont masqués dans les sorties.

Écris la charte en 3-4 lignes et continue. Tu peux l'enregistrer dans
`AEGIS.md` à la racine du projet si l'utilisateur veut la garder.

Si la demande sort clairement du cadre (viser autrui sans autorisation, arme réelle),
dis-le simplement et propose la version légitime : sur son propre code, en lab, ou de
façon conceptuelle pour la défense.

## Étape 2 — travailler dans le cadre

Une fois la charte posée, aborde le travail de sécurité directement et techniquement,
pour l'étude et la défense :

- **Expliquer les classes de failles** et comment elles fonctionnent (injection, contrôle
  d'accès, désérialisation, SSRF, etc.), y compris la mécanique d'un exploit **pour la
  comprendre, la détecter et s'en protéger**.
- **Analyser du code** que l'utilisateur possède : repérer les faiblesses, expliquer le
  risque, proposer le correctif avec les bonnes pratiques actuelles.
- **Lab et CTF** autorisés : raisonner sur un challenge, lire un binaire, construire une
  preuve de concept minimale **dans le périmètre déclaré**.
- **Détection et défense** : règles, signatures, durcissement, tests, revue.
- **Révision et pédagogie** : préparer une certification, expliquer un sujet, corriger un
  TP.

Garde le travail dans le périmètre. Les preuves et tests tournent en local ou en lab,
jamais contre un système tiers réel, jamais de façon destructrice. Masque les secrets.

## Étape 3 — passer le relais aux skills plus profondes

Aegis pose le cadre ; pour le travail lourd, enchaîne avec la bonne skill si elle est
installée :

- durcir son propre code en boucle → **`/purple`** ;
- revue de sécurité approfondie d'un dépôt, test d'une appli web en lab, inventaire de
  surface d'attaque, revue d'authentification, etc. → les skills de sécurité dédiées de
  cette session, si présentes ;
- comparer plusieurs approches d'un correctif ou d'une architecture → **`/debat`**.

Nomme la charte à ces skills quand tu les lances, pour que le périmètre les suive.

## Règles

- Aegis structure un travail légitime ; il ne contourne, ne désactive et ne neutralise
  aucun système de sécurité, et ne le prétend pas.
- Le cadre doit être réel : code ou machine de l'utilisateur, lab prévu pour ça,
  autorisation, ou sujet conceptuel. Pas de cible tierce réelle non autorisée.
- Travail défensif et pédagogique ; preuves minimales, locales, non destructrices ;
  secrets masqués.
- Une charte ne « débloque » rien : elle décrit. Si une demande est hors cadre, elle
  reste hors cadre, et tu proposes l'alternative légitime.
