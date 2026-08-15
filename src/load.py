"""
Load step: applies the schema, then loads the cleaned fact/dim CSVs
into PostgreSQL. Loads dim_provider first since fact_provider_spending
has a foreign key referencing it.
"""

import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "medicare_spending")

DIM_PATH = Path("data/processed/dim_provider.csv")
FACT_PATH = Path("data/processed/fact_provider_spending.csv")
SCHEMA_PATH = Path("sql/schema.sql")


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def apply_schema(engine):
    print("Applying schema...")
    with engine.begin() as conn:
        for statement in SCHEMA_PATH.read_text().split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    print("Schema applied.")


def load_table(engine, csv_path, table_name):
    df = pd.read_csv(csv_path)
    print(f"Loading {len(df)} rows into {table_name}...")
    df.to_sql(table_name, engine, if_exists="append", index=False,
              method="multi", chunksize=5000)
    print(f"Loaded {table_name}.")


def verify(engine):
    with engine.connect() as conn:
        dim_count = conn.execute(text("SELECT COUNT(*) FROM dim_provider")).scalar()
        fact_count = conn.execute(text("SELECT COUNT(*) FROM fact_provider_spending")).scalar()
    print(f"dim_provider rows: {dim_count}")
    print(f"fact_provider_spending rows: {fact_count}")
    assert dim_count == fact_count, "Row count mismatch after load!"
    print("Load verification passed.")


if __name__ == "__main__":
    if not DB_PASSWORD:
        raise RuntimeError("DB_PASSWORD not set. Create a .env file first.")
    engine = get_engine()
    apply_schema(engine)
    load_table(engine, DIM_PATH, "dim_provider")
    load_table(engine, FACT_PATH, "fact_provider_spending")
    verify(engine)