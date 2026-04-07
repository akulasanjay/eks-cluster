output "zone_id" { value = local.zone_id }
output "apex_fqdn" { value = aws_route53_record.apex.fqdn }
output "www_fqdn" { value = aws_route53_record.www.fqdn }
