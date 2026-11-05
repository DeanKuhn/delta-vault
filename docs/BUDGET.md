# Budget

24 focused hours from Nov 4 to Nov 11. Hours are rough estimates. Rehearsal time is not included.

Stop building on Nov 11, or three days before the panel if that comes first.

## Hours
Work through these in order.

| # | Work | Hours | Spent |
|---|------|-------|-------|
| 1 | Learn Data Vault and draw the model on paper | 4 | |
| 2 | Set up Snowflake and dbt | 2 | |
| 3 | Create source data and define expected results | 2 | |
| 4 | Staging and raw vault | 6 | |
| 5 | Marts | 3 | |
| 6 | Python ingestion and DQ gate | 4 | |
| 7 | Docs | 1 | |
| | Slack | 2 | |
| | **Total** | **24** | |

## Notes
- **Slack:** the same-as link and `customer_resolution` are expected to use most of it.
- **Staging and raw vault:** start by taking one customer through every layer with a few hand-made rows.
- **Python ingestion:** comes after the marts so the vault work is protected. Load data manually until then.
- **Docs:** write each `DECISIONS.md` entry when the decision is made. The 1 hour covers the README, the lineage diagram, and cleanup.

## If behind schedule
1. Reduce the marts to one fact table and one dimension table.
2. Protect the raw vault and being able to explain it. These are the last things to cut.

## If ahead of schedule
Snapshot one table with dbt as a one-hour exercise.
