variable "cluster_name" {
  type = string
}

variable "region" {
  type = string
}

variable "cluster_role_arn" {
  type = string
}

variable "node_role_arn" {
  type = string
}

variable "cluster_policy_attachments" {
  type    = list(string)
  default = []
}

variable "node_policy_attachments" {
  type    = list(string)
  default = []
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "cluster_security_group_id" {
  type = string
}

variable "kubernetes_version" {
  type    = string
  default = "1.31"
}

variable "node_groups" {
  description = "Map of node groups to create"
  type = map(object({
    instance_types = list(string)
    desired_nodes  = number
    min_nodes      = number
    max_nodes      = number
    labels         = optional(map(string), {})
  }))
  default = {
    default = {
      instance_types = ["t3.small"]
      desired_nodes  = 2
      min_nodes      = 2
      max_nodes      = 4
      labels         = {}
    }
  }
}

variable "tags" {
  type    = map(string)
  default = {}
}
