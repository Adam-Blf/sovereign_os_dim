# Moulinette FICHCOMP

Utilitaire d'aide au recueil des supplements FICHCOMP du PMSI, integre a la suite
Sovereign OS DIM. Il nettoie un export Excel puis genere le fichier plat FICHCOMP
au format largeur fixe attendu par l'ATIH (transports, medicaments, dispositifs medicaux).

Historiquement livre a une collegue du DIM ("Moulinette pour Elodie") pour le recueil
des transports, l'outil est ici versionne cote code source uniquement.

> **Reserve DSI/DSN.** Le nom du module, l'interface et l'ergonomie sont provisoires
> et pourront evoluer selon les demandes de la Direction des Ressources Numeriques
> du GHT Psy Sud Paris dans le cadre de la mise en conformite SI et securite.

## Ce que fait l'outil

1. **Nettoyage Excel** (`gui_moulinette.py`, interface Tkinter) - cree une copie `*_clean`
   de chaque classeur, supprime les blocs d'en-tete repetes, propage la date de la
   colonne B vers les lignes vides, et marque en rouge les lignes supprimees dans une
   feuille temoin. L'original n'est jamais modifie.
2. **Export FICHCOMP / FICHDMI** (`export_to_fichcomp.py`) - transforme la feuille
   nettoyee en texte largeur fixe conforme ATIH.
3. **Controle** (`validate_fichcomp.py`) - verifie la structure des lignes produites
   (FICHCOMP medicament = 53 caracteres, FICHCOMP DMI = 50 caracteres, FINESS et
   code UCD numeriques, date `ddmmyyyy` ou 8 espaces).

## Format FICHCOMP medicament genere

| Champ | Largeur | Regle |
|-------|---------|-------|
| FINESS | 9 | numerique, zero a gauche |
| N° administratif de sejour | 20 | texte, espaces a droite |
| Code UCD | 9 | numerique, zero a gauche |
| Nombre d'UCD administrees | 7 | entier = valeur x 1000, zero a gauche |
| Date | 8 | `ddmmyyyy`, ou 8 espaces si vide |

Le mode DMI (`--type dmi`) reprend une structure voisine avec une largeur de champ
Nombre et une position de date differentes (ligne totale de 50 caracteres).

## Usage

Interface graphique (nettoyage Excel) :

```bash
py -3 gui_moulinette.py
```

Export en ligne de commande :

```bash
py -3 export_to_fichcomp.py entree.xlsx sortie.txt --type med --finess 000000001
```

Le script lit la premiere feuille et cherche les en-tetes (insensibles a la casse)
`finess`, `admin_stay`, `code`, `nombre`, `date`. A defaut, il lit les cinq
premieres colonnes dans cet ordre.

## Fichiers

| Fichier | Role |
|---------|------|
| `gui_moulinette.py` | Interface de nettoyage Excel + generation feuille Fichcomp |
| `export_to_fichcomp.py` | Export Excel vers FICHCOMP / FICHDMI largeur fixe |
| `import_fichcomp_txt.py` | Relecture d'un fichier FICHCOMP existant |
| `validate_fichcomp.py` | Controle de longueur et de format des lignes |
| `create_fichecomp_template.py` | Generation d'un gabarit Excel FICHCOMP |
| `field_inspect.py`, `inspect_lines.py` | Aides de debug sur les colonnes et lignes |

## Perimetre versionne

- **Code source Python uniquement.** Le binaire Windows autonome (`MoulinetteExcel.exe`,
  PyInstaller) et les gabarits `.xlsx` sont distribues separement et **ne sont pas versionnes**
  (binaires lourds + donnees potentiellement nominatives fournisseurs / dates de naissance).
- Aucun fichier de donnees reel (exports transports) ne doit etre commite dans ce dossier.

## Dependances

`openpyxl` (lecture/ecriture Excel). L'interface graphique utilise `tkinter`
(inclus dans la distribution standard de Python).
