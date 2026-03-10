"""
streamlit_app.py

Streamlit interface for the Insurance Claims AI Assistant.

Features:
- Natural language query input
- RAG-based SQL generation
- Query execution on SQLite database
"""

import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px

from rag.rag_pipeline import run_query


# ------------------------------------------------
# Auto-create DB if not present (for Streamlit Cloud)
# ------------------------------------------------
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH    = os.path.join(BASE_DIR, "claims.db")
EXCEL_PATH = os.path.join(BASE_DIR, "data", "processed", "Cleaned_Processed_Claims_dataset.xlsx")

if not os.path.exists(DB_PATH):
    if os.path.exists(EXCEL_PATH):
        df_init = pd.read_excel(EXCEL_PATH)
        conn_init = sqlite3.connect(DB_PATH)
        df_init.to_sql("claims", conn_init, if_exists="replace", index=False)
        conn_init.close()
# ------------------------------------------------
# Page configuration
# ------------------------------------------------
st.set_page_config(
    page_title="Insurance Claims AI Assistant",
    page_icon="🚗",
    layout="wide"
)


# ------------------------------------------------
# App Title
# ------------------------------------------------
st.title("🚗 Insurance Claims AI Assistant")

st.markdown(
"""
Ask **natural language questions** about the insurance claims dataset.
"""
)


# ------------------------------------------------
# Sidebar — Sample Queries (all 9 from assignment)
# ------------------------------------------------
st.sidebar.header("🧪 Sample Queries")

sample_query = st.sidebar.selectbox(
    "Choose a sample query to test:",
    [
        "",
        "Which city/state has the highest loss? Average loss? No. of claims?",
        "How many claims are under investigation? How many are completed?",
        "Which vehicle make and model is most prone to damage?",
        "For the claims received, how many % required hospitalization?",
        "What was the average repair estimated cost?",
        "For a new claim received with side collision damage, what would be the average repair cost?",
        "What is the average cost of physiotherapy required?",
        "For a fractured arm, what is the ballpark number for hospitalization? Max and minimum?",
        "How many claims required hospitalization? How much % of them were severe?",
    ],
)

st.sidebar.markdown("---")

# ── Dataset overview in sidebar ──
st.sidebar.markdown("### 📊 Dataset Overview")

try:
    import sqlite3
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH  = os.path.join(BASE_DIR, "claims.db")
    conn     = sqlite3.connect(DB_PATH)

    total       = pd.read_sql('SELECT COUNT(*) AS n FROM claims', conn).iloc[0, 0]
    statuses    = pd.read_sql('SELECT "Claim Status", COUNT(*) AS n FROM claims GROUP BY "Claim Status"', conn)
    conn.close()

    st.sidebar.metric("Total Claims", f"{total:,}")
    st.sidebar.dataframe(statuses, width='stretch', hide_index=True)

except Exception:
    st.sidebar.info("Database not loaded yet.")

st.sidebar.markdown("---")



# ------------------------------------------------
# User input
# ------------------------------------------------
st.header("🔎 Ask a Question")

question = st.text_input(
    "Enter your question:",
    value=sample_query,
    placeholder="e.g. Which state has the highest total loss?",
)


# ------------------------------------------------
# Run query
# ------------------------------------------------
if st.button("Run Query", type="primary"):

    if question.strip() == "":
        st.warning("Please enter a question.")
        st.stop()

    with st.spinner("Running the query…"):
        sql, result, answer = run_query(question)

    # ── SQL ──────────────────────────────────────
    st.subheader("🧠 Generated SQL Query")
    if sql:
        st.code(sql, language="sql")
    else:
        st.warning("No SQL was generated.")

    # ── Results ───────────────────────────────────
    st.subheader("📋 Query Result")

    if result is None:
        st.info(answer)
        st.stop()

    st.dataframe(result, width='stretch', hide_index=True)

    # ── Visualization ─────────────────────────────
    if isinstance(result, pd.DataFrame) and not result.empty and len(result.columns) >= 2:

        st.subheader("📈 Visualization")

        num_cols  = result.select_dtypes(include="number").columns.tolist()
        text_cols = result.select_dtypes(exclude="number").columns.tolist()

        try:
            # Single-row summary → metric cards instead of a chart
            if len(result) == 1 and num_cols:
                cols = st.columns(len(num_cols))
                for i, col in enumerate(num_cols):
                    cols[i].metric(label=col, value=f"{result[col].iloc[0]:,.2f}")

            # Pie chart for small category counts
            elif text_cols and num_cols and len(result) <= 10:
                fig = px.pie(
                    result,
                    names=text_cols[0],
                    values=num_cols[0],
                    title=question,
                    hole=0.35,
                    color_discrete_sequence=px.colors.sequential.Blues_r,
                )
                st.plotly_chart(fig, use_container_width=True)

            # Bar chart for grouped results
            elif text_cols and num_cols:
                fig = px.bar(
                    result,
                    x=text_cols[0],
                    y=num_cols[0],
                    title=question,
                    text_auto=".2s",
                    color=num_cols[0],
                    color_continuous_scale="Blues",
                )
                fig.update_layout(xaxis_tickangle=-35, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            # Two numeric columns → scatter
            elif len(num_cols) >= 2:
                fig = px.scatter(
                    result,
                    x=num_cols[0],
                    y=num_cols[1],
                    title=question,
                )
                st.plotly_chart(fig, use_container_width=True)

        except Exception:
            st.info("Visualization not available for this query.")

    # ── Explanation ───────────────────────────────
    st.subheader("🧾 Explanation")
    st.text(answer)


# ------------------------------------------------
# Footer
# ------------------------------------------------
st.markdown("---")