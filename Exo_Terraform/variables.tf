variable "project_id" {
  description = "GCP project ID where the dataset and table will be created."
  type        = string
}

variable "region" {
  description = "Default region for the Google provider (used for API calls, not dataset location)."
  type        = string
  default     = "europe-west1"
}
