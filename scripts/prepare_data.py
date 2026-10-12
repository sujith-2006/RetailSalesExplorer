"""Prepare compact weekly sales data for the static GitHub Pages site."""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PARQUET_FILE = ROOT / "data" / "weekly_sales.parquet"
EXCEL_FILE = ROOT / "data" / "Online Retail.xlsx"
OUTPUT_FILE = ROOT / "docs" / "data" / "sales.json"


def build_weekly_data() -> pd.DataFrame:
    if PARQUET_FILE.exists():
        return pd.read_parquet(PARQUET_FILE)

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Put Online Retail.xlsx in {EXCEL_FILE.parent} and run this script again."
        )

    raw = pd.read_excel(
        EXCEL_FILE,
        usecols=["StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice"],
    )
    raw["InvoiceDate"] = pd.to_datetime(raw["InvoiceDate"], errors="coerce")
    sales = raw.dropna(
        subset=["StockCode", "InvoiceDate", "Quantity", "UnitPrice"]
    ).copy()
    sales = sales[(sales["Quantity"] > 0) & (sales["UnitPrice"] > 0)]
    sales["Description"] = sales["Description"].fillna("Unknown product")
    sales["Product"] = (
        sales["StockCode"].astype(str) + " — " + sales["Description"].astype(str)
    )
    sales["Revenue"] = sales["Quantity"] * sales["UnitPrice"]
    sales["WeekStart"] = sales["InvoiceDate"].dt.to_period("W-SUN").dt.start_time

    return (
        sales.groupby(["WeekStart", "Product"], as_index=False)
        .agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"))
    )


def main() -> None:
    weekly = build_weekly_data().sort_values(["WeekStart", "Product"])
    products = sorted(weekly["Product"].unique().tolist())
    product_ids = {product: index for index, product in enumerate(products)}
    weeks = sorted(weekly["WeekStart"].dt.strftime("%Y-%m-%d").unique().tolist())
    week_ids = {week: index for index, week in enumerate(weeks)}

    rows = [
        [
            week_ids[row.WeekStart.strftime("%Y-%m-%d")],
            product_ids[row.Product],
            round(float(row.Revenue), 2),
            int(row.Units),
        ]
        for row in weekly.itertuples(index=False)
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps({"weeks": weeks, "products": products, "rows": rows}, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Prepared {len(rows):,} weekly product records at {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
