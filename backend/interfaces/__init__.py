"""Couche d'exposition : pont pywebview in-process (aucun serveur, aucune socket).

Expose les domaines metier (pmsi, orgchart, quality, ml) a l'interface WebView2
via l'objet `Api` du pont pywebview. La logique des ecrans Sentinel v2 (cockpit,
ML, audit, CeSPA, diff, heatmap, twin, workflow) vit dans `_sentinel.py` et reste
strictement locale : aucun flux reseau, aucune surface de fuite de donnees.
"""
