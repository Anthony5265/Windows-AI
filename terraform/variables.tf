variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "windows-ai"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  sensitive   = true
  default     = "windows_ai_admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "instance_count" {
  description = "Number of ECS instances"
  type        = number
  default     = 2
}

variable "instance_type" {
  description = "ECS task CPU/Memory"
  type        = string
  default     = "256"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "Windows-AI"
    ManagedBy   = "Terraform"
    Environment = "Production"
  }
}
