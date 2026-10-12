# Retail Sales Explorer

A responsive, browser based dashboard for exploring weekly retail sales and comparing a short term forecast with a simple baseline. The public site is a static GitHub Pages website; visitors do not need Python or an account to use it.

## Features

- Explore weekly revenue or units for all products or one of the top 20 products.
- View top products by revenue.
- Forecast between one and twelve weeks with Holt's linear exponential smoothing.
- Compare MAE and RMSE on recent held out weeks against a last week repeated baseline.
- Use the site on desktop, tablet, or mobile screens.

Returns and cancelled transactions are excluded from the demand series. The forecast is a course project demonstration using about one year of data, so it should be treated as an estimate.

## Prepare the site data

Download the UCI Online Retail Excel file from the [UCI dataset page](https://archive.ics.uci.edu/dataset/352/online%2Bretail) and place it at `data/Online Retail.xlsx`. Then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/prepare_data.py
```

The script creates `docs/data/sales.json`, a compact weekly product summary used by the browser app. The original workbook and intermediate files are excluded from Git.

## Run locally

From the project folder, run:

```bash
python3 -m http.server 8000 --directory docs
```

Open <http://localhost:8000> in a browser. The site must be served over HTTP; opening `index.html` directly from Finder will prevent the browser from loading its JSON data file.

## Publish with GitHub Pages

Push the project to a GitHub repository. In the repository, open **Settings → Pages**, select **Deploy from a branch**, choose the `main` branch and the `/docs` folder, then save. GitHub will provide the public site URL. For a repository named `<username>.github.io`, the URL is `https://<username>.github.io/`; other repositories use `https://<username>.github.io/<repository>/`.

## Project structure

```text
app.py                  # Local Streamlit prototype
scripts/prepare_data.py # Builds the compact static-site dataset
docs/index.html         # GitHub Pages application
docs/data/sales.json    # Generated data used by the website
```
