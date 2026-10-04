import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="Online Retail EDA Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Online Retail Exploratory Data Analysis Dashboard")
st.markdown(
    "Interactive analysis of the UCI Online Retail dataset."
)


# -----------------------------
# Load and clean data
# -----------------------------
@st.cache_data
def load_data():

    df = pd.read_excel("Online Retail.xlsx")

    # Remove duplicate rows
    df = df.drop_duplicates().copy()

    # Remove invalid transactions
    df = df[
        (df["Quantity"] > 0) &
        (df["UnitPrice"] > 0)
    ].copy()

    # Handle missing descriptions
    df = df.dropna(subset=["Description"]).copy()

    # Convert date
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # Calculate sales
    df["Sales"] = df["Quantity"] * df["UnitPrice"]

    return df


df = load_data()


# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("🔎 Filters")

countries = sorted(df["Country"].unique())

selected_country = st.sidebar.selectbox(
    "Select Country",
    ["All Countries"] + countries
)

if selected_country != "All Countries":
    filtered_df = df[df["Country"] == selected_country].copy()
else:
    filtered_df = df.copy()


# -----------------------------
# Key metrics
# -----------------------------
total_sales = filtered_df["Sales"].sum()
total_transactions = filtered_df["InvoiceNo"].nunique()
total_products = filtered_df["StockCode"].nunique()
total_countries = filtered_df["Country"].nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "💰 Total Sales",
    f"£{total_sales:,.2f}"
)

col2.metric(
    "🧾 Transactions",
    f"{total_transactions:,}"
)

col3.metric(
    "📦 Unique Products",
    f"{total_products:,}"
)

col4.metric(
    "🌍 Countries",
    f"{total_countries:,}"
)


st.divider()


# -----------------------------
# Monthly sales
# -----------------------------
st.subheader("📈 Monthly Sales Trend")

filtered_df["YearMonth"] = (
    filtered_df["InvoiceDate"]
    .dt.to_period("M")
    .astype(str)
)

monthly_sales = (
    filtered_df
    .groupby("YearMonth")["Sales"]
    .sum()
    .reset_index()
)

fig1, ax1 = plt.subplots(figsize=(12, 5))

ax1.plot(
    monthly_sales["YearMonth"],
    monthly_sales["Sales"],
    marker="o"
)

ax1.set_xlabel("Month")
ax1.set_ylabel("Sales")
ax1.set_title("Monthly Sales Trend")

plt.xticks(rotation=45)
plt.tight_layout()

st.pyplot(fig1)


# -----------------------------
# Top 10 products
# -----------------------------
st.subheader("🏆 Top 10 Products by Sales")

top_products = (
    filtered_df
    .groupby("Description")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .sort_values()
)

fig2, ax2 = plt.subplots(figsize=(10, 6))

top_products.plot(
    kind="barh",
    ax=ax2
)

ax2.set_xlabel("Sales")
ax2.set_ylabel("Product")
ax2.set_title("Top 10 Products by Sales")

plt.tight_layout()

st.pyplot(fig2)


# -----------------------------
# Top 10 countries
# -----------------------------
st.subheader("🌍 Top 10 Countries by Sales")

country_sales = (
    filtered_df
    .groupby("Country")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .sort_values()
)

fig3, ax3 = plt.subplots(figsize=(10, 6))

country_sales.plot(
    kind="barh",
    ax=ax3
)

ax3.set_xlabel("Sales")
ax3.set_ylabel("Country")
ax3.set_title("Top 10 Countries by Sales")

plt.tight_layout()

st.pyplot(fig3)


# -----------------------------
# Quantity distribution
# -----------------------------
st.subheader("📊 Quantity Distribution")

fig4, ax4 = plt.subplots(figsize=(10, 5))

sns.histplot(
    filtered_df["Quantity"],
    bins=30,
    ax=ax4
)

ax4.set_xlim(0, 50)
ax4.set_xlabel("Quantity")
ax4.set_ylabel("Frequency")

st.pyplot(fig4)


# -----------------------------
# Correlation heatmap
# -----------------------------
st.subheader("🔥 Correlation Heatmap")

numeric_columns = [
    "Quantity",
    "UnitPrice",
    "Sales"
]

correlation = filtered_df[numeric_columns].corr()

fig5, ax5 = plt.subplots(figsize=(7, 5))

sns.heatmap(
    correlation,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    ax=ax5
)

st.pyplot(fig5)


# -----------------------------
# Data preview
# -----------------------------
st.subheader("📋 Data Preview")

st.dataframe(
    filtered_df.head(100),
    use_container_width=True
)