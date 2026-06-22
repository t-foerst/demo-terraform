variable "aws_region" {
  type        = string
  default     = "eu-central-1"
  description = "AWS region to deploy resources into"
}

variable "cluster_name" {
  type        = string
  default     = "demo-eks"
  description = "Name of the EKS cluster"
}

variable "cluster_version" {
  type        = string
  default     = "1.30"
  description = "Kubernetes version for the EKS cluster"
}
