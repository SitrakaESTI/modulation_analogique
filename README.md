# modulation_analogique

Émetteurs et récepteurs **AM, BLU, FM et PM** en simulation pure (aucun matériel SDR) :
modèles **MATLAB Simulink** et graphes de flux **GNU Radio 3.10**, avec le guide
`Guide_emetteurs_recepteurs_AM_BLU_FM_PM_v5.docx` (schémas blocs, liste des blocs, résultats).

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
