# CHANGELOG

Tous les changements notables de Sovereign OS DIM, du plus récent au plus ancien.
Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [V37.6] - 2026-10-09

### Modifié

- **Migration des icônes vers Reicon (licence MIT).** Les pictogrammes de
  l'interface viennent désormais du jeu Reicon, graisse Outline, embarqués
  en local (`frontend/vendor/reicon-icons.js`) : aucun flux réseau, aucun CDN.
  La bibliothèque d'icônes précédente et son fichier vendorisé sont retirés.
  `tools/vendor_icons.py` régénère la table à version figée du paquet `reicon`.
- Le pictogramme « Suggestion diagnostique » (cerveau), absent du jeu Reicon,
  garde son tracé d'origine.
- Le test de rendu du frontend vérifie désormais que toutes les icônes de la
  page sont dessinées.
