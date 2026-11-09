variable "cluster_name" {
  type    = string
  default = "transactions"
}

variable "namespace" {
  type    = string
  default = "transactions"
}

variable "image" {
  type    = string
  default = "transactions-pipeline:local"
}
