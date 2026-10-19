# REG.RU deployment

**CI/CD:** актуальная схема с `current`, отдельными релизами и общими загрузками описана в [ci-cd.md](ci-cd.md). Команды ниже описывают исходную установку до первого автоматического релиза.

Target: `colibrilook.ru`, REG.RU shared hosting, SSH `u3688705@37.140.192.63`.

- Application: `/var/www/u3688705/data/apps/colibri`.
- Python: application `.venv`, based on `/opt/python/python-3.14/bin/python3`.
- Public directory: `/var/www/u3688705/data/www/colibrilook.ru`.
- Private environment: application `production.json`, mode `600`, outside the public directory. Set `DJANGO_ENV_FILE` to its absolute path before management commands. Never copy this file to the repository or public directory.
- Database: MySQL, selected with `DATABASE_ENGINE=mysql`; connection parameters come from the private environment.
- Dependencies: `requirements-hosting.txt` adds the MySQL driver to the local requirements.
- Passenger entry point and `.htaccess` source: `deploy/passenger_wsgi.py`, `deploy/htaccess`.
- Public `static` and `media` symlinks point to application `staticfiles` and `media` respectively. No project code, database exports, or credentials belong in the public directory.
- The hosting nginx configuration overwrites `X-Forwarded-Proto` and forwards to Apache on loopback. `DJANGO_TRUST_PROXY_SSL=1` is enabled for this verified configuration.

Management commands:

```sh
cd /var/www/u3688705/data/apps/colibri
export DJANGO_ENV_FILE=/var/www/u3688705/data/apps/colibri/production.json
.venv/bin/python manage.py check --deploy
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
# Restart after updating code or environment:
touch /var/www/u3688705/data/www/colibrilook.ru/.restart-app
```

Before future updates, back up MySQL and the `media` directory. Do not reload the initial content fixture or rerun `seed_content` over editorial changes. The original hosting placeholder is preserved in the account's private `backups` directory.

Application installed on 2026-10-19: Python 3.14.6, Django 5.2.18, MySQL 8.0.25, mysqlclient 2.3.0. All migrations applied; 71 records imported, including 20 products, 6 looks and 2 stores; 299 static files collected. Existing administrator account transferred. `check --deploy` reports no issues. Direct server checks pass for 8 page/filter routes, 35 assets and 6 private paths (denied). Public DNS currently returns NXDOMAIN and the hosting certificate is self-signed. Public launch requires domain delegation/DNS and a valid certificate; HTTPS verification must remain enabled for normal use.

REG.RU prohibits Passenger directives in `.htaccess`; Python and Passenger are selected in the hosting panel. The startup file adds the matching Python 3.14 virtual environment site-packages to the import path. No development server is used.

## Verification and pending DNS / SSL

- All 26 published product/look detail pages return 200 using MySQL. Cyrillic search and punctuation queries work; authenticated admin dashboard, list and product creation form return 200.
- Local suite: 30 tests passed; no missing migrations. Private production JSON loading, missing-secret rejection and MySQL/proxy configuration checked.
- Uploaded archive SHA-256 matched local `c14ac294e33a3777e4e591dbf55fcb6153373799089058d94a7a60de622827dd`.
- The domain was registered on 2026-10-19, with `ns1.hosting.reg.ru` / `ns2.hosting.reg.ru`. Hosting DNS records for apex/www point to the correct IPv4/IPv6 addresses. Public resolvers still return NXDOMAIN.
- A free Let’s Encrypt request `colibrilook.ru_le1` was submitted through the authenticated hosting panel. The initial validation failed with NXDOMAIN for A/AAAA. The panel scheduled an automatic retry for 2026-10-19 14:48 server time. A trusted certificate has **not** yet been verified.
- Once DNS propagates, check the certificate request in **SSL certificates → Let’s Encrypt log**. Confirm both `https://colibrilook.ru/` and `https://www.colibrilook.ru/` with normal TLS validation before declaring public launch complete.
- HTTP checks used a direct-IP DNS override and bypassed self-signed certificate validation for diagnostics only; this is not proof of a working public HTTPS connection. Evidence: `.qa/deployment/http-results.json`.
- Initial transfer archive and fixture are in private `backups/colibri-20261019/` on the hosting account (mode 600).
