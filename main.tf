module "cleanup" {
  source       = "./modules/cleanup"
  cluster_name = var.cluster_name
  region       = var.region
}

module "networking" {
  source = "./modules/networking"

  cluster_name         = var.cluster_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  tags                 = var.tags
}

module "iam" {
  source       = "./modules/iam"
  cluster_name = var.cluster_name
}

module "eks" {
  source = "./modules/eks"

  cluster_name               = var.cluster_name
  region                     = var.region
  cluster_role_arn           = module.iam.cluster_role_arn
  node_role_arn              = module.iam.node_role_arn
  cluster_policy_attachments = module.iam.cluster_policy_attachments
  node_policy_attachments    = module.iam.node_policy_attachments
  public_subnet_ids          = module.networking.public_subnet_ids
  private_subnet_ids         = module.networking.private_subnet_ids
  cluster_security_group_id  = module.networking.cluster_security_group_id
  kubernetes_version         = var.kubernetes_version
  node_groups                = var.node_groups
  tags                       = var.tags
}

module "alb" {
  source = "./modules/alb"

  cluster_name          = var.cluster_name
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  alb_security_group_id = module.networking.alb_security_group_id
  acm_certificate_arn   = var.acm_certificate_arn
  tags                  = var.tags
}

module "dns" {
  source = "./modules/dns"

  domain_name  = var.domain_name
  create_zone  = var.create_zone
  alb_dns_name = module.alb.alb_dns_name
  alb_zone_id  = module.alb.alb_zone_id
  tags         = var.tags
}
