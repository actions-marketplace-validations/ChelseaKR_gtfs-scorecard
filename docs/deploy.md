# Deploy runbook

Everything in this repo runs for free on GitHub Actions plus GitHub Pages, and
that is how the pilot runs today. This file is for the optional AWS pieces that
the rollout roadmap (`docs/roadmap.md`) needs as the registry grows: the
feed-health email digest, the self-serve forms, and a CDN in front of the
published JSON.

All the code and Terraform for these is written and tested. None of it is
required to keep the site live.

> **Current deployment status (maintainer's account).** The artifacts CDN (§1)
> and the feed-health digest (§2) are applied and live: `gtfsscorecard.org` is
> verified in SES and out of the sandbox, and the daily workflow mirrors
> artifacts to S3 and sends the digest. The self-serve submission form (§3) and
> the fan-out compute (§4) are written but not yet applied. The steps below are
> the from-scratch runbook, so they still read as operator work to do — follow
> them for a fork or a clean rebuild, and skip the stacks that are already up.

## Who this is for

One operator with:

- An AWS account and credentials configured locally (`aws configure` or SSO).
- `terraform` >= 1.5 and the `aws` CLI installed.
- Admin (or close) on the `ChelseaKR/gtfs-scorecard` repo, to set Actions
  variables and secrets.

The four stacks use **local** Terraform state by design, except `artifacts`,
which keeps state in S3. They are independent; apply only the ones you want.

## What turns each feature on

The daily workflow (`.github/workflows/scorecard.yml`) already has the deploy
steps. They are gated on repository **variables**, so they stay off until you
set them, and forks keep working with nothing set:

| Feature | Set this Actions variable | Also needs |
| --- | --- | --- |
| Mirror artifacts to the CDN bucket | `ARTIFACTS_BUCKET` | `AWS_ROLE_ARN` secret, `infra/artifacts` applied |
| Send the feed-health email digest | `SES_FROM` | a verified SES sender, `infra/alerts` applied |
| AWS region (optional) | `AWS_REGION` | defaults to `us-west-2` |

Set variables and secrets under **Settings → Secrets and variables → Actions**.

## 0. One-time: remote state bucket (only for `artifacts`)

`infra/artifacts/backend.tf` keeps Terraform state in an S3 bucket named
`gtfs-scorecard-tfstate-ckr`. Create it once before the first apply (skip if it
exists):

```sh
aws s3api create-bucket --bucket gtfs-scorecard-tfstate-ckr \
  --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2
aws s3api put-bucket-versioning --bucket gtfs-scorecard-tfstate-ckr \
  --versioning-configuration Status=Enabled
```

Use a different name if that one is taken, and update `backend.tf` to match.

## 1. Artifacts CDN (`infra/artifacts`)

Serves the published JSON from S3 + CloudFront instead of from Pages. Optional;
Pages carries the pilot fine.

```sh
cd infra/artifacts
cp terraform.tfvars.example terraform.tfvars   # edit bucket_name to be globally unique
terraform init
terraform apply
```

Then:

1. Read the outputs: `bucket_name` and `cdn_domain`.
2. Set the `ARTIFACTS_BUCKET` Actions variable to `bucket_name` and the
   `AWS_ROLE_ARN` secret to the OIDC role this stack creates. The next daily run
   mirrors `data/artifacts` to the bucket.
3. To point the web app at the CDN, set `window.SCORECARD_DATA_BASE` in
   `web/src/config.js` to `https://<cdn_domain>/data/artifacts`. The JSON
   contract is unchanged, so this is the only frontend change. Leaving it unset
   keeps the app reading from Pages.

## 2. Feed-health email digest (`infra/alerts` + SES)

This is the highest-value piece: it emails an agency before its feed silently
expires. The subscribe API (double opt-in) and the send path are already built;
the send is off until you verify a sender and set `SES_FROM`.

1. **Verify a sender in SES.** Verify the domain `gtfsscorecard.org` (DKIM) or a
   single address like `alerts@gtfsscorecard.org`. A new SES account starts in
   the sandbox, which only sends to verified addresses; request production
   access before sending to real agencies.
2. **Apply the subscribe API** (if not already live):
   ```sh
   cd infra/alerts
   terraform init
   terraform apply -var ses_from=alerts@gtfsscorecard.org
   ```
   The `subscribe_url` output is the endpoint the web form posts to; it is
   already wired into `web/src/config.js`.
3. **Turn on sending.** Set the `SES_FROM` Actions variable to your verified
   sender. The daily `collect` job then runs
   `scorecard notify --send --from "$SES_FROM"` for confirmed subscribers only.
4. **Dry run first.** Locally, `scorecard notify` (no `--send`) reports how many
   emails would go out and to whom, without sending. Always check this before
   enabling the variable.

## 3. Self-serve submission form (`infra/submit`)

Lets an agency add itself from `web/submit.html` without opening a pull request.

```sh
cd infra/submit
terraform init
terraform apply -var github_repo=ChelseaKR/gtfs-scorecard -var github_token=<PAT>
```

The `submit_url` output is the endpoint; wire it into the form's config the same
way the subscribe URL is wired. The `github_token` is a fine-grained PAT that can
open pull requests on this repo.

## 4. Fan-out compute (`infra/compute`, Year 2)

Only needed when the daily run outgrows the Actions matrix. EventBridge + SQS +
a container-image Lambda built from `pipeline/`. See
`docs/decisions/0003-fan-out-compute.md`; apply it the same way when the time
comes.

## Teardown

Each stack is `terraform destroy` from its directory. Unset the matching Actions
variable first so the daily run stops trying to use it.

## Cost

At a few thousand small JSON files refreshed daily, S3 and CloudFront sit in or
near the free tier, and SES is fractions of a cent per email. The
single-digit-dollars-a-month budget in `CLAUDE.md` holds well into Year 2; see
the roadmap's per-tier cost notes.
