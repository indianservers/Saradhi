locals {
  name = "${var.name}-${var.environment}"
}

resource "digitalocean_vpc" "main" {
  name     = local.name
  region   = var.region
  ip_range = var.vpc_ip_range
}

resource "digitalocean_database_cluster" "postgres" {
  name                 = "${local.name}-postgres"
  engine               = "pg"
  version              = "16"
  size                 = var.database_size
  region               = var.region
  node_count           = var.database_nodes
  private_network_uuid = digitalocean_vpc.main.id
  maintenance_window {
    day  = "sunday"
    hour = "06:00:00"
  }
}

resource "digitalocean_database_cluster" "redis" {
  name                 = "${local.name}-redis"
  engine               = "redis"
  version              = "7"
  size                 = var.cache_size
  region               = var.region
  node_count           = 1
  private_network_uuid = digitalocean_vpc.main.id
}

resource "digitalocean_container_registry" "main" {
  name                   = var.registry_name
  region                 = var.region
  subscription_tier_slug = "basic"
}

resource "digitalocean_spaces_bucket" "private_objects" {
  name   = var.spaces_bucket_name
  region = var.region
  acl    = "private"
}

resource "digitalocean_kubernetes_cluster" "main" {
  name                 = local.name
  region               = var.region
  version              = var.kubernetes_version
  vpc_uuid             = digitalocean_vpc.main.id
  registry_integration = true
  auto_upgrade         = false
  surge_upgrade        = true
  node_pool {
    name       = "quickbuddy-apps"
    size       = var.kubernetes_node_size
    node_count = var.kubernetes_node_count
    auto_scale = true
    min_nodes  = var.kubernetes_node_count
    max_nodes  = max(var.kubernetes_node_count, 6)
    tags       = ["${var.name}", var.environment]
  }
}

resource "digitalocean_database_firewall" "postgres" {
  cluster_id = digitalocean_database_cluster.postgres.id
  rule {
    type  = "k8s"
    value = digitalocean_kubernetes_cluster.main.id
  }
}

resource "digitalocean_database_firewall" "redis" {
  cluster_id = digitalocean_database_cluster.redis.id
  rule {
    type  = "k8s"
    value = digitalocean_kubernetes_cluster.main.id
  }
}
