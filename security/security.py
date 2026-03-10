import re

def validate_sql(query):
    """
    Allow only SELECT queries to prevent destructive operations.
    """

    query = query.strip().lower()

    # Block dangerous SQL
    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]

    for word in forbidden:
        if re.search(rf"\b{word}\b", query):
            return False

    # Allow only SELECT
    if not query.startswith("select"):
        return False

    return True