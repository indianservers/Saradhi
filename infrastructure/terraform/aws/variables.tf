variable "aws_region" {
  type = string
}

variable "environment" {
  type    = string
  default = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Use an explicit staging or production environment."
  }
}

variable "project_name" {
  type    = string
  default = "quickbuddy"
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.40.0.0/24", "10.40.1.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.40.10.0/24", "10.40.11.0/24"]
}

variable "api_image" {
  type = string
}

variable "certificate_arn" {
  type = string
}

variable "database_url_secret_arn" {
  type      = string
  sensitive = true
}

variable "redis_url_secret_arn" {
  type      = string
  sensitive = true
}

variable "redis_auth_token" {
  type      = string
  sensitive = true
  validation {
    condition     = length(var.redis_auth_token) >= 16 && length(var.redis_auth_token) <= 128
    error_message = "ElastiCache auth tokens must be between 16 and 128 characters."
  }
}

variable "database_instance_class" {
  type    = string
  default = "db.t4g.medium"
}

variable "database_allocated_storage_gib" {
  type    = number
  default = 100
}

variable "database_backup_days" {
  type    = number
  default = 14
}

variable "api_task_cpu" {
  type    = number
  default = 1024
}

variable "api_task_memory_mib" {
  type    = number
  default = 2048
}

variable "worker_task_cpu" {
  type    = number
  default = 512
}

variable "worker_task_memory_mib" {
  type    = number
  default = 1024
}

variable "api_min_replicas" {
  type    = number
  default = 2
}

variable "api_max_replicas" {
  type    = number
  default = 10
}

variable "object_bucket_name" {
  type = string
}
