"""Weekly World Bank ingestion DAG for the exercise's Airflow 2 environment.

Deploy this file AND extract_worldbank.py to Composer's dags/ folder.
"""

from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)

from extract_worldbank import main as extract_worldbank


PROJECT_ID = "project-20d0db26-805f-47fb-90a"
BUCKET = "project-20d0db26-805f-47fb-90a-worldbank-raw"
LOCATION = "europe-west9"

SCHEMA_FIELDS = [
    {"name": "country_code", "type": "STRING", "mode": "REQUIRED"},
    {"name": "country_name", "type": "STRING", "mode": "REQUIRED"},
    {"name": "indicator_code", "type": "STRING", "mode": "REQUIRED"},
    {"name": "indicator_label", "type": "STRING", "mode": "REQUIRED"},
    {"name": "year", "type": "INT64", "mode": "REQUIRED"},
    {"name": "value", "type": "FLOAT64", "mode": "NULLABLE"},
    {"name": "load_date", "type": "DATE", "mode": "REQUIRED"},
]


def extract_and_upload_to_gcs(load_date):
    """Run only during task execution; remove the temporary CSV afterward."""
    with TemporaryDirectory(prefix="worldbank_") as directory:
        extract_worldbank(
            load_date=load_date,
            output_path=Path(directory) / "indicators.csv",
            upload=True,
            bucket_name=BUCKET,
            project_id=PROJECT_ID,
        )


with DAG(
    dag_id="worldbank_gdp_ingestion",
    description="Extract World Bank indicators to GCS, then load BigQuery.",
    start_date=pendulum.datetime(2026, 10, 25, tz="UTC"),
    schedule="@weekly",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["worldbank", "gcp", "bootcamp"],
) as dag:
    extract_and_upload = PythonOperator(
        task_id="extract_and_upload",
        python_callable=extract_and_upload_to_gcs,
        op_kwargs={"load_date": "{{ ds }}"},
        execution_timeout=timedelta(minutes=20),
        do_xcom_push=False,
    )

    load_to_bigquery = GCSToBigQueryOperator(
        task_id="load_to_bigquery",
        bucket=BUCKET,
        source_objects=["worldbank/{{ ds }}/indicators.csv"],
        destination_project_dataset_table=f"{PROJECT_ID}.raw_worldbank.indicators",
        schema_fields=SCHEMA_FIELDS,
        autodetect=False,
        source_format="CSV",
        skip_leading_rows=1,
        create_disposition="CREATE_IF_NEEDED",
        write_disposition="WRITE_TRUNCATE",
        time_partitioning={"type": "DAY", "field": "load_date"},
        cluster_fields=["country_code"],
        location=LOCATION,
        gcp_conn_id="google_cloud_default",
        execution_timeout=timedelta(minutes=20),
    )

    extract_and_upload >> load_to_bigquery
