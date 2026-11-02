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

## Airflow exercise: short bonus answers

- A failed quality check fails the task; downstream tasks using the default rule won’t run.
- Partitioning by `load_date` and clustering by `country_code` can reduce data scanned for queries filtering those fields. This configuration is already in the DAG.

## Airflow screenshots

### Composer environment running (Healthy)

![Composer environment running in europe-west9](worldbank_pipeline/Screenshot%20from%202026-10-30%2021-06-52.png)

### BigQuery query results

Result of `SELECT * FROM raw_worldbank.indicators LIMIT 20`:

![World Bank indicators loaded into BigQuery](worldbank_pipeline/Screenshot%20from%202026-11-01%2017-47-04.png)

## Terraform exercise: short answers

1. **YAML metadata changes:** changing the dataset description and adding an owner label updates the existing dataset without editing the resource definition.
2. **New column:** adding nullable `pressure_hpa` extends the table schema; existing rows can leave it empty.
3. **Incompatible type change:** the observed plan for changing `latitude` from `FLOAT64` to `STRING` proposed deleting and recreating the table. This would lose existing rows, so the change was reverted without applying it. Deletion protection should normally be enabled for production tables.
4. **Clustering:** clustering by `city` can reduce the data scanned by queries filtering on city.
5. **Second table:** `for_each` uses one resource definition to manage both `weather_readings` and `stations`. A `moved` block preserves the existing weather table's state mapping during the refactor.
6. **Real data:** the supplied Lesson 3 loader is missing, so this step has not been completed. Replacing a populated table would delete its data.
7. **Remote state bonus:** local state can give teammates different views of the infrastructure. A GCS backend shares the state and supports locking to prevent conflicting concurrent state changes.
