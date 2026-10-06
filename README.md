# Online Retail Exploratory Data Analysis (EDA) Dashboard

An interactive data analysis project built using Python, Pandas, Matplotlib, Seaborn, and Streamlit. This project explores an online retail transaction dataset to understand sales performance, product trends, country-wise revenue, data quality, and customer information.

**Live Dashboard:** https://eda-dashboard-aoqcran5crsdwuz7n69dsn.streamlit.app/

**GitHub Repository:** https://github.com/khan-221/EDA-Dashboard

---

## Table of Contents

* [Project Overview](#project-overview)
* [Objectives](#objectives)
* [Dataset](#dataset)
* [Technologies Used](#technologies-used)
* [Project Structure](#project-structure)
* [Installation and Setup](#installation-and-setup)
* [Run the Dashboard](#run-the-dashboard)
* [Data Cleaning](#data-cleaning)
* [Missing Value Analysis](#missing-value-analysis)
* [Outlier Analysis](#outlier-analysis)
* [Non-Product Transaction Filtering](#non-product-transaction-filtering)
* [Exploratory Data Analysis](#exploratory-data-analysis)
* [Dashboard Features](#dashboard-features)
* [Key Insights](#key-insights)
* [Limitations](#limitations)
* [Future Improvements](#future-improvements)
* [Author](#author)

---

## Project Overview

The Online Retail EDA Dashboard is an interactive data analytics project designed to explore retail transactions and identify useful business patterns.

The project uses Python for data cleaning and analysis and Streamlit to provide an interactive dashboard. Users can explore sales performance, examine product and country trends, and review the dataset through charts, metrics, and tables.

A separate Jupyter Notebook documents the exploratory data analysis process, including data overview, missing values, duplicates, outliers, cleaning decisions, group-by analysis, visualizations, and conclusions.

## Objectives

The main objectives of this project are:

* Understand the structure and quality of the retail dataset.
* Clean transaction data before performing analysis.
* Examine missing values and duplicate records.
* Identify potential outliers in quantity, unit price, and sales.
* Analyze total sales and invoice activity.
* Identify top-selling products and high-revenue countries.
* Build an interactive dashboard for exploring the data.
* Present findings through clear charts and statistical summaries.

## Dataset

**Dataset:** Online Retail

**Source:** UCI Machine Learning Repository

**Dataset link:** https://archive.ics.uci.edu/dataset/352/online+retail

The dataset contains transaction records for a UK-based online retailer.

Important columns include:

| Column        | Description                                  |
| ------------- | -------------------------------------------- |
| `InvoiceNo`   | Invoice number associated with a transaction |
| `StockCode`   | Product or stock identifier                  |
| `Description` | Product description                          |
| `Quantity`    | Quantity purchased in a transaction          |
| `InvoiceDate` | Date and time of the transaction             |
| `UnitPrice`   | Unit price of the item                       |
| `CustomerID`  | Customer identifier                          |
| `Country`     | Customer's country                           |

The dataset includes product transactions, customer information, invoice dates, and country-level details. It can be used to investigate sales patterns, product performance, and data-quality issues.

## Technologies Used

* **Python** — core programming language
* **Pandas** — data manipulation and analysis
* **NumPy** — numerical operations where required
* **Matplotlib** — charts and visualizations
* **Seaborn** — statistical plots and boxplots
* **Streamlit** — interactive web dashboard
* **Jupyter Notebook** — exploratory analysis and documentation
* **OpenPyXL** — reading Excel files with Pandas
* **Git and GitHub** — version control and source code hosting
* **Streamlit Community Cloud** — dashboard deployment

## Project Structure

```text
EDA-Dashboard/
│
├── app.py
├── Online Retail.xlsx
├── requirements.txt
├── README.md
│
└── notebooks/
    └── eda.ipynb
```

* `app.py` — Streamlit dashboard application
* `Online Retail.xlsx` — retail transaction dataset
* `requirements.txt` — Python dependencies
* `README.md` — project documentation
* `notebooks/eda.ipynb` — Jupyter Notebook containing exploratory data analysis

Ensure the notebook is uploaded to the `notebooks/` folder in the GitHub repository.

## Installation and Setup

### Prerequisites

Install the following before running the project:

* Python 3.10 or a compatible version supported by the project dependencies
* Git
* A code editor or terminal
* A web browser

### 1. Clone the repository

```bash
git clone https://github.com/khan-221/EDA-Dashboard.git
cd EDA-Dashboard
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS or Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the Dashboard

Start the Streamlit application with:

```bash
streamlit run app.py
```

Streamlit will display a local URL in the terminal, usually:

```text
http://localhost:8501
```

Open the URL in your browser to use the dashboard.

### Live Demo

The deployed dashboard is available here:

https://eda-dashboard-aoqcran5crsdwuz7n69dsn.streamlit.app/

## Data Cleaning

Data cleaning is performed before the main sales analysis.

The current cleaning workflow includes:

1. Loading the Excel dataset into a Pandas DataFrame.
2. Removing duplicate records.
3. Excluding transactions with non-positive quantities.
4. Excluding transactions with non-positive unit prices.
5. Removing rows with missing product descriptions where required by the cleaning workflow.
6. Converting `InvoiceDate` to a datetime format.
7. Creating a `Sales` column using:

   `Sales = Quantity × UnitPrice`

The cleaned dataset is then used for the relevant metrics, aggregations, and visualizations.

**Cancellation limitation:** Negative-quantity transactions and invoices prefixed with `C` may represent cancellations. Simply removing negative quantities does not necessarily remove the original sale associated with a cancellation. Cancellation matching should be evaluated and documented separately.

## Missing Value Analysis

Missing values are examined by calculating the missing count and missing percentage for each column. Both the original data and cleaned data should be reviewed to understand how cleaning changes the results.

### CustomerID

Some transactions have no `CustomerID`. These records are not assigned fabricated customer identifiers.

The handling approach is:

* Retain transactions with missing `CustomerID` for overall sales analysis when the required transaction fields are valid.
* Exclude missing IDs from customer-specific analysis, such as ranking identifiable customers.
* Report the number and percentage of missing IDs.
* Do not assume that missing customer IDs belong to the same customer.

### Other Columns

* **Description:** Exclude from product-name analysis when a product description is required.
* **InvoiceDate:** Exclude missing or invalid dates from time-based analysis.
* **Quantity and UnitPrice:** Investigate missing or invalid values before using them in quantity and revenue calculations.
* **StockCode:** Exclude missing codes from analyses requiring product identification.
* **Country:** If missing, use an `Unknown` category for reporting or exclude those rows from country comparisons.

Handling decisions should be based on the actual missing values and the needs of each analysis. Values should not be filled with unsupported guesses.

## Outlier Analysis

Potential outliers are examined in the following numerical columns:

* `Quantity`
* `UnitPrice`
* `Sales`

The Interquartile Range (IQR) method identifies potential outliers using:

* `IQR = Q3 − Q1`
* Lower bound: `Q1 − 1.5 × IQR`
* Upper bound: `Q3 + 1.5 × IQR`

Boxplots help visualize the distribution and extreme values.

Outliers are not automatically deleted. Large quantities or high sales values may represent legitimate bulk purchases. A restricted-range chart can be used to display the main distribution without modifying the underlying dataset.

## Non-Product Transaction Filtering

Some stock codes and descriptions may represent postage, fees, discounts, manual adjustments, or other non-product entries rather than ordinary retail products.

For product-level rankings, known non-product codes are reviewed and excluded where appropriate. The product analysis also uses valid positive quantities, positive unit prices, and available descriptions.

This filtering is applied to a separate product-analysis DataFrame so that the broader cleaned transaction dataset remains available for overall sales analysis.

Because some special stock codes can have ambiguous meanings, exclusions should be checked against the dataset before being finalized.

## Exploratory Data Analysis

The project explores the following areas:

### 1. Overall Sales Performance

Calculate total sales revenue from the transaction-level `Sales` values.

### 2. Invoice Activity

Count unique invoices to understand transaction activity.

### 3. Product Analysis

Group sales by product description and identify the top 10 products by total sales, excluding reviewed non-product entries.

### 4. Country-Wise Sales

Aggregate sales by country to identify markets contributing the most revenue.

### 5. Monthly Sales Trends

Convert invoice dates to datetime values and group sales by month to explore changes over time.

### 6. Quantity Distribution

Use histograms to examine transaction quantities and understand the distribution of purchased quantities.

### 7. Correlation Analysis

Use a correlation heatmap to examine relationships between numerical fields such as quantity, unit price, and sales.

### 8. Statistical Summaries

Use descriptive statistics to review numeric columns, including count, mean, standard deviation, quartiles, and maximum values.

### 9. Categorical Analysis

Examine country frequencies and other relevant categorical variables.

## Dashboard Features

The Streamlit dashboard includes:

* Interactive country filtering
* Total sales KPI
* Unique invoice count
* Unique product-code count
* Country count
* Monthly sales trend visualization
* Top 10 products by sales
* Country-wise sales chart
* Quantity distribution histogram
* Correlation heatmap
* Transaction data preview
* Missing-value analysis, when enabled in the dashboard

The dashboard is designed to make the analysis easier to explore without requiring users to run every notebook cell manually.

## Key Insights

The analysis is intended to help identify:

* The products contributing the most sales revenue.
* The countries generating the highest sales.
* Changes in sales across months.
* The distribution of purchased quantities.
* Missing customer identifiers and other data-quality issues.
* Potential outliers that may represent bulk purchases or unusual transactions.
* The impact of data cleaning and non-product filtering on product rankings.

**Note:** Exact numerical findings should be added after running the notebook on the final cleaned dataset. Avoid reporting estimated sales, customer counts, or rankings without checking the actual results.

## Limitations

* Missing `CustomerID` values limit customer-specific analysis.
* Cancellation records require careful matching to corresponding original transactions.
* Extreme values can influence sales summaries and charts.
* Special stock codes may represent non-product transactions and require review.
* The dataset ends during December 2011, so the final month's sales may represent a partial month rather than a genuine decline.
* Results depend on the cleaning rules and the records retained for each analysis.

## Future Improvements

Potential improvements include:

* Add a complete cancellation-matching workflow.
* Add sales by weekday and hour.
* Add average order value (AOV).
* Add customer-level analysis for records with valid customer IDs.
* Add sales and customer counts by country.
* Add better visual controls for outliers.
* Improve performance by using a more efficient data format if appropriate.
* Pin dependency versions for more reproducible deployments.
* Add dashboard screenshots to the README.

## Author

**Ali Hassan**

Online Retail Exploratory Data Analysis Dashboard

GitHub: https://github.com/khan-221/EDA-Dashboard

Live Dashboard: https://eda-dashboard-aoqcran5crsdwuz7n69dsn.streamlit.app/

---

## Acknowledgements

Thanks to the UCI Machine Learning Repository for providing the Online Retail dataset used in this project.
