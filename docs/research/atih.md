# ATIH · Référentiel complet 2026

> Source · synthèse research-analyst (4 mai 2026), URLs vérifiées sur atih.sante.fr / Légifrance / lesPMSI.com / Wikipedia / Service-Public.

## 1. Organisation ATIH

- **Statut** · EPA créé par décret n° 2000-1282 du 26 décembre 2000
- **Tutelle** · ministres de la Santé / Affaires sociales / Sécurité sociale
- **Direction générale (depuis 6 jan. 2025)** · Nathalie Fourcade
- **Précédent (2010-2024)** · Housseyni Holla
- **Première directrice (2001-2010)** · Maryse Chodorge
- **Siège** · 117 boulevard Marius-Vivier-Merle, 69003 Lyon
- **Antenne** · Paris
- **Effectifs** · ~140 agents
- **SIREN** · 180092298

### URLs institutionnelles

| Ressource | URL |
|-----------|-----|
| Site principal | <https://www.atih.sante.fr> |
| e-PMSI | <https://www.epmsi.atih.sante.fr> |
| ScanSanté | <https://www.scansante.fr> |
| CAS / e-Pass | <https://connect-pasrel.atih.sante.fr> |
| Formats PMSI 2026 | <https://www.atih.sante.fr/formats-pmsi-2026-0> |
| DRUIDES (téléchargement) | <https://www.atih.sante.fr/logiciels-espace-de-telechargement/druides> |
| Guide méthodo PSY 2026 | <https://www.atih.sante.fr/guide-methodologique-psychiatrie-2026> |
| Notice technique 2026 | <https://www.atih.sante.fr/notice-technique-nouveautes-pmsi-mco-had-smr-psychiatrie-2026-0> |

## 2. Calendrier PMSI 2026

- **Année calée sur année civile** depuis 2026 (tous champs)
- **Établissement** · transmission + validation **dans le mois** suivant la période
- **ARS** · validation **dans les 6 semaines** suivant la période

### Calendrier mensuel SMR/PSY 2026 (établissements)

| Période | Semaines ISO | Délai établissement |
|---------|------|---------|
| M1 | S1-S5 | 01/02/2026 |
| M6 | S23-S26 | 28/06/2026 |
| M7 | S27-S31 | 02/08/2026 |
| M12 | S49-S53 | 03/01/2027 |

Source · <https://www.lespmsi.com/calendrier-2026-des-transmissions-pmsi-smr/>

## 3. DRUIDES · Déploiement par champ

| Champ | Date prod | Notes |
|-------|-----------|-------|
| MCO | **M3 2023** (avril) | test 15/02-31/03/2023 |
| SMR | **M8 2024** | |
| PSY | **M1 2025** | test 09/12/2024 - 31/01/2025 |
| HAD (LAMDA) | M1 2026 | |
| MCO HTNM | M1 2026 | migration MATIS → DRUIDES |
| MCO MRC | S1 2026 | migration MATIS → DRUIDES |

### Logiciels remplacés

- MCO · GenRSA, AGRAF, Fichsup, LAMDA Séjour/ACE, Visual valo/non-valo/qualité, Preface
- PSY · **PIVOINE ex-DGF, PIVOINE ex-OQN, VisualQUALITE**
- **MAGIC v5.12.0.0 reste obligatoire en 2026** (anonymisation VID-HOSP/ANO-HOSP/VID-IPP)

## 4. Réforme PSY 2025 · Modes de prise en charge

- [Arrêté du 4 juillet 2025](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051884050) · modifie arrêté 23/12/2016
- [Arrêté du 23 juillet 2025](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000051987561) · modificatif

### Suppressions

- **CATTP** (centre d'accueil thérapeutique à temps partiel) → remplacé par **CATTG**
- **Centre de post-cure** → remplacé par **CeSPA**
- **Ateliers thérapeutiques** → supprimés du recueil PMSI 2026

### Nouvelles structures

- **CeSPA** (Centre de Soins Post-Aigus) · temps complet, prolongement post-aigu
- **CATTG** (Centre d'Activités Thérapeutiques et de Temps de Groupe) · ambulatoire

### Nouveaux types UM (FicUM)

- **331** · EMPP (Équipe Mobile Psychiatrie Précarité)
- **332** · EMPPA (EMPP Adolescents)

### Modes de prise en charge (3 catégories)

1. **Temps complet** · hospitalisation, CeSPA, AT, CAC
2. **Temps partiel** · HDJ, hôpital de nuit
3. **Soins ambulatoires** · CMP, CATTG, soins à domicile (modalité 33), consultations

## 5. Formats PSY 2026 (mises à jour)

| Format | Maj 2026 |
|--------|----------|
| **RPS** | suppression ateliers thérapeutiques · ajout codes CeSPA, CAC · recodage modes prise en charge |
| **RAA** | CATTG remplace CATTP · modalité 33 (soins à domicile) |
| **RPSA / R3A** | dérivés mis à jour |
| **FICUM-PSY** | nouveaux types UM 331/332 · 7 champs (6 obligatoires) |

## 6. Documentation 2026

- **Guide méthodo PSY 2026** · <https://www.atih.sante.fr/sites/default/files/public/content/5115/guide_methodo_psy_2026_version_provisoire_010126.pdf>
- **Notice technique ATIH-294-9-2025** (21/11/2025) · <https://www.atih.sante.fr/sites/default/files/public/content/5109/notice_technique_pmsi_2026_vdef_0.pdf>
- **Notice transmission ATIH-31-1-2025** · <https://www.atih.sante.fr/sites/default/files/public/content/4903/notice_technique_complementaire_n_atih-31-1-2025_recueil_transmission_et_validation_des_donnees_pmsi.pdf>
- **CIM-10 FR usage PMSI 2026** · <https://www.atih.sante.fr/cim-10-fr-usage-pmsi-2026>

## 7. e-PMSI · Applications hébergées

| Application | Fonction | Champs |
|------------|----------|--------|
| **Ovalide** | validation données | tous |
| **Mat2a** | valorisation T2A | MCO |
| **Datim** | tableaux activité | tous |
| **ENC** | étude nationale coûts | MCO/SMR/HAD |
| **OSCT** | suivi coûts par séjour | MCO |
| **Valco** | valorisation/contrôle | SMR |
| **Susana** | qualité/sécurité soins | tous |
| **Syrius** | restitution médico-éco PSY | PSY |

## 8. SNDS et accès chercheurs

- Données PMSI alimentent SNDS via Health Data Hub + Cnam
- **NIR pseudonymisé en NIRTEC**
- Procédure · demande HDH + autorisation CNIL (ou MR-007)
- Documentation RIM-P · <https://documentation-snds.health-data-hub.fr/snds/glossaire/rim-p>
