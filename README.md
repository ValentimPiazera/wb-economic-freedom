# wb-economic-freedom

World Bank development indicators merged with the Heritage Foundation's Index of Economic Freedom, covering 185 countries from 2001 to 2025. The question behind it is whether economic freedom tracks with higher GDP, and the answer turns out to depend on whether you compare countries against each other or a country against its own past.

Between countries the relationship is strong. Within a country over time it largely disappears. The distance between those two answers is what the analysis spends most of its time on.

## What this is

One row per country per year, built in two notebooks:

1. **Cleaning**, two messy sources reconciled into one table → [`notebooks/I-cleaning.ipynb`](notebooks/I-cleaning.ipynb)
2. **Analysis**, exploration, charts, and a correlation decomposition → [`notebooks/II-analysis.ipynb`](notebooks/II-analysis.ipynb)

### Why there is no model

The project stops at description, and the honest reason is worth stating rather than dressing up as methodological restraint. A model that predicted anything useful here would have to be a complicated one, and it would still likely reach bad conclusions: the panel barely moves from year to year, the sub-components feed the score they would be predicting, and the countries with missing data are the poor ones. On top of that, I ran a full EDA before any modelling would have begun, so snooping bias is already in place and no train/test split undoes that after the fact.

Describing what the two sources say about each other is a claim I can support. Predicting from them is not.

## Data Sources

| Source | What it covers | File |
| --- | --- | --- |
| [World Bank, World Development Indicators](https://databank.worldbank.org/source/world-development-indicators) | GDP, life expectancy, unemployment, inflation, population, FDI, CO2, poverty | `data/raw/world_bank_indicators.csv` |
| [Heritage Foundation, Index of Economic Freedom](https://www.heritage.org/index/) | An overall freedom score and its 12 sub-components | `data/raw/economic_freedom_data.csv` |

`data/reference/world_bank_metadata.csv` holds the World Bank's own definitions of each indicator. Nothing in the pipeline reads it; it is there so the column descriptions below can be checked against the source instead of taken on trust.

**The output:** `data/processed/wb_economic_freedom_merged.csv`, 4,581 country-years × 25 columns, 185 countries, 2001 to 2025.

## What Each Column Means

Coverage is the share of the 4,581 rows that carry a value. Nothing is imputed anywhere in the pipeline, so a blank cell means the source did not report it.

### Identifiers

| Column | What it is | Coverage |
| --- | --- | --- |
| `Country Name` | Standardised name. The two sources disagree constantly, so both pass through `COUNTRY_NAME_MAPPING` in `src/cleaning.py`. | 100% |
| `Country Code` | ISO 3166-1 alpha-3. | 100% |
| `Year` | World Bank calendar year, 2001 to 2025. The Heritage score joined onto it is graded slightly earlier; see the lag note below. | 100% |

### World Bank indicators

Descriptions condensed from the World Bank's own long definitions in `data/reference/world_bank_metadata.csv`.

| Column | What it measures | Units | Coverage |
| --- | --- | --- | --- |
| `GDP (current US$)` | Total income from goods and services produced in the territory, at the prices of that year, with no inflation adjustment. | US$ | 98.7% |
| `GDP growth (annual %)` | Year-on-year change in the *constant* price series, 2015 base, so this one is inflation-adjusted even though the level above is not. | % | 98.2% |
| `Population, total` | All residents regardless of legal status, counted at midyear. | people | 100% |
| `Life expectancy at birth, total (years)` | Years a newborn would live if current mortality patterns held for its whole life. | years | 96.0% |
| `Unemployment, total (% of total labor force) (modeled ILO estimate)` | Share of the labour force without work but available and looking. Modelled by the ILO rather than counted directly. | % | 96.8% |
| `Inflation, consumer prices (annual %)` | Annual change in the cost of a consumer basket. | % | 93.1% |
| `Foreign direct investment, net inflows (% of GDP)` | Investment from abroad acquiring a lasting stake, 10% or more of voting stock, net of disinvestment, over GDP. Negative when capital leaves. | % of GDP | 92.9% |
| `School enrollment, secondary (% gross)` | Total secondary enrollment over the population of the age group that officially belongs there. | % | 69.4% |
| `Carbon dioxide (CO2) emissions (total) excluding LULUCF (Mt CO2e)` | Annual CO2 from agriculture, energy, waste and industry. Excludes land use, uses the IPCC AR5 warming potentials. | Mt CO2e | 94.1% |

Three of these behave in ways worth knowing before plotting them:

- Enrollment is a **gross** ratio and legitimately exceeds 100%, reaching 164% here. Repeating students and students outside the official age band count in the numerator but not the denominator.
- FDI reaches extreme values in a handful of financial centres. Liechtenstein, Malta, Cyprus and Luxembourg between them span −1,303% to +1,283% of GDP. That is real capital moving through holding structures rather than corrupted data, but those four countries will dominate any FDI aggregate built from this column.
- Two life expectancy values were removed. The Central African Republic is recorded at 14.7 years in 2009 and 18.8 in 2022, with the neighbouring years in the forties and fifties, so both were set to `NaN`.

### Heritage Index

All eleven are scored 0 to 100, higher meaning freer, and they group into the Index's four pillars: rule of law, government size, regulatory efficiency, open markets.

| Column | What it measures | Coverage |
| --- | --- | --- |
| `Overall Score` | The headline number. In practice it sits very close to the plain average of the components below; see the checks section. | 92.9% |
| `Property Rights` | How well the legal system protects private property and enforces contracts. | 94.1% |
| `Government Integrity` | Absence of corruption: bribery, patronage, capture of the state. | 94.5% |
| `Tax Burden` | Top marginal rates and total tax take over GDP. **Inverted**, see below. | 93.3% |
| `Government Spending` | Government spending over GDP. **Inverted**, see below. | 93.6% |
| `Business Freedom` | Regulatory cost of starting, running and closing a company. | 94.1% |
| `Labor Freedom` | Flexibility of labour regulation: minimum wages, hiring and firing rules, hours. **Empty for 2001 to 2008**, since the component entered the methodology later. | 80.5% |
| `Monetary Freedom` | Price stability together with the absence of price controls. | 93.8% |
| `Trade Freedom` | Tariffs and non-tariff barriers. | 93.5% |
| `Investment Freedom` | Restrictions on capital moving in, out and around. | 93.8% |
| `Financial Freedom` | Banking efficiency and independence from government direction. | 93.3% |

`Tax Burden` and `Government Spending` are inverted relative to their names. Both use the same 0 to 100 scale as every other component, so a high number means low taxation and low government spending respectively. Read them the intuitive way and the second finding below inverts along with them.

### Derived here

| Column | How it is built | Coverage |
| --- | --- | --- |
| `GDP per capita (current US$)` | `GDP / Population`, computed in the pipeline. Ranges from $110 to $220,167. | 98.7% |
| `Continent` | Resolved from `Country Code` with `pycountry_convert`, six-continent model following UN M49: Central America and the Caribbean fall under North America, Russia under Europe, Türkiye and the Caucasus under Asia. Kosovo and Timor-Leste are hardcoded in `src/cleaning.py`, since the library cannot resolve either code. | 100% |

### In the raw files but not the clean one

Comparing the raw inputs against the merged output leaves three columns unaccounted for. All three were dropped deliberately:

| Column | Why it is gone |
| --- | --- |
| `Poverty headcount ratio at $3.00 a day` | 61% missing, with 23 countries never reporting it at all. Household consumption surveys are expensive and infrequent, so the gap reflects how the data is collected rather than a broken export, but the column was too sparse to keep. |
| `Fiscal Health` | ~64% missing. A recent addition to the Index, so most of the panel predates it. |
| `Judicial Effectiveness` | The same, ~64% missing, for the same reason. |

## What the Cleaning Stage Sorted Out

Each of these is worked through in `I-cleaning.ipynb` rather than fixed quietly in a cell.

The two sources name countries differently, `"Korea, Rep."` against `"South Korea"`, so both pass through a single mapping in `src/cleaning.py`. Territories and countries with no counterpart in the other source, among them Greenland, Bermuda, Taiwan and South Sudan, are dropped, since there is nothing to merge them onto.

Three columns were dropped for missingness and one was kept in spite of it, which is the table above. `Labor Freedom` is the one that needs care: it is kept, but its pre-2009 emptiness is a methodology change rather than a genuine gap, and any time-series work using it has to account for that.

Extreme values in FDI, GDP growth and inflation were checked individually and kept. They correspond to currency collapses, crises and financial-centre flows, and smoothing them would amount to inventing data.

The year alignment is the subtle one. The Heritage Index published for year *N* is graded on data collected through roughly mid-*N-1*, so joining it onto World Bank calendar year *N* builds in a small lag. Part IV of the cleaning notebook argues for doing it anyway, and it is one of the reasons nothing here is stated causally.

## What the Data Shows

The full write-up, with the charts, is Part V of [`notebooks/II-analysis.ipynb`](notebooks/II-analysis.ipynb).

Across countries, the Overall Score correlates 0.71 with log GDP per capita, and 0.79 in the 2025 snapshot. Removing each country's own average and each year's global average brings that down to 0.24, and against life expectancy to 0.03. The data therefore says a good deal about which countries are rich and free at the same time, and very little about what happens to a country that becomes freer.

The Overall Score is also outperformed by one of its own components. `Government Integrity` alone correlates 0.83 across countries, against 0.71 for the aggregate it feeds into. Part of the reason is that `Government Spending` at −0.45 and `Tax Burden` at −0.20 run the other way, so the headline number averages components of opposite sign, and `Tax Burden` reverses outright between the two levels.

Geography accounts for more than half of the raw spread: 54.8% of the 2025 variance in log GDP per capita sits between continents rather than within them. The relationship still holds inside all six, but the per-continent panels (figures 07 and 08) show what that looks like up close. Every continent has a handful of countries scoring well on both measures, with most of their neighbours a long way behind.

Countries also move slowly. 40% finish 2024 in the quintile they started 2001 in, rising to 67% in the top quintile, and change in score correlates only 0.41 with change in GDP per capita.

## Things I Checked Before Trusting the Data

Five properties of the dataset, measured rather than assumed. Each one fails in a way that still produces a plausible-looking result, which is why they are written down.

1. `GDP per capita` is exactly `GDP / Population`. Maximum relative error 4.0e-5, median 4.1e-7, bounded by the export's rounding rather than by any real gap. Three columns carrying two independent quantities.
2. The mean of the ten surviving freedom components reproduces `Overall Score` with R² = 0.976. The aggregate is very nearly its own arithmetic mean.
3. Year-on-year autocorrelation runs 0.98 to 0.99, which is why the analysis separates between-country from within-country variation instead of pooling both into a single correlation.
4. A plain `dropna()` cuts 4,581 rows to 2,385 and silently removes 2001 to 2004 along with all of 2025.
5. Missingness tracks the outcome. Median GDP per capita is $2,510 among countries missing school enrollment, against $5,801 among those reporting it, and three of the ten lowest-scoring countries in 2025 report no GDP per capita at all. Dropping incomplete rows means dropping poor countries.

### Picking a snapshot year

Coverage depends heavily on the year. 2025 is ~95% complete for economic freedom and GDP per capita and has no life expectancy values at all. `src/utils.py` therefore provides `latest_complete_year()`, which returns the most recent year clearing a coverage threshold for the specific columns a chart uses, and raises for columns that never clear it instead of quietly substituting another year. Snapshot charts carry a coverage note in the subtitle for the same reason: a ranking silently drops the countries that did not report, and in 2025 that removes Liechtenstein, the highest GDP per capita in the dataset, from the top ten.

## Running the Notebooks

The notebooks import project code as `from src import cleaning` and read data through paths like `data/raw/...`, so **the working directory has to be the repository root**.

```bash
pip install -r requirements.txt
```

- **VS Code:** already handled, `.vscode/settings.json` points `jupyter.notebookFileRoot` at the workspace folder.
- **Terminal:** launch Jupyter from the repository root, not from `notebooks/`.
- **Colab / Kaggle:** run the setup cell at the top of each notebook. It clones the repo, changes into the root and installs the two packages those platforms do not ship. On Kaggle, switch *Settings → Internet → On* first.

Run them in order: `I-cleaning.ipynb` writes the CSV that `II-analysis.ipynb` reads.

## Project Structure

```text
wb-economic-freedom/
│
├── data/
│   ├── raw/                  # original, untouched data
│   ├── processed/            # final merged & cleaned dataset
│   └── reference/            # metadata, not read by the pipeline
│
├── notebooks/
│   ├── I-cleaning.ipynb      # loading, standardising, merging, cleaning
│   └── II-analysis.ipynb     # exploration & visualisation
│
├── src/
│   ├── __init__.py
│   ├── cleaning.py           # cleaning & merging functions
│   ├── viz.py                # reusable plotting functions
│   └── utils.py              # coverage and panel helpers
│
├── tests/
│   ├── test_cleaning.py      # the cleaning transformations
│   ├── test_utils.py         # the coverage and panel helpers
│   └── test_viz.py           # formatters and figure export
│
├── figures/                  # the eleven exported panels, written by II-analysis
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

Both run from the repository root. The notebooks are linted as well, which is what keeps conventions such as `.isna()` over `.isnull()` from drifting back into a cell. The tests cover the pure transformations in `src/`: country-name standardisation, the melt/pivot reshaping, continent resolution including the two codes `pycountry_convert` cannot handle, the `'..'` null marker, and the coverage helpers.

## Tech Stack

- **pandas**, the data work
- **matplotlib**, the static panels, which render on GitHub
- **plotly**, the two animated charts, where the interactivity is the point; these do **not** render on GitHub, so open the notebook in Colab
- **kaleido**, writing those two out as stills for `figures/`
- **adjustText**, label placement on the crowded per-continent scatters
- **pycountry_convert**, the `Continent` column

### About those two plotly stills

`figures/05-freedom-vs-gdp-scatter-still.png` and `figures/06-freedom-choropleth-still.png` are bad images, and I would rather say so than have someone assume they represent the charts. Each is a single frame of something that animates across 25 years, and in both the movement is the argument; the hover labels are what identify the countries, and a still has neither. They are the best I could get out of a format GitHub renders, and they exist only so that something is visible there. **Open `II-analysis.ipynb` in Colab or Jupyter to see the charts as intended.** The other nine panels lose nothing as images.

## What I Read

None of the conventions in this repository are original to it, so it is worth naming where they came from.

| Book | Author | What it shaped |
| --- | --- | --- |
| *Software Engineering for Data Scientists* | Catherine Nelson | The `src/` / `notebooks/` / `tests/` layout, testing the pure transformations, treating lint and format as part of done |
| *Python for Data Analysis*, 3rd edition | Wes McKinney | pandas idiom: melt/pivot reshaping, merging, handling missing data |

For API behaviour I went to the library documentation rather than secondhand summaries: [pandas](https://pandas.pydata.org/docs/), [matplotlib](https://matplotlib.org/stable/index.html), [plotly](https://plotly.com/python/), [adjustText](https://adjusttext.readthedocs.io/), [pycountry_convert](https://pypi.org/project/pycountry-convert/), [ruff](https://docs.astral.sh/ruff/), [pytest](https://docs.pytest.org/).

**Claude Opus 5** (Anthropic) worked alongside me throughout: interpreting the data, pushing back on conclusions, and reviewing code. Everything it surfaced was checked against the dataset before being written down, so every figure quoted in this README and in the notebooks is measured rather than asserted.

## License

The data comes from the World Bank (CC BY-4.0) and the Heritage Foundation. The code in this repository is under the [MIT License](LICENSE).
