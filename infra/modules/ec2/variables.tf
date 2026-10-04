variable "project_name" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "ami_id" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "security_group_ids" {
  type = list(string)
}

variable "instance_profile" {
  type = string
}

variable "fqdn" {
  description = "Public hostname served by Caddy (HTTPS)."
  type        = string
}

variable "app_dir" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
