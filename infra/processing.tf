locals {
  s3_env = {
    S3_ENDPOINT_URL = "http://s3:8333"
    S3_BUCKET       = "transactions"
  }
}

resource "kubernetes_persistent_volume_claim_v1" "transaction_db" {
  metadata {
    name      = "transaction-db"
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

resource "kubernetes_cron_job_v1" "process_transactions" {
  metadata {
    name      = "process-transactions"
    namespace = kubernetes_namespace_v1.this.metadata[0].name
  }

  spec {
    schedule                      = "*/5 * * * *"
    concurrency_policy            = "Forbid"
    successful_jobs_history_limit = 3
    failed_jobs_history_limit     = 3

    job_template {
      metadata {}

      spec {
        backoff_limit = 0

        template {
          metadata {}

          spec {
            restart_policy = "Never"

            security_context {
              fs_group = "1000"
            }

            container {
              name              = "process"
              image             = var.image
              image_pull_policy = "IfNotPresent"
              command           = ["python", "/app/src/process.py"]
              working_dir       = "/db"

              dynamic "env" {
                for_each = local.s3_env
                content {
                  name  = env.key
                  value = env.value
                }
              }

              env {
                name = "S3_ACCESS_KEY"
                value_from {
                  secret_key_ref {
                    name = kubernetes_secret_v1.s3_credentials.metadata[0].name
                    key  = "access-key"
                  }
                }
              }

              env {
                name = "S3_SECRET_KEY"
                value_from {
                  secret_key_ref {
                    name = kubernetes_secret_v1.s3_credentials.metadata[0].name
                    key  = "secret-key"
                  }
                }
              }

              volume_mount {
                name       = "db"
                mount_path = "/db"
              }
            }

            volume {
              name = "db"
              persistent_volume_claim {
                claim_name = kubernetes_persistent_volume_claim_v1.transaction_db.metadata[0].name
              }
            }
          }
        }
      }
    }
  }

  depends_on = [terraform_data.image, kubernetes_deployment_v1.s3]
}
