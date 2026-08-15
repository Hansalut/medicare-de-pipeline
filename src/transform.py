"""
Transformation step: cleans the raw CMS extract and splits it into
a fact table (financial/utilization measures) and a dimension table
(provider descriptive attributes) — ready for loading into Postgres.
"""

import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw/medicare_provider_ca.csv")
FACT_OUTPUT = Path("data/processed/fact_provider_spending.csv")
DIM_OUTPUT = Path("data/processed/dim_provider.csv")


def load_raw(path: Path) -> pd.DataFrame:
    print(f"Loading raw data from {path} ...")
    df = pd.read_csv(path)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns.")
    return df


def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies data-quality rules and documents each decision.
    """
    before = len(df)

    # Rule 1: NPI (our primary key) must never be missing or duplicated.
    df = df.dropna(subset=["Rndrng_NPI"])
    df = df.drop_duplicates(subset=["Rndrng_NPI"])

    # Rule 2: A provider record needs at least a last/organization name
    # to be usable — this was missing in only 4 rows (0.01%), safe to drop.
    df = df.dropna(subset=["Rndrng_Prvdr_Last_Org_Name"])

    # Rule 3: First name is legitimately blank for organizational providers
    # (Rndrng_Prvdr_Ent_Cd == 'O' means Organization, not Individual) —
    # this isn't missing data, it's expected. Fill with empty string
    # rather than dropping the row.
    df["Rndrng_Prvdr_First_Name"] = df["Rndrng_Prvdr_First_Name"].fillna("")

    # Rule 4: Core financial columns must never be null for a row to be
    # usable in the fact table — if any of these are missing, the row
    # can't answer the question this project is built around.
    financial_cols = ["Tot_Sbmtd_Chrg", "Tot_Mdcr_Alowd_Amt", "Tot_Mdcr_Pymt_Amt"]
    df = df.dropna(subset=financial_cols)

    after = len(df)
    dropped = before - after
    print(f"  Data quality: dropped {dropped} rows ({dropped / before * 100:.2f}%) "
          f"for missing PK, name, or core financial data.")

    return df


def build_dim_provider(df: pd.DataFrame) -> pd.DataFrame:
    """
    Descriptive attributes about each provider — the 'who and where'.
    """
    dim = pd.DataFrame({
        "npi": df["Rndrng_NPI"],
        "provider_name": (
            df["Rndrng_Prvdr_Last_Org_Name"].str.strip()
            + ", "
            + df["Rndrng_Prvdr_First_Name"].str.strip()
        ).str.strip(", "),
        "provider_type": df["Rndrng_Prvdr_Type"],
        "entity_type": df["Rndrng_Prvdr_Ent_Cd"].map({"I": "Individual", "O": "Organization"}),
        "city": df["Rndrng_Prvdr_City"],
        "state": df["Rndrng_Prvdr_State_Abrvtn"],
        "zip_code": df["Rndrng_Prvdr_Zip5"],
        "medicare_participating": df["Rndrng_Prvdr_Mdcr_Prtcptg_Ind"],
        "rural_urban_category": df["Rndrng_Prvdr_RUCA_Desc"],
    })
    return dim


def build_fact_provider_spending(df: pd.DataFrame) -> pd.DataFrame:
    """
    The measurable, numeric facts — utilization and financials.
    """
    fact = pd.DataFrame({
        "npi": df["Rndrng_NPI"],
        "total_hcpcs_codes": df["Tot_HCPCS_Cds"],
        "total_beneficiaries": df["Tot_Benes"],
        "total_services": df["Tot_Srvcs"],
        "total_submitted_charge": df["Tot_Sbmtd_Chrg"],
        "total_medicare_allowed": df["Tot_Mdcr_Alowd_Amt"],
        "total_medicare_payment": df["Tot_Mdcr_Pymt_Amt"],
        "total_medicare_standardized": df["Tot_Mdcr_Stdzd_Amt"],
        "avg_risk_score": df["Bene_Avg_Risk_Scre"],  # may still contain nulls — that's fine for a fact measure, not a key
    })

    # A derived, analysis-ready column: the "markdown" gap that's the
    # core financial story of this project.
    fact["submitted_vs_paid_pct"] = (
        (fact["total_submitted_charge"] - fact["total_medicare_payment"])
        / fact["total_submitted_charge"] * 100
    ).round(2)

    return fact


if __name__ == "__main__":
    df = load_raw(RAW_PATH)
    df = clean_and_validate(df)

    dim_provider = build_dim_provider(df)
    fact_spending = build_fact_provider_spending(df)

    FACT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    dim_provider.to_csv(DIM_OUTPUT, index=False)
    fact_spending.to_csv(FACT_OUTPUT, index=False)

    print(f"\nSaved {len(dim_provider)} rows to {DIM_OUTPUT}")
    print(f"Saved {len(fact_spending)} rows to {FACT_OUTPUT}")

    # Final sanity check: fact and dim should have matching row counts
    # and matching NPI keys, since they came from the same cleaned source.
    assert len(dim_provider) == len(fact_spending), "Row count mismatch between fact and dim!"
    assert set(dim_provider["npi"]) == set(fact_spending["npi"]), "NPI keys don't match between fact and dim!"
    print("Validation passed: fact and dim tables are aligned.")