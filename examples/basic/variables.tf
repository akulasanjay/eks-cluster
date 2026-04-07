variable "region" { type = string }
variable "cluster_name" { type = string }
variable "vpc_cidr" { type = string }
variable "public_subnet_cidrs" { type = list(string) }
variable "private_subnet_cidrs" { type = list(string) }
variable "kubernetes_version" { type = string }
variable "node_groups" {
  type = map(object({
    instance_types = list(string)
    desired_nodes  = number
    min_nodes      = number
    max_nodes      = number
    labels         = optional(map(string), {})
  }))
}
variable "tags" { type = map(string) }
