# modulation_analogique

Émetteurs et récepteurs **AM, BLU, FM et PM** en simulation pure (aucun matériel SDR) :
modèles **MATLAB Simulink** et graphes de flux **GNU Radio 3.10**, avec le guide
`Cours_Bloc2_Theme3_Emetteurs_recepteurs_AM_BLU_FM_PM.docx` (schémas blocs, liste des blocs, résultats, exercices) et `Corrige_Exercices_Bloc2_Theme3.docx`.

Dépôt : https://github.com/SitrakaEnseignant/modulation_analogique

## Résultats
- Résultats réels figés (images, journaux, versions) : [`Schemas/Resultats_reels`](Schemas/Resultats_reels)
- Derniers résultats : branche [`resultats`](https://github.com/SitrakaEnseignant/modulation_analogique/tree/resultats)
- Historique des exécutions : onglet [Actions](https://github.com/SitrakaEnseignant/modulation_analogique/actions)

## Exécution automatique (GitHub Actions)
À chaque envoi sur `main`, le workflow `.github/workflows/simulations.yml` :
- installe **MATLAB R2024b + Simulink** (gratuit pour un dépôt public), lance
  `Simulink/construire_et_verifier_modeles.m` : construction des `.slx`, schémas réels exportés,
  simulation, contrôles « OK / ECHEC » ;
- installe **GNU Radio 3.10** (paquet Ubuntu 24.04), compile chaque `.grc` avec `grcc` et l'exécute
  sans écran (les afficheurs QT GUI sont remplacés par des Vector Sink ; aucun bloc de traitement n'est modifié) ;
- publie résultats, journaux et versions exactes (`versions.txt`) dans la branche **`resultats`**.

## Contenu
Voir `LISEZ-MOI.txt`.
