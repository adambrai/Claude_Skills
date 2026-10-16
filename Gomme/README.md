# Gomme

Skill pour Claude Code qui t'aide à réduire ce qu'internet montre de toi. Elle cherche les
pages publiques qui te concernent, t'aide à choisir la bonne démarche pour chacune, rédige
les demandes RGPD et suit les réponses avec les délais légaux.

Elle ne travaille que sur tes propres données. Rien n'est envoyé, soumis ou modifié sans
ton accord explicite, et aucune méthode ne garantit de tout retrouver ni de tout effacer.

## Ce que fait la skill, et ce qu'elle ne fait pas

Elle cherche des pages publiques, classe les résultats et rédige les demandes. Elle ne
supprime rien elle-même : c'est le site, ou le moteur de recherche, qui décide. Il y a
trois démarches différentes qu'il ne faut pas confondre :

- supprimer le contenu sur le site source ;
- demander le déréférencement à un moteur de recherche (un résultat retiré de Google peut
  rester en ligne sur le site d'origine) ;
- limiter la visibilité de tes propres profils.

Ces demandes sont normalement gratuites. Compte plusieurs étapes et un suivi, pas un
effacement en dix minutes.

## Deux façons de commencer

- **Depuis toi** : la skill vérifie d'abord que la recherche web est disponible, puis
  cherche les pages publiques à ton nom (et, si besoin, ta ville ou un ancien pseudo).
  Elle donne l'adresse et une courte description, signale les doutes et les homonymes,
  n'invente aucun lien. Tu ouvres et tu vérifies chaque lien, puis tu confirmes ceux qui te
  concernent. Elle regarde aussi les annuaires et sites de recherche de personnes. Ne lui
  donne jamais de mot de passe, de pièce d'identité ni de numéro sensible.
- **Depuis une info précise** : tu as trouvé une page, une photo ou un numéro dans un
  annuaire. La skill part de cet élément, trouve la procédure officielle du site et
  rédige la demande, sans chercher autre chose sur toi. Si elle ne peut pas lire la page,
  elle le dit, et elle n'invente ni formulaire ni adresse.

Si la recherche web n'est pas disponible, ou si elle refuse de chercher des coordonnées
personnelles, la skill ne cherche pas à contourner. Tu peux chercher toi-même : ton nom entre
guillemets, puis nom + ville ou ancien pseudo, puis tes propres profils. Ne rien trouver ne
prouve pas qu'il n'y a rien. Colle seulement les adresses qui t'intéressent, données
sensibles masquées.

## Les démarches

Pour chaque élément, la skill choisit entre :

- supprimer ou masquer un contenu sur un compte que tu contrôles ;
- demander l'effacement au site qui publie la donnée (article 17 du RGPD) ;
- demander le déréférencement à un moteur de recherche, quand la page reste en ligne
  mais ne doit plus apparaître dans les résultats ;
- signaler un résultat obsolète, quand la page a déjà disparu ;
- demander l'accès à tes données (article 15) ou t'opposer à leur usage commercial
  (article 21).

Sur un compte que tu contrôles, on regarde d'abord les réglages de confidentialité et de
suppression. Sinon, la skill cherche la page « Confidentialité », « Exercer mes droits » ou
le contact du délégué à la protection des données. Quand elle ne peut pas vérifier la
procédure officielle, elle écrit « à vérifier ».

Le droit à l'effacement a des conditions et des exceptions : conservation imposée par la loi,
liberté d'expression et d'information. Une page gênante n'est donc pas forcément
supprimable. La skill te le dit quand c'est le cas, te pose des questions pour trouver la
vraie raison de ta demande, et n'invente pas de justification juridique.

## Envoyer la demande

La skill rédige un brouillon : l'adresse de la page, les données concernées (décrites, pas
recopiées), ta raison, l'article 17 du RGPD « dans la mesure où ses conditions sont
réunies », la demande d'être informé dans le délai applicable, les motifs en cas de refus,
et de quoi t'identifier au minimum. Objet : « Demande d'effacement de données
personnelles ». La commande `python3 suivi.py modele 1` l'affiche.

Tu relis le destinataire, les données et la raison avant tout envoi, et tu passes par le
formulaire ou le contact officiel. Ne joins pas ta pièce d'identité par défaut : si le site
exige une vérification, utilise son canal officiel et donne le minimum. Garde la demande, sa
date et l'accusé de réception. Un brouillon n'est pas une demande envoyée, et une demande
envoyée n'est pas une suppression confirmée.

Option : si tu as Claude dans Chrome (offre payante), la skill peut remplir une page
officielle vérifiée avec le brouillon que tu as approuvé. Elle te montre les champs et le
destinataire, attend ton accord explicite avant de valider, s'arrête devant un CAPTCHA, une
connexion ou une vérification d'identité, et ne signale qu'une confirmation qu'elle a vue.
Si ça échoue, tu fais la démarche à la main.

## Les outils officiels, sans assistant

- Google « Résultats vous concernant » pour repérer et demander le retrait de résultats
  qui affichent tes coordonnées ;
- le formulaire Google de demande de retrait d'informations personnelles : il retire le
  résultat de Google, pas la page source, et n'est pas automatique ;
- l'outil Google pour le contenu obsolète ;
- le formulaire équivalent de Bing ;
- les pages de la CNIL sur le droit à l'effacement et le droit au déréférencement.

## Si tu es en Algérie

La loi 18-07 sur la protection des données personnelles s'applique, avec l'ANPDP comme
autorité. Elle prévoit notamment des droits d'accès, de rectification et d'opposition ;
vérifie le texte en vigueur pour l'effacement. Un site ou une entreprise établi dans l'UE,
ou qui s'adresse à des résidents de l'UE, reste soumis au RGPD, où que tu vives. La skill
indique le régime qui lui semble applicable et marque « à vérifier » quand elle hésite.

## Données qui restent

Certaines données sont conservées légalement, d'autres ne sont pas dans les moteurs de
recherche, d'autres encore réapparaissent. Pense à repasser vérifier. Pour limiter les
dégâts : règle la confidentialité de tes profils, supprime les comptes que tu n'utilises
plus, ne publie pas tes coordonnées. Sur les annuaires et sites de recherche de personnes,
fais une demande par site et note-la dans le tableau.

## Autres nettoyages utiles

La skill peut aussi te guider, un point à la fois et seulement si tu es d'accord, pour :

- désactiver l'usage de tes conversations avec un assistant IA pour entraîner le modèle,
  et vider ce que l'assistant a mémorisé sur toi ;
- désactiver les « fonctionnalités intelligentes » de Gmail qui exploitent le contenu de
  tes courriels pour personnaliser ;
- te désabonner des courriels commerciaux et filtrer le reste hors de la boîte de
  réception. L'assistant ne supprime jamais définitivement un message.

## Le suivi

`suivi.py` tient un tableau de tes demandes dans `gomme/suivi.csv` : le site, l'adresse,
les données visées (décrites, pas recopiées), la démarche, l'état, la date d'envoi, la
preuve, la réponse, la date de relance et le résultat vérifié. L'échéance est calculée
automatiquement : un mois après l'envoi, ou trois mois si l'organisme annonce une
prolongation. Le fichier ne contient jamais les données elles-mêmes, seulement leur
description.

```bash
python3 suivi.py add --site "Annuaire" --url https://... --donnees "adresse postale" --demarche suppression
python3 suivi.py envoyee 1 --date 2026-10-16 --preuve "accusé de réception"
python3 suivi.py echeances
```

`echeances` liste les demandes en retard ou proches de l'échéance. Sans réponse dans les
délais, tu peux saisir la CNIL avec tes preuves.

Autres commandes :

```bash
python3 suivi.py verifie 1 --source disparu --recherche visible   # page source et résultats de recherche, vérifiés séparément
python3 suivi.py resume            # brouillons, envoyées, refus, suppressions confirmées
python3 suivi.py relance 1         # brouillon de relance, jamais envoyé
python3 suivi.py export --format markdown
```

Le tableau distingue les brouillons, les demandes envoyées, les refus et les suppressions
confirmées. `--demarche` accepte aussi `desabonnement` et `parametre`.

L'organisme répond normalement sous un mois. Ce délai peut être prolongé de deux mois s'il
l'annonce et le justifie pendant le premier mois. Un délai n'est pas une garantie. Si la
réponse ne te convient pas, ou s'il n'y en a pas, tu peux saisir la CNIL avec tes preuves.
Vérifie séparément la page source et les résultats de recherche.

Un rappel demande une vraie tâche planifiée : une promesse dans la conversation n'est pas
une surveillance. La skill prépare une relance si tu la demandes et ne l'envoie jamais
toute seule.

## Utilisation

```
/gomme
/gomme https://site.exemple/page-avec-mon-numero
/gomme suivi
```

## Installation

```bash
git clone https://github.com/adambrai/Claude_Skills.git
mkdir -p ~/.claude/skills/gomme
cp Claude_Skills/Gomme/{SKILL.md,suivi.py} ~/.claude/skills/gomme/
```

## Tests

```bash
cd Gomme && python3 -m unittest discover -s tests -v
```

Cette skill donne une aide pratique générale. Elle ne remplace pas un avis juridique
adapté à une situation particulière.

## Licence

MIT, voir [LICENSE](../LICENSE).
