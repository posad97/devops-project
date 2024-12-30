#--------------------
# Global
#--------------------

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "zone" {
  description = "Zone to deploy GCP resources"
  type        = string
  default     = "us-central1-c"
}

variable "region" {
  description = "Region to deploy GCP resources"
  type        = string
  default     = "us-central1"
}

#--------------------
# GKE cluster config
#--------------------

variable "gke_cluster_name" {
  description = "Name of the GKE cluster."
  type        = string
}

variable "regional" {
  description = "Is this cluster regional or zonal?"
  type        = bool
  default     = false
}

variable "remove_default_node_pool" {
  description = "Whether to remove the default node pool GKE creates"
  type        = bool
  default     = true
}

variable "initial_node_count" {
  description = "The initial number of nodes in the pool."
  type        = number
  default     = 1
}

#--------------------
# GKE node pool config
#--------------------

variable "preemptible" {
  description = "Deploy worker nodes as spot instances?"
  type        = bool
  default     = true
}

variable "machine_type" {
  description = "Machine types to deploy nodes on."
  type        = string
  default     = "e2-medium"
}

variable "disk_size_gb" {
  description = "Disk size for each node"
  type        = number
  default     = 30
}

variable "oauth_scopes" {
  description = "Which GCP resources nodes will have access to."
  type        = list(string)
  default     = ["https://www.googleapis.com/auth/cloud-platform",]
}

#--------------------
# Firewall settings
#--------------------

variable "gke_firewall_rules" {
  description = "Firewall rules specific to GKE"
  type = list(map(string))
  default = [
       {
         name = "allow-nodeport-ingress"
         network = "default"
         protocol = "tcp"
         ports = ["30000-32767"]
         source_ranges = ["0.0.0.0/0"]
       }
  ]
}