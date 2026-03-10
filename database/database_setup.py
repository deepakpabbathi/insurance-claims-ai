"""
database_setup.py

Purpose
-------
Load the cleaned dataset and store it in a SQLite database.
"""

import pandas as pd
from sqlalchemy import create_engine
import os


def create_database():

    # Get project root (one level above database folder)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Path to cleaned dataset
    data_path = os.path.join(
        project_root,
        "data",
        "processed",
        "Cleaned_Processed_Claims_dataset.xlsx"
    )

    print("Loading cleaned dataset...")
    df = pd.read_excel(data_path)

    # Path for SQLite database (root folder)
    db_path = os.path.join(project_root, "claims.db")

    print("Creating SQLite database...")
    engine = create_engine(f"sqlite:///{db_path}")

    print("Writing dataset into SQL table...")

    df.to_sql(
        name="claims",
        con=engine,
        if_exists="replace",
        index=False
    )

    print("Database created successfully!")
    print("Database location:", db_path)

    print("\nDatabase Schema:")
    print(df.dtypes)


if __name__ == "__main__":
    create_database()