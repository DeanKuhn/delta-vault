# Structure

Model names are provisional until the model is drawn on paper.

## Layout
```
delta-vault/
├── README.md                 Run steps, sample output, lineage diagram
├── docs/
│   ├── PLAN.md               Definition of finished
│   ├── STRUCTURE.md          This layout
│   └── DECISIONS.md          Modeling decisions and reasoning
├── data/                     Source files for each load
│   ├── batch_1/              Starting state, including unmapped 9001
│   ├── batch_2/              Rename and plan change
│   ├── batch_3/              9001 gets mapped
│   └── bad_batch/            Deliberately fails the DQ gate
├── ingestion/                Plain functions, no classes
│   ├── source.py             Returns one page of local data at a time
│   ├── dq_checks.py          Hard-fail checks
│   └── load.py               Runs paging, DQ checks, and the Snowflake load
└── dbt/
    ├── macros/               Hash key and hashdiff macros
    ├── tests/                Reload and revenue reconciliation tests
    └── models/
        ├── staging/          Clean names and types, add hashes
        ├── raw_vault/        hub_customer, hub_subscription,
        │                     link_customer_subscription, sal_customer,
        │                     sat_customer_crm, sat_customer_billing,
        │                     sat_subscription, plus payments once decided
        ├── business_vault/   customer_resolution
        └── marts/            dim_customer (SCD2), dim_plan, fact_payment
```

## Snowflake schemas
Each layer has its own schema, so the database mirrors the folders: `RAW`, `STAGING`, `RAW_VAULT`, `BUSINESS_VAULT`, and `MARTS`.

## Source data
- Data is small, static files with about 5-10 customers, so the expected result for each row is known.
- Files are generated once and committed. There is no generator script.

## Batch flow
1. `load.py` runs the DQ checks on a batch. If a hard check fails, nothing loads.
2. `RAW` keeps every batch, tagged with a `batch_id`. Loading a batch again replaces that batch's rows.
3. dbt receives the `batch_id` as a variable, and staging reads only that batch.
4. Hubs insert only new keys, and satellites insert only rows with a changed hashdiff, so rerunning a batch adds no vault rows.

Batches must run through dbt one at a time and in order. Running them out of order corrupts satellite history.
