# 🚗 Insurance Claims AI Assistant (RAG-Based Text-to-SQL)

## Project Overview

An AI-powered Insurance Claims Assistant that allows users to ask **natural language questions** about an insurance claims dataset.

The system uses a **Retrieval-Augmented Generation (RAG)** approach to convert user questions into SQL queries, retrieve data from a SQLite database, and generate clear natural language explanations of the results — all through an interactive Streamlit web interface.

---

## Architecture

```
User Question
      │
      ▼
Prompt Builder
(schema + business rules)
      │
      ▼
LLM (OpenAI GPT-4o-mini)
Generates SQL Query
      │
      ▼
SQL Validation Layer
(Security Check)
      │
      ▼
SQLite Database
(claims.db)
      │
      ▼
Query Result (Pandas DataFrame)
      │
      ▼
LLM Explanation Generator
      │
      ▼
Streamlit UI
(Table + Charts + Explanation)
```

---

## Project Structure

```
insurance_claims_ai/
│
├── app/
│   └── streamlit_app.py          # Streamlit web interface
│
├── rag/
│   ├── rag_pipeline.py           # Core Text-to-SQL pipeline
│   ├── prompt_builder.py         # Prompt engineering
│   └── schema.py                 # Database schema definitions
│
├── security/
│   └── security.py               # SQL validation & injection prevention
│
├── preprocessing/
│   └── Claims_Preprocessing.ipynb  # Data cleaning notebook
│
├── database_setup.py             # Creates claims.db from cleaned data
├── claims.db                     # SQLite database
├── requirements.txt
├── README.md
└── .env                          # API keys (not committed)
```

---

## Getting Started

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Set OpenAI API key

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_api_key_here
```

### Step 3 — Create the database

```bash
python database_setup.py
```

This creates `claims.db` with the `claims` table from the cleaned dataset.

### Step 4 — Run the Streamlit app

```bash
streamlit run app/streamlit_app.py
```

### Step 5 — Open in browser

```
http://localhost:8501
```

---

## Key Components

### 1. Data Preprocessing
Raw claims data is cleaned and transformed using a Jupyter notebook. Key steps include handling missing values, standardizing categorical fields, cleaning hospital and repair cost columns, and preparing structured data for SQL querying.

**Output:** `Cleaned_Processed_Claims_dataset.xlsx`

### 2. RAG Pipeline (`rag_pipeline.py`)

| Step | Description |
|------|-------------|
| Prompt Engineering | Injects database schema and business rules into the LLM prompt |
| SQL Generation | LLM converts natural language to valid SQLite query |
| SQL Validation | Blocks unsafe commands; only SELECT queries are allowed |
| Query Execution | Runs validated SQL on `claims.db`, returns Pandas DataFrame |
| Explanation | LLM converts SQL results into a plain-text human-readable summary |

### 3. Security Layer (`security/security.py`)

Prevents SQL injection and unauthorized database access.

- ✅ Allowed: `SELECT`
- ❌ Blocked: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`

---

## Sample Queries

| # | Query |
|---|-------|
| 1 | Which city/state has the highest loss? Average loss? No. of claims? |
| 2 | How many claims are under investigation? How many are completed? |
| 3 | Which vehicle make and model is most prone to damage? |
| 4 | For the claims received, how many % required hospitalization? |
| 5 | What was the average repair estimated cost? |
| 6 | For a new claim received with side collision damage, what would be the average repair cost? |
| 7 | What is the average cost of physiotherapy required? |
| 8 | For a fractured arm, what is the ballpark number for hospitalization? Max and minimum? |
| 9 | How many claims required hospitalization? How much % of them were severe? |

---

## Visualizations

The app automatically generates charts based on query results:

- **Metric cards** — for single-row aggregate results
- **Pie charts** — for small category distributions (≤10 groups)
- **Bar charts** — for grouped comparisons
- **Scatter plots** — for two numeric columns

Libraries used: Plotly, Pandas, Streamlit

---

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| Empty query | Returns warning message |
| Invalid SQL generation | Handled safely with error message |
| SQL injection attempts | Blocked by security layer |
| Query returning no results | Displays "No results found" |
| Query too long (>300 chars) | Rejected with length validation |
| Ambiguous natural language | LLM attempts best-effort SQL mapping |

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Core language |
| OpenAI API (GPT-4o-mini) | SQL generation & explanation |
| Streamlit | Web interface |
| SQLite + SQLAlchemy | Database storage and querying |
| Pandas | Data manipulation |
| Plotly | Interactive visualizations |
| python-dotenv | Environment variable management |
