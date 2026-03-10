# Claims Data Preprocessing — Approach & Decision Log

## Overview

This document explains the reasoning behind every preprocessing decision made in `Claims_Preprocessing_final.ipynb`. It covers what problems were found in the raw data, what approaches were explored, why certain methods were rejected, and what the final solution was.

---

## 1. City & State Extraction from `Loss Location`

### The Problem

The `Loss Location` field contained multi-line free-text addresses in the following format:

```
123 Main Street
Springfield, IL 62701
```

There were no dedicated `City` or `State` columns in the raw dataset. To enable geographic grouping and querying, structured `City` and `State` columns had to be derived from this field.

### What Was Tried First

The initial approach attempted to extract City and State by looking for a comma-separated pattern anywhere in the string:

```python
# First attempt — discarded
df["City"] = df["Loss Location"].str.extract(r"\n(.*),")
df["State"] = df["Loss Location"].str.extract(r",\s([A-Z]{2})")
```

**Why it was rejected:** This regex matched inconsistently across multi-line addresses. Street lines sometimes contained commas (e.g., `Apt 3, Suite B`), which caused false matches and extracted the wrong line as City.

### Final Approach

```python
last_line = df["Loss Location"].str.split("\n").str[-1]

df["City"] = last_line.str.extract(r"^(.+?)(?=,|\s[A-Z]{2})")
df["State"] = last_line.str.extract(r"\b([A-Z]{2})\b")

df.loc[last_line.str.contains("DPO|APO|FPO"), "City"] = "Military Post Office"
```

**Why this works:**

- Always taking the **last line** of the address avoids ambiguity from street lines that contain commas or city-like text.
- The City regex `^(.+?)(?=,|\s[A-Z]{2})` lazily captures everything before either a comma or a two-letter state abbreviation — the two standard US address delimiters.
- The State regex `\b([A-Z]{2})\b` targets the exact two-letter uppercase state code with word boundaries to avoid partial matches.

**Special case — Military Addresses:**
Records with `APO`, `DPO`, or `FPO` designators are military postal codes that don't follow standard US city/state formatting. These were standardised to `"Military Post Office"` as a named city category rather than being left as nulls or miscategorised.

**QC Checks Performed:**
After extraction, both columns were checked for nulls:

```python
df[df["City"].isna()]["Loss Location"]   # verified no unexpected nulls
df[df["State"].isna()]["Loss Location"]  # verified no unexpected nulls
```



---

## 2. Repair Estimate Cost — Null Imputation

### The Problem

`Repair Estimate Cost` had a meaningful percentage (48%) of null values. Simply dropping these rows would reduce dataset size and potentially bias results. Simple global mean/median imputation would ignore the fact that repair costs vary significantly by vehicle type and damage.

### Exploratory Analysis Performed

**Null rate check:**
```python
df["Repair Estimate Cost"].isna().mean() * 100
```

**Variance check:**
```python
overall_variance = df["Repair Estimate Cost"].var()
```
High overall variance confirmed that a global fill would be too imprecise.



### Grouping Strategy — How It Was Decided

The key question was: **which combination of columns produces the most homogeneous groups for imputing repair cost?**

Six candidate groupings were evaluated based on domain knowledge:

```python
groups = [
    ["Vehicle Make", "Vehicle Model", "Vehicle Year", "Damage Description"],
    ["Vehicle Make", "Vehicle Model", "Damage Description"],
    ["Vehicle Make", "Damage Description"],
    ["Vehicle Make", "Vehicle Model", "Vehicle Year"],
    ["Vehicle Make", "Vehicle Model"],
    ["Vehicle Make"]
]
```

Two metrics were computed for each grouping:

**1. Average within-group variance** (lower = more homogeneous = better imputation quality):
```python
var = df.groupby(g)["Repair Estimate Cost"].var().mean()
```

**Variance results (sorted ascending — lower is better):**

| Rank | Grouping | Average Variance |
|------|----------|-----------------|
| 1 | Make + Model + Year | 1,578,793 |
| 2 | Make + Model | 1,593,580 |
| 3 | Make + Model + Damage Description | 1,596,198 |
| 4 | Make | 1,624,600 |
| 5 | Make + Damage Description | 1,630,417 |
| 6 | Make + Model + Year + Damage Description | 1,853,486 |

**2. Group size coverage** (higher = more rows can actually be filled):
```python
sizes = df.groupby(g).size()
print("Median group size:", sizes.median())
print("Groups ≥5 records:", (sizes >= 5).mean())
```

**Group size results:**

| Grouping | Median Group Size | Groups ≥5 Records |
|----------|------------------|-------------------|
| Make + Model + Year + Damage Description | 1.0 | 0% |
| Make + Model + Damage Description | 5.0 | 64% |
| Make + Damage Description | 34.5 | 100% |
| Make + Model + Year | 2.0 | 2.2% |
| Make + Model | 28.0 | 100% |
| Make | 166.5 | 100% |

**The tradeoff identified from both analyses:**

- `Make + Model + Year` had the lowest variance (best precision) but a median group size of only 2 and just 2.2% of groups having 5+ records — **too sparse to be reliable**.
- `Make + Model + Year + Damage Description` was the most granular but had the **highest variance** and median group size of 1 — effectively useless for imputation.
- `Make + Model` offered nearly the same low variance as Year-based groups, with a median group size of 28 and 100% coverage — **the best balance of precision and reliability**.
- `Make + Model + Damage Description` added damage context with acceptable group sizes (64% ≥5 records), making it a strong secondary pass.

### Final Decision — Cascading Fallback Strategy

Rather than picking a single grouping, a **cascading hierarchy** was applied — starting with the best balance of precision and coverage, then falling back to broader groupings only for remaining nulls:

```python
group_levels = [
    ["Vehicle Make", "Vehicle Model"],                        # Best balance: low variance, large groups
    ["Vehicle Make", "Vehicle Model", "Damage Description"],  # Adds damage context as second pass
    ["Vehicle Make"],                                         # Broad fallback for obscure models
    ["Vehicle Make", "Damage Description"]                    # Catch remaining with damage context
]

for cols in group_levels:
    df["Repair Estimate Cost"] = df["Repair Estimate Cost"].fillna(
        df.groupby(cols)["Repair Estimate Cost"].transform("median")
    )

# Final safety net — global median
df["Repair Estimate Cost"].fillna(df["Repair Estimate Cost"].median(), inplace=True)
```


**Why `Vehicle Year` was excluded from the final grouping:**
Despite having the lowest variance on paper, `Make + Model + Year` had a median group size of just 2 records and only 2.2% of groups contained 5+ records. A median computed from 1–2 values is statistically unreliable. Year was therefore dropped — the marginal gain in variance reduction did not justify the severe loss in group coverage.

---

## 3. Hospital Cost & Third-Party Insurance — Left as Nulls

### Hospital Cost

Nulls in `Hospital Cost` were investigated:

```python
df.loc[
    (df["Medical & Injury Documentation"] == "NO") &
    (df["Hospital Cost"].isnotna())
]
```

**Decision:** Nulls here are **structurally meaningful** — if `Medical & Injury Documentation` is `NO`, hospital cost is expected to be null (no hospitalisation occurred). Imputing these would be factually incorrect. The column was left as-is.



### Third-Party Insurance

Similarly investigated:

```python
df.loc[
    (df["Third-Party Information"] == "NO") &
    (df["Third-Party Insurance"].isnotna())
]
```

**Decision:** Nulls were left as-is. Missing third-party insurance details where `Third-Party Information = NO` indicates incomplete claim records, not a systematic data gap that should be filled.

---

## 4. Output

The cleaned dataset was exported and then loaded into a SQLite database:

```python
# Export cleaned data
df.to_excel("Cleaned_Processed_Claims_dataset.xlsx", index=False)

# Load into SQLite
conn = sqlite3.connect("claims.db")
df.to_sql("claims", conn, if_exists="replace", index=False)
```

The final `claims` table is verified by querying the first 5 rows via SQLAlchemy before the pipeline proceeds.

---

## Summary of Decisions

| Area | Decision | Key Reason |
|------|----------|------------|
| City/State extraction | Use last line of address + regex | Avoids false matches from street-line commas |
| Military addresses | Map APO/DPO/FPO → "Military Post Office" | Non-standard format; prevents null and miscategorisation |
| Case normalisation | Not applied | Risk of breaking proper nouns (e.g., BMW); LLM handles it |
| Repair Cost imputation | Cascading group median | Balances precision vs coverage; median handles skew |
| Vehicle Year in grouping | Excluded | Creates too-small groups; unreliable median |
| Hospital Cost nulls | Not imputed | Nulls are structurally valid (no hospitalisation) |
| Third-Party Insurance nulls | Not imputed | Incomplete records, not systematic gaps |

