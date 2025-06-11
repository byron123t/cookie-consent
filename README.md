# Cookie-Consent Project

The following was tested on a macbook running MacOS 15.5, conda 25.5.0 and pip 24.2 and an Ubuntu server running 22.04 LTS, conda 24.3.0, and pip 24.2.

## Set up environment

1. Install miniconda via https://www.anaconda.com/

2. Create a virtual environment

```bash
conda create --name cookies python=3.8
conda activate cookies
```

3. Install the requirements

```bash
pip install playwright==1.47.0
playwright install
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

4. Install ooutil library

```bash
cd ooutil
pip install -e .
```

## Crawl Websites

Run the following command to do the experiments and crawl the data. The output will be in the `data/yyyy-mm-dd` directory.

```bash
./scripts/crawl.sh
```

This script will run the `run_crawler.py` script in `ooutil/`. You can update the `SITE_TO_URLS` dictionary using a list of websites from the Tranco list for large-scale crawls. The `proxy_url` variable contains the URL of the AWS, DigitalOcean, or other proxy server in the region you are trying to collect measurements from. Update the `location` string as well.

## Crawl Data Download

Unzip the tar file with the following command. It will output into the `data/` directory. This data contains the October 4-12 raw crawl data and processed crawl data from the 8 regions evaluated. Note that some supplementary crawl data is omitted (e.g., cookie banner screenshots, category consent choice JSONs, etc.), due to the large size of the data.

[https://drive.google.com/file/d/1cHoXduxecLJnJUREx2tfeXZ46sNpRoeZ/view?usp=sharing](https://drive.google.com/file/d/1cHoXduxecLJnJUREx2tfeXZ46sNpRoeZ/view?usp=sharing)

```bash
tar -xzvf consentchk_data.tar.gz
```

This data will be unzipped into a `data/` folder which should go in the root of the repository. It should contain raw data from `2024-10-04/` to `2024-10-12/`, `regions/` with processed `.parquet` files, `plots/`, and several JSON files used in the personal information detector (`cookie_purposes.json`), the cookie banner UI analysis `cmp_ui_data.json`, and more.

## Cookie Consistency Checking

This script will use raw cookie data from crawls in `data/yyyy-mm-dd/` and perform a consistency analysis. The resulting data will be placed into `.parquet` files in `data/regions/`.

```bash
./scripts/check.sh
```

In `ooutil/run_consistency.py`, `LOCATION_TO_EXPER_DATE` contains the mapping from measurements from a certain start date, to the region these measurements were performed in. The outer for-loop controls for the number of repeated measurements to process in the cookie consent checking. The `.parquet` files will contain a dataframe of cookie data where each row contains a cookie's name, domain, path, site, compliance, etc. 

## Analyzing Data

This script will update the `.parquet` files in `data/regions/` with personal information detection results.

```bash
./scripts/analyze.sh
```

In `analysis/apply_comply.py`, a number of keywords and regex patterns allow for a lightweight personal information detector. These classifications are written to the dataframes in the `contains_personal_info` column and are placed in the `data/regions/{region}/scan_0k_20k_comply_{iteration}.parquet` files.

## Plotting Scripts

Run the following command to plot the data. The resulting plots will be in the `data/plots` directory.

```bash
./scripts/plot_data.sh
```

This array of scripts processes the `.parquet` files containing the personal info classifications, plotting mean or normalized violation rates of 1st party cookies, 3rd party cookies, same-site differences in cookies and cookie violations between regions, raw cookie counts, UI and CMP settings, etc. In the plots and labels, `incorrect` corresponds to `Ignored Cookie Rejection Violation`, `omit` corresponds to `Undeclared Cookie Violation`, and `ambiguous` corresponds to `Wrong Cookie Category Violation`. 

## Other Information

`ooutil/consent/cmp/` contains CMP specific code for the crawler to handle automating consent choices and storing CMP library data with.

`ooutil/consent/crawler/` contains crawler implementation code.

`ooutil/src/ooutil/` contains utilities such as Playwright stealth, browser data and html dumping, detecting language, dumping cookie data, user agent spoofing, etc.
