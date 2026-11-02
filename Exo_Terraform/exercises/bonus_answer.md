# Bonus: remote state

With local state, each teammate can have a different view of the infrastructure, causing conflicting changes or attempts to create resources that already exist.

A GCS backend stores a shared Terraform state in a Cloud Storage bucket. It also supports state locking, preventing two Terraform operations from changing that state at the same time.
