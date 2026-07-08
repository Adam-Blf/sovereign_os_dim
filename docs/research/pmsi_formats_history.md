# PMSI Formats History 2000-2026 · Référence XGBoost

> Source · synthèse research-analyst (4 mai 2026), URLs vérifiées sur format-pmsi.fr / lespmsi.com / atih.sante.fr / SNDS.

**Encoding** · tous les fichiers PMSI utilisent **Latin-1 (ISO-8859-1)**.
**Format DDN** · varie par format · DDMMYYYY (RSS groupé, VID-IPP) vs YYYYMMDD (HAD, SSR/SMR, PSY, RSS non-groupé 022+).

---

## Tokens discriminants par champ (XGBoost feature primaire)

| Champ | Position du token | Pattern |
|-------|------------------|---------|
| **HAD** | **pos 1-3** | `H01`-`H0B`, `H17`-`H1B` (unique · seul champ qui met le format en tête) |
| **MCO RSS/RUM** | pos 10-12 | `011`-`023` (non-grp), `111`-`123` (grp) |
| **MCO RSA** | pos 10-12 | `215`-`220` |
| **MCO FICHCOMP** | pos 10-11 (2 chars) | type code (MO, DM, etc.) |
| **SSR/SMR non-grp** | pos 10-12 | `M04`-`M0D` |
| **SSR/SMR grp** | pos 11-13 (après filler 10 chars) | `M19`/`M1A`-`M1D` |
| **PSY (RPS+RAA)** | **pos 19-21** | `P03`-`P14` (après double FINESS pos 1-9 + 10-18) |
| **VID-HOSP** | pos 49-52 (4 chars) | `V008`-`V016` |
| **VID-IPP PSY** | pos 49-52 | `I00A` |

---

## PSY · RPS (Résumé Par Séquence) · priorité GHT Sud Paris

Structure unique · **double FINESS** (juridique + géographique) en tête.

| Format | Années actives | Token pos 19-21 | IPP pos | DDN pos | Min length |
|--------|---------------|-----------------|---------|---------|-----------|
| RPS P03/P04 | jul 2006 - ~2010 | `P03`/`P04` | 22-41 | 42-49 | ~120+ var |
| RPS P05 | ~2010 - jun 2017 | `P05` | 22-41 | 42-49 | ~152+ var |
| RPS P07 | ~2015-2016 | `P07` | 22-41 | 42-49 | ~152+ var |
| RPS P08 | jan 2017 - ~2018 | `P08` | 22-41 | 42-49 | ~152+ var |
| RPS P09-P11 | 2018-2020 | `P09`-`P11` | 22-41 | 42-49 | ~152+ var |
| **RPS P12** | **~2021 - present** | `P12` | 22-41 | 42-49 | ~152+ var |

### RPS P05 · positions détaillées (référence ATIH)

| Champ | Position |
|-------|---------|
| FINESS juridique | 1-9 |
| FINESS géographique | 10-18 |
| Format (P05) | 19-21 |
| IPP | 22-41 (20 chars) |
| DDN | 42-49 (YYYYMMDD) |
| Sexe | 50 |
| Code postal | 51-55 |
| Forme d'activité | 56-57 |
| N° de séjour | 58-77 |
| Date entrée séjour | 78-85 |
| Date sortie séjour | 88-95 |
| N° unité médicale | 98-101 |
| Date début séquence | 109-116 |
| Date fin séquence | 117-124 |
| Jours de présence | 125-127 |
| Diagnostic principal | 141-148 |

## PSY · RAA (Résumé d'Activité Ambulatoire)

Même structure que RPS, token au pos 19-21.

| Format | Années | Token | IPP | DDN | Min length |
|--------|--------|-------|-----|-----|-----------|
| RAA P06 | ~2010-2016 | `P06` | 22-41 | 42-49 | ~98+ var |
| RAA P07 | ~2015-2016 | `P07` | 22-41 | 42-49 | 81+ var |
| RAA P09 | jan 2017 - ~2019 | `P09` | 22-41 | 42-49 | 81+ var |
| RAA P10-P13 | 2019-2022 | `P10`-`P13` | 22-41 | 42-49 | 81+ var |
| **RAA P14** | **~2022 - present** | `P14` | 22-41 | 42-49 | 81+ var |

---

## HAD · RPSS (token pos 1-3, unique)

Structure unique · format en tête, double FINESS, IPP **pos 22-41**.

| Format | Années | Token pos 1-3 | FINESS jur | FINESS géo | IPP | DDN |
|--------|--------|--------------|-----------|-----------|-----|-----|
| RPSS H01 | jan 2005 - jan 2007 | `H01` | 4-12 | 13-21 | 22-41 | 62-69 (YYYYMMDD) |
| RPSS H02 | jan 2007 - mar 2010 | `H02` | 4-12 | 13-21 | 22-41 | 62-69 |
| RPSS H03/H04 | mar 2010 - 2013 | `H03`/`H04` | 4-12 | 13-21 | 22-41 | 62-69 |
| RAPSS H07/H08 | jan 2014 - mar 2019 | `H07`/`H08` | 4-12 | 13-21 | 22-41 | 62-69 |
| RPSS H17/H18 (grp) | jan 2014 - mar 2019 | `H17`/`H18` | 4-12 | 13-21 | 22-41 | 62-69 |
| RAPSS H09 / RPSS H19 | 2015-2018 | `H09`/`H19` | 4-12 | 13-21 | 22-41 | 62-69 |
| **RAPSS H0B / RPSS H1B** | **mar 2019 - present** | `H0B`/`H1B` | 4-12 | 13-21 | 22-41 | 62-69 |

---

## MCO · RSS/RUM (sans IPP, identifié par N° séjour)

Format DDN · DDMMYYYY pour grouped, YYYYMMDD pour non-grouped 022+.

| Format (non-grp/grp) | Années | Token 10-12 | FINESS | DDN | Format DDN |
|---------------------|--------|------------|--------|-----|-----------|
| RUM 013 / RSS 113 | mar 2006 - mar 2008 | `013`/`113` | 16-24 (grp) | 78-85 | DDMMYYYY |
| RSS 117 / 017 | 2013-2016 | `117`/`017` | 16-24 | 78-85 | DDMMYYYY |
| RSS 119 / 019 | mar 2019 - jan 2020 | `119`/`019` | 16-24 | 78-85 | DDMMYYYY |
| RSS 121 / 021 | 2021-2022 | `121`/`021` | 16-24 | 78-85 | DDMMYYYY |
| RSS 122 / 022 | mar 2023 - jan 2026 | `122`/`022` | grp 16-24 / non-grp 1-9 | grp 78-85 / non-grp 63-70 | grp DDMMYYYY / non-grp YYYYMMDD |
| **RSS 123 / 023** | **jan 2026+** | `123`/`023` | 1-9 (non-grp) | 63-70 | YYYYMMDD |

**Pas d'IPP dans RSS/RUM standard** · l'IPP vit dans VID-HOSP, RSF-A (depuis 2020), RSF-ACE A (depuis 2019).

---

## SSR/SMR · RHS (sans IPP)

| Format | Années | Type | Token | FINESS | DDN |
|--------|--------|------|-------|--------|-----|
| RHS M05 | 2008-2009 | non-grp | `M05` (10-12) | 1-9 | 60-67 |
| RHS M09 (non-grp) | 2013-2017 | non-grp | `M09` (10-12) | 1-9 | 68-75 |
| RHS M19 (grp) | 2013-2017 | grp | `M19` (11-13, après filler) | 14-22 | 81-88 |
| RHS M0B/M1B | 2018-2019 | non-grp/grp | `M0B`/`M1B` | 1-9 / 14-22 | 68-75 / 81-88 |
| RHS M0C/M1C | 2022-2024 | non-grp/grp | `M0C`/`M1C` | 1-9 / 14-22 | 68-75 / 81-88 |
| **RHS M0D/M1D** | **2025-2026** | non-grp/grp | `M0D`/`M1D` | 1-9 / 14-22 | 69-76 / 82-89 |

**Discriminant grouped vs non-grouped** · filler 10 chars en tête (positions 1-10) si grouped.

---

## Transversal · VID-HOSP (4 champs partagés)

NIR aux positions 1-13, format au pos 49-52.

| Format | Années | Length | Notes |
|--------|--------|--------|-------|
| V009 | ~2013-2017 | ~312+ | VID-HOSP pour ex-DGF |
| V012 | jan 2018 - 2021 | ~353+ | +12 nouveaux champs facturation |
| **V014** | **~2022 - sep 2025** | **466 (exact)** | stable |
| V015 | mar 2025 - jan 2026 | 468 + 50×N | DMT count 2 chars + blocs 50 chars |
| **V016** | **jan 2026+** | **469 + 50×N** | DMT count 3 chars (000 = non facturable) |

---

## VID-IPP PSY (chaînage ambulatoire DAF, depuis 2020)

| Champ | Position |
|-------|----------|
| N° immatriculation assuré | 1-13 |
| DDN bénéficiaire | 16-23 (DDMMYYYY) |
| Format (`I00A`) | 49-52 |
| FINESS ePMSI | 53-61 |
| IPP | 81-93 (13 chars) |
| **Total length** | **106 chars** |

---

## Stratégie features XGBoost

1. **char[0:3]** · si match `H01`-`H1B` → HAD direct
2. **char[10:13]** · si match `M0X`/`M1X` → SSR/SMR · si `0XX`/`1XX` → MCO RSS · si `215`-`220` → RSA
3. **char[19:22]** · si match `P0X`/`P12`/`P14` → PSY direct
4. **char[49:53]** · si match `V0XX` → VID-HOSP · si `I00A` → VID-IPP
5. **Length brackets** · 466 = VID-HOSP V014 · 106 = VID-IPP · 105 = FICHCOMP MO · 81 = RAA min · 154 = RPS P05
6. **Double FINESS test** · char[0:9] et char[9:18] tous deux numériques 9-chars → PSY signature
7. **Leading filler 10 chars** · indique RSS/RHS grouped

---

## Sources

- [ATIH Formats PMSI 2026](https://www.atih.sante.fr/formats-pmsi-2026-0)
- [format-pmsi.fr · catalogue complet](https://www.format-pmsi.fr/)
- [format-pmsi.fr · PSY RPS P05](https://www.format-pmsi.fr/PSY/RPS/P05/)
- [format-pmsi.fr · HAD H0B](https://www.format-pmsi.fr/HAD/RPSS/H0B/)
- [lespmsi.com · RPS RAA 2017](https://www.lespmsi.com/nouveaux-formats-rps-et-raa-en-2017/)
- [lespmsi.com · VID-HOSP 2025](https://www.lespmsi.com/evolutions-du-vid-hosp-en-2025/)
- [lespmsi.com · VID-IPP PSY](https://www.lespmsi.com/format-du-fichier-vid-ipp-chainage-des-ipp-pour-lambulatoire-des-etablissements-daf-psy/)
- [refpmsi · denisgustin](https://denisgustin.github.io/refpmsi/articles/formats_pmsi.html)
- [SNDS PSY documentation](https://documentation-snds.health-data-hub.fr/snds/fiches/pmsi_psy)
