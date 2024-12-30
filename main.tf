provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# GKE Cluster
resource "google_container_cluster" "zonal_cluster" {
  name               = var.gke_cluster_name
  location           = var.zone
  remove_default_node_pool = var.remove_default_node_pool
  initial_node_count = var.initial_node_count
}

# Node Pool
resource "google_container_node_pool" "zonal_node_pool" {
  cluster    = var.gke_cluster_name
  location   = var.zone
  node_count = var.initial_node_count

  node_config {
    preemptible  = var.preemptible
    machine_type = var.machine_type
    disk_size_gb = var.disk_size_gb

    oauth_scopes = var.oauth_scopes
  }
}

# Firewall Rule for NodePort Access
resource "google_compute_firewall" "allow_nodeport" {

  for_each = { for idx, rule in var.gke_firewall_rules : rule["name"] => rule }

  name    = each.value["name"]
  network = each.value["network"]

  allow {
    protocol = each.value["protocol"]
    ports    = each.value["ports"]
  }

  source_ranges = each.value["source_ranges"]
}