variable "project" {
  description = "Tag/name prefix for resources."
  type        = string
  default     = "gtfs-scorecard"
}

variable "bucket_name" {
  description = "Globally-unique S3 bucket name for published artifacts."
  type        = string
}

variable "region" {
  description = "AWS region for the artifacts bucket."
  type        = string
  default     = "us-west-2"
}
