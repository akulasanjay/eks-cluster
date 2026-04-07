resource "aws_eks_cluster" "this" {
  name     = var.cluster_name
  role_arn = var.cluster_role_arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = concat(var.public_subnet_ids, var.private_subnet_ids)
    security_group_ids      = [var.cluster_security_group_id]
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]
  }

  depends_on = [var.cluster_policy_attachments]

  tags = var.tags
}

resource "aws_eks_node_group" "this" {
  for_each = var.node_groups

  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${var.cluster_name}-${each.key}"
  node_role_arn   = var.node_role_arn
  subnet_ids      = var.private_subnet_ids
  version         = var.kubernetes_version

  instance_types = each.value.instance_types

  scaling_config {
    desired_size = each.value.desired_nodes
    min_size     = each.value.min_nodes
    max_size     = each.value.max_nodes
  }

  labels = lookup(each.value, "labels", {})

  update_config {
    max_unavailable = 1
  }

  depends_on = [var.node_policy_attachments]

  tags = merge(var.tags, { NodeGroup = each.key })
}
