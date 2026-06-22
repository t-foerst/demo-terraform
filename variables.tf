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

variable "cloudflare_api_token" {
  type        = string
  sensitive   = true
  description = "Cloudflare API token (Zone:DNS:Edit permission on the foerst.haus zone)"
}

variable "domain_name" {
  type        = string
  default     = "foerst.haus"
  description = "Cloudflare-managed root domain"
}

variable "demo_hostname" {
  type        = string
  default     = "demo.foerst.haus"
  description = "Hostname the demo app should be reachable under"
}

variable "alb_hostname" {
  type        = string
  default     = null
  description = "DNS name of the ALB created by the AWS Load Balancer Controller for the demo Ingress. Leave null until the Ingress exists, then set it to create the CNAME."
}
