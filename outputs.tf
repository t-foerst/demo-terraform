output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "configure_kubectl" {
  value = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "lbc_irsa_role_arn" {
  value = module.aws_lbc_irsa.iam_role_arn
}

output "apps_certificate_arn" {
  value = aws_acm_certificate_validation.apps.certificate_arn
}

output "app_hostnames" {
  value = var.app_hostnames
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
