variable "project" {
  type    = string
  default = "ai-customer-support"
}

variable "region" {
  type    = string
  default = "ap-south-1" # Mumbai; change to taste
}

variable "instance_type" {
  type    = string
  default = "t3.small" # 2 GB RAM. t3.micro (Free Tier) works but is tight
  # given the reranker + embedding models; user-data adds 2 GB swap either way.
}

variable "public_key_path" {
  type        = string
  description = "SSH public key to install on the host"
  default     = "~/.ssh/aicsp.pub"
}

variable "ssh_ingress_cidr" {
  type        = string
  description = "CIDR allowed to SSH (your public IP /32)"
}

variable "db_username" {
  type    = string
  default = "aicsp"
}

variable "db_password" {
  type      = string
  sensitive = true
}
