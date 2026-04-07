variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "demo-eks-cluster"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for ALB HTTPS listener"
  type        = string
}

variable "domain_name" {
  description = "Root domain name, e.g. example.com"
  type        = string
}

variable "create_zone" {
  description = "true = create a new Route 53 hosted zone, false = look up existing"
  type        = bool
  default     = false
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS cluster and node groups"
  type        = string
  default     = "1.31"
}

variable "node_groups" {
  description = "Map of node groups — define as many as you need with different instance types"
  type = map(object({
    instance_types = list(string)
    desired_nodes  = number
    min_nodes      = number
    max_nodes      = number
    labels         = optional(map(string), {})
  }))
}