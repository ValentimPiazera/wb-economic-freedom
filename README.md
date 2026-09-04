# wb-economic-freedom

Two datasets that have opinions about the same 185 countries: the World Bank's development indicators, and the Heritage Foundation's Index of Economic Freedom. This repository merges them into one clean country-year table and then asks what they actually say about each other.

## What this is

The question behind it is the obvious one — do countries with more economic freedom (secure property rights, honest government, open trade) end up richer, healthier, more employed? The answer turns out to depend entirely on how you ask, which is most of what the analysis is about.

Two stages, both finished:

1. **Cleaning** — merge two messy real-world sources into one dataset → [`notebooks/I-cleaning.ipynb`](notebooks/I-cleaning.ipynb)
2. **Analysis** — exploration, charts, and a correlation decomposition → [`notebooks/II-analysis.ipynb`](notebooks/II-analysis.ipynb)

It stops at description on purpose. The point is to establish what the two sources say about each other and to be clear about the questions they can't answer, which — as the analysis shows — includes nearly every causal one.

## Data Sources

| Source | What it covers | File |
| --- | --- | --- |
| [World Bank — World Development Indicators](https://databank.worldbank.org/source/world-development-indicators) | GDP, life expectancy, unemployment, inflation, population, FDI, CO2, poverty | `data/raw/world_bank_indicators.csv` |
| [Heritage Foundation — Index of Economic Freedom](https://www.heritage.org/index/) | An overall freedom score and its 12 sub-components | `data/raw/economic_freedom_data.csv` |

`data/reference/world_bank_metadata.csv` holds the World Bank's own indicator definitions and sources. Nothing in the pipeline reads it — it's there so the column descriptions below can be checked against the source rather than taken on trust.

**The output:** `data/processed/wb_economic_freedom_merged.csv` — 4,581 country-years × 25 columns, 185 countries, 2001 to 2025.

## What Each Column Means

Coverage is the share of the 4,581 rows that actually carry a value. Nothing is imputed anywhere in the pipeline, so an empty cell means the source didn't report it.

### Identifiers

| Column | What it is | Coverage |
| --- | --- | --- |
| `Country Name` | Standardised name. The two sources disagreed constantly, so both are mapped through `COUNTRY_NAME_MAPPING` in `src/cleaning.py`. | 100% |
| `Country Code` | ISO 3166-1 alpha-3. | 100% |
| `Year` | World Bank calendar year, 2001–2025. The Heritage score joined onto it is graded slightly earlier — see the note on the lag below. | 100% |

### World Bank indicators

Descriptions condensed from the World Bank's own long definitions in `data/reference/world_bank_metadata.csv`.

| Column | What it measures | Units | Coverage |
| --- | --- | --- | --- |
| `GDP (current US$)` | Total income from goods and services produced in the territory, at the prices of the year in question — no inflation adjustment. | US$ | 98.7% |
| `GDP growth (annual %)` | Year-on-year change in the *constant*-price series (2015 base), so this one is inflation-adjusted even though the level above isn't. | % | 98.2% |
| `Population, total` | Everyone resident regardless of legal status, counted at midyear. | people | 100% |
| `Life expectancy at birth, total (years)` | Years a newborn would live if today's mortality patterns held for its whole life. | years | 96.0% |
| `Unemployment, total (% of total labor force) (modeled ILO estimate)` | Share of the labour force without work but available and looking. Modelled by the ILO, not counted directly. | % | 96.8% |
| `Inflation, consumer prices (annual %)` | Annual change in the cost of a consumer basket. | % | 93.1% |
| `Foreign direct investment, net inflows (% of GDP)` | Investment from abroad buying a lasting stake (10%+ of voting stock), net of disinvestment, over GDP. Goes negative when money leaves. | % of GDP | 92.9% |
| `School enrollment, secondary (% gross)` | Everyone enrolled in secondary school over the population of the age group that officially belongs there. | % | 69.4% |
| `Carbon dioxide (CO2) emissions (total) excluding LULUCF (Mt CO2e)` | Annual CO2 from agriculture, energy, waste and industry. Excludes land use; uses the IPCC AR5 warming potentials. | Mt CO2e | 94.1% |

Three of these misbehave in ways worth knowing before you plot them:

- **Enrollment is a *gross* ratio and routinely passes 100%** — 164% at the top here — because repeating and out-of-age students count in the numerator but not the denominator. It's not an error.
- **FDI swings enormously** in a handful of financial-centre economies: Liechtenstein, Malta, Cyprus and Luxembourg between them span −1,303% to +1,283% of GDP. Real money moving through holding structures, not bad data, but enough for four countries to dominate any FDI aggregate you build.
- **Two life expectancy values were deleted.** The Central African Republic is recorded at 14.7 years in 2009 and 18.8 in 2022, with neighbouring years in the forties and fifties. Both were set to `NaN` as isolated errors.

### Heritage Index

All eleven are scored 0–100, higher meaning freer, and they group into the Index's four pillars: rule of law, government size, regulatory efficiency, open markets.

| Column | What it measures | Coverage |
| --- | --- | --- |
| `Overall Score` | The headline number. In practice it's very close to the plain average of the components below — see the checks section. | 92.9% |
| `Property Rights` | How well the legal system protects private property and enforces contracts. | 94.1% |
| `Government Integrity` | Absence of corruption — bribery, patronage, capture of the state. | 94.5% |
| `Tax Burden` | Top marginal rates and total tax take as a share of GDP. **Scores high when taxes are low.** | 93.3% |
| `Government Spending` | Government spending as a share of GDP. **Scores high when spending is low.** | 93.6% |
| `Business Freedom` | Regulatory cost of starting, running and closing a company. | 94.1% |
| `Labor Freedom` | Flexibility of labour regulation — minimum wages, hiring and firing rules, hours. **Empty for 2001–2008**, since the component entered the methodology later. | 80.5% |
| `Monetary Freedom` | Price stability plus the absence of price controls. | 93.8% |
| `Trade Freedom` | Tariffs and non-tariff barriers. | 93.5% |
| `Investment Freedom` | Restrictions on capital moving in, out and around. | 93.8% |
| `Financial Freedom` | Banking efficiency and independence from government direction. | 93.3% |

The two bolded rows are the trap in this table. `Tax Burden` and `Government Spending` are inverted relative to their names: a country with heavy taxation scores *low* on `Tax Burden`. Read them the intuitive way and the second finding below reads backwards.

### Derived here

| Column | How it's built | Coverage |
| --- | --- | --- |
| `GDP per capita (current US$)` | `GDP / Population`, computed in the pipeline. Ranges from $110 to $220,167. | 98.7% |
| `Continent` | Resolved from `Country Code` with `pycountry_convert`, six-continent model following UN M49 — Central America and the Caribbean sit under North America, Russia under Europe, Türkiye and the Caucasus under Asia. Two codes the library can't resolve (Kosovo, Timor-Leste) are hardcoded in `src/cleaning.py`. | 100% |

### In the raw files but not the clean one

If you compare the raw inputs against the merged output, three columns are missing and it's deliberate:

| Column | Why it's gone |
| --- | --- |
| `Poverty headcount ratio at $3.00 a day` | 61% missing, and 23 countries never report it at all. Household consumption surveys are expensive and infrequent — the gap is how the world works, not a broken export — but it was too sparse to keep. |
| `Fiscal Health` | ~64% missing. Added to the Index recently, so most of the panel predates it. |
| `Judicial Effectiveness` | Same, ~64% missing, same reason. |

## What the Cleaning Stage Sorted Out

Each of these is worked through in `I-cleaning.ipynb` rather than fixed quietly in a cell somewhere.

The two sources name countries differently — `"Korea, Rep."` against `"South Korea"` — so both go through one mapping in `src/cleaning.py`. Territories and countries with no counterpart in the other source (Greenland, Bermuda, Taiwan, South Sudan and others) are dropped, because there's nothing to merge them onto.

Three columns were dropped for missingness and one was kept despite it; that's the table above. `Labor Freedom` is the one to watch: it's kept, but its pre-2009 emptiness is a methodology change, not a genuine gap, and any time-series work needs to know that.

Extreme values in FDI, GDP growth and inflation were checked one by one and kept. They're real economic events — currency collapses, crises, financial-centre flows — and smoothing them would be inventing data.

The year alignment is the subtle one. The Heritage Index published for year *N* is graded on data collected through roughly mid-*N-1*, so joining it onto World Bank calendar year *N* builds in a small lag. Part IV of the cleaning notebook argues for doing it anyway, and it's one of the reasons the analysis doesn't make causal claims.

## What the Data Shows

Full write-up with the charts is Part V of [`notebooks/II-analysis.ipynb`](notebooks/II-analysis.ipynb).

**The freedom–prosperity relationship is strong, and almost entirely between countries rather than within them.** Across countries, the Overall Score correlates 0.71 with log GDP per capita, and 0.79 in the 2025 snapshot. Strip out each country's own average and each year's global average, and it drops to 0.24 — against life expectancy, to 0.03. So the data has plenty to say about which countries are rich and free at the same time, and very little about what happens to a country that gets freer.

**The Overall Score is beaten by one of its own components.** `Government Integrity` alone correlates 0.83 across countries; the aggregate it feeds into manages 0.71. Part of the reason is that `Government Spending` (−0.45) and `Tax Burden` (−0.20) point the other way, so the headline number is averaging components of opposite sign. `Tax Burden` even flips direction between the two levels.

**Geography explains more than half the raw spread.** 54.8% of the 2025 variance in log GDP per capita sits between continents rather than within them. The relationship still holds inside all six, but a comparison that ignores continents is partly measuring continents.

**Countries barely move.** 40% finish 2024 in the same quintile they started 2001 in, and 67% of the top quintile stays put. Change in score correlates only 0.41 with change in GDP per capita.

## Things I Checked Before Trusting the Data

Five properties of the dataset, measured rather than assumed. Each one fails in a way that looks like a perfectly good result, which is why they're worth stating.

1. `GDP per capita` is exactly `GDP / Population` — max relative error 4.0e-5, median 4.1e-7, and that's the export's rounding rather than any real gap. Three columns, two independent quantities.
2. The mean of the ten surviving freedom components reproduces `Overall Score` with R² = 0.976. The aggregate is very nearly its own arithmetic mean.
3. Year-on-year autocorrelation runs 0.98–0.99. That's why the analysis splits between-country from within-country variation instead of pooling everything into one correlation.
4. A plain `dropna()` cuts 4,581 rows to 2,385 and silently takes 2001–2004 and all of 2025 with it.
5. Missingness tracks the outcome. Median GDP per capita is $2,510 among countries missing school enrollment against $5,801 among those reporting it, and three of the ten lowest-scoring countries in 2025 report no GDP per capita at all. Dropping incomplete rows drops poor countries.

### Picking a snapshot year

Coverage depends heavily on the year: 2025 is ~95% complete for economic freedom and GDP per capita, and has no life expectancy values whatsoever. So `src/utils.py` has `latest_complete_year()`, which picks the most recent year clearing a coverage threshold for the specific columns a chart needs, and raises for columns that never clear it instead of quietly substituting another year. Snapshot charts carry a coverage note in the subtitle for the same reason — a ranking drops non-reporting countries without saying so, and in 2025 that quietly removes Liechtenstein, the highest GDP per capita in the dataset, from the top ten.

## Running the Notebooks

They import project code as `from src import cleaning` and read data via paths like `data/raw/...`, so **the working directory has to be the repository root**.

```bash
pip install -r requirements.txt
```

- **VS Code:** nothing to do — `.vscode/settings.json` points `jupyter.notebookFileRoot` at the workspace folder.
- **Terminal:** start Jupyter from the repository root, not from `notebooks/`.
- **Colab / Kaggle:** run the setup cell at the top of each notebook. It clones the repo, changes into the root and installs the two packages those platforms don't ship. On Kaggle, switch *Settings → Internet → On* first.

Run them in order — `I-cleaning.ipynb` writes the CSV that `II-analysis.ipynb` reads.

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

Both from the repository root. Notebooks are linted too, which is what stops conventions like `.isna()` over `.isnull()` from creeping back into a cell. The tests cover the pure transformations in `src/`: country-name standardisation, the melt/pivot reshaping, continent resolution including the two codes `pycountry_convert` can't handle, the `'..'` null marker, and the coverage helpers.

## Tech Stack

- **pandas** — the data work
- **matplotlib** — the static panels, which render on GitHub
- **plotly** — the two animated charts, where the interactivity is the whole point (these do **not** render on GitHub; open the notebook in Colab)
- **kaleido** — writing those two out as stills for `figures/`
- **adjustText** — label placement on the crowded per-continent scatters
- **pycountry_convert** — the `Continent` column

### About those two plotly stills

`figures/05-freedom-vs-gdp-scatter-still.png` and `figures/06-freedom-choropleth-still.png` are the weakest images in the folder by a wide margin. Both are single frames of charts that animate across 25 years, and in both the movement is the argument. The hover labels are what tell you which country you're looking at, and a PNG has neither. They exist so that *something* shows up on GitHub, which doesn't render plotly. **Open `II-analysis.ipynb` in Colab or Jupyter to see them properly.** The other nine panels lose nothing as images.

## What I Read

The conventions here are borrowed rather than invented, so it seems fair to say from where.

| Book | Author | What it shaped |
| --- | --- | --- |
| *Software Engineering for Data Scientists* | Catherine Nelson | The `src/` — `notebooks/` — `tests/` layout, testing the pure transformations, treating lint and format as part of done |
| *Python for Data Analysis*, 3rd edition | Wes McKinney | pandas idiom — melt/pivot reshaping, merging, handling missing data |

For API behaviour I went to the library documentation rather than secondhand summaries: [pandas](https://pandas.pydata.org/docs/), [matplotlib](https://matplotlib.org/stable/index.html), [plotly](https://plotly.com/python/), [adjustText](https://adjusttext.readthedocs.io/), [pycountry_convert](https://pypi.org/project/pycountry-convert/), [ruff](https://docs.astral.sh/ruff/), [pytest](https://docs.pytest.org/).

**Claude Opus 5** (Anthropic) worked alongside me throughout — interpreting the data, pushing back on conclusions, reviewing code. Everything it turned up was checked against the dataset before it went into writing. Every figure quoted in this README and in the notebooks is measured, not asserted.

## License

The data comes from the World Bank (CC BY-4.0) and the Heritage Foundation. The code in this repository is under the [MIT License](LICENSE).
