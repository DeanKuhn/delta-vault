# Definition of Finished
Target: Nov 4 to Nov 26 (extended from Nov 11, then Nov 14, then Nov 19).

Stop rule: stop building on Thursday, Nov 26. **This date is final and will not be extended.** Whatever exists on Nov 26 is the finished project. The panel is expected around Dec 4; use the remaining week to rehearse.

## Architecture
- [x] Python ingestion is simple and uses a generator for paging, a context manager for connections, and a timing decorator.
- [x] Raw vault has 2-3 hubs, 1-2 links, a same-as link, and 3-4 satellites.
- [ ] A PIT table merges the CRM and billing satellite timelines for the SCD2 customer dimension.
- [ ] Marts have one fact table and two dimension tables, including an SCD2 dimension.
- [ ] All schemas are built and populated on Snowflake.
- [ ] `DECISIONS.md` explains each modeling decision.

## Requirements
- [x] CRM and billing data cover three load batches.
- [x] Batches include a rename, a plan change, an unmapped customer, and that customer being mapped later.
- [x] A deliberately bad batch fails the data quality gate and loads nothing.
- [ ] Reloading the same batch adds no vault rows.
- [x] Staging has a `unique` test on hash key, so each batch has at most one row per key.
- [ ] `dbt build` passes on Snowflake.
- [ ] Customer resolution model maps CRM and billing customers loaded under fallback IDs to their account numbers and keeps unmapped customers separate until they are mapped.
- [ ] Revenue totals match from source to mart, including after a customer is mapped.
- [ ] Repo has a lineage diagram and a README with run steps and sample output, so it still makes sense after the Snowflake trial expires.

## Interview (done from memory)
- [ ] Draw the model on paper and trace an example customer through all layers.
- [ ] Write a hub load, a satellite load with a hashdiff, and an SCD2 window query.
- [ ] Write a sample dbt macro.
- [ ] Write a sample Python generator, context manager, and decorator.
- [ ] Answer these out loud:
    - Why this business key?
    - What happens with unmapped customers?
    - Is the restated revenue a bug?
    - What happens with two changes between loads?
    - Why a vault before a star schema?
    - Where do Kafka events land?
    - What is an ODS, and how does it differ from a vault?

## Deliberately skipping
- **Sources:** API server, event feed / Kafka, contacts and opportunities, fuzzy customer matching.
- **Stack:** Portable, Sigma, Salesforce data shares.
- **Modeling:** AutomateDV. Bridge tables, unless a mart needs them.
- **Engineering:** Orchestration, CI, multiple environments.
- **Optional:** dbt snapshot, only if time is left.
