output "dataset_id" {
  description = "The BigQuery dataset ID that was created."
  value       = google_bigquery_dataset.this.dataset_id
}

output "table_full_id" {
  description = "Fully-qualified table ID: project.dataset.table"
  value       = "${var.project_id}.${google_bigquery_dataset.this.dataset_id}.${google_bigquery_table.this["weather_readings"].table_id}"
}

output "table_full_ids" {
  description = "Fully-qualified IDs of all managed tables."
  value = {
    for id, table in google_bigquery_table.this :
    id => "${var.project_id}.${google_bigquery_dataset.this.dataset_id}.${table.table_id}"
  }
}

output "bucket_names" {
  description = "Names of every GCS bucket created from config/buckets.yaml."
  value       = { for k, b in google_storage_bucket.this : k => b.name }
}
