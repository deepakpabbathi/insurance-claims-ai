"""
rag_pipeline.py

Text-to-SQL pipeline using OpenAI
"""

import os
import re
import pandas as pd
from sqlalchemy import create_engine
from openai import OpenAI
from dotenv import load_dotenv

from rag.prompt_builder import build_prompt
from security.security import validate_sql


# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -----------------------------
# Database connection
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "claims.db")

if not os.path.exists(DB_PATH):
    raise FileNotFoundError("Database not found. Run database_setup.py first.")

engine = create_engine(f"sqlite:///{DB_PATH}")


# -----------------------------
# Clean SQL
# -----------------------------
def clean_sql(sql):

    if not sql:
        return ""

    sql = sql.strip()

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")

    if "SELECT" in sql.upper():
        sql = sql[sql.upper().index("SELECT"):]

    sql = sql.split(";")[0] + ";"

    return sql.strip()


# -----------------------------
# Generate SQL
# -----------------------------
def generate_sql(question):

    prompt = build_prompt(question)

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        sql = response.choices[0].message.content

    except Exception as e:
        return f"OPENAI_ERROR:{str(e)}"

    sql = clean_sql(sql)

    if not sql.upper().startswith("SELECT"):
        return "INVALID_SQL"

    if not validate_sql(sql):
        return "SECURITY_ERROR"

    return sql


# -----------------------------
# Execute SQL
# -----------------------------
def execute_sql(sql):

    try:

        result = pd.read_sql(sql, engine)

        if result.empty:
            return "NO_RESULTS"

        return result

    except Exception as e:

        return f"SQL_ERROR:{str(e)}"


# -----------------------------
# Generate explanation
# -----------------------------
def generate_answer(question, result):

    data_text = result.to_string(index=False)

    prompt = f"""
You are a data analyst explaining results from an insurance claims dataset.

Guidelines:

- Explain only what is shown in the result table.
- Do NOT assume rankings unless explicitly stated in the question.
- If the question asks for highest or lowest, apply that only to the relevant metric.
- Do NOT claim other columns are highest or lowest.
- Use the numeric values directly from the result.
- Keep the explanation concise (1–2 sentences).
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

        # Remove ALL backtick variants (inline and block) using regex
        answer = re.sub(r'`+', '', answer)
        answer = answer.strip()

        print(repr(answer))
        return answer

    except Exception as e:

        return f"Explanation generation error: {str(e)}"


# -----------------------------
# Main pipeline
# -----------------------------
def run_query(question):

    if question.strip() == "":
        return None, None, "Please enter a question."

    if len(question) > 300:
        return None, None, "Query too long."

    sql = generate_sql(question)

    if isinstance(sql, str) and sql.startswith("OPENAI_ERROR"):
        return None, None, sql

    if sql == "INVALID_SQL":
        return None, None, "AI could not generate valid SQL."

    if sql == "SECURITY_ERROR":
        return None, None, "Blocked unsafe SQL query."

    result = execute_sql(sql)

    if isinstance(result, str):

        if result == "NO_RESULTS":
            return sql, None, "No results found."

        if result.startswith("SQL_ERROR"):
            return sql, None, result

    answer = generate_answer(question, result)

    return sql, result, answer