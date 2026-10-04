resource "aws_route53_record" "app" {
  zone_id = var.hosted_zone_id
  name    = var.fqdn
  type    = "A"
  ttl     = 60
  records = [var.public_ip]
}
