# wb-economic-freedom

Exploring how economic freedom relates to real-world development outcomes, by merging World Bank development indicators with the Heritage Foundation's Index of Economic Freedom.

> **Status:** cleaning is complete and the merged dataset is published to `data/processed/`. Exploratory analysis is in progress; the machine learning stage has not started.

## Project Goal

This project investigates the relationship between economic freedom (property rights, government integrity, trade freedom, etc.) and development outcomes (GDP per capita, life expectancy, unemployment, and more) across countries and years.

Stages:

1. **Cleaning** *(complete)* — merge two messy, real-world sources into a single clean dataset → [`notebooks/I-cleaning.ipynb`](notebooks/I-cleaning.ipynb)
2. **Analysis** *(in progress)* — exploratory data analysis and visualisation → [`notebooks/II-analysis.ipynb`](notebooks/II-analysis.ipynb)
3. **Machine Learning** *(not started)* — predictive modelling on the cleaned dataset → [`notebooks/III-ml.ipynb`](notebooks/III-ml.ipynb)

## Data Sources

| Source | Description | Location |
| --- | --- | --- |
| [World Bank — World Development Indicators](https://databank.worldbank.org/source/world-development-indicators) | Country-level indicators: GDP, life expectancy, unemployment, inflation, population, FDI, CO2 emissions, poverty | `data/raw/world_bank_indicators.csv` |
| [Heritage Foundation — Index of Economic Freedom](https://www.heritage.org/index/) | Overall economic freedom score plus 12 sub-components (property rights, tax burden, trade freedom, etc.) | `data/raw/economic_freedom_data.csv` |

Reference material (indicator definitions, sources, methodology — not used in the pipeline itself):

| File | Location |
| --- | --- |
| World Bank indicator metadata | `data/reference/world_bank_metadata.csv` |

**Cleaned output:** `data/processed/wb_economic_freedom_merged.csv` — 4,581 country-year rows × 25 columns, covering 185 countries from 2001 to 2025.

## What the Cleaning Stage Resolved

Each of these is investigated and documented in `I-cleaning.ipynb` rather than fixed silently:

- **Country naming.** The two sources name countries differently (`"Korea, Rep."` vs `"South Korea"`). Names were standardised through a single mapping in `src/cleaning.py`; territories and countries with no counterpart in the other source (Greenland, Bermuda, Taiwan, South Sudan, …) were dropped, since they cannot be merged.
- **Poverty headcount ratio.** 61% missing, spread fairly evenly across all 25 years, with 23 countries never reporting it at all. This reflects how infrequently household consumption surveys are run, not a data error — but it was too sparse to keep, so the column was **dropped**.
- **Fiscal Health and Judicial Effectiveness.** Dropped: ~64% missing, both being recently-added Index components.
- **Labor Freedom.** 19.5% missing, concentrated in 2001–2008 because the component entered the Index methodology later. Kept, with the caveat that time-series work involving it should not read pre-2009 as a genuine gap.
- **School enrollment, secondary.** 30.6% missing, spiking to 95.6% in 2025 through reporting lag. Kept.
- **Life expectancy.** Two implausible Central African Republic values (14.7 years in 2009, 18.8 in 2022) were set to `NaN` as isolated data errors.
- **Extreme FDI, GDP growth, and inflation values.** Verified as real economic phenomena rather than errors and kept as-is. FDI-to-GDP swings concentrate in four financial-centre economies (Liechtenstein, Malta, Cyprus, Luxembourg) and may need capping or a dedicated flag before use as an ML feature.
- **Year alignment.** The Heritage Index published for year *N* is graded on data collected through roughly mid-*N-1*, so joining it onto World Bank calendar year *N* builds in a small lag. This is documented as a deliberate choice in Part IV of the cleaning notebook and should be revisited before any causal or predictive framing.

## Modelling Constraints

Six properties of the cleaned dataset were measured because each one produces a *plausible-looking result* rather than an error, and would otherwise only surface after modelling work had been built on top of it. They are written up in full, with the measured figures, at the bottom of [`notebooks/III-ml.ipynb`](notebooks/III-ml.ipynb). In short:

1. `GDP per capita` is exactly `GDP / Population` (relative error 2.5e-16) — leaving both in the features gives R² ≈ 1.00 for free.
2. The mean of the ten remaining freedom sub-components predicts `Overall Score` with R² = 0.976 — predicting one from the others re-derives Heritage's formula, not economics.
3. Year-on-year autocorrelation is 0.98–0.99, so a shuffled train/test split leaks; use `GroupKFold` by country or a temporal split.
4. A naive `dropna()` cuts the data from 4,581 rows to 2,385 and silently removes 2001–2004 and all of 2025.
5. Missingness tracks the outcome (median GDP per capita $2,510 for countries missing school enrollment vs $5,801 for those reporting it), so mean imputation injects the inverse bias.
6. The `Index Year` lag stops being cosmetic as soon as the framing becomes causal.

### A note on snapshot years

Indicator coverage is strongly year-dependent: 2025 is ~95% complete for economic freedom and GDP per capita but has **no** life expectancy values at all. `src/utils.py` therefore provides `latest_complete_year()`, which picks the most recent year clearing a coverage threshold for the specific columns a chart uses, and raises for columns that never clear it rather than quietly substituting another year. Snapshot charts carry a coverage note in their subtitle for the same reason.

## Running the Notebooks

The notebooks import project code as `from src import cleaning` and read data via paths like `data/raw/...`, so **they must run with the repository root as the working directory**.

```bash
pip install -r requirements.txt
```

- **VS Code:** already handled — `.vscode/settings.json` sets `jupyter.notebookFileRoot` to the workspace folder.
- **Terminal:** launch Jupyter from the repository root, not from `notebooks/`.
- **Colab / Kaggle:** run the setup cell at the top of each notebook; it clones the repo, changes into its root, and installs the two packages that are not preinstalled there. On Kaggle, enable *Settings → Internet → On* first.

Run them in order: `I-cleaning.ipynb` writes the processed CSV that `II-analysis.ipynb` reads.

## Project Structure

```text
wb-economic-freedom/
│
├── data/
│   ├── raw/                  # original, untouched data
│   ├── interim/              # partially cleaned data (if needed)
│   ├── processed/            # final merged & cleaned dataset
│   └── reference/            # metadata / documentation, not used in the pipeline
│
├── notebooks/
│   ├── I-cleaning.ipynb      # loading, standardising, merging, cleaning
│   ├── II-analysis.ipynb     # exploratory data analysis & visualisation
│   └── III-ml.ipynb          # future: predictive modelling
│
├── src/
│   ├── __init__.py
│   ├── cleaning.py           # data cleaning & merging functions
│   ├── viz.py                # reusable plotting functions
│   └── utils.py              # generic helper functions
│
├── tests/
│   ├── test_cleaning.py      # unit tests for the cleaning transformations
│   └── test_utils.py         # unit tests for the coverage helpers
│
├── reports/
│   └── figures/              # exported charts
│
├── conftest.py               # puts the repo root on sys.path for pytest
├── ruff.toml                 # lint + format configuration
├── requirements.txt
├── requirements-dev.txt      # tooling; not needed to run the notebooks
├── .gitignore
└── README.md
```

## Development

```bash
pip install -r requirements-dev.txt
```

```bash
pytest
```

```bash
ruff check src tests notebooks && ruff format --check src tests
```

Both commands run from the repository root. Notebooks are linted too, which is what keeps conventions such as `.isna()` over `.isnull()` from drifting back into a cell. The test suite covers the pure transformations in `src/` — country-name standardisation, the melt/pivot reshaping, continent resolution including the codes `pycountry_convert` cannot handle, the `'..'` null-marker conversion, and the coverage helpers.

## Tech Stack

- **pandas** — data manipulation
- **matplotlib** — the static, portfolio-facing panels (these render on GitHub)
- **plotly** — the two animated charts, where interactivity is the point (these do **not** render on GitHub; open the notebook in Colab to view them)
- **adjustText** — label placement on the dense per-continent scatter panels
- **pycountry_convert** — deriving the `Continent` column from ISO3 codes
- **scikit-learn** *(future)* — machine learning

## Roadmap

- [x] Define project scope and data sources
- [x] Set up folder structure
- [x] Download raw data (World Bank + Economic Freedom Index)
- [x] Standardise country names/codes across sources
- [x] Merge datasets into a single country-year table
- [x] Handle missing data and outliers
- [x] Export the cleaned dataset to `data/processed/`
- [ ] Exploratory analysis and visualisation *(in progress — correlation analysis and key findings still to write)*
- [ ] Feature selection for modelling
- [ ] Machine learning model

## Technical References

The conventions in this repository are not invented ad hoc; each one is borrowed from a source that argues for it.

| Reference | Author | What it informed here |
| --- | --- | --- |
| *Hands-On Machine Learning with Scikit-Learn, Keras & TensorFlow*, 3rd edition | Aurélien Géron | The modelling stage — validation strategy, leakage, and the reasoning behind the measured constraints in `III-ml.ipynb` |
| *Software Engineering for Data Scientists* | Catherine Nelson | Repository layout (`src/` — `notebooks/` — `tests/`), testing the pure transformations, linting and formatting as a definition of done |
| *Python for Data Analysis*, 3rd edition | Wes McKinney | pandas idiom — reshaping with melt/pivot, merging, missing-data handling |

Library documentation was the reference of record for API behaviour, in preference to secondhand summaries:
[pandas](https://pandas.pydata.org/docs/), [matplotlib](https://matplotlib.org/stable/index.html), [plotly](https://plotly.com/python/), [scikit-learn](https://scikit-learn.org/stable/), [pycountry_convert](https://pypi.org/project/pycountry-convert/), [ruff](https://docs.astral.sh/ruff/), [pytest](https://docs.pytest.org/).

**Claude Opus 5** (Anthropic) was used as a working assistant throughout: interpreting the data, pressure-testing conclusions, and reviewing code. Every finding it surfaced was verified against the dataset before being written down — the figures quoted in this README and in the notebooks are measured, not asserted.

## License

Data is provided by the World Bank (CC BY-4.0) and the Heritage Foundation. This repository's code is available under the [MIT License](LICENSE).
