# Scout deployment

Scout targets Python 3.12 and Django 5.2 LTS. GitHub Actions builds the image,
publishes it to GHCR, and the server pulls that immutable artifact. Gunicorn is
available only through `127.0.0.1:8010`; the existing host nginx instance
handles public traffic.

## WSL development

The Scout checkout is `/home/scout/scout`.

    cd /home/scout/scout
    chmod +x scoutctl
    ./scoutctl init
    ./scoutctl setup

`setup` builds the image, applies MySQL development migrations, starts the
service, checks dependencies, compiles Python, checks Django, detects migration
drift, verifies the MySQL connection, and checks HTTP health. Automated tests
run only against GitHub Actions' disposable MySQL service.

Useful commands:

    ./scoutctl doctor
    ./scoutctl verify
    ./scoutctl logs
    ./scoutctl shell
    ./scoutctl createsuperuser

## Production preparation

1. Back up the existing Scout MySQL database and media.
2. Copy existing uploads to `/opt/scout/project/docker-data/media`.
3. Copy `.env.example` to `.env` and replace all placeholders.
4. Set the real Scout hostname and CSRF origin.
5. Add real database and integration credentials.
6. Allow host nginx to traverse the deployment home without exposing its
   contents: `chown scoutdeploy:www-data /opt/scout && chmod 750 /opt/scout`.
7. Run `./scoutctl preflight`.

This legacy repository has no registration migration history. Do not use
`migrate --run-syncdb` or generate production migrations until the existing
schema has been baselined and compared with the Django models.

## Image publishing

Pushes to `main` publish:

    ghcr.io/shanukarn11/scout-site:<commit-sha>
    ghcr.io/shanukarn11/scout-site:latest

For deterministic production rollouts, set `SCOUT_IMAGE` to the commit-specific
tag. The server must authenticate to GHCR if the package is private.

## Production deployment

    cd /opt/scout/project
    chmod +x scoutctl
    ./scoutctl preflight
    ./scoutctl deploy

`deploy`:

1. validates tools, `.env`, and Compose;
2. acquires a deployment lock;
3. pulls and validates the configured image;
4. creates and verifies a compressed MySQL backup;
5. records the currently running image;
6. applies migrations and collects static files;
7. recreates the container;
8. waits for HTTP health;
9. automatically returns to the prior image when health fails.

Database migrations are not automatically reversed during image rollback.

Operational commands:

    ./scoutctl status
    ./scoutctl health
    ./scoutctl prod-logs
    ./scoutctl backup
    ./scoutctl rollback

Backups are stored under `backups/` with SHA-256 checksum files. Move them to
durable off-server storage according to the server backup policy.

## nginx

Adapt `deploy/nginx.conf.example`, install it beside the IKF virtual host, then:

    sudo nginx -t
    sudo systemctl reload nginx

Configure TLS and verify the home page, admin, registration flow, static files,
uploads, database access, and payment configuration.
