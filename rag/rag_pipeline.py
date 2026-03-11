"""
rag_pipeline.py

Text-to-SQL pipeline using OpenAI.
Flow: run_query → generate_sql → execute_sql → generate_answer
"""

import os
import re
import pandas as pd
from sqlalchemy import create_engine
from openai import OpenAI
from dotenv import load_dotenv

from rag.prompt_builder import build_prompt
from security.security import validate_sql


load_dotenv()

# Fail fast if API key is missing rather than getting a cryptic error at query time
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY is not set. Add it to your .env file or Streamlit Secrets.")

client = OpenAI(api_key=OPENAI_API_KEY)


# Walk up from /rag/ to project root to locate claims.db regardless of run location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "claims.db")

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Database not found at {DB_PATH}. Run database_setup.py first.")

engine = create_engine(f"sqlite:///{DB_PATH}")


# Cap rows sent to the explanation LLM to avoid exceeding token limits
MAX_ROWS_FOR_EXPLANATION = 50


# -----------------------------
# Input Validation
# -----------------------------

def is_meaningful(question):
    """Returns True if question has at least one real word (3+ letters). Rejects gibberish."""
    return len(re.findall(r'[a-zA-Z]{3,}', question)) >= 1


# -----------------------------
# Clean SQL
# -----------------------------

def clean_sql(sql):
    """Strips markdown fences, slices to SELECT, and drops everything after the first semicolon."""
    if not sql:
        return ""

    sql = sql.strip()
    sql = sql.replace("```sql", "").replace("```", "")

    if "SELECT" in sql.upper():
        sql = sql[sql.upper().index("SELECT"):]

    # Only keep the first statement — prevents multi-statement execution
    sql = sql.split(";")[0] + ";"

    return sql.strip()


# -----------------------------
# Generate SQL
# -----------------------------

def generate_sql(question):
    """
    Builds prompt → calls OpenAI → validates and returns SQL.

    Returns SQL string or one of:
        OPENAI_ERROR:<msg> | IRRELEVANT_QUESTION | INVALID_SQL | SECURITY_ERROR
    """
    prompt = build_prompt(question)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        sql = response.choices[0].message.content.strip()

    except Exception as e:
        return f"OPENAI_ERROR:{str(e)}"

    # LLM returns this token when question is out-of-domain (per prompt instructions)
    if "IRRELEVANT_QUESTION" in sql:
        return "IRRELEVANT_QUESTION"

    sql = clean_sql(sql)

    if not sql.upper().startswith("SELECT"):
        return "INVALID_SQL"

    # Catches dummy SQL like SELECT 0; that pass the SELECT check but don't query claims
    if "claims" not in sql.lower():
        return "INVALID_SQL"

    if not validate_sql(sql):
        return "SECURITY_ERROR"

    return sql


# -----------------------------
# Execute SQL
# -----------------------------

def execute_sql(sql):
    """Runs SQL on claims.db. Returns DataFrame, 'NO_RESULTS', 'TOO_MANY_RESULTS', or 'SQL_ERROR:<msg>'."""
    try:
        result = pd.read_sql(sql, engine)
        if result.empty:
            return "NO_RESULTS"
        # Block raw dumps — only flag if result is large AND has many columns (unaggregated)
        if len(result) > 100 and len(result.columns) > 5:
            return "TOO_MANY_RESULTS"
        return result
    except Exception as e:
        return f"SQL_ERROR:{str(e)}"


# -----------------------------
# Generate Explanation
# -----------------------------

def generate_answer(question, result):
    """Sends SQL result to OpenAI and returns a plain-English explanation."""

    # Safety guard — result should always be a DataFrame here, never a string
    if not isinstance(result, pd.DataFrame):
        return "Unexpected result format. Please try again."

    # Truncate large results before sending to LLM to avoid token limit errors
    if len(result) > MAX_ROWS_FOR_EXPLANATION:
        data_text = (
            result.head(MAX_ROWS_FOR_EXPLANATION).to_string(index=False)
            + f"\n(Showing top {MAX_ROWS_FOR_EXPLANATION} of {len(result)} rows)"
        )
    else:
        data_text = result.to_string(index=False)

    prompt = f"""
You are a data analyst explaining results from an insurance claims dataset.

Guidelines:

- Explain only what is shown in the result table.
- Do NOT assume rankings unless explicitly stated in the question.
- If the question asks for highest or lowest, apply that only to the relevant metric.
- Do NOT claim other columns are highest or lowest.
- Use the numeric values directly from the result.
- Keep the explanation concise (1-2 sentences).
- Format dollar amounts with $ prefix and 2 decimal places (e.g., $4,512.30).
- Format percentages with % suffix and 2 decimal places (e.g., 23.50%).
- Return plain text only.
- Do NOT use markdown.
- Do NOT use backticks.
- Do NOT use code blocks.

User Question:
{question}

SQL Result:
{data_text}

Explanation:
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content
        answer = re.sub(r'`+', '', answer).strip()  # Strip any backticks LLM adds

        print(repr(answer))
        return answer

    except Exception as e:
        return f"Explanation generation error: {str(e)}"


# -----------------------------
# Main Pipeline
# -----------------------------

def run_query(question):
    """
    Orchestrates the full pipeline with input validation before each API call.

    Returns: (sql, result, answer) — any can be None on early failure.
    """

    if question.strip() == "":
        return None, None, "Please enter a question."

    if len(question) > 300:
        return None, None, "Query too long. Please keep your question under 300 characters."

    if not is_meaningful(question):
        return None, None, "Please enter a valid question."

    sql = generate_sql(question)

    if isinstance(sql, str) and sql.startswith("OPENAI_ERROR"):
        return None, None, sql

    if sql == "IRRELEVANT_QUESTION":
        return None, None, "This assistant only answers questions related to insurance claims data."

    if sql == "INVALID_SQL":
        return None, None, "AI could not generate a valid SQL query for this question."

    if sql == "SECURITY_ERROR":
        return None, None, "Blocked unsafe SQL query."

    result = execute_sql(sql)

    if isinstance(result, str):
        if result == "NO_RESULTS":
            return sql, None, "No results found for this query."
        if result == "TOO_MANY_RESULTS":
            return sql, None, "Query returned too many rows. Please ask a more specific question (e.g. filter by city, status, or use aggregations like COUNT or AVG)."
        if result.startswith("SQL_ERROR"):
            return sql, None, result

    answer = generate_answer(question, result)

    return sql, result, answer