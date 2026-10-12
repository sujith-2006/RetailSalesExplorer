"""Prepare compact weekly sales data for the static GitHub Pages site."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INDIA_CSV = ROOT / "data" / "Amazon Sale Report.csv"
PARQUET_FILE = ROOT / "data" / "weekly_sales.parquet"
EXCEL_FILE = ROOT / "data" / "Online Retail.xlsx"
OUTPUT_FILE = ROOT / "docs" / "data" / "sales.json"


def build_india_weekly_data() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(INDIA_CSV, low_memory=False)
    raw.columns = raw.columns.str.strip()
    required = {"Date", "Category", "Qty", "Amount"}
    missing = sorted(required.difference(raw.columns))
    if missing:
        raise ValueError(f"Amazon report is missing required columns: {', '.join(missing)}")

    raw["Date"] = pd.to_datetime(raw["Date"], format="%m-%d-%y", errors="coerce")
    raw["Qty"] = pd.to_numeric(raw["Qty"], errors="coerce").fillna(0)
    raw["Amount"] = pd.to_numeric(raw["Amount"], errors="coerce")
    raw["Category"] = raw["Category"].astype("string").str.strip().str.title()

    sales = raw.dropna(subset=["Date", "Category"]).copy()
    sales = sales[(sales["Qty"] > 0) & sales["Category"].ne("")]
    if "Status" in sales:
        excluded = sales["Status"].astype("string").str.contains(
            r"cancel|return|reject|lost|refund", case=False, na=False
        )
        sales = sales[~excluded]
    if "currency" in sales:
        sales = sales[sales["currency"].isna() | sales["currency"].astype("string").str.upper().isin(["INR", "₹"])]

    # Do not let a few days at either edge masquerade as a full week. Uneven
    # boundary weeks can distort both the displayed history and the forecast.
    sales["WeekStart"] = sales["Date"].dt.to_period("W-SUN").dt.start_time
    first_week = sales["WeekStart"].min()
    last_week = sales["WeekStart"].max()
    if sales["Date"].min().normalize() > first_week:
        sales = sales[sales["WeekStart"] != first_week]
    if sales["Date"].max().normalize() < last_week + pd.Timedelta(days=6):
        sales = sales[sales["WeekStart"] != last_week]

    sales["Revenue"] = sales["Amount"].fillna(0).clip(lower=0)
    weekly = (
        sales.groupby(["WeekStart", "Category"], as_index=False)
        .agg(Revenue=("Revenue", "sum"), Units=("Qty", "sum"))
    )
    metadata = {
        "market": "Amazon India",
        "currency": "INR",
        "productLabel": "Product category",
        "source": "Amazon Sale Report (Kaggle)",
        "sourceUrl": "https://www.kaggle.com/datasets/thedevastator/unlock-profits-with-e-commerce-sales-data",
        "excludedTransactions": "Cancelled, returned, rejected, lost, or refunded orders",
    }
    return weekly, metadata


def build_uci_weekly_data() -> tuple[pd.DataFrame, dict]:
    if PARQUET_FILE.exists():
        weekly = pd.read_parquet(PARQUET_FILE)
    else:
        if not EXCEL_FILE.exists():
            raise FileNotFoundError(
                f"Put Amazon Sale Report.csv or Online Retail.xlsx in {EXCEL_FILE.parent}."
            )
        raw = pd.read_excel(
            EXCEL_FILE,
            usecols=["StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice"],
        )
        raw["InvoiceDate"] = pd.to_datetime(raw["InvoiceDate"], errors="coerce")
        sales = raw.dropna(subset=["StockCode", "InvoiceDate", "Quantity", "UnitPrice"]).copy()
        sales = sales[(sales["Quantity"] > 0) & (sales["UnitPrice"] > 0)]
        sales["Description"] = sales["Description"].fillna("Unknown product")
        sales["Product"] = sales["StockCode"].astype(str) + " — " + sales["Description"].astype(str)
        sales["Revenue"] = sales["Quantity"] * sales["UnitPrice"]
        sales["WeekStart"] = sales["InvoiceDate"].dt.to_period("W-SUN").dt.start_time
        weekly = sales.groupby(["WeekStart", "Product"], as_index=False).agg(
            Revenue=("Revenue", "sum"), Units=("Quantity", "sum")
        )
    if "Product" not in weekly and "Description" in weekly:
        weekly["Product"] = weekly["Description"]
    metadata = {
        "market": "Online Retail (United Kingdom)",
        "currency": "GBP",
        "productLabel": "Product",
        "source": "UCI Online Retail",
        "sourceUrl": "https://archive.ics.uci.edu/dataset/352/online%2Bretail",
        "excludedTransactions": "Returns and cancelled transactions",
    }
    return weekly, metadata


def main() -> None:
    weekly, metadata = build_india_weekly_data() if INDIA_CSV.exists() else build_uci_weekly_data()
    weekly = weekly.sort_values(["WeekStart", "Category" if "Category" in weekly else "Product"])
    product_column = "Category" if "Category" in weekly else "Product"
    products = sorted(weekly[product_column].astype(str).unique().tolist())
    product_ids = {product: index for index, product in enumerate(products)}
    first_week = weekly["WeekStart"].min()
    last_week = weekly["WeekStart"].max()
    weeks = pd.date_range(first_week, last_week, freq="7D").strftime("%Y-%m-%d").tolist()
    week_ids = {week: index for index, week in enumerate(weeks)}

    rows = [
        [
            week_ids[row.WeekStart.strftime("%Y-%m-%d")],
            product_ids[str(getattr(row, product_column))],
            round(float(row.Revenue), 2),
            int(row.Units),
        ]
        for row in weekly.itertuples(index=False)
    ]
    metadata["periodStart"] = weeks[0]
    metadata["periodEnd"] = weeks[-1]
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps({"weeks": weeks, "products": products, "rows": rows, **metadata}, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Prepared {len(rows):,} weekly product records at {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
