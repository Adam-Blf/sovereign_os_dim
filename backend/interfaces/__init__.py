"""Couche d'exposition : API frontend, application FastAPI et bridge HTTP local.

Expose les domaines metier (pmsi, orgchart, quality, ml) a l'interface WebView2
(via l'objet Api pywebview) et a l'integration PHP (via le bridge REST securise
sur 127.0.0.1 avec jeton Bearer).
"""
