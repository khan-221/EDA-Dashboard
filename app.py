import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Online Retail EDA Dashboard",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Online Retail EDA Dashboard")
st.write(
    "Explore retail sales, product performance, country trends, "
    "missing values, and potential outliers."
)

# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------
@st.cache_data
def load_data(file_path="Online Retail.xlsx"):
    data = pd.read_excel(file_path, engine="openpyxl")

    # Normalize column names only by stripping accidental spaces.
    data.columns = data.columns.astype(str).str.strip()

    required_columns = [
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country"
    ]
    missing_columns = [c for c in required_columns if c not in data.columns]
    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: "
            + ", ".join(missing_columns)
        )

    # Preserve raw data for missing-value reporting.
    raw_data = data.copy()

    # Remove exact duplicate rows.
    deduplicated_data = data.drop_duplicates().copy()

    # Convert fields to useful types.
    deduplicated_data["InvoiceNo"] = (
        deduplicated_data["InvoiceNo"].astype("string").str.strip()
    )
    deduplicated_data["StockCode"] = (
        deduplicated_data["StockCode"].astype("string").str.strip()
    )
    deduplicated_data["InvoiceDate"] = pd.to_datetime(
        deduplicated_data["InvoiceDate"], errors="coerce"
    )
    deduplicated_data["Quantity"] = pd.to_numeric(
        deduplicated_data["Quantity"], errors="coerce"
    )
    deduplicated_data["UnitPrice"] = pd.to_numeric(
        deduplicated_data["UnitPrice"], errors="coerce"
    )
    deduplicated_data["Sales"] = (
        deduplicated_data["Quantity"] * deduplicated_data["UnitPrice"]
    )

    return raw_data, deduplicated_data


try:
    raw_df, df = load_data()
except FileNotFoundError:
    st.error(
        "Dataset not found. Put `Online Retail.xlsx` in the same folder "
        "as `app.py`, then restart the app."
    )
    st.stop()
except Exception as error:
    st.error(f"Could not load the dataset: {error}")
    st.stop()

# ---------------------------------------------------------
# DATA QUALITY: MISSING VALUES (BEFORE ROW FILTERING)
# ---------------------------------------------------------
st.header("1. Missing Values Analysis")

st.caption(
    "Counts below are calculated after exact-duplicate removal but before "
    "filtering invalid transactions or missing descriptions."
)

missing_decisions = {
    "InvoiceNo": (
        "Investigate; exclude from invoice-level analysis if it cannot be recovered."
    ),
    "StockCode": (
        "Keep for overall totals where possible; exclude from product-level analysis if missing."
    ),
    "Description": (
        "Keep for overall transaction totals when possible; exclude from product-name rankings if missing."
    ),
    "Quantity": (
        "Required for quantity and sales calculations; exclude affected rows if missing or invalid."
    ),
    "InvoiceDate": (
        "Do not invent dates; exclude rows with invalid dates from time-based analysis."
    ),
    "UnitPrice": (
        "Required for revenue calculations; exclude affected rows if missing or invalid."
    ),
    "CustomerID": (
        "Keep missing as Unknown for overall sales; do not invent IDs. Exclude from customer-specific analysis."
    ),
    "Country": (
        "Do not guess the country; report as Unknown or exclude from country comparisons."
    ),
}

missing_report = pd.DataFrame({
    "Column": df.columns,
    "Missing Count": df.isna().sum().values,
    "Missing Percentage (%)": (df.isna().mean() * 100).round(2).values,
    "Non-Missing Count": df.notna().sum().values,
    "Handling Decision": [
        missing_decisions.get(
            col,
            "Review according to the column's purpose; do not invent values."
        )
        for col in df.columns
    ]
}).sort_values("Missing Count", ascending=False).reset_index(drop=True)

st.dataframe(missing_report, use_container_width=True, hide_index=True)

if "CustomerID" in df.columns:
    missing_customer_count = int(df["CustomerID"].isna().sum())
    missing_customer_pct = (
        df["CustomerID"].isna().mean() * 100 if len(df) else 0
    )
    k1, k2, k3 = st.columns(3)
    k1.metric("Rows before transaction filtering", f"{len(df):,}")
    k2.metric("Missing CustomerID", f"{missing_customer_count:,}")
    k3.metric("CustomerID missing (%)", f"{missing_customer_pct:.2f}%")

st.info(
    "CustomerID decision: missing IDs are not filled with made-up values. "
    "Those transactions can still contribute to overall sales if quantity "
    "and unit price are valid, but they are excluded from customer-specific "
    "analysis."
)

# ---------------------------------------------------------
# DUPLICATES AND CANCELLATIONS
# ---------------------------------------------------------
st.header("2. Data Cleaning and Cancellation Handling")

st.write(f"Rows in source file: **{len(raw_df):,}**")
st.write(f"Rows after removing exact duplicates: **{len(df):,}**")

# Identify cancellation invoices (invoice number begins with C).
invoice_text = df["InvoiceNo"].fillna("").astype(str).str.strip()
is_cancellation = invoice_text.str.upper().str.startswith("C")
cancellation_rows = df[is_cancellation].copy()
normal_rows = df[~is_cancellation].copy()

# Match cancellation lines to original positive lines by key fields.
# A match requires the same StockCode, normalized Description,
# absolute Quantity, UnitPrice, and CustomerID, with original date <=
# cancellation date. This is a conservative line-level matching approach.
def normalize_text(series):
    return (
        series.fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )

def cancellation_adjustment(data):
    work = data.copy().reset_index(drop=True)

    inv = work["InvoiceNo"].fillna("").astype(str).str.strip()
    cancel_mask = inv.str.upper().str.startswith("C")
    cancel_positions = list(work.index[cancel_mask])
    original_positions = list(work.index[~cancel_mask])

    work["_desc_key"] = normalize_text(work["Description"])
    work["_stock_key"] = normalize_text(work["StockCode"])
    work["_customer_key"] = work["CustomerID"].astype("string").fillna("UNKNOWN")
    work["_price_key"] = pd.to_numeric(work["UnitPrice"], errors="coerce").round(4)
    work["_qty"] = pd.to_numeric(work["Quantity"], errors="coerce")
    work["_date"] = pd.to_datetime(work["InvoiceDate"], errors="coerce")

    # Build candidate lists for original positive lines.
    candidates = defaultdict(list)
    for pos in original_positions:
        row = work.loc[pos]
        if pd.isna(row["_qty"]) or row["_qty"] <= 0:
            continue
        key = (
            row["_stock_key"], row["_desc_key"],
            round(float(row["_qty"]), 4),
            row["_price_key"], str(row["_customer_key"])
        )
        candidates[key].append(pos)

    # Sort each candidate list by date, then index.
    for key in candidates:
        candidates[key].sort(
            key=lambda p: (
                work.loc[p, "_date"] if pd.notna(work.loc[p, "_date"])
                else pd.Timestamp.min,
                p
            )
        )

    removed_original_positions = set()
    matched_cancel_count = 0
    unmatched_cancel_count = 0

    # Process cancellation lines in date order.
    cancel_positions.sort(
        key=lambda p: (
            work.loc[p, "_date"] if pd.notna(work.loc[p, "_date"])
            else pd.Timestamp.max,
            p
        )
    )

    for cpos in cancel_positions:
        row = work.loc[cpos]
        if pd.isna(row["_qty"]) or row["_qty"] >= 0:
            unmatched_cancel_count += 1
            continue

        key = (
            row["_stock_key"], row["_desc_key"],
            round(abs(float(row["_qty"])), 4),
            row["_price_key"], str(row["_customer_key"])
        )
        possible = candidates.get(key, [])

        # Prefer the most recent still-available original line on/before cancellation date.
        match_pos = None
        for opos in reversed(possible):
            if opos in removed_original_positions:
                continue
            original_date = work.loc[opos, "_date"]
            cancel_date = row["_date"]
            if pd.isna(cancel_date) or pd.isna(original_date) or original_date <= cancel_date:
                match_pos = opos
                break

        if match_pos is not None:
            removed_original_positions.add(match_pos)
            matched_cancel_count += 1
        else:
            unmatched_cancel_count += 1

    # Exclude all cancellation invoice lines, and matched original lines.
    keep_mask = ~cancel_mask & ~work.index.isin(removed_original_positions)
    cleaned = work.loc[keep_mask].copy()

    helper_cols = [
        "_desc_key", "_stock_key", "_customer_key",
        "_price_key", "_qty", "_date"
    ]
    cleaned.drop(columns=[c for c in helper_cols if c in cleaned.columns],
                 inplace=True, errors="ignore")

    return cleaned, len(cancel_positions), matched_cancel_count, unmatched_cancel_count, len(removed_original_positions)


df_cancel_adjusted, cancellation_invoice_rows, matched_cancellations, unmatched_cancellations, matched_originals_removed = cancellation_adjustment(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cancellation invoice rows", f"{cancellation_invoice_rows:,}")
c2.metric("Matched cancellation lines", f"{matched_cancellations:,}")
c3.metric("Original lines removed", f"{matched_originals_removed:,}")
c4.metric("Unmatched cancellation lines", f"{unmatched_cancellations:,}")

st.caption(
    "Cancellation handling: cancellation invoice rows (InvoiceNo beginning with C) "
    "are excluded. Where a cancellation line matches an earlier positive line by "
    "stock code, description, quantity, unit price, and customer, the original line "
    "is also excluded. Unmatched cancellation lines are counted above; matching is "
    "conservative and may not resolve every complex/partial cancellation."
)

# Keep valid positive transactions for the sales dashboard.
df_clean = df_cancel_adjusted.copy()
df_clean = df_clean[
    df_clean["Quantity"].notna()
    & df_clean["UnitPrice"].notna()
    & df_clean["InvoiceDate"].notna()
    & (df_clean["Quantity"] > 0)
    & (df_clean["UnitPrice"] > 0)
].copy()

df_clean["Sales"] = df_clean["Quantity"] * df_clean["UnitPrice"]

# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------
st.sidebar.header("Dashboard Filters")

if df_clean.empty:
    st.warning("No valid positive transactions remain after cleaning.")
    st.stop()

countries = sorted(df_clean["Country"].dropna().astype(str).unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Select country/countries",
    options=countries,
    default=countries
)

filtered_df = df_clean[
    df_clean["Country"].astype(str).isin(selected_countries)
].copy()

if filtered_df.empty:
    st.warning("No rows match the selected country filter.")
    st.stop()

# ---------------------------------------------------------
# KEY METRICS
# ---------------------------------------------------------
st.header("3. Key Metrics")

total_sales = filtered_df["Sales"].sum()
unique_invoices = filtered_df["InvoiceNo"].nunique()
unique_products = filtered_df["StockCode"].nunique()
unique_countries = filtered_df["Country"].nunique()
known_customers = filtered_df["CustomerID"].nunique()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Sales", f"{total_sales:,.2f}")
m2.metric("Unique Invoices", f"{unique_invoices:,}")
m3.metric("Unique Stock Codes", f"{unique_products:,}")
m4.metric("Countries", f"{unique_countries:,}")

st.caption(
    f"Known unique customers in selected data: {known_customers:,}. "
    "Rows with missing CustomerID are not counted as known customers."
)

# ---------------------------------------------------------
# MONTHLY SALES
# ---------------------------------------------------------
st.header("4. Monthly Sales Trend")

monthly_df = filtered_df.copy()
monthly_df["Month"] = monthly_df["InvoiceDate"].dt.to_period("M").astype(str)
monthly_sales = monthly_df.groupby("Month", as_index=False)["Sales"].sum()

fig, ax = plt.subplots(figsize=(12, 5))
sns.lineplot(data=monthly_sales, x="Month", y="Sales", marker="o", ax=ax)
ax.set_title("Monthly Sales")
ax.set_xlabel("Month")
ax.set_ylabel("Sales")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.caption(
    "The dataset ends during December 2011, so December represents a partial "
    "month and should not automatically be interpreted as a full-month decline."
)

# ---------------------------------------------------------
# NON-PRODUCT FILTERING
# ---------------------------------------------------------
st.header("5. Top 10 Products by Sales")

non_product_codes = {
    "POST", "DOT", "M", "BANK CHARGES", "AMAZONFEE",
    "CRUK", "D", "S", "C2", "PADS", "DCGS", "ADJUST", "ADJUST2"
}

product_df = filtered_df.copy()
product_df["_stock_normalized"] = (
    product_df["StockCode"].astype("string").str.strip().str.upper()
)
product_df = product_df[
    (~product_df["_stock_normalized"].isin(non_product_codes))
    & product_df["Description"].notna()
].copy()

# Also exclude descriptions that clearly identify common non-product entries.
non_product_description_pattern = (
    r"postage|bank charge|amazon fee|manual adjustment|"
    r"discount|carriage|insurance"
)
product_df = product_df[
    ~product_df["Description"].astype(str).str.contains(
        non_product_description_pattern, case=False, na=False, regex=True
    )
].copy()

top_products = (
    product_df.groupby("Description", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)

if top_products.empty:
    st.info("No product rows are available for the current filter.")
else:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=top_products, x="Sales", y="Description", ax=ax)
    ax.set_title("Top 10 Products by Sales (non-product entries excluded)")
    ax.set_xlabel("Total Sales")
    ax.set_ylabel("Product")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

st.caption(
    "Known postage, fee, discount, and adjustment stock codes/descriptions are "
    "excluded from this product ranking only. The broader sales dataset is retained."
)

# ---------------------------------------------------------
# COUNTRY SALES
# ---------------------------------------------------------
st.header("6. Sales by Country")

# With one selected country, the chart still shows that country's sales.
country_sales = (
    filtered_df.groupby("Country", as_index=False)["Sales"]
    .sum()
    .sort_values("Sales", ascending=False)
    .head(10)
)

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=country_sales, x="Sales", y="Country", ax=ax)
ax.set_title("Top Countries by Sales (selected countries)")
ax.set_xlabel("Total Sales")
ax.set_ylabel("Country")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ---------------------------------------------------------
# OUTLIER ANALYSIS
# ---------------------------------------------------------
st.header("7. Outlier Analysis")

st.write(
    "Potential outliers are identified with the IQR method. They are not "
    "automatically deleted because large quantities or sales may represent "
    "legitimate bulk orders."
)

outlier_columns = ["Quantity", "UnitPrice", "Sales"]
outlier_results = []

for col in outlier_columns:
    series = filtered_df[col].dropna()
    if series.empty:
        continue

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)

    outlier_results.append({
        "Column": col,
        "Q1": round(float(q1), 2),
        "Q3": round(float(q3), 2),
        "IQR": round(float(iqr), 2),
        "Lower Bound": round(float(lower), 2),
        "Upper Bound": round(float(upper), 2),
        "Outlier Count": int(mask.sum()),
        "Outlier Percentage (%)": round(float(mask.mean() * 100), 2)
    })

if outlier_results:
    st.dataframe(
        pd.DataFrame(outlier_results),
        use_container_width=True,
        hide_index=True
    )

box_cols = st.columns(3)
for col, container in zip(outlier_columns, box_cols):
    with container:
        fig, ax = plt.subplots(figsize=(4, 4))
        sns.boxplot(y=filtered_df[col].dropna(), ax=ax)
        ax.set_title(f"{col} Boxplot")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

st.subheader("Quantity Distribution (1 to 50)")
quantity_view = filtered_df[
    filtered_df["Quantity"].between(1, 50)
]
fig, ax = plt.subplots(figsize=(10, 4))
sns.histplot(data=quantity_view, x="Quantity", bins=30, ax=ax)
ax.set_title("Quantity Distribution — Restricted View")
ax.set_xlabel("Quantity")
ax.set_ylabel("Frequency")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.caption(
    "The restricted histogram is for visualization only. It does not remove "
    "these or other rows from the cleaned dataset."
)

# ---------------------------------------------------------
# CORRELATION
# ---------------------------------------------------------
st.header("8. Correlation Heatmap")

correlation_columns = ["Quantity", "UnitPrice", "Sales"]
correlation_data = filtered_df[correlation_columns].corr(numeric_only=True)

fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(
    correlation_data,
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    ax=ax
)
ax.set_title("Correlation Between Numeric Variables")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ---------------------------------------------------------
# STATISTICAL AND CATEGORICAL ANALYSIS
# ---------------------------------------------------------
st.header("9. Statistical Summary")

st.dataframe(
    filtered_df[["Quantity", "UnitPrice", "Sales"]].describe().round(2),
    use_container_width=True
)

st.header("10. Country Frequency Analysis")
country_counts = (
    filtered_df["Country"].value_counts(dropna=False)
    .rename_axis("Country")
    .reset_index(name="Transaction Rows")
)
st.dataframe(country_counts, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# CUSTOMER-LEVEL ANALYSIS
# ---------------------------------------------------------
st.header("11. Customer Analysis")

known_customer_df = filtered_df[filtered_df["CustomerID"].notna()].copy()
missing_customer_rows = int(filtered_df["CustomerID"].isna().sum())

st.write(
    f"Rows with missing CustomerID in the selected data: "
    f"**{missing_customer_rows:,}**. These are retained for overall sales "
    "metrics but are not included in the customer ranking below."
)

if not known_customer_df.empty:
    top_customers = (
        known_customer_df.groupby("CustomerID", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(10)
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=top_customers,
        x="Sales",
        y=top_customers["CustomerID"].astype(str),
        ax=ax
    )
    ax.set_title("Top 10 Known Customers by Sales")
    ax.set_xlabel("Total Sales")
    ax.set_ylabel("CustomerID")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("No known CustomerID values are available for customer analysis.")

# ---------------------------------------------------------
# DATA PREVIEW
# ---------------------------------------------------------
st.header("12. Cleaned Data Preview")
st.dataframe(
    filtered_df.head(100),
    use_container_width=True,
    hide_index=True
)

st.success("Dashboard loaded successfully.")
