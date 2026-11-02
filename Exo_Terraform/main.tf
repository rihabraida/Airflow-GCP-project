locals {
  dataset_config = yamldecode(file("${path.module}/config/dataset.yaml"))
  table_configs = [
    yamldecode(file("${path.module}/config/table.yaml")),
    yamldecode(file("${path.module}/config/stations_table.yaml")),
  ]
  tables_by_id   = { for table in local.table_configs : table.table_id => table }
  buckets_config = yamldecode(file("${path.module}/config/buckets.yaml"))

  buckets_by_name = { for b in local.buckets_config.buckets : b.name => b }
}


resource "google_bigquery_dataset" "this" {
  dataset_id    = local.dataset_config.dataset_id
  friendly_name = local.dataset_config.friendly_name
  description   = local.dataset_config.description
  location      = local.dataset_config.location
  labels        = local.dataset_config.labels

  delete_contents_on_destroy = local.dataset_config.delete_contents_on_destroy
}


resource "google_bigquery_table" "this" {
  for_each = local.tables_by_id

  dataset_id  = google_bigquery_dataset.this.dataset_id
  table_id    = each.value.table_id
  description = each.value.description

  schema     = jsonencode(each.value.schema)
  clustering = try(each.value.clustering, null)

  dynamic "time_partitioning" {
    for_each = try([each.value.partitioning], [])
    content {
      type  = time_partitioning.value.type
      field = time_partitioning.value.field
    }
  }

  deletion_protection = false
}

# Preserve the existing table when introducing for_each resource addresses.
moved {
  from = google_bigquery_table.this
  to   = google_bigquery_table.this["weather_readings"]
}


resource "google_storage_bucket" "this" {
  for_each = local.buckets_by_name

  name                        = "${var.project_id}-${each.value.name}"
  location                    = each.value.location
  storage_class               = each.value.storage_class
  force_destroy               = each.value.force_destroy
  uniform_bucket_level_access = true
  labels                      = each.value.labels
}
