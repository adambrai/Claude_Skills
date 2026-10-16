<!-- fourmi:start -->
## Économie de contexte

### Choix du modèle (alias : ils suivent toujours la dernière version)
- `haiku` : recherches rapides, inventaires de fichiers, résumés, vérification de liens.
- `sonnet` : modifications simples, tests, documentation, commits, SEO et accessibilité.
- `opus` : implémentation complexe, changements sur plusieurs fichiers, refactors, bugs difficiles, architecture, revue finale.
- Un modèle facturé en crédits supplémentaires seulement si on me le demande.
- Toujours passer le paramètre `model` quand je lance un sous-agent.

### Sous-agents
- Seulement pour isoler un travail qui produirait beaucoup de lecture, ou pour des tâches vraiment indépendantes en parallèle.
- Jamais deux sous-agents sur les mêmes fichiers en même temps.
- Je garde le plan, les décisions et l'intégration ; un sous-agent rend un résumé court, pas tout ce qu'il a lu.
- Si une décision dépend d'un fichier, je relis la partie utile moi-même.

### Lecture
- Chercher avant de lire : Grep/Glob d'abord, puis seulement les lignes utiles d'un fichier.
- Ne pas relire un fichier déjà lu dans la conversation sauf s'il a changé.
- Sorties de commandes longues : filtrer (`| tail`, `| grep`) au lieu de tout afficher.
- Une seule validation de direction au début d'un gros travail, pas une par étape.
<!-- fourmi:end -->
