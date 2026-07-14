---
profile_id: django-5.2-lts
profile_version: 1.0
compatibility: Django >=5.2,<5.3
validated_django: 5.2.16
validated_playwright: 1.61.0
supported_python: 3.12 | 3.13 | 3.14
last_validated: 2026-07-12
maintainer: WebBuilder project
---

# Django 5.2 LTS Golden Profile

Maintained full-stack reference profile for data-backed operational applications with server-rendered workflows.

## Maintenance Basis

- [Django 5.2 release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/)
- [Playwright Python installation](https://playwright.dev/python/docs/intro)

## Selection Criteria

Select this profile when the project is:

- a data-backed operational application
- server-rendered workflows with forms and navigation
- using built-in authentication, admin, ORM, and migrations
- a team accepting a Python stack

## Rejection Criteria

Reject this profile when the project is:

- a static-only site with no server logic
- a browser-only SPA requirement with no server rendering
- a non-Python existing stack that cannot adopt Django
- requiring a mandatory edge runtime

## Capability Defaults

```yaml
ui: required
database: required
authentication: required
rbac: not_applicable
audit: not_applicable
docker: not_applicable
accessibility: required
performance: baseline
security: baseline
```

## Verification Commands

```text
python -m pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py seed_reference
python manage.py check --deploy
python manage.py test
python manage.py runserver 127.0.0.1:8000
python -m unittest e2e.test_primary_flow -v
```

## Expected Local-Only Security Warnings

`python manage.py check --deploy` reports the following warnings for the local development reference application. These are expected and not suppressed because the reference runs locally only; production deployments must resolve all of them.

- `security.W004` — SECURE_HSTS_SECONDS not set
- `security.W008` — SECURE_SSL_REDIRECT not set
- `security.W009` — SECRET_KEY is the insecure development default
- `security.W012` — SESSION_COOKIE_SECURE not set
- `security.W016` — CSRF_COOKIE_SECURE not set
- `security.W018` — DEBUG is True

## Upgrade Policy

Dependency pins are refreshed only through a PR that reruns the maintained example. The profile records the last validated pins and compatibility range; pins are not auto-bumped.

## Deprecation Policy

A profile becomes deprecated when its supported Django line is outside security support or the example cannot pass supported-host CI.
