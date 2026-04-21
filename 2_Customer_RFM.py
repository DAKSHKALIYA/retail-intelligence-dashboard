from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from data_utils import load_clean_transactions, load_rfm_table


st.set_page_config(page_title="Customer RFM", page_icon=":busts_in_silhouette:", layout="wide")

st.markdown(
    """
    <style>
    .main {background: linear-gradient(180deg, #f9f9ff 0%, #ffffff 80%);}
    .segment-badge {
        display:inline-block;
        padding:8px 14px;
        border-radius:999px;
        background:#1f6feb;
        color:white;
        font-weight:700;
        font-size:0.95rem;
    }
    .card {
        background: #ffffff;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 2px 14px rgba(0,0,0,0.05);
        border: 1px solid #eef1f7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Customer RFM Explorer")
st.caption("Page 2: Customer Segmentation, Profile, and Recommendations")

tx = load_clean_transactions()
rfm = load_rfm_table()

tx = tx[tx["CustomerID"].notna()].copy()
tx["CustomerID"] = tx["CustomerID"].astype(int).astype(str)

# Recreate same segment logic so profile can show segment even if not in CSV.
def rfm_segment(row: pd.Series) -> str:
    r, f, m = int(row["R_Score"]), int(row["F_Score"]), int(row["M_Score"])
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 4 and f >= 3 and m >= 3:
        return "Loyal Customers"
    if r == 5 and f <= 2:
        return "New Customers"
    if r >= 4 and m >= 4 and f <= 2:
        return "Big Spenders (New/Occasional)"
    if r <= 2 and f >= 4:
        return "At Risk"
    if r == 1 and f == 1 and m <= 2:
        return "Hibernating"
    if r <= 2 and m >= 4:
        return "Cannot Lose Them"
    if r >= 3 and f <= 2 and m <= 2:
        return "Promising"
    return "Needs Attention"


rfm["Segment"] = rfm.apply(rfm_segment, axis=1)
segment_actions = {
    "Champions": "Reward loyalty with VIP perks, exclusive drops, and referral offers.",
    "Loyal Customers": "Upsell with bundles and maintain engagement via personalized campaigns.",
    "New Customers": "Nurture second purchase through onboarding flow and timed incentives.",
    "Big Spenders (New/Occasional)": "Provide concierge-style follow-up and premium cross-sell suggestions.",
    "At Risk": "Launch urgent win-back campaign with stronger but targeted offers.",
    "Cannot Lose Them": "Use high-touch reactivation strategy and account-level outreach.",
    "Promising": "Encourage repeat purchases with low-friction recommendations and reminders.",
    "Hibernating": "Use low-cost periodic reactivation and suppress expensive ad spend.",
    "Needs Attention": "Deploy lifecycle nudges to move customer into loyal/champion tiers.",
}

customer_ids = sorted(rfm["CustomerID"].astype(str).unique())
left, right = st.columns([2, 1])
with left:
    search_text = st.text_input("Search customer ID", placeholder="Type customer ID...")
with right:
    selected = st.selectbox(
        "Or select customer",
        options=customer_ids,
        index=0,
    )

if search_text:
    matches = [cid for cid in customer_ids if search_text.strip() in cid]
    if matches:
        selected = matches[0]
    else:
        st.warning("No matching customer ID found. Showing selected dropdown customer.")

cust_tx = tx[tx["CustomerID"] == selected].copy()
cust_rfm = rfm[rfm["CustomerID"] == selected].iloc[0]
segment = cust_rfm["Segment"]

st.markdown(f'<span class="segment-badge">{segment}</span>', unsafe_allow_html=True)
st.info(segment_actions.get(segment, "Maintain targeted lifecycle communication."))

country_mode = cust_tx["Country"].mode().iloc[0] if not cust_tx.empty else "Unknown"
first_purchase = cust_tx["InvoiceDate"].min()
last_purchase = cust_tx["InvoiceDate"].max()
tx_count = int(cust_tx["InvoiceNo"].nunique())
total_revenue = float(cust_tx["Revenue"].sum())
aov = total_revenue / tx_count if tx_count else 0.0

metric_cols = st.columns(5)
metric_cols[0].metric("Customer ID", selected)
metric_cols[1].metric("Country", country_mode)
metric_cols[2].metric("Transactions", f"{tx_count:,}")
metric_cols[3].metric("Total Revenue", f"{total_revenue:,.2f}")
metric_cols[4].metric("AOV", f"{aov:,.2f}")

date_cols = st.columns(2)
date_cols[0].markdown(f"**First purchase:** {first_purchase:%Y-%m-%d}")
date_cols[1].markdown(f"**Last purchase:** {last_purchase:%Y-%m-%d}")

top_products = (
    cust_tx.groupby("Description", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"))
    .sort_values("Revenue", ascending=False)
    .head(10)
)

top_categories = (
    cust_tx.groupby("Category", as_index=False)
    .agg(Revenue=("Revenue", "sum"))
    .sort_values("Revenue", ascending=False)
)

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.markdown("### Top Products Purchased")
    fig = px.bar(
        top_products.sort_values("Revenue"),
        x="Revenue",
        y="Description",
        orientation="h",
        template="plotly_white",
        color="Revenue",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=430, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.markdown("### Product Category Mix")
    fig = px.pie(
        top_categories,
        values="Revenue",
        names="Category",
        template="plotly_white",
        hole=0.45,
        color_discrete_sequence=px.colors.sequential.Tealgrn,
    )
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Customer transaction history"):
    tx_view = cust_tx.sort_values("InvoiceDate", ascending=False)[
        ["InvoiceDate", "InvoiceNo", "Description", "Quantity", "UnitPrice", "Revenue", "Country"]
    ]
    st.dataframe(tx_view, use_container_width=True)
