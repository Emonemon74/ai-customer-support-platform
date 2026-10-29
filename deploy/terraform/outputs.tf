output "app_ip" {
  description = "Public IP of the app host"
  value       = aws_eip.app.public_ip
}

output "site_address" {
  description = "nip.io hostname that resolves to the app host (use for SITE_ADDRESS)"
  value       = "${replace(aws_eip.app.public_ip, ".", "-")}.nip.io"
}

output "db_endpoint" {
  description = "RDS endpoint host:port"
  value       = aws_db_instance.postgres.endpoint
}

output "database_url" {
  description = "DATABASE_URL for the app .env"
  value       = "postgresql+psycopg2://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/ai_support"
  sensitive   = true
}

output "ssh" {
  value = "ssh -i ~/.ssh/aicsp ec2-user@${aws_eip.app.public_ip}"
}

output "instance_id" {
  description = "EC2 instance id (GitHub variable DEPLOY_INSTANCE_ID)"
  value       = aws_instance.app.id
}

output "releases_bucket" {
  description = "S3 bucket for release tarballs (GitHub variable DEPLOY_BUCKET)"
  value       = aws_s3_bucket.releases.bucket
}

output "github_deploy_role_arn" {
  description = "IAM role GitHub Actions assumes (GitHub variable AWS_DEPLOY_ROLE_ARN)"
  value       = aws_iam_role.github_deploy.arn
}

output "env_parameter_name" {
  description = "SSM parameter the host reads its .env from"
  value       = var.env_parameter_name
}
