# EKS Cluster — Full Project Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Modules](#modules)
5. [Inputs](#inputs)
6. [Outputs](#outputs)
7. [Getting Started](#getting-started)
8. [Node Groups](#node-groups)
9. [Destroy](#destroy)
10. [Security Considerations](#security-considerations)
11. [Requirements](#requirements)

---

## Overview

This Terraform package provisions a production-ready Amazon EKS cluster on AWS. It is fully modular — each concern (networking, IAM, EKS, cleanup, storage) lives in its own reusable module. The root module wires them together and exposes a clean interface via `variables.tf` and `outputs.tf`.

**What gets created:**
- A VPC with public and private subnets across multiple availability zones
- Internet Gateway, NAT Gateway, and route tables
- Security groups for the EKS control plane and worker nodes
- IAM roles and managed policy attachments for the cluster and node groups
- An EKS cluster with configurable Kubernetes version
- One or more managed node groups with configurable instance types and scaling
- Pre-destroy cleanup automation to drain Kubernetes resources before VPC deletion

---

## Architecture

```
Internet
    │
    ▼
Internet Gateway
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  VPC (10.1.0.0/16)                                  │
│                                                     │
│  ┌──────────────────┐   ┌──────────────────┐        │
│  │  Public Subnet 1 │   │  Public Subnet 2 │        │
│  │  (us-east-1a)    │   │  (us-east-1b)    │        │
│  │  NAT Gateway     │   │                  │        │
│  └────────┬─────────┘   └──────────────────┘        │
│           │ (outbound)                               │
│  ┌────────▼─────────┐   ┌──────────────────┐        │
│  │  Private Subnet 1│   │  Private Subnet 2│        │
│  │  (us-east-1a)    │   │  (us-east-1b)    │        │
│  │  Worker Nodes    │   │  Worker Nodes    │        │
│  └──────────────────┘   └──────────────────┘        │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  EKS Control Plane (AWS Managed)             │   │
│  │  - API Server (public + private endpoint)    │   │
│  │  - etcd, scheduler, controller-manager       │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘

IAM
├── eks-cluster-role        → AmazonEKSClusterPolicy, AmazonEKSServicePolicy
└── eks-nodegroup-role      → AmazonEKSWorkerNodePolicy, AmazonEKS_CNI_Policy,
                              AmazonEC2ContainerRegistryReadOnly

Security Groups
├── cluster-sg  (control plane) ← port 443 from nodes + admin CIDR
└── nodes-sg    (worker nodes)  ← all traffic from cluster-sg + node-to-node
```

---

## Project Structure

```
eks-cluster/
├── README.md                      ← quick-start guide
├── DOCUMENTATION.md               ← this file
├── versions.tf                    ← Terraform + provider version constraints
├── provider.tf                    ← AWS provider configuration
├── main.tf                        ← root module — wires all child modules
├── variables.tf                   ← all input variables
├── outputs.tf                     ← all output values
├── terraform.tfvars               ← your environment values (gitignored)
├── examples/
│   └── basic/                     ← complete runnable example
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
└── modules/
    ├── networking/                ← VPC, subnets, IGW, NAT, route tables, SGs
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── versions.tf
    ├── iam/                       ← IAM roles + policy attachments
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── versions.tf
    ├── eks/                       ← EKS cluster + managed node groups
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── versions.tf
    ├── cleanup/                   ← pre-destroy drain automation
    │   ├── main.tf
    │   ├── variables.tf
    │   └── versions.tf
    ├── s3/                        ← reusable S3 bucket (versioning, encryption)
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── versions.tf
    └── s3-backend/                ← Terraform remote state bootstrap
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── provider.tf
```

---

## Modules

### `modules/networking`

Provisions all network infrastructure inside a dedicated VPC.

**Resources created:**
| Resource | Description |
|----------|-------------|
| `aws_vpc` | VPC with DNS support and hostnames enabled |
| `aws_subnet.public` | Public subnets (one per AZ), tagged for ELB use |
| `aws_subnet.private` | Private subnets (one per AZ), tagged for internal ELB |
| `aws_internet_gateway` | IGW attached to the VPC |
| `aws_eip` | Elastic IP for the NAT Gateway |
| `aws_nat_gateway` | NAT Gateway in the first public subnet |
| `aws_route_table.public` | Routes 0.0.0.0/0 → IGW |
| `aws_route_table.private` | Routes 0.0.0.0/0 → NAT Gateway |
| `aws_security_group.eks_cluster` | Control plane SG — allows egress all, ingress port 443 |
| `aws_security_group.eks_nodes` | Worker node SG — allows egress all, node-to-node, cluster-to-node |
| `aws_security_group_rule` (×4) | nodes→cluster:443, node↔node all, cluster→nodes all, admin→cluster:443 |

**Outputs:** `vpc_id`, `public_subnet_ids`, `private_subnet_ids`, `cluster_security_group_id`, `nodes_security_group_id`, `nat_gateway_ip`

---

### `modules/iam`

Creates IAM roles and attaches AWS managed policies required by EKS.

**Resources created:**
| Resource | Description |
|----------|-------------|
| `aws_iam_role.eks_cluster` | Cluster role — trusted by `eks.amazonaws.com` |
| `aws_iam_role.eks_node_group` | Node role — trusted by `ec2.amazonaws.com` |
| Policy attachment × 2 | `AmazonEKSClusterPolicy`, `AmazonEKSServicePolicy` |
| Policy attachment × 3 | `AmazonEKSWorkerNodePolicy`, `AmazonEKS_CNI_Policy`, `AmazonEC2ContainerRegistryReadOnly` |

**Outputs:** `cluster_role_arn`, `node_role_arn`, `cluster_policy_attachments`, `node_policy_attachments`

---

### `modules/eks`

Provisions the EKS cluster and one or more managed node groups.

**Resources created:**
| Resource | Description |
|----------|-------------|
| `aws_eks_cluster` | EKS control plane with public+private API endpoint |
| `aws_eks_node_group` (for_each) | One managed node group per entry in `var.node_groups` |

**Key behaviours:**
- `version` is set on both the cluster and every node group — they always stay in sync
- Node groups run in **private subnets** only (outbound via NAT)
- `depends_on` uses IAM policy attachment IDs passed from the IAM module to ensure correct ordering
- `update_config.max_unavailable = 1` ensures rolling updates

**Outputs:** `cluster_name`, `cluster_endpoint`, `cluster_ca_certificate`, `eks_node_group_arns`

---

### `modules/cleanup`

Runs pre-destroy scripts to remove Kubernetes-managed AWS resources that Terraform doesn't track, which would otherwise block VPC deletion.

**Resources created:**
| Resource | Description |
|----------|-------------|
| `null_resource.drain_and_cleanup` | Deletes all `LoadBalancer` services and PVCs on destroy |
| `null_resource.deregister_nodes` | Scales all node groups to 0 before cluster deletion |

**Destroy order:**
1. `drain_and_cleanup` — removes ELBs, ENIs, EBS volumes via kubectl
2. `deregister_nodes` — scales node groups to 0, waits for EC2 termination
3. Terraform destroys EKS → IAM → networking in dependency order

---

### `modules/s3`

A reusable, hardened S3 bucket module.

**Resources created:**
| Resource | Description |
|----------|-------------|
| `aws_s3_bucket` | S3 bucket |
| `aws_s3_bucket_versioning` | Versioning enabled |
| `aws_s3_bucket_server_side_encryption_configuration` | AES256 encryption |
| `aws_s3_bucket_public_access_block` | All public access blocked |

**Inputs:** `bucket_name`, `force_destroy`, `tags`  
**Outputs:** `bucket_name`, `bucket_arn`

---

### `modules/s3-backend`

A standalone root module that bootstraps the Terraform remote state S3 bucket. Uses a `backend "local"` so it manages its own state locally (chicken-and-egg bootstrap).

Wraps `modules/s3` and adds a `random_id` suffix to ensure a globally unique bucket name.

**Usage:**
```bash
terraform -chdir=modules/s3-backend init
terraform -chdir=modules/s3-backend apply
# outputs the bucket name to use in your backend config
```

---

## Inputs

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `region` | `string` | `"us-east-1"` | AWS region to deploy into |
| `cluster_name` | `string` | `"demo-eks-cluster"` | Name prefix for all resources |
| `vpc_cidr` | `string` | `"10.0.0.0/16"` | CIDR block for the VPC |
| `public_subnet_cidrs` | `list(string)` | — | CIDRs for public subnets (one per AZ) |
| `private_subnet_cidrs` | `list(string)` | — | CIDRs for private subnets (one per AZ) |
| `kubernetes_version` | `string` | `"1.31"` | Kubernetes version for cluster and node groups |
| `node_groups` | `map(object)` | — | Map of node groups — see [Node Groups](#node-groups) |
| `tags` | `map(string)` | `{}` | Tags applied to all resources |

### `node_groups` object schema

```hcl
node_groups = {
  <name> = {
    instance_types = list(string)   # e.g. ["t3.medium"]
    desired_nodes  = number         # current desired count
    min_nodes      = number         # autoscaler minimum
    max_nodes      = number         # autoscaler maximum
    labels         = map(string)    # optional k8s node labels
  }
}
```

---

## Outputs

| Name | Description |
|------|-------------|
| `cluster_name` | EKS cluster name |
| `cluster_endpoint` | EKS API server endpoint URL |
| `cluster_ca_certificate` | Base64-encoded cluster CA certificate |
| `eks_node_group_arns` | Map of `{ node_group_name => ARN }` |
| `vpc_id` | VPC ID |
| `public_subnet_ids` | List of public subnet IDs |
| `private_subnet_ids` | List of private subnet IDs |
| `cluster_security_group_id` | Control plane security group ID |
| `nodes_security_group_id` | Worker nodes security group ID |
| `nat_gateway_ip` | Public IP of the NAT Gateway |
| `configure_kubectl` | Ready-to-run `aws eks update-kubeconfig` command |

---

## Getting Started

### 1. Bootstrap remote state (first time only)

```bash
terraform -chdir=modules/s3-backend init
terraform -chdir=modules/s3-backend apply
```

Copy the output bucket name into a `backend.tf` in the root:

```hcl
terraform {
  backend "s3" {
    bucket = "<output-bucket-name>"
    key    = "eks-cluster/terraform.tfstate"
    region = "us-east-1"
  }
}
```

### 2. Configure your values

Edit `terraform.tfvars`:

```hcl
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
}
```

### 3. Deploy

```bash
terraform init
terraform plan
terraform apply
```

### 4. Configure kubectl

```bash
$(terraform output -raw configure_kubectl)
kubectl get nodes
```

---

## Node Groups

You can define any number of node groups with different instance types, sizes, and labels:

```hcl
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
  gpu = {
    instance_types = ["g4dn.xlarge"]
    desired_nodes  = 0
    min_nodes      = 0
    max_nodes      = 2
    labels         = { role = "gpu" }
  }
}
```

Use `nodeSelector` in your pod specs to target a specific group:

```yaml
spec:
  nodeSelector:
    role: general
```

---

## Destroy

```bash
terraform destroy
```

The `cleanup` module automatically runs before destruction:
1. Deletes all Kubernetes `LoadBalancer` services → removes ELBs/ENIs/SGs
2. Deletes all PVCs → releases EBS volumes
3. Scales all node groups to 0 → terminates EC2 instances cleanly
4. Terraform then destroys EKS cluster, IAM roles, and VPC in order

---

## Security Considerations

| Area | Current Setting | Recommendation |
|------|----------------|----------------|
| API server public access | `0.0.0.0/0` | Restrict to your IP/CIDR in `public_access_cidrs` |
| Admin kubectl access | `203.0.113.0/24` | Change `cluster_api_from_admin` rule to your actual IP |
| Node subnets | Private only | ✅ Nodes have no public IPs |
| S3 state bucket | Public access blocked + AES256 | ✅ |
| IAM roles | Least-privilege managed policies | ✅ |

---

## Requirements

| Name | Version |
|------|---------|
| Terraform | `>= 1.5.0` |
| AWS provider | `~> 5.0` |
| Null provider | `~> 3.0` |
| Random provider (s3-backend only) | `~> 3.0` |
| AWS CLI | Required for cleanup scripts |
| kubectl | Required for cleanup scripts |
| jq | Required for cleanup scripts |
