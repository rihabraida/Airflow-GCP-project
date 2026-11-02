# World Bank ingestion

`extract_worldbank.py` supports local testing. `worldbank_gdp_ingestion.py`
defines the Airflow 2 DAG that runs the extraction, uploads a temporary CSV,
and loads `raw_worldbank.indicators` in BigQuery.

The extraction currently covers 2020–2023 for the five required countries
and indicators. Change `DATE_RANGE` in `extract_worldbank.py` to expand it.

## Deploy to Composer

1. Confirm the environment is Healthy and uses Airflow 2 (the exercise uses
   Airflow 2.11.1). This DAG has not been validated against Airflow 3.
2. In the Composer environment, open its **DAGs folder** link.
3. Upload **both** `worldbank_gdp_ingestion.py` and `extract_worldbank.py`
   into that folder. Do not upload `.venv`, local credentials, or CSV files.
4. Open the Airflow UI and wait for `worldbank_gdp_ingestion` to appear.
   Check import errors if it does not appear. Composer must have `requests`,
   `google-cloud-storage`, and its Google Airflow provider available; do not
   install the local requirements wholesale over Composer's managed packages.
5. Unpause the DAG and trigger a manual run. Unpausing may also start the
   latest eligible weekly run; `catchup=False` prevents historical backfills.
6. Inspect both task logs and the dated CSV in the raw bucket, then query:

```sql
SELECT *
FROM `project-20d0db26-805f-47fb-90a.raw_worldbank.indicators`
LIMIT 20;
```

Composer uses its configured environment service account automatically.
No local login command or credentials file is needed in the DAG.

Both tasks use Airflow's `{{ ds }}` logical date, which can differ from
the calendar date when the task actually runs. The CSV is partitioned in
BigQuery by `load_date` and clustered by `country_code`.
`WRITE_TRUNCATE` replaces the whole table's data on each successful load;
previous CSV files remain in GCS. Partitioning does not retain earlier loads.

On extraction failure, the task retries twice; the loading task only runs
after extraction succeeds. The optional quality-check task is not added yet.

## Short bonus answers

- A failed quality check fails the task; downstream tasks using the default rule won’t run.
- Partitioning by `load_date` and clustering by `country_code` can reduce data scanned for queries filtering those fields. This configuration is already in the DAG.
