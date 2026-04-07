output "cluster_role_arn" {
  value = aws_iam_role.eks_cluster.arn
}

output "node_role_arn" {
  value = aws_iam_role.eks_node_group.arn
}

output "cluster_policy_attachments" {
  value = [
    aws_iam_role_policy_attachment.eks_cluster_AmazonEKSClusterPolicy.id,
    aws_iam_role_policy_attachment.eks_cluster_AmazonEKSServicePolicy.id,
  ]
}

output "node_policy_attachments" {
  value = [
    aws_iam_role_policy_attachment.node_AmazonEKSWorkerNodePolicy.id,
    aws_iam_role_policy_attachment.node_AmazonEKS_CNI_Policy.id,
    aws_iam_role_policy_attachment.node_AmazonEC2ContainerRegistryReadOnly.id,
  ]
}
