# Antimicrobial Peptide Source Notes and Bucket Assignment

This doc tracks curated peptides from public repositories and the bucket they map to for seed curation.

## Source priority
1. DBAASP (main): experimental antimicrobial and toxicity readouts.
2. DRAMP 4.0: clinical context, patent/translation notes, and added annotations.
3. APD/APD3: natural AMP references, families, and physicochemical context.
4. CAMPR4: sequence/activity cross-checks and selected additional liabilities.

## Bucket map

### Positive examples (known antimicrobial activity)
- `AMP_SRC_DBAASP_763` — Pexiganan (MSI-78)
  - Activity: Broad antibacterial MIC support against Gram+ and Gram- bacteria (example 8–16 µg/ml against *S. aureus*; multiple targets in DBAASP/DRAMP).
  - Source evidence:
    - [DBAASP DBAASPS_763](https://dbaasp.org/api/v3/peptides/DBAASPS_763)
    - [DRAMP18057](https://dramp.cpu-bioinfor.org/browse/clinical-information.php?id=DRAMP18057)

- `AMP_SRC_DBAASP_690` — Magainin 2
  - Activity: antibacterial MIC in the low–mid µg/ml range.
  - Source evidence:
    - [DBAASP DBAASPS_690](https://dbaasp.org/api/v3/peptides/DBAASPS_690)
    - [APD AP00144](https://aps.unmc.edu/database/peptide)

- `AMP_SRC_CAMPSQ11798` — LL-37 (human cathelicidin)
  - Activity: antibacterial activity across Gram+ and Gram- bacteria in CAMPR4 and historical literature.
  - Source evidence:
    - [CAMPR4 CAMPSQ11798](https://camp.bicnirrh.res.in/seqDisp.php?id=CAMPSQ11798)
    - [APD AP00310](https://aps.unmc.edu/database/peptide)

### Liability examples (host safety/manufacturing risk)
- `AMP_SRC_DBAASP_6669` — Iseganan (IB-367)
  - Liability signals: high hemolysis and cytotoxicity; disulfide folding complexity.
  - Source evidence:
    - [DBAASP DBAASPS_6669](https://dbaasp.org/api/v3/peptides/DBAASPS_6669)
    - [DRAMP18059](https://dramp.cpu-bioinfor.org/browse/clinical-information.php?id=DRAMP18059)

### Near-negative / weak examples
- `AMP_SRC_CAMPSQ11922` — Temporin-SHf
  - Weakness signals: poor antifungal potency (MIC >100 µM) and high hydrophobicity that often hurts formulation margins.
  - Source evidence:
    - [CAMPR4 CAMPSQ11922](https://camp.bicnirrh.res.in/seqDisp.php?id=CAMPSQ11922)
