# Cookie-Consent Project

The following was tested on a macbook running MacOS 15.5, conda 25.5.0 and pip 24.2.

# Set up environment

1. Install miniconda via https://www.anaconda.com/

2. Create a virtual environment

```bash
conda create --name test1 python=3.8
conda activate test1
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

## Experiment cookie consent on a websites

Run the following command to do the experiments and crawl the data. The output will be in the `script/craw_results` directory.

```bash
cd script
python run_crawler.py
```