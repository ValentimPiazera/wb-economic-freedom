# freedom-vs-development

Exploring how economic freedom relates to real-world development outcomes, by merging World Bank development indicators with the Heritage Foundation's Index of Economic Freedom.

> **Status:** 🚧 Work in progress — this is a provisional README (checkpoint zero). Folder structure and raw data are in place; cleaning, analysis, and modeling are still to come.

## Project Goal

This project investigates the relationship between economic freedom (property rights, government integrity, trade freedom, etc.) and development outcomes (GDP per capita, life expectancy, unemployment, poverty, and more) across countries and years.

Planned stages:

1. **Cleaning** — merge two messy, real-world sources into a single clean dataset
2. **Analysis** — exploratory data analysis and visualization (plotly, matplotlib)
3. **Machine Learning** *(future)* — predictive modeling on the cleaned dataset

## Data Sources

| Source | Description | Location |
| --- | --- | --- |
| [World Bank — World Development Indicators](https://databank.worldbank.org/source/world-development-indicators) | Country-level indicators: GDP, life expectancy, unemployment, inflation, population, FDI, CO2 emissions, poverty | `data/raw/world_bank_data.csv` |
| [Heritage Foundation — Index of Economic Freedom](https://www.heritage.org/index/) | Overall economic freedom score plus 12 sub-components (property rights, tax burden, trade freedom, etc.) | `data/raw/economic_freedom_data.csv` |

Reference material (indicator definitions, sources, methodology — not used in the pipeline itself):

| File | Location |
| --- | --- |
| World Bank indicator metadata | `data/reference/world_bank_metadata.csv` |

**Coverage:** ~25 years of data (2001–2025, subject to per-indicator availability), all countries (excluding World Bank regional/income aggregates).

**Known data quality issues to address during cleaning:**

- Inconsistent country names/codes between sources (e.g. `"Korea, Rep."` vs `"South Korea"`)
- Poverty indicator (`Poverty headcount ratio at $3.00 a day`) has near-complete data only for 2021, following a World Bank methodology rebase (PPP 2017 → PPP 2021)
- Missing values vary significantly by indicator, country, and year
- Heritage Foundation's Index methodology changed over time (10 → 12 components)

## Project Structure

```text
freedom-vs-development/
│
├── data/
│   ├── raw/                 # original, untouched data
│   ├── interim/             # partially cleaned data (if needed)
│   ├── processed/           # final merged & cleaned dataset
│   └── reference/           # metadata / documentation, not used in the pipeline
│
├── notebooks/
│   ├── I_cleaning.ipynb      # loading, standardizing, merging, cleaning
│   ├── II_analysis.ipynb     # exploratory data analysis & visualization
│   └── III_ml.ipynb          # future: predictive modeling
│
├── src/
│   ├── __init__.py
│   ├── cleaning.py           # data cleaning & merging functions
│   ├── viz.py                # reusable plotting functions
│   └── utils.py              # generic helper functions
│
├── reports/
│   └── figures/               # exported charts
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Tech Stack

- **pandas** / **numpy** — data manipulation
- **matplotlib** / **plotly** — visualization
- **scikit-learn** *(future)* — machine learning

## Roadmap

- [x] Define project scope and data sources
- [x] Set up folder structure
- [x] Download raw data (World Bank + Economic Freedom Index)
- [ ] Standardize country names/codes across sources
- [ ] Merge datasets into a single country-year table
- [ ] Handle missing data and outliers
- [ ] Exploratory analysis and visualization
- [ ] Feature selection for modeling
- [ ] Machine learning model (future)

## License

Data is provided by the World Bank (CC BY-4.0) and the Heritage Foundation. This repository's code is available under [MIT License](LICENSE) *(add license file when ready)*.
