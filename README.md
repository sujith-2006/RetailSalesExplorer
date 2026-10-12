# Retail Sales Explorer

A responsive dashboard for exploring retail sales and comparing short term forecasts with a simple baseline. The public site is a static GitHub Pages website; visitors do not need Python or an account to use it.

The dashboard is tailored to the Indian Amazon Sale Report. It groups orders by readable clothing category and forecasts weekly revenue in Indian rupees or units sold. Visitors choose a category, what they want to forecast, and how many weeks ahead. The page then shows the estimated total, next week's estimate, recent direction, and a chart. The forecast is a planning estimate, not a guarantee.

## Features

- Explore weekly revenue or units for all categories or one chosen category.
- Forecast between one and twelve weeks with damped-trend Holt exponential smoothing, which softens the recent trend further into the future.
- Compare MAE and RMSE on recent held-out weeks against a last-week-repeated baseline.
- Use the site on desktop, tablet, or mobile screens.

## Prepare the data

For the India focused dashboard, download **Amazon Sale Report.csv** from [Kaggle's E-Commerce Sales Dataset](https://www.kaggle.com/datasets/thedevastator/unlock-profits-with-e-commerce-sales-data) and place it at `data/Amazon Sale Report.csv`. It contains order dates, product categories, quantities, amounts, and Indian shipping locations. Then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/prepare_data.py
```

The script creates `docs/data/sales.json`, a compact weekly summary used by the browser app. It excludes cancelled, returned, rejected, lost, or refunded orders and incomplete first or last weeks. The raw CSV is not included in the repository; follow Kaggle's dataset terms when using or sharing it.

If `data/Amazon Sale Report.csv` is not present, the script falls back to the original UCI Online Retail dataset. Download it from the [UCI dataset page](https://archive.ics.uci.edu/dataset/352/online%2Bretail) and save it as `data/Online Retail.xlsx`.

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
