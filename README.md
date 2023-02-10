# Généalogie ESR


## I- Scripts

Scripts python de test de generation de graph a partir de la [base de l'Abes](https://www.data.gouv.fr/fr/datasets/theses-soutenues-en-france-depuis-1985/).

Le process est divisé en deux parties:

1. `GenerateGenealogyGraph.py`: chargement du fichier csv source et extraction des informations de chaque thèse et création d'un graph associant candidats et directeurs avec NetworkX. Sauvegarde dans trois fichiers pickle.
2. `GetSubGraphPerPerson.py`: fonctions basiques de recherche dans le graph et de sortie du graph d'une personne donnée. Utilises les fichiers pickle de 1.


## II- www.genealogie-esr.fr

Sources de l'application Flask de [www.genealogie-esr.fr](https://www.genealogie-esr.fr/).


## Limites
- La base n'est pas forcément complète (des entrées presentent dans theses.fr ne sont pas dans la base)
- Souvent seul le directeur est renseigné (pas de co-encadrants)
- Le code n'est pas optimisé (ni bien documenté)

## Liens et ressources
- La base de données des theses sur le site [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/theses-soutenues-en-france-depuis-1985/)
- Python graph package [NetworkX](https://networkx.org/)
- Python [pandas package](https://pandas.pydata.org/)
- Python [rapidFuzz](https://github.com/maxbachmann/RapidFuzz/) package
- Python [wordcloud](http://amueller.github.io/word_cloud/) package
- Une genealogie des Maths (mondiale): [Mathematics Genealogy Project](https://genealogy.math.ndsu.nodak.edu/)
