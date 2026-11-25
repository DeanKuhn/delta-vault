# Structure

Model names are provisional until the model is drawn on paper.

## Layout
```
delta-vault/
├── README.md                 Run steps, sample output, lineage diagram
├── docs/
│   ├── PLAN.md               Definition of finished
│   ├── STRUCTURE.md          This layout
│   ├── BUDGET.md             Hours by block of work
│   ├── DECISIONS.md          Modeling decisions and reasoning
│   └── notes/                Personal learning notes (gitignored)
├── data/                     Source files, one CRM and one billing CSV per batch
│   ├── batch_1/              Starting state, including unmapped B-9001
│   ├── batch_2/              Rename and plan change
│   ├── batch_3/              B-9001 gets mapped
│   ├── bad_batch/            Deliberately fails the DQ gate
│   └── dq_cases/             One CSV per DQ case, never loaded
├── ingestion/                Plain functions; the only class is the exception
│   ├── schema.py             One-time setup: warehouse, database, schemas, RAW tables
│   ├── connection.py         Snowflake connection, and the transaction context manager
│   ├── source.py             Reads headers, and yields one page of rows at a time
│   ├── dq_checks.py          Hard-fail checks
│   ├── exceptions.py         DataQualityError
│   ├── timed.py              Timing decorator
│   ├── load.py               Runs paging, DQ checks, and the Snowflake load
│   └── run_dq_cases.py       Offline check of every DQ case and batch ID rule
└── dbt/
    ├── dbt_project.yml       Project name and per-folder defaults
    ├── profiles.yml.example  Connection template
    ├── macros/               Schema name macro
    ├── tests/                Reload and revenue reconciliation tests
    └── models/
        ├── staging/          Clean names and types, add hashes
        ├── raw_vault/        hub_customer, hub_subscription,
        │                     link_customer_subscription, sal_customer,
        │                     sat_customer_crm, sat_customer_billing,
        │                     sat_subscription, plus payments once decided
        ├── business_vault/   customer_resolution, pit_customer
        └── marts/            dim_customer (SCD2), dim_plan, fact_payment
```

## Snowflake schemas
Each layer has its own schema, so the database mirrors the folders: `RAW`, `STAGING`, `RAW_VAULT`, `BUSINESS_VAULT`, and `MARTS`.

## Source data
- Data is small, static files with about 5-10 customers, so the expected result for each row is known.
- Files are generated once and committed. There is no generator script.
- `dq_cases/` files are named for the one problem or allowed case they show. `run_dq_cases.py` lists the expected result for each, so a new file needs a line there.

## Batch flow
1. `load.py` takes one batch folder and reads the `batch_id` from its name (`batch_1` is 1, `bad_batch` is -1). Any other name is rejected.
2. It reads both CSVs in full and runs the DQ checks. If a hard check fails, it stops before connecting to Snowflake, so nothing loads.
3. `RAW` keeps every batch, tagged with a `batch_id` and one `_loaded_at`. Loading a batch again replaces that batch's CRM and billing rows in one transaction and keeps the original `_loaded_at`.
4. dbt receives the `batch_id` as a variable, and staging reads only that batch.
5. Hubs insert only new keys, and satellites insert only rows with a changed hashdiff, so rerunning a batch adds no vault rows.

Batches must run through dbt one at a time and in order. Running them out of order corrupts satellite history.
