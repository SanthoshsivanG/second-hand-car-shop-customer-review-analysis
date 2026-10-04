variable "aws_region" {
  description = "AWS region for all resources. Use the project-allowed region (AWS Projects RegionFloor SCP)."
  type        = string
  default     = "ap-southeast-2"
}

variable "project_name" {
  description = "Short name used for resource Name tags."
  type        = string
  default     = "review-dashboard"
}

variable "domain_name" {
  description = "Registered root domain (no trailing dot). Set only in terraform.tfvars (gitignored)."
  type        = string
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID for the root domain. Set only in terraform.tfvars (gitignored)."
  type        = string
}

variable "subdomain" {
  description = "Subdomain label for this app (e.g. review-insights)."
  type        = string
  default     = "review-insights"
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
  default     = "t3.small"
}

variable "app_dir" {
  description = "Absolute path on the instance where Docker Compose app files live."
  type        = string
  default     = "/opt/review-dashboard"
}
