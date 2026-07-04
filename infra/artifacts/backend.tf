# Remote state in S3 (versioned bucket), so the state outlives any one machine.
# No DynamoDB lock table: this is a single-operator project on Terraform 1.5,
# which predates S3 native locking. Add one (or upgrade to use_lockfile) if more
# than one person ever runs apply.
terraform {
  backend "s3" {
    bucket  = "gtfs-scorecard-tfstate-ckr"
    key     = "artifacts/terraform.tfstate"
    region  = "us-west-2"
    encrypt = true
  }
}
