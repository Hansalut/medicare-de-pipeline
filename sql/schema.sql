DROP TABLE IF EXISTS fact_provider_spending;
DROP TABLE IF EXISTS dim_provider;

CREATE TABLE dim_provider (
    npi BIGINT PRIMARY KEY,
    provider_name TEXT,
    provider_type TEXT,
    entity_type TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    medicare_participating TEXT,
    rural_urban_category TEXT
);

CREATE TABLE fact_provider_spending (
    npi BIGINT PRIMARY KEY REFERENCES dim_provider(npi),
    total_hcpcs_codes INTEGER,
    total_beneficiaries INTEGER,
    total_services NUMERIC,
    total_submitted_charge NUMERIC,
    total_medicare_allowed NUMERIC,
    total_medicare_payment NUMERIC,
    total_medicare_standardized NUMERIC,
    avg_risk_score NUMERIC,
    submitted_vs_paid_pct NUMERIC
);