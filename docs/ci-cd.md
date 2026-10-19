# GitHub Actions → REG.RU

Repository: https://github.com/kozarezov/colibrilook
Workflow: `.github/workflows/deploy.yml`.

## Trigger and checks

A push to `main` starts checks and, if they pass, automatic deployment. Pull requests to `main` run checks only. A manual Actions run is also available for `main`.

Checks use Python 3.14, run Django tests with SQLite and a disposable MySQL 8.0 service, verify missing migrations and run deployment safety tests. The production MySQL database is never used for the test suite.

Deployment requires the `production` environment, restricted to `main`. There is no manual approval gate. Only one production deployment runs at a time, and an active deployment is not cancelled by a newer push. A stale commit is rejected before SSH access if `main` has advanced.

## Secrets and server access

The following environment secrets are configured in GitHub (not in the repository):

- `DEPLOY_SSH_KEY`: dedicated Ed25519 private key.
- `DEPLOY_KNOWN_HOSTS`: pinned host key for `37.140.192.63`; fingerprint explicitly confirmed by the owner: `SHA256:LdeZyYBXRfRuHgbRPYhwWCgN7taGNFux7vA7dcVKJEQ`.

The SSH public key is installed with `restrict` and a forced command:

```
/opt/python/python-3.14/bin/python3 /var/www/u3688705/data/apps/colibri/deploy/receive.py
```

It accepts `deploy <40-character commit SHA> <numeric run ID>-<attempt>` or `check` with the same arguments, with the archive on stdin. `check` prepares the candidate and prints the migration plan, but never applies migrations, creates backups, or switches the site. The only additional command is `manifest`: it returns JSON containing paths and SHA-256 hashes of public source files in the current release's `static/` directory. It cannot read arbitrary paths or private configuration. Interactive shells, SCP, forwarding and arbitrary commands are unavailable with this key. The trusted receiver/controller (`assets.py`, `release.py`, `receive.py`) live in the shared application `deploy/` directory and are installed through the administrator connection. Install `assets.py` before updating its consumers. Changes to these controller files require a deliberate administrator update; an uploaded release cannot replace the controller automatically.

`production.json` and database credentials stay on the server. SSH host verification is mandatory; do not use `StrictHostKeyChecking=no` or `curl -k` in the workflow.

## Deployment sequence

1. Fetch the server's static manifest over authenticated SSH. Build an allowlisted archive of application code, requirements, a complete `STATIC_MANIFEST.json`, and only new or changed static assets. Local credentials, `.env`, database files, uploads and QA files are excluded.
2. Stream the archive over SSH to the restricted receiver. Validate its paths, types, size and revision. Transfer progress and server preparation stages appear in the Actions log.
3. Prepare `apps/colibri/releases/<SHA>-<run>-<attempt>` with its own Python environment. Copy omitted assets locally from the current release and verify every resulting asset against its expected SHA-256. Only manifest-listed files are included, so removed assets stay removed. Copies are independent files, preserving rollback isolation. Missing, corrupt or stale assets abort preparation before database migrations or activation. The running release continues serving requests.
4. Install dependencies, run production checks, check migrations and collect static files.
5. Create a compressed MySQL snapshot and a media archive in `apps/colibri/backups/<release>/` before migrations.
6. Run migrations. Never run `seed_content`, `loaddata` or replace the production database.
7. Atomically switch `current` and the public `static` symlink, then restart Passenger. Media stays in `apps/colibri/media`; the private environment stays in `apps/colibri/production.json`.
8. Check the running revision, database connection, home, catalog, admin login and CSS via Apache's loopback address. On activation failure, restore previous code/static symlinks and restart.
CSS and JS URLs include the running revision, so browsers fetch the updated files after deployment.

9. Verify public HTTPS and the deployed revision from GitHub. DNS/certificate errors fail this external check without silently disabling TLS or undoing a working application deployment.

Three recent release directories and three backup directories are retained after successful deployments. The legacy first installation and its original backups are retained separately. Failed attempts may leave diagnostics in `incoming/` and incomplete release directories; inspect these before cleanup.

### Incremental transfer and recovery

The first measured Actions run spent 9m25s in upload/activation while sending an 83.7 MB archive. Dependencies and checks accounted for a small part of that step. With the same 172 public static files already on the server, the updated builder produced a 47 KB archive locally, about 1,800 times smaller. This is an artifact-size measurement, not a measured end-to-end GitHub deployment time. Uploading new videos still requires transferring their full compressed files; static assets are not recompressed or reduced in quality.

If an operator changes the active release between manifest retrieval and preparation, mismatched reused assets fail safely. Rerun the latest workflow to fetch a fresh manifest. A full standalone artifact can be built by omitting `--base-manifest`:

```sh
python deploy/package.py "$(git rev-parse HEAD)" /tmp/colibri-release.tar.gz
```

The updated controller also accepts legacy full archives without a manifest, so the previously pushed workflow remains compatible while this optimization awaits a push. The manifest itself is not cached between workflow runs. Uploads created in the Django admin remain in shared `media/` and are unaffected.

## Migration limitations

MySQL schema migrations are not transactional. Automatic code rollback does **not** restore the database. Keep migrations compatible with the old and new application versions; split destructive changes across deployments. If a migration fails, the current code remains selected, but the database may be partially changed. Inspect the Actions log and restore from the private backup or apply a forward fix through the administrator connection. Automatic database restore could erase new editorial changes and is deliberately not implemented.

For ordinary code rollback, use the administrator connection to restore `current` and public `static` to a known compatible release, then create `.restart-app` in the domain directory. After the first successful deployment, management commands must use the current release:

```sh
export DJANGO_ENV_FILE=/var/www/u3688705/data/apps/colibri/production.json
export DJANGO_MEDIA_ROOT=/var/www/u3688705/data/apps/colibri/media
cd /var/www/u3688705/data/apps/colibri/current
.venv/bin/python manage.py check --deploy
```

## Activation

GitHub environment, secrets and server receiver can be prepared before the repository has commits. The workflow itself becomes active only after the project files, including `.github/workflows/deploy.yml`, are committed and pushed to `main`. No push is performed as part of setup without the owner's explicit command.

Public DNS and a valid certificate must be working for the final HTTPS check to pass. At the time CI/CD was prepared, public DNS was still propagating after domain registration.

## Setup verification — 2026-10-19

- `origin` points to `https://github.com/kozarezov/colibrilook.git`; no commits or push were made.
- GitHub Actions enabled; environment `production` restricted to `main`; both environment secrets installed and read back by name.
- Dedicated SSH key authenticated with the confirmed host key and rejected an arbitrary `id` command.
- The same key streamed the full release in `check` mode. Python 3.14 dependencies installed, `check --deploy` passed, no missing migrations, 299 static files collected, migration plan empty. Candidate removed afterward; production was not switched.
- MySQL backup command was separately executed and its gzip output validated (private `apps/colibri/backups/ci-preflight/database.sql.gz`).
- Local checks: 33 Django tests, 12 deployment tests, Python compilation and actionlint 1.7.12 passed. Rollback tests cover current/static links and the Passenger startup file.
- The GitHub-hosted workflow and MySQL CI service have not yet run because the repository has no pushed files. The first owner-authorized push to `main` activates them.
- A real production test deployment was not performed: automatic approval review rejected migration/application switching without separate approval. The preparation-only check above was used instead.

## Incremental deployment update — 2026-10-19

- Since the initial setup, the owner's push activated GitHub Actions. Run `39250953206` passed tests and installed commit `d749234f8074d08fddbe91e3238b92af79f36fc1`. Only the final public HTTPS check failed while DNS/SSL were unavailable.
- Added incremental static transfers and progress reporting; preserved backups, migration checks, revision health checks and rollback behavior.
- Installed the three updated trusted controller files through the hosting panel's authenticated HTTPS file manager, because local SSH connections stalled during banner exchange. Read every file back and verified exact content. Previous `release.py` and `receive.py` are saved beside them with suffix `.before-incremental-20261019`. No application activation or migrations were performed during this update.
- Verification: 22 deployment tests and 33 Django tests passed; actionlint, Django checks, missing-migration check and Python compilation passed. Tests cover changed/new/deleted assets, missing or corrupt base files, manifest traversal, symlinks, legacy archives and restricted manifest access.
- An end-to-end incremental check on the server and GitHub timing remain unverified because SSH was unavailable. The GitHub workflow changes are local and have not been pushed; they become active after the owner pushes them to `main`.
