output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.windows_ai.dns_name
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.windows_ai.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.windows_ai.name
}

output "rds_cluster_endpoint" {
  description = "RDS cluster endpoint"
  value       = aws_rds_cluster.windows_ai.endpoint
  sensitive   = true
}

output "rds_reader_endpoint" {
  description = "RDS reader endpoint"
  value       = aws_rds_cluster.windows_ai.reader_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.windows_ai.cache_nodes[0].address
  sensitive   = true
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.windows_ai.id
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.windows_ai.repository_url
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = "http://${aws_lb.windows_ai.dns_name}"
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.windows_ai.name
}
