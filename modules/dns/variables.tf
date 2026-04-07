variable "domain_name" {
  description = "Root domain name, e.g. example.com"
  type        = string
}
variable "create_zone" {
  description = "true = create a new Route 53 hosted zone, false = look up existing"
  type        = bool
  default     = false
}
variable "alb_dns_name" { type = string }
variable "alb_zone_id" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
