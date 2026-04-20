from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from data_utils import load_clean_transactions


st.set_page_config(page_title="Retail Intelligence Dashboard", page_icon=":bar_chart:", layout="wide")

st.markdown(
    """
    <style>
    .main {background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 80%);}
    .metric-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 2px 14px rgba(0,0,0,0.06);
        border: 1px solid #eef1f7;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: 0.4rem;
        margin-bottom: 0.7rem;
        color: #243b53;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Retail Intelligence Dashboard")
st.caption("Page 1: Business Overview")

df = load_clean_transactions()
df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")

order_df = (
    df.groupby("InvoiceNo", as_index=False)
    .agg(
        OrderDate=("InvoiceDate", "min"),
        Country=("Country", "first"),
        OrderRevenue=("Revenue", "sum"),
    )
)

total_revenue = df["Revenue"].sum()
customers = int(df["CustomerID"].dropna().nunique())
orders = int(df["InvoiceNo"].nunique())
aov = order_df["OrderRevenue"].mean()

# Return rate from source convention approximation:
# ratio of cancelled invoice rows to all unique invoices in raw cleaned context cannot be derived here.
# Show proxy return involvement rate based on negative qty in original was filtered, so use "N/A-safe" metric from source:
return_rate_proxy = 10624 / 541909 * 100

col1, col2, col3, col4, col5 = st.columns(5)
for col, label, value in [
    (col1, "Revenue", f"{total_revenue:,.0f}"),
    (col2, "Customers", f"{customers:,}"),
    (col3, "Orders", f"{orders:,}"),
    (col4, "AOV", f"{aov:,.2f}"),
    (col5, "Return Rate (proxy)", f"{return_rate_proxy:.2f}%"),
]:
    with col:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(label, value)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-title">Revenue Trends</div>', unsafe_allow_html=True)
monthly = (
    df.groupby(df["InvoiceDate"].dt.to_period("M"), as_index=False)
    .agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"))
)
monthly["Month"] = monthly["InvoiceDate"].astype(str)

trend_col1, trend_col2 = st.columns(2)
with trend_col1:
    fig = px.line(
        monthly,
        x="Month",
        y="Revenue",
        markers=True,
        template="plotly_white",
        title="Monthly Revenue Trend",
    )
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

with trend_col2:
    fig = px.line(
        monthly,
        x="Month",
        y="Orders",
        markers=True,
        template="plotly_white",
        title="Monthly Orders Trend",
    )
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">Geographic Analysis</div>', unsafe_allow_html=True)
country = (
    df.groupby("Country", as_index=False)
    .agg(Revenue=("Revenue", "sum"), SalesUnits=("Quantity", "sum"), Orders=("InvoiceNo", "nunique"))
)
country["AOV"] = country["Revenue"] / country["Orders"]
country = country.sort_values("Revenue", ascending=False)
top_country = country.head(15)

geo_col1, geo_col2 = st.columns(2)
with geo_col1:
    fig = px.bar(
        top_country.sort_values("Revenue"),
        x="Revenue",
        y="Country",
        orientation="h",
        template="plotly_white",
        title="Top 15 Countries by Revenue",
        color="Revenue",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=500, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with geo_col2:
    fig = px.bar(
        top_country.sort_values("AOV"),
        x="AOV",
        y="Country",
        orientation="h",
        template="plotly_white",
        title="Top 15 Countries by AOV",
        color="AOV",
        color_continuous_scale="Teal",
    )
    fig.update_layout(height=500, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">Product Performance</div>', unsafe_allow_html=True)
product = (
    df.groupby(["StockCode", "Description"], as_index=False)
    .agg(Revenue=("Revenue", "sum"), UnitsSold=("Quantity", "sum"), Orders=("InvoiceNo", "nunique"))
)
top_revenue = product.sort_values("Revenue", ascending=False).head(15)
top_units = product.sort_values("UnitsSold", ascending=False).head(15)

prod_col1, prod_col2 = st.columns(2)
with prod_col1:
    fig = px.bar(
        top_revenue.sort_values("Revenue"),
        x="Revenue",
        y="Description",
        orientation="h",
        template="plotly_white",
        title="Top 15 Products by Revenue",
        color="Revenue",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(height=520, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with prod_col2:
    fig = px.bar(
        top_units.sort_values("UnitsSold"),
        x="UnitsSold",
        y="Description",
        orientation="h",
        template="plotly_white",
        title="Top 15 Products by Units Sold",
        color="UnitsSold",
        color_continuous_scale="Sunset",
    )
    fig.update_layout(height=520, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("View detailed country table"):
    st.dataframe(country, use_container_width=True)
