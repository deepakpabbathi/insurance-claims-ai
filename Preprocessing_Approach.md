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

## 2. Repair Estimate Cost — Left as Nulls

### Repair Estimate Cost

Nulls in `Repair Estimate Cost` were investigated:

```python
df.loc[
    (df["Repair Estimate"] == "NO") &
    (df["Repair Estimate Cost"].notna())
]
```

**Decision:** Nulls here are **structurally meaningful** — if `Repair Estimate` is `NO`, Repair estimation cost is expected to be null. Imputing these would be factually incorrect. The column was left as-is.

---

## 3. Hospital Cost & Third-Party Insurance — Left as Nulls

### Hospital Cost

Nulls in `Hospital Cost` were investigated:

```python
df.loc[
    (df["Medical & Injury Documentation"] == "NO") &
    (df["Hospital Cost"].notna())
]
```

**Decision:** Nulls here are **structurally meaningful** — if `Medical & Injury Documentation` is `NO`, hospital cost is expected to be null (no hospitalisation occurred). Imputing these would be factually incorrect. The column was left as-is.



### Third-Party Insurance

Similarly investigated:

```python
df.loc[
    (df["Third-Party Information"] == "NO") &
    (df["Third-Party Insurance"].notna())
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
| Repair Cost imputation | Not imputed | Nulls are structurally valid |
| Vehicle Year in grouping | Excluded | Creates too-small groups; unreliable median |
| Hospital Cost nulls | Not imputed | Nulls are structurally valid (no hospitalisation) |
| Third-Party Insurance nulls | Not imputed | Incomplete records, not systematic gaps |

