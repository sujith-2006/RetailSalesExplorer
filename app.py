from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.holtwinters import ExponentialSmoothing


DATA_FILE = Path("data/Online Retail.xlsx")
CACHE_FILE = Path("data/weekly_sales.parquet")


st.set_page_config(
    page_title="Retail Sales Explorer",
    page_icon="🛍️",
    layout="wide",
)

st.title("Retail Sales Explorer")
st.write("Explore historical retail sales and forecast weekly revenue or units.")


@st.cache_data(show_spinner="Loading and preparing the dataset...")
def load_weekly_data(source_modified_time):
    # Use the prepared file if it is newer than the original Excel file.
    if CACHE_FILE.exists() and CACHE_FILE.stat().st_mtime >= source_modified_time:
        return pd.read_parquet(CACHE_FILE)

    raw = pd.read_excel(
        DATA_FILE,
        usecols=[
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
        ],
    )

    raw["InvoiceDate"] = pd.to_datetime(raw["InvoiceDate"], errors="coerce")

    sales = raw.dropna(
        subset=["StockCode", "InvoiceDate", "Quantity", "UnitPrice"]
    ).copy()

    # Exclude returns/cancellations and rows without a usable price.
    sales = sales[(sales["Quantity"] > 0) & (sales["UnitPrice"] > 0)]

    sales["Description"] = sales["Description"].fillna("Unknown product")
    sales["StockCode"] = sales["StockCode"].astype(str)
    sales["Product"] = sales["StockCode"] + " — " + sales["Description"].astype(str)
    sales["Revenue"] = sales["Quantity"] * sales["UnitPrice"]

    # Weeks start on Monday.
    sales["WeekStart"] = sales["InvoiceDate"].dt.to_period("W-SUN").dt.start_time

    weekly = sales.groupby(["WeekStart", "Product"], as_index=False).agg(
        Revenue=("Revenue", "sum"),
        Units=("Quantity", "sum"),
    )

    weekly.to_parquet(CACHE_FILE, index=False)
    return weekly


if not DATA_FILE.exists():
    st.error(
        f"Dataset not found at {DATA_FILE}. "
        "Make sure Online Retail.xlsx is inside the data folder."
    )
    st.stop()


try:
    weekly_data = load_weekly_data(DATA_FILE.stat().st_mtime)
except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.stop()


# Offer all products and the 20 highest-revenue products.
top_products = (
    weekly_data.groupby("Product")["Revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(20)
)

product_options = ["All products"] + top_products.index.tolist()

st.sidebar.header("Explorer settings")
selected_product = st.sidebar.selectbox("Product", product_options)
selected_metric = st.sidebar.selectbox("Measure", ["Revenue (GBP)", "Units"])
forecast_weeks = st.sidebar.slider(
    "Weeks to forecast", min_value=1, max_value=12, value=4
)

metric_column = "Revenue" if selected_metric == "Revenue (GBP)" else "Units"

if selected_product == "All products":
    selected_data = weekly_data
else:
    selected_data = weekly_data[weekly_data["Product"] == selected_product]


# Aggregate the selected product or all products by week.
series = selected_data.groupby("WeekStart")[metric_column].sum().sort_index()

# Fill weeks without recorded sales with zero.
if not series.empty:
    complete_weeks = pd.date_range(
        start=series.index.min(),
        end=series.index.max(),
        freq="W-MON",
    )
    series = series.reindex(complete_weeks, fill_value=0.0)
    series.index.name = "Week"

if series.empty:
    st.warning("There is no sales data for this selection.")
    st.stop()


# Summary cards
total_revenue = selected_data["Revenue"].sum()
total_units = selected_data["Units"].sum()
first_week = series.index.min().strftime("%d %b %Y")
last_week = series.index.max().strftime("%d %b %Y")

card1, card2, card3 = st.columns(3)
card1.metric("Revenue (GBP)", f"£{total_revenue / 1_000_000:.2f}M")
card2.metric("Units sold", f"{total_units:,.0f}")
card3.metric("Weeks of data", f"{len(series)}")

st.caption(
    f"Showing {selected_product.lower()} from {first_week} to {last_week}. "
    "Returns and cancelled transactions are excluded."
)


# Historical sales chart
st.subheader(f"Weekly {selected_metric}")

history_chart = go.Figure()
history_chart.add_trace(
    go.Scatter(
        x=series.index,
        y=series.values,
        mode="lines",
        name="Historical sales",
    )
)
history_chart.update_layout(
    xaxis_title="Week",
    yaxis_title=selected_metric,
    hovermode="x unified",
)
st.plotly_chart(history_chart, use_container_width=True)


# Top products chart, shown when exploring all products.
if selected_product == "All products":
    st.subheader("Top 10 products by revenue")

    top_10 = (
        weekly_data.groupby("Product")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .sort_values()
    )

    # Shorten labels so more of each product name fits on the chart.
    top_10.index = [product[:32] for product in top_10.index]
    st.bar_chart(top_10, horizontal=True)


# Forecast and validation comparison
st.subheader("Forecast")

if len(series) < 12:
    st.warning("At least 12 weeks of data are needed to show a forecast.")
else:
    holdout_weeks = min(8, max(4, len(series) // 5))
    training_data = series.iloc[:-holdout_weeks]
    actual_values = series.iloc[-holdout_weeks:]

    try:
        # Fit exponential smoothing on earlier weeks and predict the holdout.
        validation_model = ExponentialSmoothing(
            training_data,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        ).fit()

        validation_predictions = validation_model.forecast(holdout_weeks)

        actual = actual_values.to_numpy()
        predicted = validation_predictions.to_numpy()

        mae = float(np.mean(np.abs(actual - predicted)))
        rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))

        # Baseline: predict each holdout week as the last training week.
        baseline_predictions = np.repeat(training_data.iloc[-1], holdout_weeks)
        baseline_mae = float(np.mean(np.abs(actual - baseline_predictions)))
        baseline_rmse = float(np.sqrt(np.mean((actual - baseline_predictions) ** 2)))

        st.markdown("**Exponential smoothing**")
        score1, score2 = st.columns(2)
        score1.metric("MAE", f"{mae:,.2f}")
        score2.metric("RMSE", f"{rmse:,.2f}")

        st.markdown("**Naive baseline**")
        base1, base2 = st.columns(2)
        base1.metric("MAE", f"{baseline_mae:,.2f}")
        base2.metric("RMSE", f"{baseline_rmse:,.2f}")

        # Refit using all available weeks for the future forecast.
        final_model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal=None,
            initialization_method="estimated",
        ).fit()

        future_values = final_model.forecast(forecast_weeks)
        future_dates = pd.date_range(
            start=series.index[-1] + pd.Timedelta(days=7),
            periods=forecast_weeks,
            freq="W-MON",
        )
        future_values.index = future_dates
        future_values = future_values.clip(lower=0)

        forecast_chart = go.Figure()
        forecast_chart.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                name="Historical sales",
            )
        )
        forecast_chart.add_trace(
            go.Scatter(
                x=future_values.index,
                y=future_values.values,
                mode="lines+markers",
                name="Forecast",
                line={"dash": "dash"},
            )
        )
        forecast_chart.update_layout(
            xaxis_title="Week",
            yaxis_title=selected_metric,
            hovermode="x unified",
        )
        st.plotly_chart(forecast_chart, use_container_width=True)

        forecast_table = pd.DataFrame(
            {
                "Week": future_values.index.strftime("%d %b %Y"),
                f"Forecast {selected_metric}": future_values.values,
            }
        )
        st.dataframe(
            forecast_table,
            hide_index=True,
            use_container_width=True,
        )

        st.caption(
            "Lower MAE and RMSE indicate smaller errors. "
            "Compare exponential smoothing with the naive baseline "
            "to see whether the model improves on a simple last-week guess."
        )

    except Exception as error:
        st.error(f"Could not create the forecast: {error}")


with st.expander("Recent weekly data"):
    recent_data = series.tail(12).rename(selected_metric).reset_index()
    st.dataframe(
        recent_data,
        hide_index=True,
        use_container_width=True,
    )
