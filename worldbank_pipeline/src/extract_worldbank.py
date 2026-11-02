import argparse
import csv
from datetime import date
from pathlib import Path

import requests


COUNTRIES = ["MAR", "TUN", "DZA", "EGY", "FRA"]
INDICATORS = [
    "NY.GDP.MKTP.CD",      # GDP
    "FP.CPI.TOTL.ZG",     # Inflation
    "SP.POP.TOTL",        # Population
    "SL.UEM.TOTL.ZS",     # Unemployment
    "SP.DYN.LE00.IN",     # Life expectancy
]
DATE_RANGE = "2020:2023"
DEFAULT_BUCKET = "project-20d0db26-805f-47fb-90a-worldbank-raw"
CSV_COLUMNS = [
    "country_code", "country_name", "indicator_code", "indicator_label",
    "year", "value", "load_date",
]


def fetch_records(country, indicator):
    """Fetch every page for one country and indicator, or fail explicitly."""
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    records = []
    page = 1

    while True:
        response = requests.get(
            url,
            params={
                "format": "json",
                "date": DATE_RANGE,
                "per_page": 100,
                "page": page,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        # World Bank can return an error message even with HTTP 200.
        error_container = data[0] if isinstance(data, list) and data else data
        if isinstance(error_container, dict) and "message" in error_container:
            raise ValueError(
                f"World Bank API error for {country}/{indicator}: "
                f"{error_container['message']}"
            )

        if (
            not isinstance(data, list)
            or len(data) != 2
            or not isinstance(data[0], dict)
            or not isinstance(data[1], list)
            or not data[1]
        ):
            raise ValueError(f"No usable records for {country}/{indicator}: {data}")

        records.extend(data[1])
        if page >= int(data[0]["pages"]):
            return records
        page += 1


def write_csv(records, output_path, load_date):
    """Convert API records to the seven columns required by BigQuery."""
    date.fromisoformat(load_date)
    with Path(output_path).open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "country_code": record["countryiso3code"],
                "country_name": record["country"]["value"],
                "indicator_code": record["indicator"]["id"],
                "indicator_label": record["indicator"]["value"],
                "year": int(record["date"]),
                # None becomes an empty CSV cell, preserving missing data.
                "value": float(record["value"]) if record["value"] is not None else None,
                "load_date": load_date,
            })


def upload_to_gcs(output_path, bucket_name, load_date, project_id=None):
    """Upload using local default credentials or Composer's service identity."""
    from google.cloud import storage

    object_name = f"worldbank/{load_date}/indicators.csv"
    client = storage.Client(project=project_id)
    blob = client.bucket(bucket_name).blob(object_name)
    blob.upload_from_filename(str(output_path), content_type="text/csv", timeout=120)
    uri = f"gs://{bucket_name}/{object_name}"
    print(f"Uploaded to: {uri}")
    return uri


def main(load_date, output_path, upload=False, bucket_name=DEFAULT_BUCKET, project_id=None):
    all_records = []
    for country in COUNTRIES:
        for indicator in INDICATORS:
            records = fetch_records(country, indicator)
            all_records.extend(records)
            available = sum(record["value"] is not None for record in records)
            print(
                f"{country} | {indicator}: {len(records)} records, "
                f"{available} with a value"
            )

    print(f"Total: {len(all_records)} records")
    write_csv(all_records, output_path, load_date)
    print(f"CSV saved to: {Path(output_path).resolve()}")
    if upload:
        upload_to_gcs(output_path, bucket_name, load_date, project_id)
    return all_records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract World Bank data to CSV.")
    parser.add_argument("--load-date", type=date.fromisoformat, required=True)
    parser.add_argument("--output", default="indicators.csv")
    parser.add_argument("--upload", action="store_true", help="Upload the CSV to GCS.")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--project", help="GCP project ID for the Storage client.")
    args = parser.parse_args()
    main(args.load_date.isoformat(), args.output, args.upload, args.bucket, args.project)
