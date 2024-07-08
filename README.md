# Quick Start

```
bft git clone https://github.com/mariostg/bft.git
cd bft
python -m venv .env-bft
source .env-bft/bin/activate
python -m pip install pip-tools
pip-compile
pip-sync --ask
cp .env-exemple .env #Edit as needed
mkdir log # adapt settings.py accorfingly
python manage.py createsuperuser.
python manage.py runserver
```
# Useful terminal commands

## Populate Fundamental data
In development, one can populate the BFT with the following command:

```
python manage.py populate
```
which will yield the following output to the terminal if all goes well:

```
Set FY to 2023
Set Quarter to 1
Set Period to 1
8 funds(s) have been uploaded.
7 sources(s) have been uploaded.
8 fund center(s) have been uploaded.
3 cost center(s) have been uploaded.
2 capital project(s) have been uploaded.
13 In Year Capital Forecasts(s) have been uploaded.
4 New Year Capital Forecasts(s) have been uploaded.
4 CapitalProjectYearEndProcessor Year End Capital Forecasts(s) have been uploaded.
2 cost center allocation(s) have been uploaded.
3 fund center allocation(s) have been uploaded.
```

## Upload encumbrance report
This will upload a DRMIS encumbrance report aa long as the report meets the formatting conditions.

```
python manage.py uploadcsv test-data/encumbrance_2184A3-p1.txt
```
