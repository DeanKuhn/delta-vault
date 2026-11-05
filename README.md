# delta-vault

## Purpose
A learning project for Data Vault modeling, built on dbt and Snowflake. It models a fictional membership company whose customer data lives in separate CRM and billing systems.

## Problems explored
- Combining records for the same customer across sources
- Keeping an accurate history as records change, such as a business renaming itself
- Stopping bad data before it loads
- Keeping billing records that don't map to a CRM account yet

## Status
Planning is complete. Next up are the data model, sample data, raw vault, and ingestion pipeline.

## Architecture
Planned flow:

Source files → Python ingestion → Raw tables → Staging → Raw vault → Business vault → Star-schema marts
