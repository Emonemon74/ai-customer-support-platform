# Deploying to AWS

Single EC2 host running the production compose stack, managed Postgres on RDS,
Caddy terminating TLS. Sized for the AWS Free Tier (`t3.micro` + `db.t3.micro`);
`t3.small` is the safer default because the reranker and embedding models are
memory-hungry.

```
                 Let's Encrypt
                      │
   internet ──► Caddy (443) ──► frontend (nginx) ──► backend ──► RDS Postgres
                 (EC2 host)          │                 │
                                     └── /api ─────────┤── redis, chroma, worker
                                                        (all containers on the host)
```

## Prerequisites (local machine)

```bash
brew install awscli terraform            # or your package manager
aws configure                            # IAM user with programmatic access
ssh-keygen -t ed25519 -f ~/.ssh/aicsp -N ''
```

The IAM user needs EC2, RDS, VPC, EIP, IAM (roles and an OIDC provider), S3 and
SSM permissions (`AdministratorAccess` is simplest for a personal project).

## 1. Provision infrastructure

```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars
# edit: ssh_ingress_cidr (your IP /32 -> `curl -s ifconfig.me`), db_password, region
terraform init
terraform apply
```

Takes ~10 minutes (RDS is the slow part). Then:

```bash
terraform output                 # app_ip, site_address, db_endpoint
terraform output -raw database_url
```

## 2. Configure the app

```bash
cd ../..
cp deploy/.env.prod.example deploy/.env.prod
```

Fill in from the terraform outputs:
- `DATABASE_URL` — `terraform output -raw database_url`
- `SITE_ADDRESS` — `terraform output -raw site_address` (e.g. `13-234-56-78.nip.io`)
- `SITE_URL` — `https://<SITE_ADDRESS>`
- `ACME_EMAIL`, `GROQ_API_KEY`, `SECRET_KEY` — yours

`nip.io` resolves `<ip-with-dashes>.nip.io` to that IP, so Caddy can get a real
Let's Encrypt certificate without registering a domain.

## 3. Deploy

```bash
deploy/deploy.sh
```

Rsyncs the repo to the host, writes `.env`, and runs
`docker compose -f docker-compose.prod.yml up -d --build`. The first build takes
5–10 minutes on a small instance (swap is configured in user-data).

Visit `https://<SITE_ADDRESS>`. Redeploy after code changes with the same
command.

## Continuous deployment (no SSH)

[`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml) redeploys the
host whenever CI passes on `main` (or when run by hand from the Actions tab),
then smoke-tests `https://<SITE_ADDRESS>/health`.

How it works: the job assumes an AWS role through GitHub OIDC (no stored AWS
keys), uploads a `git archive` tarball to a private S3 bucket, and sends the
host a Systems Manager Run Command that downloads it, writes `.env` from SSM
Parameter Store and runs `docker compose up -d --build`
([`remote-deploy.sh`](remote-deploy.sh)). Port 22 is not involved, so
`ssh_ingress_cidr` can stay locked to your own IP. The role is trusted only
for this repository's `production` environment and can only upload releases and
run one command document on this one instance.

One-time setup after `terraform apply`:

```bash
# 1. Store the production .env where the host can read it (stays out of GitHub).
aws ssm put-parameter --name /aicsp/prod/env --type SecureString \
  --value file://deploy/.env.prod --overwrite

# 2. Print the values the workflow needs.
terraform -chdir=deploy/terraform output
```

3. In GitHub, create an environment named `production` (Settings →
   Environments; add yourself as a required reviewer if you want a manual
   gate), then add these **repository variables** (not secrets):

| Variable | From `terraform output` |
|---|---|
| `AWS_REGION` | the `region` you applied with |
| `AWS_DEPLOY_ROLE_ARN` | `github_deploy_role_arn` |
| `DEPLOY_INSTANCE_ID` | `instance_id` |
| `DEPLOY_BUCKET` | `releases_bucket` |
| `SITE_ADDRESS` | `site_address` |

To change a setting (for example `GLOBAL_DAILY_CHAT_LIMIT`), re-run step 1 and
re-run the workflow. If the account already has a GitHub OIDC provider, set
`github_oidc_provider_arn` in `terraform.tfvars` instead of creating a second
one. This workflow has not run yet: it needs a provisioned host.

## Operating

```bash
ssh -i ~/.ssh/aicsp ec2-user@$(terraform -chdir=deploy/terraform output -raw app_ip)
cd /opt/app
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml ps
```

## Costs & teardown

Free Tier: EC2 750h/mo `t3.micro`, RDS 750h/mo `db.t3.micro` + 20 GB — roughly
\$0 for the first 12 months, then ~\$15–20/mo (`t3.small` + RDS + EBS + EIP).

```bash
terraform -chdir=deploy/terraform destroy
```

## Notes / limitations

- Single host: no HA, and a redeploy has a few seconds of downtime while
  containers restart.
- ChromaDB and uploads live on the host's EBS volume (Docker named volumes).
  Snapshot the volume or `docker run --rm -v ...` to back them up.
- Path to cloud-native (ECS/Fargate + EFS + ALB + ElastiCache) is sketched in
  the root README; it's ~5x the cost and not warranted at this stage.
