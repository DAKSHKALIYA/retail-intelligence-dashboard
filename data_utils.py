from __future__ import annotations

from pathlib import Path
import re

import pandas as pd
import streamlit as st


DATA_FILE = Path("Online Retail.xlsx")
RFM_FILE = Path("rfm_customer_table.csv")


def _category_from_description(description: str) -> str:
    d = (description or "").upper()
    if any(k in d for k in ["CHRISTMAS", "XMAS", "NOEL"]):
        return "Seasonal"
    if any(k in d for k in ["BAG", "TOTE", "SHOPPER"]):
        return "Bags"
    if any(k in d for k in ["LIGHT", "LAMP", "LANTERN", "CANDLE", "HOLDER"]):
        return "Home Decor & Lighting"
    if any(k in d for k in ["MUG", "BOWL", "PLATE", "TEA", "CUP", "JAR"]):
        return "Kitchen & Dining"
    if any(k in d for k in ["CARD", "WRAP", "RIBBON", "PAPER", "STICKER"]):
        return "Stationery & Gift Wrap"
    if any(k in d for k in ["TOY", "DOLL", "CHILD", "BABY", "RABBIT"]):
        return "Kids & Toys"
    if any(k in d for k in ["POSTAGE", "MANUAL", "BANK CHARGES"]):
        return "Services & Adjustments"
    if any(k in d for k in ["CAKE", "PARTY", "BUNTING"]):
        return "Party & Celebrations"
    return "Other"


@st.cache_data(show_spinner=False)
def load_clean_transactions() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError("Online Retail.xlsx not found in workspace root.")

    df = pd.read_excel(DATA_FILE).copy()
    df = df.drop_duplicates()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df = df.dropna(subset=["InvoiceDate", "InvoiceNo", "Description", "Country", "Quantity", "UnitPrice"])

    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["Description"] = df["Description"].astype(str).str.strip()
    df["Country"] = df["Country"].astype(str).str.strip()

    # Keep CustomerID optional for overview; handle in page-specific logic.
    if "CustomerID" in df.columns:
        df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")

    df["IsCancelled"] = df["InvoiceNo"].str.startswith("C")
    df["IsReturn"] = df["Quantity"] < 0

    # Build clean sales frame for business overview and RFM profile.
    clean = df[(~df["IsCancelled"]) & (~df["IsReturn"]) & (df["Quantity"] > 0) & (df["UnitPrice"] > 0)].copy()
    clean["Revenue"] = clean["Quantity"] * clean["UnitPrice"]
    clean["Category"] = clean["Description"].apply(_category_from_description)
    return clean


@st.cache_data(show_spinner=False)
def load_rfm_table() -> pd.DataFrame:
    if not RFM_FILE.exists():
        raise FileNotFoundError("rfm_customer_table.csv not found. Run RFM analysis first.")
    rfm = pd.read_csv(RFM_FILE)
    rfm["CustomerID"] = rfm["CustomerID"].astype(str)
    return rfm

