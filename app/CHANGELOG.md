# Changelog

## Unreleased

- Add `infra/` Terraform (modular EC2 + SG + IAM/SSM + DNS + Caddy bootstrap); apply is manual.
- Default deploy region `ap-southeast-2` (AWS Projects RegionFloor SCP; Tokyo denied).
- Fix EC2 user_data: do not install conflicting `curl` on Amazon Linux 2023 (`curl-minimal`).
- Install Caddy from official binary (Cloudsmith RPM GPG fails on AL2023).
- Dashboard loads journey×satisfaction topics and filters bubble names by cell sentiment.
- Bubble chart: pad X/Y domains so edge bubbles are fully visible; show average stars with 1 decimal.
- Fix idea generation crash in Docker when resolving local `.env` paths (`IndexError: 1`).
- Add Postgres (`idea_policy`, `generated_ideas`) under `backend/postgres/` with `init.sql`.
- Store idea-generation policy in DB; edit via dashboard **Edit policy** or `GET/PUT /api/policy`.
- Persist each AI idea generation into `generated_ideas`.
- Fix backend crash in Docker: `config.py` no longer assumes a repo-root `parents[2]` path when running from `/app`.
