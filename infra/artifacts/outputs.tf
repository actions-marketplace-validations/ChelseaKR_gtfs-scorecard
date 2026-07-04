output "bucket_name" {
  description = "S3 bucket holding published artifacts."
  value       = aws_s3_bucket.artifacts.bucket
}

output "cdn_domain" {
  description = "CloudFront domain; set this as ARTIFACTS_CDN for the web app."
  value       = aws_cloudfront_distribution.artifacts.domain_name
}

output "sync_command" {
  description = "Deploy step: mirror local artifacts to the bucket."
  value       = "aws s3 sync data/artifacts s3://${aws_s3_bucket.artifacts.bucket}/data/artifacts --delete"
}
