import pandas as pd
from pathlib import Path

DIM_PATH = Path("data/processed/dim_provider.csv")
FACT_PATH = Path("data/processed/fact_provider_spending.csv")


def test_files_exist():
    assert DIM_PATH.exists()
    assert FACT_PATH.exists()


def test_row_counts_match():
    dim = pd.read_csv(DIM_PATH)
    fact = pd.read_csv(FACT_PATH)
    assert len(dim) == len(fact)


def test_primary_key_unique():
    dim = pd.read_csv(DIM_PATH)
    assert dim["npi"].is_unique


def test_no_negative_payments():
    fact = pd.read_csv(FACT_PATH)
    assert (fact["total_medicare_payment"] >= 0).all()


def test_keys_match_between_tables():
    dim = pd.read_csv(DIM_PATH)
    fact = pd.read_csv(FACT_PATH)
    assert set(dim["npi"]) == set(fact["npi"])