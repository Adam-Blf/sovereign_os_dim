# DIM · Valeur métier quantifiée 2026

> Source · synthèse research-analyst (4 mai 2026), URLs vérifiées sur ARS Bretagne, lesPMSI, ATIH, ScienceDirect (étude OPTIC), HAS.

## 1. Pain points DIM (par fréquence)

| # | Pain point | Coût TIM estimé |
|---|-----------|-----------------|
| 1 | **Rejet e-PMSI / DRUIDES** · taux anomalies RPSA national 10,5 %, meilleurs étab. 6,3 % | 13-20 h TIM/mois pour 100 anomalies |
| 2 | **Collisions IDV / IPP doublonnés** · taux chaînage national 95,4 %, meilleurs 99,5 % | 20-45 min/doublon |
| 3 | **Retard transmission ARS** · DFA suspendue jusqu'à régularisation | 8-16 h correction + flux DFA différé |
| 4 | **FicUM incomplet** · UM non rattachée → RPSA non exporté (DRUIDES depuis M1 2025) | 4-8 h investigation/incident |
| 5 | **DP absent / codes Z génériques** · dégrade DQC (2 % du financement) | jusqu'à 1 M€/an perdu sur étab. 50 M€ |

## 2. Coût d'erreur · CHS de 800 lits

| Erreur | Impact |
|--------|--------|
| Rejet transmission ARS (1 mois) | DFA suspendue 750 K€/mois (étab 60 M€) ou 3,25 M€/mois (GHT Sud Paris 260 M€) |
| 200 collisions IDV | 67-150 h TIM (~2 ETP-semaines) |
| 150 doublons IPP | 112-225 h TIM |
| DP manquant en MCO | perte ~1 470 €/RSS recodable (étude OPTIC CHRU Tours, 2022) |

## 3. Temps standard par tâche TIM

| Tâche | Durée |
|-------|-------|
| Lot mensuel RPS (preflight + soumission + corrections) | 12-20 h pour 500-800 séquences |
| Résolution 100 collisions IPP | 33-75 h |
| Preflight DRUIDES complet | 2-4 h |
| Sanitisation export FICHCOMP | 1-2 h (lot propre) → 6 h (anomalies) |
| Contrôle qualité MCO | médiane ~3 min/dossier (CHR Metz-Thionville) |
| Tableau de bord chef de pôle | 4-8 h (vs 1-2 h avec IA) |

**Note** · ratio 1:2 entre temps déclaré et réel (LesPMSI) → les agents sous-estiment systématiquement.

## 4. ROI documenté

| Solution | ROI publié |
|----------|-----------|
| **Étude OPTIC** (CHRU Tours, 2022) | **1 470 € de gain par RSS recodé** · 70 % des 111 RSS analysés revalorisables |
| **Sclépios IA** (CH Cateau-Cambrésis) | **520 K€/an** valorisés sur 19 000 passages · 15 min/patient économisées |
| **Ospi Cod+** | 46 % temps codage économisé · 50 % automation séjours simples · 1 500 €/séjour ciblé |
| **Dedalus + Sancare** | 50-60 % réduction temps codage · 400+ établissements |

**Vigilance** · LesPMSI souligne que beaucoup de chiffres IA fournisseurs ne sont **pas audités indépendamment**. Seule l'étude OPTIC (Revue d'Épidémiologie 2022) a métrique publique vérifiée.

## 5. Indicateurs qualité PMSI suivis ARS

| Indicateur | Cible / National |
|-----------|-----------------|
| Taux anomalies RPSA | < 8 %, alerte > 10 % |
| Taux chaînage ANO-HOSP | > 97 %, < 95 % = alerte ARS |
| Complétude DP | indexé sur DQC depuis 2022 |
| Délai codage à la sortie | < J+15 (séjours temps plein) |
| FicUM actives vs UM ouvertes | 100 % obligatoire |

### Indicateurs IQSS HAS psy

- Évaluation cardio-vasculaire et métabolique
- Repérage et aide arrêt addictions
- Évaluation gastro-intestinale (campagne 2026)
- Évaluation douleur somatique
- Qualité de la lettre de liaison de sortie

## 6. Réforme financière 2024-2028

| Compartiment | Part | Logique |
|--------------|------|---------|
| **DotPop** | 78 % | démographie/social régional |
| **DFA** | 15 % | file active |
| **DQC** | 2 % | qualité codage OVALIDE |
| IFAQ | ~2 % | indicateurs HAS |
| Spécifiques | 1,5 % | supra-régional |
| Nouvelles | 0,5 % | AAP |
| Recherche | < 0,5 % | psy/pédopsy |
| Transformation | < 0,5 % | projets |

### Sécurisation prolongée (DGOS 26/09/2025)

| Année | Sécurisation |
|-------|-------------|
| 2026 | 97,5 % |
| 2027 | 95 % |
| 2028 | 90 % |
| **2029** | **0 %** (exposition pleine) |

→ Pression PMSI **explosive sur 2027-2029** · pas de filet de sécurité après 2028.

## 7. Tendances IA en DIM (état art 2026)

| Type | Solutions |
|------|-----------|
| **Référentiel CIM-10** | cimAI, aideaucodage.fr, PMSIM (gratuits) |
| **NLP du DPI** | DIMbox/Alicante, Ospi Cod+, Maincare CORA, Sclépios |
| **Contrôle post-codage** | OPTIC CHRU Tours (16 algos REGEX), 0,8 % yield mais 1 470 €/RSS |
| **IDV par ML** | Lifen, Vigident (pas de publication académique avec métriques auditées) |
| **Prédiction rejet PMSI** | **gap identifié** · pas de solution commerciale dédiée 2026 |

→ Sovereign OS DIM positionnement · combler le gap **IDV ML + prédiction rejet** avec XGBoost local.

## 8. KPIs dashboard chef DIM (mensuels recommandés)

### File active & activité
- File active totale (12 mois glissants)
- File active stable / dynamique (ratio)
- File active ambulatoire vs hospitalisation temps plein
- Taux patients cross-modalités

### Qualité PMSI
- Taux séjours sans DP codé (cible < 5 %)
- Taux anomalies OVALIDE mensuel (cible < 8 %)
- Taux chaînage ANO-HOSP / ANO-AMBU (cible > 97 %)
- Délai moyen codage à la sortie (cible < J+15)
- Taux RPS transmis dans délai ATIH (cible 100 %)
- Nombre FicUM actives vs UM ouvertes

### Identitovigilance
- Doublons IPP détectés/mois
- Collisions résolues/mois
- Taux IPP avec INS qualifiée (Ségur)

### Valorisation & financement
- DFA estimée vs réalisée (alerte > 2 % écart)
- Score DQC mensuel
- Séquences RPSA rejetées vs soumises
- Potentiel revalorisation identifié

### Ressources DIM
- Charge TIM mensuelle (heures PMSI vs disponibles)
- Taux formation TIM à jour (DRUIDES 2025, CIM-10 2026, RIM-P 2025)

## 9. Sources

- [ARS Bretagne · Bilan PMSI-PSY 2021](https://www.bretagne.ars.sante.fr/bilan-synthetique-pmsi-2021-psychiatrie-rim-p)
- [ATIH · Financement psychiatrie](https://www.atih.sante.fr/financement-des-etablissements/psy)
- [LesPMSI · DRUIDES PSY 2025](https://www.lespmsi.com/druides-en-pmsi-psy-en-2025/)
- [LesPMSI · Coût codage PMSI](https://www.lespmsi.com/calculer-le-cout-du-codage-du-pmsi-elements-de-reflexion/)
- [LesPMSI · Durée contrôle qualité MCO](https://www.lespmsi.com/les-determinants-de-la-duree-du-controle-qualite-du-codage-pmsi-mco-etude-chr-metz-thionville/)
- [LesPMSI · IA pour DIM](https://www.lespmsi.com/lia-pour-les-dim-en-dehors-du-codage/)
- [ScienceDirect · OPTIC CHRU Tours 2022](https://www.sciencedirect.com/science/article/pii/S0398762022000852)
- [APM News · Sécurisation prolongée 2028](https://www.apmnews.com/freestory/10/427983/reforme-du-financement-de%C2%A0la%C2%A0psychiatrie-la%C2%A0securisation-prolongee-jusqu-en-2028)
- [HAS · IQSS psychiatrie](https://www.has-sante.fr/jcms/c_970481/fr/indicateurs-de-qualite-et-de-securite-des-soins-en-etablissements-de-sante)
- [Scansante · OVALIDE PSY](https://www.scansante.fr/actualites/tableaux-detailles-de-validation-du-pmsi-psy)
- [MySIH · Outils DIM](https://www.mysih.fr/au-coeur-des-dim-quels-outils-pour-traiter-les-informations-medicales/)
- [Ospi · Codage PMSI IA](https://ospi.fr/codage-pmsi-par-ia/)
- [Lifen · Identitovigilance](https://www.lifen.fr/ressources/blog/comment-ameliorer-lidentitovigilance-tout-en-dechargeant-le-personnel-hospitalier)
