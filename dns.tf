data "cloudflare_zone" "this" {
  filter = {
    name = var.domain_name
  }
}

resource "aws_acm_certificate" "apps" {
  domain_name               = var.app_hostnames[0]
  subject_alternative_names = slice(var.app_hostnames, 1, length(var.app_hostnames))
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "cloudflare_dns_record" "apps_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.apps.domain_validation_options : dvo.domain_name => dvo
  }

  zone_id = data.cloudflare_zone.this.id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  content = each.value.resource_record_value
  ttl     = 60
  proxied = false
}

resource "aws_acm_certificate_validation" "apps" {
  certificate_arn = aws_acm_certificate.apps.arn
  validation_record_fqdns = [
    for dvo in aws_acm_certificate.apps.domain_validation_options : dvo.resource_record_name
  ]
}

resource "cloudflare_dns_record" "apps_cname" {
  for_each = var.alb_hostname != null ? toset(var.app_hostnames) : toset([])

  zone_id = data.cloudflare_zone.this.id
  name    = each.value
  type    = "CNAME"
  content = var.alb_hostname
  ttl     = 300
  proxied = false
}
