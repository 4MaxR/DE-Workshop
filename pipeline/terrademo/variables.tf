variable "location" {
  description = "Project Location"
  default     = "EU"
}

variable "region" {
  description = "Project Region"
  default     = "europe-west1"
}

variable "gcs_bucket_name" {
  description = "My Storage Bucket Name"
  default     = "mustafa-data-lake-123456"
}

variable "bq_dataset_name" {
  description = "My BigQuery Dataset Name"
  default     = "demo_dataset"
}


variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default     = "STANDARD"
}

variable "project" {
  description = "Project Name"
  default     = "datatalkclub-498309"
}
