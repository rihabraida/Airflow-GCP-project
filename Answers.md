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
