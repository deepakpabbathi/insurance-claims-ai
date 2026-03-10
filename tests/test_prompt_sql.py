from rag.rag_pipeline import generate_sql

question = "Which state has the highest total loss?"

sql = generate_sql(question)

print(sql)