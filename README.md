# Medicare Provider Spending Pipeline

An end-to-end data pipeline that extracts, cleans, and models real CMS Medicare provider financial data, revealing the gap between what providers bill and what Medicare actually pays.

## Overview

This pipeline ingests real, publicly available CMS data on ~80,000 California-based Medicare providers, validates and transforms it in Python, loads it into a PostgreSQL star schema, and produces analytics-ready tables for SQL and Power BI analysis.

## Business Problem

Healthcare providers submit charges to Medicare, but Medicare pays a standardized, often much lower amount. Understanding this "billed vs. paid" gap — and how it varies by specialty, geography, and provider type — is core to healthcare finance and value-based care analysis, directly relevant to Medicare cost containment and provider network design.

## Architecture