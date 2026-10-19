# Count on Me? A Replication of "Social Ties in Academia: A Friend Is a Treasure"

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Stata 17+](https://img.shields.io/badge/Stata-17%2B-1a5f91)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776ab)
![Numbers checked](https://img.shields.io/badge/numbers%20in%20the%20paper-checked-brightgreen)

Data and code for Huynh, Jacho-Chávez and Sánchez-Aragón, "Count on Me? A Replication of 'Social Ties in Academia: A Friend Is a Treasure'". The paper replicates Colussi (2018, *Review of Economics and Statistics* 100(1): 45 to 50).

One notebook, `count_on_me_tables.ipynb`, reproduces every table, figure and computed number of the paper. It follows the paper section by section, so it can be read side by side with the PDF. It also checks each number written in the text against the value computed from the data, and stops if any of them differs.

## Contents

| File or folder | What it is |
|:---|:---|
| `count_on_me_tables.ipynb` | The reproducibility notebook |
| `count_on_me_tables.py` | Functions the notebook imports: Colussi's Table 1, the LaTeX tables, Figure 1 and their HTML previews |
| `data/original/` | Colussi's replication files: `ARTICLES.dta`, `AUTHORS.dta`, `FINAL_SAMPLE.dta`, `TOREG.dta` |
| `data/corrected/` | The same files after the 35 corrections of the narrow replication: `ARTICLES_UPDATED.dta`, `AUTHORS_UPDATED.dta`, `FINAL_SAMPLE_UPDATED.dta`, `TOREG_UPDATED.dta` |
| `output/` | Written by the notebook: LaTeX tables, Figure 1 and CSV files |
| `requirements.txt` | Python packages |
| `CITATION.cff`, `LICENSE`, `NOTICE` | How to cite, license and notices |

The notebook builds version 2 of the corrected data (`FINAL_SAMPLE_UPDATED_v2.dta` and `TOREG_UPDATED_v2.dta`) in `data/corrected/`. Appendix A of the paper explains the fixes.

## What the notebook produces

| Paper | Output |
|:---|:---|
| Table 1 | `output/tables/tab_descriptives.tex` |
| Figure 1 | `output/figures/fig_zeros.tex` |
| Table 2 | `output/tables/tab_ppml_table3.tex` |
| Table 3 | `output/tables/tab_comparison.tex` |
| Table A-3 | `output/tables/tab_corrections.tex` |
| Table B-1 | `output/tables/tab_table3_reghdfe_extended.tex` |
| Table C-1 | `output/tables/tab_python.tex` |

## How to run

1. Install Stata 17 or later. The notebook installs `require`, `ftools`, `reghdfe` and `ppmlhdfe` from SSC if they are missing.
2. Install Python 3.11 or later and the packages: `pip install -r requirements.txt`.
3. Open `count_on_me_tables.ipynb` from this folder and run all cells. If Stata is not in one of the usual folders, add its path to the list in the first set-up cell.

A full run takes a few minutes. The last section lists every number of the paper next to the value computed here.

## Software

Stata estimates use `reghdfe` and `ppmlhdfe`. Appendix C of the paper estimates every regression again in Python with `fasthdfe`; the coefficients and estimation samples are the same.

## Citation

If you use this code or data, please cite:

```bibtex
@unpublished{HuynhJachoChavezSanchezAragon2026_countonme,
  author = {Huynh, Kim P. and Jacho-Ch{\'a}vez, David T. and S{\'a}nchez-Arag{\'o}n, Leonardo},
  title  = {Count on Me? {A} Replication of ``{Social Ties in Academia: A Friend Is a Treasure}''},
  note   = {Unpublished manuscript. Data and code at \url{https://github.com/lfsanche/count_on_me}},
  year   = {2026}
}
```

and the original study:

```bibtex
@article{Colussi2018,
  author  = {Colussi, Tommaso},
  title   = {Social Ties in Academia: A Friend Is a Treasure},
  journal = {Review of Economics and Statistics},
  year    = {2018},
  volume  = {100},
  number  = {1},
  pages   = {45--50}
}
```

## Authors

Kim P. Huynh (corresponding author), Department of Economics, Indiana University, Bloomington, IN, USA, and Laboratoire d'Économie d'Orléans, Université d'Orléans, Orléans, France. kim@huynh.tv

David T. Jacho-Chávez, Department of Economics, Emory University, Atlanta, GA, USA. djachocha@emory.edu

Leonardo Sánchez-Aragón, Facultad de Ciencias Sociales y Humanísticas, Escuela Superior Politécnica del Litoral (ESPOL), Guayaquil, Ecuador. lfsanche@espol.edu.ec

## License

The code is released under the Apache License 2.0; see `LICENSE`. The files in `data/original/` are Colussi's replication files, redistributed only to reproduce the paper; they remain under the terms set by their author and the journal (see `NOTICE`).
