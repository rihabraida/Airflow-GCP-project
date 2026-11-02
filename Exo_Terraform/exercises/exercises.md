# Exercises

Work through these after `terraform apply` has succeeded once. Difficulty
increases top to bottom.

## 1. Change something through YAML only (warm-up)
Edit `config/dataset.yaml`: change the `description` and add a label
`owner: <your name>`. Run `terraform plan` — confirm Terraform shows an
in-place update, with no `.tf` file touched. Apply it.

## 2. Add a field to the table
Add a `pressure_hpa` (FLOAT64, NULLABLE) field to the `schema` list in
`config/table.yaml`. Run `terraform plan`. Notice BigQuery table schemas
only support *adding* columns without recreating the table — Terraform
should show an update, not a destroy/recreate. Apply it and confirm the
column appears in the BigQuery console.

## 3. Break it on purpose
Change a field's `type` in `config/table.yaml` (e.g. `latitude` from
`FLOAT64` to `STRING`) and run `terraform plan`. BigQuery does not allow
changing a column's type in place. What does Terraform propose to do? Why
is that dangerous for a table that already has data in it? (This is the
same risk `deletion_protection = false` in `main.tf` was hiding from you —
discuss why that flag is fine for a lab and wrong for production.)

## 4. Add clustering
BigQuery lets you cluster a table on up to 4 columns to speed up filtered
queries. Add a `clustering: [city]` key to `config/table.yaml`, then wire
it into `main.tf` with a `clustering = local.table_config.clustering`
argument on `google_bigquery_table`. Verify in the console that the table
is now clustered.

## 5. Provision a second table
Add `config/stations_table.yaml` describing a small reference table (e.g.
`city`, `region`, `elevation_m`). You have two options:
- copy the `google_bigquery_table.this` block and adjust it for a second
  resource (simplest, but duplicates code), or
- turn `table_config` into a **list** of tables and use `for_each` to
  create one `google_bigquery_table` per entry (more idiomatic, but
  requires restructuring the YAML into a list under a `tables:` key).

Try the `for_each` version — it's the pattern real infrastructure repos use
once they have more than one or two similar resources.

## 6. Load real data into your Terraform-managed table
Point the Lesson 3 ETL pipeline (`load_to_bigquery.py`) at the dataset and
table you just created here (`weather_lab_tf.weather_readings`) instead of
the ones it creates by default. Run the pipeline once. Then try Exercise 3
again — now that the table has real rows, what does `terraform plan`
propose for a type change, and what would actually happen if you applied
it?

## 7. Bonus: remote state
Right now Terraform state lives on your laptop (`terraform.tfstate`, which
is gitignored). Research what problem that causes the moment a second
person on your team runs `terraform apply`, and what a GCS backend
(`backend "gcs"`) does to solve it. You don't need to implement it — just
be ready to explain the problem and the fix.
