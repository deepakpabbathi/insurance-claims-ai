"""
prompt_builder.py

Builds the LLM prompt for SQL generation.
"""

from .schema import SCHEMA_DICT, EXAMPLES


# -----------------------------
# Build schema dynamically
# -----------------------------
def build_schema():

    schema_text = "Table: claims\n\nColumns:\n"

    for column, description in SCHEMA_DICT.items():
        schema_text += f'"{column}" - {description}\n'

    return schema_text


# -----------------------------
# Generate SQL prompt
# -----------------------------
def build_prompt(question):

    schema = build_schema()

    prompt = f"""
You are an expert SQL developer converting natural language questions into SQLite SQL queries.

DATABASE SCHEMA
----------------
{schema}


BUSINESS RULES
---------------

1. Total Loss = IFNULL("Repair Estimate Cost",0) + IFNULL("Hospital Cost",0)
2. "City" and "State" are separate columns


SQL GENERATION PROCESS
-----------------------

Before writing SQL:

1. Identify relevant columns from the schema
2. Identify required aggregations (COUNT, SUM, AVG, MIN, MAX)
3. Determine if GROUP BY is required
4. Determine if ranking is required (highest, lowest, top, bottom)


SQL STRUCTURE
--------------

SELECT
FROM
WHERE
GROUP BY
ORDER BY
LIMIT


SQL RULES
----------

• Use SQLite syntax  
• Only generate SELECT queries  
• Use double quotes for columns with spaces  
• Only use columns listed in the schema  
• Do NOT invent new columns  
• Return ONLY the SQL query  
• Do NOT include explanations  
• Do NOT include markdown formatting  


MULTIPLE METRICS RULE
----------------------

If the user asks multiple metrics in one question:

• Generate ONE SQL query
• Return each metric as separate columns

Use aggregation functions:

COUNT()
SUM()
AVG()
MIN()
MAX()

If different conditions are required use:

SUM(CASE WHEN ... THEN 1 ELSE 0 END)


LOCATION RULE
--------------

If the question involves city or state level analysis:

• Use GROUP BY "City","State"


RANKING RULE
-------------

If the question asks for highest or lowest value:

• Use ORDER BY
• Use DESC for highest
• Use ASC for lowest
• Use LIMIT 1 if only one result is required


EXAMPLES
---------
{EXAMPLES}


USER QUESTION
--------------
{question}
"""

    return prompt