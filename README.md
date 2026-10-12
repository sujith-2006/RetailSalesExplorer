# Retail Sales Explorer

An interactive dashboard that explores clothing sales from an Amazon India dataset and estimates sales for the coming weeks.

**Live website:** [sujith-2006.github.io/RetailSalesExplorer](https://sujith-2006.github.io/RetailSalesExplorer/)

## What the website does

Choose a product category, a measure, and how many weeks ahead to forecast. The dashboard shows:

- **Revenue (₹):** estimated sales value in Indian rupees.
- **Units sold:** estimated number of items sold.
- **Forecast summary:** the estimated total across the selected weeks, next week's estimate, and whether the recent pattern is rising or easing.
- **Chart:** past weekly sales followed by the forecast.

These are estimates based on past sales. They are useful for exploring patterns, but they are not guaranteed results.

## How the forecast works

The project groups order records into weekly totals, then uses **damped-trend Holt exponential smoothing** to forecast those totals. In simple terms, the model looks at the recent sales level and whether sales have been moving up or down. It carries that direction into the forecast, while gradually reducing its effect further into the future.

The dashboard also checks the model against recent weeks that were held back from fitting. It reports **MAE** and **RMSE**, two measures of prediction error. Smaller values mean the estimates were closer to actual sales. A simple “repeat the last observed week” forecast is included as a baseline for comparison.

## Dataset and preparation

The dashboard uses the [Amazon Sale Report dataset on Kaggle](https://www.kaggle.com/datasets/thedevastator/unlock-profits-with-e-commerce-sales-data). The source file contains order dates, product categories, quantities, and amounts.

To prepare the data:

1. Download `Amazon Sale Report.csv` from Kaggle.
2. Put it in the project's `data` folder, using this exact filename:

   ```text
   data/Amazon Sale Report.csv
   ```

3. From the project folder, create an environment, install the required packages, and prepare the weekly data:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python scripts/prepare_data.py
   ```

The preparation script removes cancelled and other excluded orders, leaves out incomplete first and last weeks, and writes a smaller summary file to `docs/data/sales.json`. The original CSV is not included in this repository; follow the dataset's terms when downloading or sharing it.

## Run the website on your computer

From the project folder, run:

```bash
python3 -m http.server 8000 --directory docs
```

Then open [http://localhost:8000](http://localhost:8000). The site needs to be served this way so it can load its sales data.

## Publish with GitHub Pages

The live website is hosted by GitHub Pages from the repository's `main` branch and `/docs` folder. After pushing changes to `main`, GitHub Pages updates the site automatically, usually after a short delay.

## Project files

```text
scripts/prepare_data.py  # Cleans the CSV and creates weekly totals
docs/index.html          # Dashboard layout, charts, and forecast logic
docs/data/sales.json     # Weekly data loaded by the website
app.py                   # Earlier local Streamlit prototype
```
