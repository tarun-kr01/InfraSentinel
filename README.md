# InfraSentinel

InfraSentinel is a small Python 3.11 tool for deterministic Terraform plan
review. It parses `terraform show -json` output, builds a NetworkX dependency
graph, computes downstream blast radius, evaluates safety policies, and can
read an Infracost JSON delta.

```bash
pip install .
infrasentinel scan --plan plan.json --config .infrasentinel.yaml
```

The command prints structured JSON and exits non-zero when a blocking policy
finding exists. Supported checks include wildcard IAM, internet-open security
groups (except 80/443), required `env`/`owner` tags on creates, public S3 ACLs,
unencrypted RDS/EBS, and destructive production changes. Optional provider
summarizers currently fall back to the deterministic template so no API key is
required.
