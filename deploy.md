# Deployment plan

> **⚠️ DRAFT** — this is a planning document, not yet implemented. Decisions
> and steps below are subject to change as we build things out.

## Goal

Deploy Picura on a Hetzner VPS. Docker-based, lightweight (no Dokku). Custom
domain `picura.org` (registered with a different company — no transfer needed,
just DNS records).

## Decisions so far

| Topic | Decision |
|---|---|
| Settings | Single `settings.py`, env-toggled (already in place) |
| Static files | **WhiteNoise** — Django serves static, baked into the image |
| Media files | **Hetzner Object Storage** (S3-compatible) via `django-storages` |
| Reverse proxy | **Caddy** — automatic HTTPS (Let's Encrypt), auto-renewal |
| Database | **Postgres in a container** + named volume; backups via `pg_dump` |
| Image build | **CI builds the image from the start**; box pulls, never builds |
| Registry | **GHCR**, image is **public** (no box-side auth needed) |
| Provisioning | **cloud-init** (lightweight, native to Hetzner); Ansible only if we outgrow one box |
| Deploy trigger | **Manual for now** (not automatic); push-button via CI later |

## Target architecture

```
                  picura.org (A/AAAA → VPS IP)
                            │
Internet ──► Caddy :80/:443 (auto-TLS, reverse proxy)
                            │  proxy_pass
                            ▼
                   web : gunicorn → Django :8000
                       │                    │
                       ▼                    ▼
              db : Postgres          Hetzner Object Storage
              (+ named volume)       (user-uploaded photos = media)
```

One VPS, one `docker compose` stack, three containers: `caddy`, `web`, `db`.

- **Caddy** is a pure reverse proxy: terminates TLS, forwards to gunicorn.
  Config is ~4 lines; cert is fetched/renewed automatically once DNS resolves.
- **Static** → WhiteNoise (in the app image). No shared volume with Caddy.
- **Media** → Hetzner Object Storage. Survives container/box rebuilds.
- **Postgres** → container + named volume. Can graduate to managed DB later.

### Build/deploy flow

```
GitHub push ─► GitHub Actions
                 1. test   (existing pytest job)
                 2. build  multi-stage image (vite build + uv + collectstatic)
                 3. push   → ghcr.io/marcaltmann/picura:<git-sha>  (+ :latest)
                 4. deploy MANUAL for now

VPS only holds:  compose.prod.yml   Caddyfile   .env
                 └─ docker compose pull && migrate && up -d
```

The VPS never holds application source — only `compose.prod.yml`, `Caddyfile`,
and the secret `.env`. The compose file references
`image: ghcr.io/marcaltmann/picura:latest`.

Image tagging: every build tagged with the **git SHA** (rollback handle) plus a
moving `:latest`. Roll back by pinning a previous SHA and `up -d`.

## Implementation slices

Following the project's vertical-slice + TDD convention. Slices 1–4 are pure
repo work and independently testable.

1. **gunicorn + production Dockerfile** — multi-stage (Vite build + `uv` install),
   runs `collectstatic`, non-root user.
2. **WhiteNoise for static** — middleware + compressed-manifest storage; test the
   storage backend in production mode.
3. **Media → Hetzner Object Storage** — `django-storages` S3 backend, env-toggled
   so dev stays on local disk; test the storage selection. Note: `django-imagekit`
   writes generated thumbnails to the same backend — decide whether its cache
   stays local or goes to the bucket.
4. **Production security settings** — `SECURE_*`, `CSRF_TRUSTED_ORIGINS`,
   `SECURE_PROXY_SSL_HEADER`, HSTS/secure cookies; gated on `not DEBUG`; tests.
5. **Production compose + Caddyfile** — `caddy` + `web` + `db`; prod `.env.example`.
6. **Provisioning + first deploy** (see below).
7. **CD pipeline** — extend Actions to build + push to GHCR; manual-trigger deploy
   job that SSHes and runs pull/migrate/up.
8. **Backups** (later) — scheduled `pg_dump`; object-storage lifecycle.

## Slice 6 — Provisioning + first deploy (detail)

### A. Provision the box (Hetzner Cloud console)
- Ubuntu 24.04 LTS, small shared-vCPU type (e.g. CX22: 2 vCPU / 4 GB), EU location.
- Attach SSH **public key** at creation (no password login).
- Note the **IPv4 and IPv6**.
- Optional: enable the **Hetzner Cloud Firewall** (network-level) allowing only
  22/80/443 — defense in depth alongside the on-box firewall.

### B. Point DNS (do early — propagation takes time)
At the registrar, for `picura.org`:
- **A** → IPv4
- **AAAA** → IPv6

Verify:
```bash
dig +short picura.org A
dig +short picura.org AAAA
```
Caddy can't obtain a cert until the name resolves to the box.

### C. Harden the server (via cloud-init, one-time)
- Create a non-root sudo user; log in as that user thereafter.
- `/etc/ssh/sshd_config`: disable root login and password auth (key-only).
- Firewall (`ufw`): allow 22/80/443, deny the rest.
- Enable `unattended-upgrades`.

Capture this as a committed cloud-init `user-data` file so rebuilding the box is
mechanical.

### D. Install Docker (via cloud-init)
- Docker Engine + Compose plugin from Docker's official apt repo.
- Add the user to the `docker` group.

### E. Put files + secrets on the box
The box holds **no source**, only:
1. `compose.prod.yml`, `Caddyfile`.
2. A production `.env` that is **never in git**, created on the box by hand the
   first time:
   - `DJANGO_ENV=production`
   - `SECRET_KEY=` (generate fresh: `python -c 'import secrets; print(secrets.token_urlsafe(64))'`)
   - `ALLOWED_HOSTS=picura.org`
   - `CSRF_TRUSTED_ORIGINS=https://picura.org`
   - DB credentials (strong password, not the dev default)
   - Hetzner Object Storage keys + bucket (bucket/keys created once in console)

### F. First deploy
With the public image already pushed to GHCR by CI:
```bash
docker compose -f compose.prod.yml pull
docker compose -f compose.prod.yml run --rm web python manage.py migrate
docker compose -f compose.prod.yml up -d
```
- `collectstatic` happens at **image build** (WhiteNoise has files baked in).
- `createsuperuser` once, interactively.
- Caddy requests the Let's Encrypt cert automatically on first boot.
- Migration strategy: decide entrypoint-runs-migrate vs. explicit
  `compose run migrate` (leaning explicit, controlled order).

### G. Smoke test
- `https://picura.org` loads with a valid cert (no warning).
- Static assets load (confirms WhiteNoise).
- Log in to admin; upload a photo (confirms object storage).
- `docker compose logs -f` is clean.

## Later: push-button deploy

Slice 7 automates only phase F. The deploy job (manual trigger / git tag) SSHes
to the box with a deploy key in GitHub secrets and runs pull → migrate → up.
Everything from slice 6 carries over unchanged; the only difference is who runs
the commands.

## Open questions / to decide later

- Migration execution: entrypoint vs. explicit one-off.
- `django-imagekit` cache location with remote storage.
- Backup destination and schedule (slice 8).
- When/whether to move from cloud-init to Ansible (only if we outgrow one box).
