resource "null_resource" "drain_and_cleanup" {
  triggers = {
    cluster_name = var.cluster_name
    region       = var.region
  }

  provisioner "local-exec" {
    when       = destroy
    on_failure = continue
    command    = <<-EOT
      aws eks update-kubeconfig --name ${self.triggers.cluster_name} --region ${self.triggers.region}

      # Delete all LoadBalancer services (removes ELBs, ENIs, SGs created by k8s)
      kubectl get svc --all-namespaces -o json \
        | jq -r '.items[] | select(.spec.type=="LoadBalancer") | "\(.metadata.namespace) \(.metadata.name)"' \
        | xargs -r -L1 bash -c 'kubectl delete svc -n $0 $1'

      # Delete PVCs so EBS volumes are released
      kubectl delete pvc --all --all-namespaces

      # Wait for cloud controller to clean up ELBs and EBS volumes
      sleep 60
    EOT
  }
}

# Detaches all node groups so nodes drain before cluster deletion
resource "null_resource" "deregister_nodes" {
  triggers = {
    cluster_name = var.cluster_name
    region       = var.region
  }

  provisioner "local-exec" {
    when       = destroy
    on_failure = continue
    command    = <<-EOT
      for ng in $(aws eks list-nodegroups --cluster-name ${self.triggers.cluster_name} --region ${self.triggers.region} --query 'nodegroups[*]' --output text); do
        aws eks update-nodegroup-config \
          --cluster-name ${self.triggers.cluster_name} \
          --nodegroup-name $ng \
          --scaling-config minSize=0,maxSize=0,desiredSize=0 \
          --region ${self.triggers.region}
      done
      # Wait for nodes to terminate
      sleep 90
    EOT
  }

  depends_on = [null_resource.drain_and_cleanup]
}
