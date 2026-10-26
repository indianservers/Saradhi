variable "environment" {
  type    = string
  default = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Use a separate, explicitly named staging or production state."
  }
}

variable "name" {
  type    = string
  default = "quickbuddy"
}

variable "region" {
  type = string
}

variable "vpc_ip_range" {
  type    = string
  default = "10.50.0.0/16"
}

variable "database_size" {
  type    = string
  default = "db-s-2vcpu-4gb"
}

variable "cache_size" {
  type    = string
  default = "db-s-1vcpu-1gb"
}

variable "database_nodes" {
  type    = number
  default = 2
}

variable "kubernetes_version" {
  type = string
}

variable "kubernetes_node_size" {
  type    = string
  default = "s-4vcpu-8gb"
}

variable "kubernetes_node_count" {
  type    = number
  default = 2
}

variable "registry_name" {
  type = string
}

variable "spaces_bucket_name" {
  type = string
}
