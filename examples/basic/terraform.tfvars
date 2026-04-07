region       = "us-east-1"
cluster_name = "my-eks-cluster"

vpc_cidr             = "10.1.0.0/16"
public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
private_subnet_cidrs = ["10.1.11.0/24", "10.1.12.0/24"]

kubernetes_version = "1.31"

node_groups = {
  general = {
    instance_types = ["t3.medium"]
    desired_nodes  = 2
    min_nodes      = 2
    max_nodes      = 4
    labels         = { role = "general" }
  }
}

tags = {
  Environment = "dev"
  Project     = "eks-demo"
  Owner       = "infrastructure"
}
