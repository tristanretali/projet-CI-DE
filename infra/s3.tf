locals {
  s3_config      = file("${path.module}/../config/s3.json")
  s3_credentials = jsondecode(local.s3_config).identities[0].credentials[0]
}

resource "kubernetes_namespace_v1" "this" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_secret_v1" "s3_credentials" {
  metadata {
    name      = "s3-credentials"
    namespace = kubernetes_namespace_v1.this.metadata[0].name
  }

  data = {
    "access-key" = local.s3_credentials.accessKey
    "secret-key" = local.s3_credentials.secretKey
    "s3.json"    = local.s3_config
  }
}

resource "kubernetes_persistent_volume_claim_v1" "s3_data" {
  metadata {
    name      = "s3-data"
    namespace = kubernetes_namespace_v1.this.metadata[0].name
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "1Gi"
      }
    }
  }

  wait_until_bound = false
}

resource "kubernetes_deployment_v1" "s3" {
  metadata {
    name      = "s3"
    namespace = kubernetes_namespace_v1.this.metadata[0].name
  }

  spec {
    replicas = 1

    strategy {
      type = "Recreate"
    }

    selector {
      match_labels = {
        app = "s3"
      }
    }

    template {
      metadata {
        labels = {
          app = "s3"
        }
      }

      spec {
        enable_service_links = false

        security_context {
          fs_group = "1000"
        }

        container {
          name  = "seaweedfs"
          image = "chrislusf/seaweedfs"
          args  = ["server", "-dir=/data", "-s3", "-s3.config=/etc/seaweedfs/s3.json"]

          port {
            name           = "s3"
            container_port = 8333
          }

          port {
            name           = "filer"
            container_port = 8888
          }

          readiness_probe {
            tcp_socket {
              port = "s3"
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }

          volume_mount {
            name       = "data"
            mount_path = "/data"
          }

          volume_mount {
            name       = "config"
            mount_path = "/etc/seaweedfs"
            read_only  = true
          }
        }

        volume {
          name = "data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.s3_data.metadata[0].name
          }
        }

        volume {
          name = "config"
          secret {
            secret_name = kubernetes_secret_v1.s3_credentials.metadata[0].name
            items {
              key  = "s3.json"
              path = "s3.json"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "s3" {
  metadata {
    name      = "s3"
    namespace = kubernetes_namespace_v1.this.metadata[0].name
  }

  spec {
    selector = {
      app = "s3"
    }

    port {
      name = "s3"
      port = 8333
    }

    port {
      name = "filer"
      port = 8888
    }
  }
}
