terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  fqdn = "${var.subdomain}.${var.domain_name}"
  tags = {
    Project = var.project_name
    Managed = "terraform"
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
  tags         = local.tags
}

module "security_group" {
  source = "./modules/security_group"

  project_name = var.project_name
  vpc_id       = data.aws_vpc.default.id
  tags         = local.tags
}

module "ec2" {
  source = "./modules/ec2"

  project_name       = var.project_name
  instance_type      = var.instance_type
  ami_id             = data.aws_ami.al2023.id
  subnet_id          = data.aws_subnets.default.ids[0]
  security_group_ids = [module.security_group.security_group_id]
  instance_profile   = module.iam.instance_profile_name
  fqdn               = local.fqdn
  app_dir            = var.app_dir
  tags               = local.tags
}

module "dns" {
  source = "./modules/dns"

  hosted_zone_id = var.hosted_zone_id
  fqdn           = local.fqdn
  public_ip      = module.ec2.public_ip
}

output "instance_id" {
  description = "EC2 instance ID (use with AWS SSM Session Manager)."
  value       = module.ec2.instance_id
}

output "public_ip" {
  description = "Elastic IP attached to the instance."
  value       = module.ec2.public_ip
}

output "app_hostname" {
  description = "Hostname served by Caddy (prefix with https:// in the browser)."
  value       = local.fqdn
}
