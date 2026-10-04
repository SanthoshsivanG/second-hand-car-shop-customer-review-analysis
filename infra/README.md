# AWS infrastructure (`infra/`)

Simple portfolio hosting for the **review dashboard** only  
(frontend + backend + Postgres). Data preprocessing stays on your laptop.

HTTPS and DNS are automated: Route 53 points a subdomain at an Elastic IP; **Caddy** on the instance gets a Let’s Encrypt certificate.

---

## Big picture

```
                    Internet
                       |
                       |  HTTPS :443  (HTTP :80 for redirect / ACME)
                       v
              +------------------+
              |   Route 53 DNS   |   A record: <subdomain>.<your-domain>
              +--------+---------+
                       |
                       |  resolves to
                       v
              +------------------+
              |   Elastic IP     |
              +--------+---------+
                       |
                       v
         +-------------+--------------+
         |     EC2  t3.small          |
         |  (Amazon Linux 2023)       |
         |                            |
         |  +----------------------+  |
         |  | Caddy                |  |  TLS termination
         |  | reverse_proxy :3000  |  |
         |  +----------+-----------+  |
         |             |              |
         |             v              |
         |  +----------------------+  |
         |  | Docker Compose       |  |
         |  |                      |  |
         |  |  frontend :3000      |  |  nginx (UI + /api proxy)
         |  |       |              |  |
         |  |       v              |  |
         |  |  backend  :8000      |  |  FastAPI
         |  |       |              |  |
         |  |       v              |  |
         |  |  postgres           |  |  ideas + policy tables
         |  +----------------------+  |
         +-------------+--------------+
                       ^
                       |
              SSM Session Manager
              (no SSH required for v1)
```

**Not used (on purpose):** private subnets, NAT, ALB, WAF, ECS/EKS.

---

## Folder layout

```
infra/
├── main.tf                     # wires modules + provider
├── variables.tf                # inputs (region, domain, size, …)
├── terraform.tfvars.example    # copy → terraform.tfvars (gitignored)
├── terraform.tfvars            # YOUR secrets/domain — never commit
├── README.md
└── modules/
    ├── iam/                    # EC2 role + SSM instance profile
    ├── security_group/         # :80 and :443 only
    ├── ec2/                    # instance, EIP, user_data (Docker + Caddy)
    └── dns/                    # Route 53 A record → EIP
```

Root stays thin; each AWS “service concern” lives in its own module.

---

## What each module does

| Module | Creates | Role |
|--------|---------|------|
| `iam` | IAM role + instance profile | Lets the instance use **SSM** (shell without SSH) |
| `security_group` | One SG | Inbound **80/443** from the internet; all outbound |
| `ec2` | EC2 + Elastic IP | Runs Docker Compose + Caddy; bootstrap via `user_data` |
| `dns` | Route 53 `A` record | `<subdomain>.<domain>` → Elastic IP |

Default VPC / public subnet are discovered with data sources (no custom VPC).

---

## Traffic flow (request path)

```
Browser
  --HTTPS--> Caddy (:443)
               --HTTP--> frontend container (:3000)
                            |-- static React UI
                            '-- /api/* --> backend (:8000) --> Postgres
```

Caddy handles certificates. You do **not** upload certs or use ACM/ALB.

---

## Prerequisites

1. AWS CLI configured (`aws sts get-caller-identity` works)
2. Permission to use **EC2, IAM, EIP, Route 53** in your account  
   For AWS Projects accounts, deploy in the **project region** (`ap-southeast-2` here).  
   Tokyo (`ap-northeast-1`) is denied by the org `RegionFloor` SCP.
3. A Route 53 **hosted zone** for your registered domain
4. Terraform `>= 1.5`

Quick region check:

```bash
aws ec2 describe-vpcs --region ap-southeast-2   # should work
aws ec2 describe-vpcs --region ap-northeast-1   # SCP deny on Projects accounts
```

---

## Configure (local only)

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` (gitignored):

| Variable | Meaning |
|----------|---------|
| `aws_region` | `ap-southeast-2` (Sydney; required for AWS Projects RegionFloor SCP) |
| `domain_name` | your root domain |
| `hosted_zone_id` | from `aws route53 list-hosted-zones` |
| `subdomain` | e.g. `review-insights` |
| `instance_type` | default `t3.small` |

Hostname becomes: **`<subdomain>.<domain_name>`**

Never commit real domain / zone IDs / keys.

---

## Deploy (you run apply)

```bash
cd infra
terraform init
terraform plan
terraform apply          # only when you are ready
```

After apply:

1. Wait a few minutes for DNS + Caddy certificate
2. Open `https://<subdomain>.<domain_name>`
3. Upload app files + processed data (CSV/JSON) onto the instance
4. Put `GEMINI_API_KEY` in `/opt/review-dashboard/app/.env`
5. `docker compose up -d --build` in `/opt/review-dashboard`

### Connect without SSH (SSM)

```bash
aws ssm start-session --target "$(terraform output -raw instance_id)"
```

SSH can be added later if you want.

---

## Cost (rough)

| Piece | Notes |
|-------|--------|
| `t3.small` | Main cost (always-on) |
| EBS ~30 GB gp3 | Root volume |
| Elastic IP | Free while attached to a running instance |
| Route 53 hosted zone | Small monthly fee + queries |
| Domain registration | Yearly (separate from free tier) |

Stop or `terraform destroy` when you do not need the demo.

---

## Destroy

```bash
cd infra
terraform destroy
```

This removes the instance, EIP, SG, IAM profile pieces, and the subdomain record.  
It does **not** delete your registered domain or hosted zone.
