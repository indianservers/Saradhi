output "vpc_id" {
  value = digitalocean_vpc.main.id
}

output "postgres_private_host" {
  value = digitalocean_database_cluster.postgres.private_host
}

output "redis_private_host" {
  value = digitalocean_database_cluster.redis.private_host
}

output "container_registry_endpoint" {
  value = digitalocean_container_registry.main.endpoint
}

output "spaces_bucket_name" {
  value = digitalocean_spaces_bucket.private_objects.name
}

output "kubernetes_endpoint" {
  value = digitalocean_kubernetes_cluster.main.endpoint
}
