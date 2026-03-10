"""
test_queries.py

Purpose:
--------
Verify that SQL queries work on the claims database.
"""

import pandas as pd
from sqlalchemy import create_engine

# Connect to database
engine = create_engine("sqlite:///claims.db")

print("\nTop 5 states by total loss\n")

query = """
SELECT State,
SUM("Repair Estimate Cost" + IFNULL("Hospital Cost",0)) AS total_loss
FROM claims
GROUP BY State
ORDER BY total_loss DESC
LIMIT 5
"""

result = pd.read_sql(query, engine)

print(result)