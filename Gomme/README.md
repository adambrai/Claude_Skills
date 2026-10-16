# Gomme

Skill pour Claude Code qui t'aide à réduire ce qu'internet montre de toi. Elle cherche les
pages publiques qui te concernent, t'aide à choisir la bonne démarche pour chacune, rédige
les demandes RGPD et suit les réponses avec les délais légaux.

Elle ne travaille que sur tes propres données. Rien n'est envoyé, soumis ou modifié sans
ton accord explicite, et aucune méthode ne garantit de tout retrouver ni de tout effacer.

## Deux façons de commencer

- **Depuis toi** : la skill cherche les pages publiques à ton nom (et, si besoin, ta ville
  ou un ancien pseudo). Tu confirmes celles qui te concernent vraiment.
- **Depuis une info précise** : tu as trouvé une page, une photo ou un numéro dans un
  annuaire. La skill part de cet élément, trouve la procédure officielle du site et
  rédige la demande, sans chercher autre chose sur toi.

## Les démarches

Pour chaque élément, la skill choisit entre :

- supprimer ou masquer un contenu sur un compte que tu contrôles ;
- demander l'effacement au site qui publie la donnée (article 17 du RGPD) ;
- demander le déréférencement à un moteur de recherche, quand la page reste en ligne
  mais ne doit plus apparaître dans les résultats ;
- signaler un résultat obsolète, quand la page a déjà disparu ;
- demander l'accès à tes données (article 15) ou t'opposer à leur usage commercial
  (article 21).

Le droit à l'effacement a des conditions et des exceptions. La skill te le dit quand c'est
le cas, et n'invente pas de justification juridique.

## Le suivi

`suivi.py` tient un tableau de tes demandes dans `gomme/suivi.csv` : le site, l'adresse,
la démarche, l'état, la date d'envoi, la preuve et l'échéance. L'échéance est calculée
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
