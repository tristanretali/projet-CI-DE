resource "kind_cluster" "this" {
  name            = var.cluster_name
  wait_for_ready  = true
  kubeconfig_path = pathexpand("~/.kube/config")
}

provider "kubernetes" {
  host                   = kind_cluster.this.endpoint
  cluster_ca_certificate = kind_cluster.this.cluster_ca_certificate
  client_certificate     = kind_cluster.this.client_certificate
  client_key             = kind_cluster.this.client_key
}

resource "terraform_data" "image" {
  triggers_replace = sha256(join("", concat(
    [
      filesha256("${path.module}/../Dockerfile"),
      filesha256("${path.module}/../requirements.txt"),
    ],
    [for f in sort(fileset("${path.module}/../src", "*.py")) : filesha256("${path.module}/../src/${f}")],
  )))

  provisioner "local-exec" {
    working_dir = path.module
    command     = "docker build -t ${var.image} .. && kind load docker-image ${var.image} --name ${var.cluster_name}"
  }

  depends_on = [kind_cluster.this]
}
