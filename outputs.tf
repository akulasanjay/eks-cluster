output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_ca_certificate" {
  value = module.eks.cluster_ca_certificate
}

output "eks_node_group_arns" {
  value = module.eks.eks_node_group_arns
}

output "vpc_id" {
  value = module.networking.vpc_id
}

output "public_subnet_ids" {
  value = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

output "cluster_security_group_id" {
  value = module.networking.cluster_security_group_id
}

output "nodes_security_group_id" {
  value = module.networking.nodes_security_group_id
}

output "nat_gateway_ips" {
  value = module.networking.nat_gateway_ips
}

output "configure_kubectl" {
  value = "aws eks --region ${var.region} update-kubeconfig --name ${module.eks.cluster_name}"
}

output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

output "app_url" {
  value = "https://${module.dns.apex_fqdn}"
}

output "route53_zone_id" {
  value = module.dns.zone_id
}
