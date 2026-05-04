# ARS Île-de-France & Écosystème DIM · 2026

> Source · synthèse research-analyst (4 mai 2026), URLs vérifiées sur iledefrance.ars.sante.fr / psysudparis.fr / Légifrance / CNIL.

## 1. ARS Île-de-France

- **Siège** · Immeuble "Le Curve", 13 rue du Landy, 93200 Saint-Denis
- **Téléphone** · 01 44 02 00 00
- **DG (depuis 10 avril 2024)** · Denis Robin
- **DGA délégations territoriales** · Marie-Anne Jacquet
- **Site** · <https://www.iledefrance.ars.sante.fr>

### Délégations départementales

| Dép. | Adresse | Tél |
|------|---------|-----|
| **75 (Paris)** | 13 rue du Landy, 93200 Saint-Denis | 01 44 02 09 00 |
| 77 | 13 av. Pierre Point, 77127 Lieusaint | 01 78 48 23 00 |
| 78 | 143 bd de la Reine, 78000 Versailles | 01 30 97 73 00 |
| 91 | 6/8 rue Prométhée, 91000 Évry | 01 69 36 71 71 |
| 92 | 28 allée d'Aquitaine, 92000 Nanterre | n.d. |
| 93 | 13 rue du Landy, 93200 Saint-Denis | 01 41 60 70 00 |
| **94 (Val-de-Marne)** | 25 ch. des Bassins, 94010 Créteil Cdx | 01 49 81 86 04 |
| 95 | 2 av. de la Palette, 95011 Cergy-Pontoise Cdx | n.d. |

### Datalogue (catalogue ouvert)

<https://datalogue.iledefrance.ars.sante.fr> · 5 bases référencées · Odissé (SPF), ScanSanté (ATIH), SNDS (Cnam, accès individuel), FINESS (DREES), Cartographie pathologies (Cnam, restreint).

## 2. GHT Psy Sud Paris

- **Convention validée par ARS IDF le 1er juillet 2016**
- **Convention signée janvier 2017**
- **Établissement support** · GH Fondation Vallée - Paul Guiraud (FINESS juridique **94 014 004 9**)
- **Membre fondateur 2** · EPS Erasme (Antony, 92)
- **Partenaires associés** · AP-HP (HU Paris-Saclay), HIA Percy, 8 ESMS

### Adresse établissement support

GH Fondation Vallée - Paul Guiraud  
54 avenue de la République, BP 20065, 94800 Villejuif Cedex  
Tél · 01 42 11 70 00

### Volumétrie GHT

| Indicateur | Valeur |
|-----------|--------|
| Territoire | 40 communes, 1,3 M habitants |
| Départements | 94 + 92 |
| Secteurs psychiatrie adulte | 14 |
| Secteurs pédopsychiatrie | 4 |
| Patients en file active | **37 000** |
| Lits (capacité) | 741 |
| ETP personnel | 2 860 |
| Budget fonctionnement | 260 M€ |
| Spécialité | **100 % PSY** (aucun MCO/SSR/HAD propre) |

Source · <https://www.psysudparis.fr/groupement-hospitalier-territoire-ght-psy-sud-paris>

## 3. Profession DIM

### Composition type d'une équipe DIM

| Profil | Statut | Salaire |
|--------|--------|---------|
| **Médecin DIM (MIM)** | PH/PHC | 55 000 - 98 000 € brut/an (médiane ~55K) |
| **TIM** | Cat. B (TSH) FPH | 1 607 - 2 357 € brut/mois (FPH) · 2 083 - 3 000 € (privé) |
| **Ingénieur PMSI** | Cat. A | 35 000 - 55 000 € brut/an |

Composition typique CH intermédiaire · 1,6 ETP médecin DIM + 1 ETP ingénieur + 4 ETP TIM.

### Diplômes / certifications

- **DU TIM** · Universités Angers, Lille, AMU, UPEC · 1 an (307,5 h + stage) · ~7 035 € + droits univ. (financement ANFH/FAF PM)
- **Diplôme Expert PMSI EHESP** · pour médecins DIM
- **Master Méthodes traitement information biomédicale** · UPEC, autres

### Sociétés savantes

- **CNIM** (Collège National Information Médicale) · médecins + ingénieurs DIM
- **CNIM-Psy** · émanation thématique psy

## 4. Écosystème logiciel DIM (concurrents)

| Éditeur | Solution | Forces | Limites |
|---------|----------|--------|---------|
| **Maincare/Docaposte** | CORA PMSI · DIMReport · DIMXpert SMR | n°1 marché · ergo moderne | coût élevé · GHT complexe |
| **Medasys** | DxCare (DPI + DIM) | natif clinique · 43 % CHU-CHR | DIM secondaire |
| **Ospi** | Cod+ (IA) · PMSIpilot · BI Ospi | IA codage avancée | spécialisé valorisation |
| **Sclépios I.A.** | codage IA urgences/SMR | 15 min/patient · 520 K€/an gain (Cateau-Cambrésis) | spécialisé urg/SMR |
| **PMSISoft** | DATAMIS | gratuit (standard) · HDS | requêtage seulement |
| **Berger-Levrault** | BL.PMSI (SIGEMS) | intégré gestion admin | suite globale |
| **Atalante** | groupage PMSI tous champs | éditeur indé | étab. moyens |
| **HOPSIIA** | DataLakeHouse + FHIR | architecture data moderne | jeune |

### Positionnement Sovereign OS DIM

| Axe | Concurrents | Sovereign OS DIM |
|-----|-------------|-------------------|
| Déploiement | SaaS / client lourd complexe | Portable .exe, zéro install |
| Données | cloud éditeur souvent | **100 % local, RGPD-natif** |
| PSY | module secondaire souvent | **natif PSY, 23 formats ATIH** |
| Identitovigilance | rare | **MPI SQLite, résolution collisions** |
| Transparence | propriétaire | **MIT open-source** |
| IA codage | Ospi/Sclépios | CimSuggester (LLM cloud ou Ollama local) |
| Contraintes EDR | .bat/.ps1 souvent requis | **zéro script bloqué** |

## 5. Code de la santé publique · articles PMSI

- **L. 6113-7** · obligation analyse activité par DIM, secret médical levé entre praticiens et MIM
- **L. 6113-8** · conditions utilisation données pour T2A et contrôles ARS
- **R. 6113-1 à R. 6113-11** · données autorisées, modalités, exception secret médical au personnel sous autorité MIM (R. 6113-5)
- **R. 6113-12 à R. 6113-14** · modalités recueil, sécurisation, durée conservation, transmission CPAM/ATIH
- **R. 6123-174** · obligation prise en charge psy en 3 modes (temps partiel, complet, ambulatoire) · arrêté 4 juillet 2025 liste les structures hors site

## 6. CNIL & RGPD · obligations DIM

- **Conservation dossier médical** · 20 ans à compter du dernier acte · puis anonymisation/destruction
- **Données SNDS** · pseudonymisées (NIRTEC), conservation longue
- **DPO obligatoire** (art. 37 RGPD) · DIM associé étroit
- **Registre art. 30** · chaque traitement (PMSI, MPI, exports e-PMSI) doit y figurer
- **Données FICHSUP-PSY** (contraintes, isolement, modes légaux) · cat. spéciale art. 9 RGPD · base mission intérêt public art. 9.2.g
- **k-anonymity** · k ≥ 5 standard recommandé pour exports recherche

Sources · <https://www.cnil.fr/sites/cnil/files/atoms/files/referentiel_-_traitements_dans_le_domaine_de_la_sante_hors_recherches.pdf>

## 7. PMSI-Psy · réforme financement (8 compartiments)

| Compartiment | Part | Logique |
|---|---|---|
| **DotPop** (populationnelle) | **78 %** | démographie/social régional |
| **DFA** (file active) | **15 %** | patients pondérés par classification |
| **DQC** (qualité codage) | **2 %** | complétude OVALIDE |
| IFAQ (qualité soins) | ~2 % | indicateurs HAS |
| Activités spécifiques | ~1,5 % | supra-régionales |
| Nouvelles activités | ~0,5 % | AAP |
| Recherche | <0,5 % | psy/pédopsy |
| Transformation | <0,5 % | projets |

### Sécurisation prolongée jusqu'en 2028 (DGOS, 26/09/2025)

| Année | Sécurisation |
|-------|-------------|
| 2026 | 97,5 % |
| 2027 | 95 % |
| 2028 | 90 % |
| **2029** | **0 %** (exposition pleine) |

→ **Pression croissante sur la qualité PMSI** entre 2027 et 2029.

Sources · <https://www.atih.sante.fr/financement-des-etablissements/psy> · <https://www.apmnews.com/freestory/10/427983/reforme-du-financement-de%C2%A0la%C2%A0psychiatrie-la%C2%A0securisation-prolongee-jusqu-en-2028>
