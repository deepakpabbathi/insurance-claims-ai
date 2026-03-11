from rag.rag_pipeline import run_query

question = "Which state has the highest total loss?"

sql, result, answer = run_query(question)

print("\nGenerated SQL:\n", sql)
print("\nQuery Result:\n", result)
print("\nExplanation:\n", answer)