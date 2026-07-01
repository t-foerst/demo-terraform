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

variable "app_hostnames" {
  type        = list(string)
  default     = ["cicd.foerst.haus", "gitops.foerst.haus", "argocd.foerst.haus"]
  description = "Hostnames that should be reachable through the cluster ALB"
}

variable "alb_hostname" {
  type        = string
  default     = "k8s-democluster-f5f36f3c4f-33140793.eu-central-1.elb.amazonaws.com" # change this
  description = "DNS name of the ALB created by the AWS Load Balancer Controller for the cluster Ingress. Leave null until the Ingress exists, then set it to create the CNAMEs."
}

variable "github_repo" {
  type        = string
  default     = "t-foerst/demo-app"
  description = "GitHub repo (org/repo) allowed to assume the CI/CD deploy role via OIDC"
}

variable "db_name" {
  type        = string
  default     = "appdb"
  description = "Name of the PostgreSQL database to create"
}

variable "db_username" {
  type        = string
  default     = "appuser"
  description = "Master username for the RDS PostgreSQL instance"
}
