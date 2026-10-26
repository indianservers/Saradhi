output "api_origin" { value = "https://${aws_lb.api.dns_name}" }
output "api_image_repository" { value = aws_ecr_repository.api.repository_url }
output "web_image_repositories" { value = { for name, repo in aws_ecr_repository.web : name => repo.repository_url } }
output "postgres_endpoint" { value = aws_db_instance.main.address }
output "redis_primary_endpoint" { value = aws_elasticache_replication_group.main.primary_endpoint_address }
output "private_object_bucket" { value = aws_s3_bucket.private_objects.bucket }
output "ecs_cluster_name" { value = aws_ecs_cluster.main.name }
