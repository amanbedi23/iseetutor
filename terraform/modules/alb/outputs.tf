# Outputs for ALB Module

output "alb_arn" {
  description = "ARN of the ALB"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the ALB"
  value       = aws_lb.main.zone_id
}

output "backend_target_group_arn" {
  description = "ARN of the backend target group"
  value       = aws_lb_target_group.backend.arn
}

output "frontend_target_group_arn" {
  description = "ARN of the frontend target group"
  value       = aws_lb_target_group.frontend.arn
}

output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}

output "https_listener_arn" {
  description = "ARN of the HTTPS listener"
  value       = length(aws_lb_listener.https) > 0 ? aws_lb_listener.https[0].arn : ""
}

output "certificate_arn" {
  description = "ARN of the certificate used"
  value       = var.certificate_arn != "" ? var.certificate_arn : (length(aws_acm_certificate.cert) > 0 ? aws_acm_certificate.cert[0].arn : "")
}

output "domain_validation_options" {
  description = "Domain validation options for the certificate"
  value       = length(aws_acm_certificate.cert) > 0 ? aws_acm_certificate.cert[0].domain_validation_options : []
}