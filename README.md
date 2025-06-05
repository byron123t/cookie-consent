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

Run the following command to do the experiments and crawl the data. The output will be in the `script/craw_results` directory.

```bash
./scripts/crawl.sh
```

## Cookie Consistency Checking

This script will use raw cookie data from crawls in `data/yyyy-mm-dd/` and perform a consistency analysis. The resulting data will be placed into .parquet files in `data/regions/`.

```bash
./scripts/check.sh
```

## Analyzing Data

This script will update the .parquet files in `data/regions/` with personal information detection results.

```bash
./scripts/analyze.sh
```

## Data Download

Unzip the tar file with the following command. It will outpupt into the `data/` directory

```bash
tar -xzvf consentchk_data.tar.gz
```

## Plotting Scripts

Run the following command to plot the data. The resulting plots will be in the `data/plots` directory.

```bash
./scripts/plot_data.sh
```
