module "eks_cluster" {
  source = "../../"

  region               = var.region
  cluster_name         = var.cluster_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  kubernetes_version   = var.kubernetes_version
  node_groups          = var.node_groups
  tags                 = var.tags
}
