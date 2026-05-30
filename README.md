[![Build Status](https://github.com/openelections/openelections-data-wv/actions/workflows/data_tests.yml/badge.svg?branch=master)](https://github.com/openelections/openelections-data-wv/actions/workflows/data_tests.yml?query=branch%3Amaster)

OpenElections Data West Virginia
=====================

This repository contains CSV files with West Virginia election results. Recent results (2020 and later) are fetched directly from the West Virginia Secretary of State's [Clarity Elections system](https://results.enr.clarityelections.com) using the scripts described below. Older results were converted from [PDFs produced by the state](https://sos.wv.gov/elections/Pages/HistElecResults.aspx). The filenames are [constructed according to the specifications described in the OpenElections documentation](http://docs.openelections.net/archive-standardization/).

Older CSV files are converted from [original source files](https://github.com/openelections/openelections-sources-wv) from individual counties. You can see [county-specific inventories](https://github.com/openelections/openelections-data-wv/blob/master/county_matrix.csv) and refer to the below table for overall progress. Elections marked as `done` have all counties completed for that level. Those marked as `working` mean that at least one volunteer is working on this election, and this could be a good place to start if you're new. `Not started` means that this election is wide open and could use a volunteer.

## Scripts

Dependencies are managed with [uv](https://docs.astral.sh/uv/). To install:

```bash
uv sync
```

### clarity_parser.py

Downloads results directly from the West Virginia Clarity Elections system. Accepts a Clarity summary URL and produces CSV output.

**County-level results** (one row per county per candidate):

```bash
uv run python scripts/clarity_parser.py statewide <URL> <output_file>
```

Example:
```bash
uv run python scripts/clarity_parser.py statewide \
  https://results.enr.clarityelections.com/WV/126209/web.345435/#/summary \
  2026/20260513__wv__primary__county.csv
```

**Precinct-level results** (one file per county, written into the directory prefix given by `filename`):

```bash
uv run python scripts/clarity_parser.py precincts <URL> <filename_prefix>
```

Example:
```bash
uv run python scripts/clarity_parser.py precincts \
  https://results.enr.clarityelections.com/WV/126209/web.345435/#/summary \
  2026/counties/20260513__wv__primary
```

This produces files named `<filename_prefix>__<county>__precinct.csv` for each county that has XML results available.

### statewide_generator.py

Combines per-county precinct CSVs into a single statewide precinct file.

```bash
uv run python statewide_generator.py consolidate <year> <election> [election_type]
```

`election_type` defaults to `general`. Example:

```bash
uv run python statewide_generator.py consolidate 2024 20241105
uv run python statewide_generator.py consolidate 2026 20260513 primary
```

County precinct files must be placed in `<year>/counties/` before running. Additional subcommands:

```bash
uv run python statewide_generator.py headers <year> <election>   # inspect column headers
uv run python statewide_generator.py offices <year> <election>   # list unique office names
```

## Precinct Results

| year  | general  | primary  |
|---|---|---|
| 2024  | [done](https://github.com/openelections/openelections-data-wv/blob/master/2024/20241105__wv__general__precinct.csv) | [done](https://github.com/openelections/openelections-data-wv/blob/master/2024/20240514__wv__general__precinct.csv) |
| 2022  | [done](https://github.com/openelections/openelections-data-wv/blob/master/2022/20221108__wv__general__precinct.csv) | [done](https://github.com/openelections/openelections-data-wv/blob/master/2022/20220510__wv__general__precinct.csv) |
| 2020  | [done](https://github.com/openelections/openelections-data-wv/blob/master/2020/20201103__wv__general__precinct.csv) | [done](https://github.com/openelections/openelections-data-wv/blob/master/2020/20200609__wv__primary__precinct.csv) |
| 2018  | [done](https://github.com/openelections/openelections-data-wv/blob/master/2018/20181106__wv__general__precinct.csv) | [done](https://github.com/openelections/openelections-data-wv/blob/master/2018/20180508__wv__primary__precinct.csv) |
| 2016  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20161108__wv__general__precinct__raw.csv)  |  [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20160510__wv__primary__precinct__raw.csv) |
| 2014 |  [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20141104__wv__general__precinct__raw.csv) | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20140513__wv__primary__precinct__raw.csv)  |
| 2012  |  [done](https://github.com/openelections/openelections-results-wv/blob/master/raw/20121106__wv__general__precinct__raw.csv) | [done](https://github.com/openelections/openelections-results-wv/blob/master/raw/20120508__wv__primary__precinct__raw.csv) |
| 2011  | [working](https://github.com/openelections/openelections-data-wv/issues/23) | [working](https://github.com/openelections/openelections-data-wv/issues/22) |
| 2010  |  [working](https://github.com/openelections/openelections-data-wv/issues/10) | [working](https://github.com/openelections/openelections-data-wv/issues/20) |
| 2008  |  [working](https://github.com/openelections/openelections-data-wv/issues/3) | not started |


## County Results

| year  | general  | primary  |
|---|---|---|
| 2026  | - | [done](https://github.com/openelections/openelections-data-wv/blob/master/2026/20260513__wv__primary__county.csv) |
| 2024  | [done](https://github.com/openelections/openelections-data-wv/blob/master/2024/20241105__wv__general__county.csv) | [done](https://github.com/openelections/openelections-data-wv/blob/master/2024/20240514__wv__primary__county.csv) |
| 2022  | [done](https://github.com/openelections/openelections-data-wv/blob/master/2022/20221108__wv__general__county.csv) | [done](https://github.com/openelections/openelections-data-wv/blob/master/2022/20220510__wv__primary__county.csv) |
| 2020  | [done](https://github.com/openelections/openelections-data-wv/blob/master/2020/20201103__wv__general__county.csv) | [done](https://github.com/openelections/openelections-data-wv/blob/master/2020/20200609__wv__primary__county.csv) |
| 2018  | [done](https://github.com/openelections/openelections-data-wv/blob/master/2018/20180508__wv__general__county.csv) | [done](https://github.com/openelections/openelections-data-wv/blob/master/2018/20180508__wv__primary__county.csv) |
| 2016  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20161108__wv__general__county__raw.csv)  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20160510__wv__primary__county__raw.csv) |
| 2014  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20141104__wv__general__county__raw.csv)  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20160510__wv__primary__county__raw.csv) |
| 2012  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20121106__wv__general__county__raw.csv) | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20120508__wv__primary__county__raw.csv) |
| 2010  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20101102__wv__general__county__raw.csv) | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20100511__wv__primary__county__raw.csv) |
| 2008  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20081104__wv__general__county__raw.csv) | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20080513__wv__primary__county__raw.csv) |
| 2006  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20061107__wv__general__county__raw.csv) | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20060509__wv__primary__county__raw.csv) |
| 2004  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20041102__wv__general__county__raw.csv) | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20040511__wv__primary__county__raw.csv) |
| 2002  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20021105__wv__general__county__raw.csv) | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20020514__wv__primary__county__raw.csv) |
| 2000  | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20001107__wv__general__county__raw.csv) | [published](https://github.com/openelections/openelections-results-wv/blob/master/raw/20000509__wv__primary__county__raw.csv) |

To contribute, email openelections@gmail.com and let us know what counties/elections you'd like to work on. You also can leave a comment on one of the [issues](https://github.com/openelections/openelections-data-wv/issues) in this repository. Volunteers can do as much or as little as they like - one county or all of them.