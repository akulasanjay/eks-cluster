# eks-cluster

A Terraform package for provisioning a production-ready Amazon EKS cluster with modular, reusable components.

For presentation-ready documentation and architecture flow drawings, see [PRESENTATION.md](./PRESENTATION.md) and [project-flow.drawio](./project-flow.drawio).

## Modules

| Module | Description |
|--------|-------------|
| `modules/networking` | VPC, subnets, IGW, NAT gateway, route tables, security groups |
| `modules/iam` | EKS cluster role and node group role with policy attachments |
| `modules/eks` | EKS cluster and node groups (supports multiple node groups) |
| `modules/cleanup` | Pre-destroy cleanup of Kubernetes-managed AWS resources |
| `modules/s3` | Reusable S3 bucket with versioning, encryption, public access block |
| `modules/s3-backend` | Terraform remote state bucket (bootstraps S3 backend, local state) |

## Usage

```hcl
module "eks_cluster" {
  source = "github.com/your-org/eks-cluster"

  region               = "us-east-1"
  cluster_name         = "my-eks-cluster"
  vpc_cidr             = "10.1.0.0/16"
  public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
  private_subnet_cidrs = ["10.1.11.0/24", "10.1.12.0/24"]
  kubernetes_version   = "1.31"

  node_groups = {
    general = {
      instance_types = ["t3.medium"]
      desired_nodes  = 2
      min_nodes      = 2
      max_nodes      = 4
      labels         = { role = "general" }
    }
    spot = {
      instance_types = ["t3.large", "t3a.large"]
      desired_nodes  = 1
      min_nodes      = 0
      max_nodes      = 5
      labels         = { role = "spot" }
    }
  }

  tags = {
    Environment = "dev"
    Project     = "eks-demo"
  }
}
```

See [`examples/basic`](./examples/basic) for a complete runnable example.

## Bootstrap Remote State (first time only)

```bash
terraform -chdir=modules/s3-backend init
terraform -chdir=modules/s3-backend apply
```

## Deploy

```bash
terraform init
terraform plan
terraform apply
```

## Destroy

```bash
terraform destroy   # cleanup module drains k8s resources before deletion
```

## Inputs

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `region` | AWS region | `string` | `"us-east-1"` |
| `cluster_name` | EKS cluster name | `string` | `"demo-eks-cluster"` |
| `vpc_cidr` | VPC CIDR block | `string` | `"10.0.0.0/16"` |
| `public_subnet_cidrs` | Public subnet CIDRs | `list(string)` | — |
| `private_subnet_cidrs` | Private subnet CIDRs | `list(string)` | — |
| `kubernetes_version` | Kubernetes version | `string` | `"1.31"` |
| `node_groups` | Map of node groups to create | `map(object)` | see variables.tf |
| `tags` | Tags applied to all resources | `map(string)` | `{}` |

## Outputs

| Name | Description |
|------|-------------|
| `cluster_name` | EKS cluster name |
| `cluster_endpoint` | EKS API server endpoint |
| `cluster_ca_certificate` | Cluster CA certificate |
| `vpc_id` | VPC ID |
| `public_subnet_ids` | Public subnet IDs |
| `private_subnet_ids` | Private subnet IDs |
| `nat_gateway_ip` | NAT gateway public IP |
| `eks_node_group_arns` | Map of node group ARNs |
| `configure_kubectl` | kubectl config command |

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0 |
| aws | ~> 5.0 |
| null | ~> 3.0 |
