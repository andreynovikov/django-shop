# Server setup

The [Ansible playbook](ansible/site.yml) configures the production server and backup host. It installs packages,
creates users, and manages nginx, service units, timers and log rotation. PostgreSQL, application checkouts in
`/www`, TLS files and application secrets are provisioned separately. Start with the [Ansible runbook](ansible/README.md)
for inventory setup and first-run instructions. The manual steps below also serve as a reference for the resulting setup.

Historically server is run under latest Debian Stable.

The following packages are required:

```sh
apt install sudo
apt install exim4
apt install rsync
apt install python3
apt install postgresql-client
apt install nginx
apt install libnginx-mod-http-brotli-filter
apt install uwsgi
apt install uwsgi-plugin-python3
apt install memcached
apt install redis-server
apt install certbot
apt install git
apt install curl acl systemd-timesyncd
```

The following packages are required for building python packages:

```sh
apt install build-essential
apt install python3-dev
apt install libmemcached-dev
apt install libpq-dev
apt install libjpeg-dev
apt install tidy
```

Python packages are installed with uv, which Debian does not package:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh
```

The following packages are optional:

```sh
apt install less
apt install emacs-nox
apt install bind9-dnsutils
apt install htop
apt install apache2-utils
```

Install Docker (<https://docs.docker.com/engine/install/debian/#install-using-the-repository>)

Create users in this particular order (to preserve uids):

```sh
adduser andrey
adduser nikolays
adduser maria
adduser egor
```

Add users `andrey` and `nikolays` to `adm` group, which reads the logs in `/var/log`, nginx's among them.
Add user `andrey` to `docker` group.
Add users `andrey` and `nikolays` to `sudo` and `www-data` groups.
Add users `maria` and `egor` to `www-data` group.

Setup correct timezone:

```sh
timedatectl set-timezone Europe/Moscow
```

Enable time synchronization. Ansible writes `/etc/systemd/timesyncd.conf.d/ntp.conf`:

```ini
[Time]
NTP=ru.pool.ntp.org
```

then restart time service:

```sh
systemctl restart systemd-timesyncd
timedatectl set-ntp true
```

Reconfigure Exim for internet mode to be able to send mails:

```sh
dpkg-reconfigure exim4-config
```

Increase memcached limits in `/etc/memcached.conf` file:

```
-m 256
```

## Service user

uWSGI, Celery and the backups run as the system user `sworld`. It has no password, shell, home or sudo, and the
code of the sites is read-only for it, so a hole in the app gives nobody a login or the code:

```sh
adduser --system --group --home /nonexistent --no-create-home sworld
```

The services run with the group `sworld` as well, which alone can read the secrets. They are kept out of
`www-data`, because people share directories through that group, and some of them hold what the deploys run, such as
the `docker-compose.yaml` of a frontend. nginx reaches the uWSGI sockets through the group `www-data` of the socket
units, and reads the uploads and static files, which everyone may read. [Environment setup](#environment-setup) lists
the directories the user writes.

## ssh

Create `/etc/ssh/sshd_config.d/10-server.conf`. sshd keeps the first value it reads of each option, and the files
of `sshd_config.d` come first, in the order of their names. Cloud images have `50-cloud-init.conf` with
`PasswordAuthentication yes`, so this file must sort before it:

```
PermitRootLogin no
PasswordAuthentication no
X11Forwarding no
AllowUsers andrey nikolays maria egor deploy
ClientAliveInterval 60
ClientAliveCountMax 8
```

`PasswordAuthentication` covers only the `password` method of ssh, which cannot ask for an OTP code. Logins with a
password go through `keyboard-interactive`, which asks for the password and the OTP code, see
[Two factor authentication](#two-factor-authentication). Ansible builds `AllowUsers` from `server_users` and
`server_ssh_extra_users`, which includes the frontend deployment account `deploy` by default.

## Two factor authentication

Install required package:

```sh
apt install libpam-google-authenticator
```

Execute `google-authenticator -t -d -f -r 3 -R 30 -W` for every interactive user to generate OTP codes.

Add the following line to the bottom of the `/etc/pam.d/sshd`:

```
auth required pam_google_authenticator.so
```

Enable keyboard-interactive logins, formerly called challenge response, in `/etc/ssh/sshd_config.d/two_factor.conf`:

```
KbdInteractiveAuthentication yes
```

`journalctl -u ssh | grep Accepted` shows how users log in: `publickey`, or `keyboard-interactive/pam` for a
password with an OTP code.

## Firewall

Only ssh, HTTP, HTTPS and HTTP/3 are open, and the hosting's Zabbix servers may reach the agent. Everything else, such
as Prometheus and node-exporter, is reachable from the server itself only. Skip this section where the hosting's
firewall allows the same and nothing else. `/etc/nftables.conf`:

```
#!/usr/sbin/nft -f
# Only the table "host" is replaced on reload. Docker keeps its own tables, which "flush ruleset" would delete.
table inet host
delete table inet host

table inet host {
    chain input {
        type filter hook input priority filter; policy drop;
        ct state established,related accept
        ct state invalid drop
        iif lo accept
        iifname "docker0" accept
        meta l4proto { icmp, ipv6-icmp } accept
        udp dport { 68, 546 } accept
        tcp dport { 22, 80, 443 } accept
        udp dport { 443 } accept
        ip saddr { 92.53.116.12, 92.53.116.111, 92.53.116.119 } tcp dport 10050 accept
    }
}
```

Debian's `nftables.service` runs `nft flush ruleset` when it stops or restarts, which deletes Docker's rules too and
cuts the containers off the network. Make it remove only this table, in
`/etc/systemd/system/nftables.service.d/docker.conf`:

```ini
[Service]
ExecStop=
ExecStop=-/usr/sbin/nft delete table inet host
```

Keep an ssh session open, then:

```sh
systemctl daemon-reload
systemctl enable --now nftables
```

After changing the rules, apply them with `systemctl reload nftables`.

This firewall does not cover the ports Docker publishes. Docker forwards them to the container before the `input`
chain sees them, so a container published as `-p 9324:8080` is open to everyone. Publish on the loopback only, as
the frontends do: `127.0.0.1:9324:8080`.

# Nginx setup

The `nginx` tag installs the [bundled `nginx.conf`, site files and shared includes](ansible/roles/server/files/nginx/).
It creates `/var/cache/nginx`, enables the 11 sites listed in `server_nginx_sites_enabled`, and removes Debian's
`sites-enabled/default` link in favor of the bundled `default.conf`. To retire a site, remove it from the enabled
list and add it to `server_nginx_sites_disabled`. Other links are left alone.

Before applying the role, provision each site's TLS certificate and key at the paths in its server blocks. Install
`/etc/nginx/htpasswd` with owner `root`, group `www-data` and mode `0640`. The bundled `basic_auth` include uses
that file. Keep the TLS files and password hashes outside git.

From `deploy/ansible`, preview the nginx changes and then apply them together with log rotation:

```sh
ansible-playbook -i inventory.yml site.yml --limit server.example.ru -K --tags nginx --check --diff
ansible-playbook -i inventory.yml site.yml --limit server.example.ru -K --tags nginx,logrotate
```

Use the production host from your inventory in place of `server.example.ru`. During apply, Ansible runs `nginx -t`
with the installed files before reloading nginx. Changed nginx files get timestamped backups. Review the
[nginx runbook](ansible/README.md#nginx-sites) for first-run and recovery steps.

Site logs live under `/var/log/nginx`, with filenames based on the site:

```nginx
access_log   /var/log/nginx/www.sewing-world.ru_access.log upstream;
access_log   /var/log/nginx/www.sewing-world.ru_5xx.log errored if=$errored;
error_log    /var/log/nginx/www.sewing-world.ru_error.log;
```

nginx opens its logs as root, and on reopen gives them to `www-data`. Whoever can write the directory of a log can
replace the log with a symbolic link, and nginx then writes to the file it points to as root (CVE-2016-1247). Only
root can write `/var/log/nginx`, while `/www/<site>/logs` belongs to the [service user](#service-user). Debian's
`/etc/logrotate.d/nginx` rotates `/var/log/nginx/*.log` and keeps 14 days. The files belong to the group `adm`.
The legacy redirect log uses a `.jsonl` extension and has a [separate rotation rule](#log-rotation).

The bundled `nginx.conf` sets the worker limits, shared TLS session cache, upstream log formats, gzip and Brotli
compression, and the `next_image` cache. If configuring a server manually, install `libnginx-mod-http-brotli-filter`
and create `/var/cache/nginx` before checking the configuration with `nginx -t`.

## Storefront outage pages

Each storefront deployment, including stage, provides `unavailable.html` in its own `.docker/public/` directory.
nginx serves it internally for 502, 503 and 504 responses from the storefront proxy. Clients receive HTTP 503
with `Retry-After: 120` and `Cache-Control: no-store`. If the file is missing, nginx still returns 503. Keep the
page self-contained so it can render while the container is down. Next.js handles storefront 404 responses.

## Media files

Content admins upload the files that HTML text links to (images, videos, documents) in the admin's file manager,
"Швейный Мир › Файлы" ([django-admin-filemanager](https://github.com/andreynovikov/django-admin-filemanager)), and not over FTP. The files go into the site's `media/`, which the
[service user](#service-user) writes, so FTP can be turned off once nobody uses it.

- The bundled admin site sets `client_max_body_size 10M`. For larger uploads, adjust the limit in its site file
  and apply the `nginx` tag.
- The main and API sites set `expires 14d` on `/media/`. This works for files with unique URLs. If a file is
  replaced at the same URL, clients can keep using a cached copy. The production storefronts also cache successful
  `/_next/image` responses in `next_image` for up to 30 days.

# TLS certificates

certbot gets the certificates of the sites from Let's Encrypt and renews them. It proves a domain through the site
directory: it puts the challenge into `.well-known/acme-challenge/` there, and the `location /.well-known/` of the
site's nginx server serves it. `certbot.timer` checks the certificates twice a day and renews those that expire
within 30 days. The `certbot` tag enables the timer and installs
`/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh`, so that nginx serves a renewed certificate:

```sh
#!/bin/bash
systemctl try-reload-or-restart nginx
```

Moving to a new server, copy all of `/etc/letsencrypt`. `tar` keeps the links from `live/` to `archive/`, and the
settings in `renewal/` keep working while the sites stay in the same directories:

```sh
sudo tar -C /etc -czf letsencrypt.tgz letsencrypt    # on the old server
sudo tar -C /etc -xzf letsencrypt.tgz                # on the new one
```

A certificate for a new site:

```sh
certbot certonly --webroot -w /www/janome.club -d janome.club -d www.janome.club
```

Let's Encrypt asks over HTTP and follows the redirect to HTTPS, so on renewal the site's HTTPS server answers. A new
site has no HTTPS server yet. Until it gets its certificate, let its port 80 server answer, with `return 301` moved
into `location /`:

```nginx
location /.well-known/acme-challenge/ {
  root /www/janome.club;
}
```

# PostgreSql setup\*

- currently we use separate postgresql server, so this step should be skipped

Create necessary roles and databases:

```sql
CREATE ROLE andrey SUPERUSER LOGIN;
CREATE ROLE nikolays SUPERUSER LOGIN;
CREATE ROLE sworld LOGIN;
CREATE DATABASE sworld OWNER andrey;
CREATE DATABASE sworld_dev OWNER andrey;
```

Permit database login without password to `sworld` in `/etc/postgresql/*.*/main/pg_hba.conf`:

```
local   all             sworld                                  trust
```

Import data from backup:

```sh
cat sworld.db | psql sworld
```

# UWSGI setup

Create `/etc/systemd/system/uwsgi@.socket`:

```ini
[Unit]
Description=Socket for uWSGI app %i

[Socket]
ListenStream=/run/uwsgi/%i.socket
SocketUser=sworld
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
```

Create `/etc/systemd/system/uwsgi@.service`:

```ini
[Unit]
Description=%i uWSGI app
After=syslog.target

[Service]
ExecStart=/usr/bin/uwsgi \
        --ini /etc/uwsgi/apps-available/%i.ini \
        --socket /run/uwsgi/%i.socket
User=sworld
Group=sworld
Restart=on-failure
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
```

`/etc/tmpfiles.d/uwsgi.conf` creates `/run/uwsgi` for an app that is started without its socket unit and binds
the socket itself. Such a socket belongs to the group `sworld`, and nginx cannot connect to it, so start every app
through its socket unit:

```
d /run/uwsgi 0755 sworld www-data -
```

Create an ini file in `/etc/uwsgi/apps-available` for each app: `prod` and `admin` of `www.sewing-world.ru`,
and `dev` of `dev.sigalev.ru`. **Do not** set any links in `apps-enabled`.

Typical application setup (`prod.ini`) looks as follows:

```ini
[uwsgi]
master = true
plugins = python3,logfile
chdir = /www/www.sewing-world.ru
virtualenv = /www/www.sewing-world.ru/.venv
module = sewingworld.wsgi:application
need-app = true
single-interpreter = true
lazy-apps = true
processes = 6
threads = 4
thunder-lock = true
buffer-size = 8192
uid = sworld
gid = sworld
chmod-socket = 660
env = PYTHONIOENCODING=UTF-8
harakiri = 60
vacuum = true
max-requests = 5000
reload-on-rss = 600
touch-chain-reload = /www/www.sewing-world.ru/.touch_reload
logger = file:/www/www.sewing-world.ru/logs/uwsgi_error.log
log-date = true
disable-logging = true
log-5xx = true
log-slow = 2000
stats = 127.0.0.1:9191
stats-http = true
```

`touch .touch_reload` in the site directory reloads the workers one by one, which needs `lazy-apps`. With
`need-app`, uWSGI stops when Django cannot be loaded, also on such a reload, and systemd starts it again until the
code loads. The API runs mostly Python, which a process runs on one core at a time, so `prod` has 6 processes of 4
threads rather than 3 of 8. uWSGI logs only failed requests and those slower than 2 seconds, nginx logs them all.
Keep `harakiri` a little shorter than nginx's `uwsgi_read_timeout`. The bundled nginx configuration waits 65 s for
`prod` and `dev`, which have a 60 s worker limit. The admin vhost waits 310 s for `admin`, which has a 300 s limit.

The admin site (`admin.ini`) is the same with `env = ADMIN=True`, `processes = 2`, `harakiri = 300` for exports and
labels, and without `stats`, and it logs to `admin_uwsgi_error.log`. `dev.ini` has `processes = 1` and
`threads = 2`. Reload it after a pull with `touch /www/dev.sigalev.ru/.touch_reload`.

Each application should be:

```sh
systemctl enable uwsgi@app.socket
systemctl start uwsgi@app.socket
systemctl enable uwsgi@app
systemctl start uwsgi@app
```

where `app` is the name of the uwsgi configuration file. Start it once its site is deployed, see
[Environment setup](#environment-setup).

# Celery setup

`/etc/systemd/system/celery@.service`

```ini
[Unit]
Description=Celery worker for %I
Wants=redis-server.service
After=network.target redis-server.service

[Service]
User=sworld
Group=sworld
Type=forking
EnvironmentFile=-/etc/celery/%i_worker
ExecStart=/bin/sh -c "$$VIRTUALENV/bin/celery multi start $CELERYD_NODES $CELERYD_OPTS"
ExecStop=/bin/sh -c "$$VIRTUALENV/bin/celery multi stopwait $CELERYD_NODES"
ExecReload=/bin/sh -c "$$VIRTUALENV/bin/celery multi restart $CELERYD_NODES $CELERYD_OPTS"

[Install]
WantedBy=multi-user.target
```

Each node of `celery multi` keeps its own pid file, by default `/run/celery/<node>.pid`. A `--pidfile` without
`%n` would give all the nodes one file, and only the first of them would start.

`/etc/systemd/system/celery_beat@.service`:

```ini
[Unit]
Description=Celery beat for %I
Wants=redis-server.service
After=network.target redis-server.service

[Service]
User=sworld
Group=sworld
Type=forking
EnvironmentFile=-/etc/celery/%I_beat
PIDFile=/run/celery/%I_beat.pid
ExecStart=/bin/sh -c "$$VIRTUALENV/bin/celery $CELERYD_OPTS beat --detach --pidfile=/run/celery/%I_beat.pid $CELERYD_BEAT_OPTS"

[Install]
WantedBy=multi-user.target
```

systemd stops beat with SIGTERM to the process in `PIDFile`, so the unit needs no `ExecStop`.

The units read their settings from `/etc/celery`. `prod_worker` starts a node for each queue:

```sh
VIRTUALENV=/www/www.sewing-world.ru/.venv
CELERYD_NODES=priority import integrations revalidation default
CELERYD_OPTS=-Q:priority priority -Q:import import -Q:integrations integrations -Q:revalidation revalidation -Q:default default,celery --workdir=/www/www.sewing-world.ru --app=sewingworld --logfile=/www/www.sewing-world.ru/logs/celery_%n.log --loglevel=INFO --verbose --events --time-limit=300 --concurrency=2 --concurrency:priority,integrations=4 --concurrency:import=1
```

`prod_beat`:

```sh
VIRTUALENV=/www/www.sewing-world.ru/.venv
CELERYD_OPTS=--workdir=/www/www.sewing-world.ru/ --app=sewingworld
CELERYD_BEAT_OPTS=--logfile=/www/www.sewing-world.ru/logs/celery_beat.log --loglevel=INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

`/etc/tmpfiles.d/celery.conf`:

```
d /run/celery 0755 sworld www-data -
```

Set proper permissions, otherwise services will fail to start:

```sh
mkdir /run/celery
chown sworld:www-data /run/celery
```

Once the site is deployed, see [Environment setup](#environment-setup):

```sh
systemctl enable --now celery@prod celery_beat@prod
```

# Environment setup

All sites are located in `/www` folder. The following description is included for general reference.

The backend is on the `main` branch only, and is deployed by hand. Its production checkout is
`/www/www.sewing-world.ru`, which runs the API, the admin site and Celery for all the sites (see
[UWSGI setup](#uwsgi-setup) and [Celery setup](#celery-setup)), and `/www/dev.sigalev.ru` is the development one.
Every other branch of this repository is a storefront, never a copy of the backend: see
[Frontend deployment](#frontend-deployment). A backend checkout has its Python virtualenv in `.venv`, which uv fills
from `uv.lock`:

```sh
cd /www
git clone git@github.com:andreynovikov/django-shop.git www.sewing-world.ru
cd www.sewing-world.ru
uv sync --locked --no-dev --compile-bytecode
mkdir media static logs .cache import
sudo chown -R sworld:www-data media static logs .cache import
sudo chmod 2775 media static .cache import
sudo chmod 2755 logs
sudo chown root:sworld .env* sewingworld/settings/integrations.py*
sudo chmod 640 .env* sewingworld/settings/integrations.py*
```

The [service user](#service-user) writes only those directories: the uploads, the collected static files, the logs,
the file cache of the sitemap and the files of the 1C import. The code belongs to whoever deploys it and is read-only
for the service. Only root and the service user can read the secrets, so run `manage.py` as that user:

```sh
sudo -u sworld .venv/bin/python manage.py migrate
```

The service user cannot write `__pycache__` into the code either, and without compiled files Python compiles each
module again at every start. `--compile-bytecode` above compiles the packages, and after each `git pull` compile
the code as yourself:

```sh
.venv/bin/python -m compileall -q -x '/\.venv/' .
```

# Frontend deployment

The Next.js frontends are branches of this repository, one per site. They run on the server as Docker containers,
built by GitHub Actions:

| Branch | Directory                 | NAME   | Port |
|--------|---------------------------|--------|------|
| sworld | /www/www.sewing-world.ru  | sworld | 4104 |
| sworld | /www/cartzilla.sigalev.ru | stage  | 4004 |
| family | /www/familysew.ru         | family | 4101 |
| janome | /www/janome.club          | janome | 4103 |
| singer | /www/singer.ru            | singer | 4102 |
| dortak | /www/dor-tak.ru           | dortak | 4105 |

The second sworld line is the stage site. Each directory holds the branch's `docker-compose.yaml` and its
`templates/`, which is mounted into the container for the XML feeds. At start the container copies its static files
into `.docker/`, where nginx serves them from. nginx proxies everything else to `127.0.0.1:<port>`.

Each branch has its own `.github/workflows/frontend.yml`. Every push to the branch runs lint and type checks, builds
the image with the frontend's `.env`, and pushes it to `ghcr.io/andreynovikov/<branch>`. The image is tagged with
the commit's date in Moscow time and its short hash, such as `2026.11.11-7f57710`, and with `latest`. sworld also
runs the Playwright tests and deploys every push to stage.

To deploy a frontend to production, open Actions → Frontend CI → Run workflow on GitHub and choose its branch. The run
deploys the image of the branch's last commit, and fails if that commit's build has not finished or has failed. To roll
back, re-run an earlier deploy run (GitHub allows re-runs for 30 days), or start an older image on the server.
`docker images` lists the ones it has; pulling another one needs `docker login ghcr.io` with a token that can read
packages:

```sh
cd /www/janome.club
NAME=janome PORT=4103 IMAGE=ghcr.io/andreynovikov/janome:2026.11.10-eb964ab docker compose up -d
```

The `frontend.yml` on `main` only puts the Run workflow button on the Actions page: GitHub shows it only for workflows
on the default branch. Run on `main`, it fails.

## GitHub settings

- Environments `sworld`, `family`, `janome`, `singer` and `dortak`, one per branch, each limited to its
  branch. Each holds the secret `ENV_FILE`, the frontend's `.env`. Next.js builds it into the image, so the build
  job reads it too, and sworld's stage runs the production image. Don't add required reviewers: they would also hold
  up the build job, which reads the environment without deploying to it.
- No repository secret `ENV_FILE`: a job falls back to it when its environment has none, and would build a frontend
  with another one's `.env`.
- Repository secrets `DEPLOY_HOST`, `DEPLOY_USER` and `SSH_PRIVATE_KEY`: the ssh login of the deploy jobs.
  The `deployment` tag provisions the default `deploy` account and installs the
  [restricted deployment command](ansible/roles/server/files/deploy-frontend). The key's forced command
  accepts a storefront name and an image tag. Set `DEPLOY_USER` to `deploy` when using this account.
- The `Protected branches` ruleset lists the frontend branches by name. Update it when a branch is added or renamed.

# Database backups

The database provider keeps its own backups, these are ours in case the provider is lost. Every hour the production
server runs `manage.py backup_db`, which streams `pg_dump` output into a [restic](https://restic.net) repository
on our backup host. restic encrypts, compresses and deduplicates it, so a daily full dump costs only what changed.
The production server can only add snapshots to the repository. `deploy/backup/maintain.sh` on the backup host
applies the retention policy, checks the repository, test-restores it weekly and raises alarms.

The repository is encrypted with its password. Keep it in the password manager and on paper: without it the backups
cannot be read.

There are three kinds of snapshots, with settings in `sewingworld/settings/backup.py`:

- **full**: once a day at 03:00, or on the first run after it, and after migrations. It holds the whole database with
  its schema, but not the rows of the `errors` and `django_celery_results` tables. Kept 14 days, 8 weeks and
  12 months.
- **hot**: every other hour. It holds only the rows of orders, order items, boxes, users, serials and favorites.
  Kept 48 hours.
- **config**: `.env`, `.env.admin` and `sewingworld/settings/integrations.py`, saved with each full snapshot.
  Kept 14 days and 12 months.

## Backup host

Any Debian machine of ours with enough disk for about twice the database. Besides the server it needs the tools for
maintenance and restore tests, and a mail transport for `mail`. `postgresql` must be at least the major version
of the production server, take it from apt.postgresql.org if Debian's is older:

```sh
apt install restic-rest-server restic jq apache2-utils bsd-mailx postgresql
```

The packaged service runs as the `restic-rest-server` user. Maintenance runs as the same user, so that it can delete
what the server writes. Create the repository, its password, and the login of the production server. With
`--private-repos`, the login name is the repository directory:

```sh
mkdir -p /srv/restic /etc/db-backup
chown restic-rest-server: /srv/restic
openssl rand -base64 30 > /etc/db-backup/restic-password  # save it in the password manager
chown restic-rest-server: /etc/db-backup/restic-password && chmod 400 /etc/db-backup/restic-password
sudo -u restic-rest-server restic init --no-cache --repo /srv/restic/sworld --password-file /etc/db-backup/restic-password
htpasswd -B /etc/restic-rest-server/users.htpasswd sworld
sudo -u postgres createuser --createdb restic-rest-server  # for restore tests
```

Set `/etc/default/restic-rest-server` as follows and run `systemctl restart restic-rest-server`. The TLS
certificate is for the host name and must be readable by `restic-rest-server`. Open the port only to the
production server:

```
LISTEN = :8000
BACKUP_DIR = /srv/restic/
ARGS = "\
  --htpasswd-file /etc/restic-rest-server/users.htpasswd \
  --append-only --private-repos \
  --tls --tls-cert /etc/restic-rest-server/cert.pem --tls-key /etc/restic-rest-server/key.pem \
"
```

Copy `deploy/backup/*.sh` into `/usr/local/lib/db-backup/` and create `/etc/default/db-backup`. `DB_HOSTS`
lists the database names, `CONFIG_HOSTS` the project directory names of the deployments:

```sh
RESTIC_REPOSITORY=/srv/restic/sworld
RESTIC_PASSWORD_FILE=/etc/db-backup/restic-password
DB_HOSTS="sworld"
CONFIG_HOSTS="www.sewing-world.ru"
ALERT_EMAIL=admin@sewing-world.ru
PGHOST=/var/run/postgresql
TMPDIR=/var/tmp  # restore tests unpack a full dump here, /tmp is in memory on Debian 13
```

`/etc/systemd/system/db-backup@.service`:

```ini
[Unit]
Description=Database backup maintenance: %i

[Service]
Type=oneshot
User=restic-rest-server
CacheDirectory=db-backup
Environment=RESTIC_CACHE_DIR=%C/db-backup
ExecStart=/usr/local/lib/db-backup/maintain.sh %i
```

Three timers start it: `db-backup@fresh.timer` with `OnCalendar=*:30`, `db-backup@prune.timer` with
`OnCalendar=12:00` and `db-backup@verify.timer` with `OnCalendar=Sun 13:00`. Each one looks like this:

```ini
[Unit]
Description=Database backup maintenance: %i

[Timer]
OnCalendar=*:30
Persistent=true

[Install]
WantedBy=timers.target
```

Enable them with `systemctl enable --now db-backup@fresh.timer db-backup@prune.timer db-backup@verify.timer`.

## Production server

With Ansible, set `server_db_backup_deployments` to the sites that own a database and
`server_db_backup_config_deployments` to sites that only need daily configuration backups. The `backup` tag copies
the repository password and enables the configured timers when a backup host is present in the inventory.
Add the `RESTIC_*` settings to the site's `.env` before enabling its timer.

1. `apt install restic`. It must be 0.17 or later, and `pg_dump --version` must not be older than the database
   server.

2. Copy the password file from the backup host into `/etc/db-backup/` with owner `sworld` and mode `400`,
   and add to `.env` of the deployment that owns the database:

   ```sh
   RESTIC_REPOSITORY=rest:https://sworld:<htpasswd password>@backup.example.ru:8000/sworld/
   RESTIC_PASSWORD_FILE=/etc/db-backup/restic-password
   ```

   With a self-signed certificate, copy it too and add `RESTIC_CACERT=/etc/db-backup/cert.pem`.

3. Check that the production server cannot delete. Save a test snapshot and try to forget it. restic exits with 0
   even when the server refuses, so look at the output instead: `forget` must print `403 Forbidden`, and the
   snapshot must still be listed:

   ```sh
   sudo -u sworld sh -c 'export $(grep "^RESTIC_" .env)
     echo test | restic --no-cache backup --stdin --host append-test
     restic --no-cache forget --host append-test latest
     restic --no-cache snapshots --host append-test'
   ```

   If the snapshot is gone, check `--append-only` on the backup host. Remove the test snapshot there:
   `sudo -u restic-rest-server restic forget --prune --host append-test latest`, with the settings of
   `/etc/default/db-backup`.

4. Check which tables are the largest, and add logs that need no backup to `EXCLUDE_DATA_APPS` or
   `EXCLUDE_DATA_TABLES`:

   ```sql
   SELECT relname, pg_size_pretty(pg_total_relation_size(oid)) FROM pg_class
   WHERE relkind = 'r' ORDER BY pg_total_relation_size(oid) DESC LIMIT 20;
   ```

5. Run `sudo -u sworld .venv/bin/python manage.py backup_db --dry-run`, then the same with `--kind full` instead
   of `--dry-run`. restic warns that it cannot open its cache, the user has no home. The units below give it one.

6. Create `/etc/systemd/system/db_backup@.service`:

   ```ini
   [Unit]
   Description=Database backup for %I
   Wants=network-online.target
   After=network-online.target

   [Service]
   Type=oneshot
   User=sworld
   Group=sworld
   WorkingDirectory=/www/%I
   CacheDirectory=db_backup
   Environment=RESTIC_CACHE_DIR=%C/db_backup
   ExecStart=/www/%I/.venv/bin/python manage.py backup_db
   Nice=10
   IOSchedulingClass=idle
   ```

   and `/etc/systemd/system/db_backup@.timer`:

   ```ini
   [Unit]
   Description=Hourly database backup for %I

   [Timer]
   OnCalendar=hourly
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

   Enable the timer for the deployment that owns the database: `systemctl enable --now db_backup@www.sewing-world.ru.timer`.
   Do this for only one deployment per database. Another deployment with its own `.env` saves its config daily with
   copies of these units named `db_backup_config@`, with `backup_db --kind config` and `OnCalendar=daily`. Add
   its directory name to `CONFIG_HOSTS` on the backup host.

Failures are logged to `logs/backup.log` and mailed to `ADMINS`. The backup host raises its own alarm when
snapshots stop coming, even if the production server is down.

## Restore

On the backup host, or any machine with restic, jq and the PostgreSQL client tools, take the password from the
password manager. `TMPDIR` needs room for an uncompressed full dump:

```sh
export RESTIC_REPOSITORY=/srv/restic/sworld RESTIC_PASSWORD_FILE=/etc/db-backup/restic-password TMPDIR=/var/tmp
restic snapshots
restic restore latest --tag config --host www.sewing-world.ru --target /var/tmp/config
PGHOST=<new server> PGUSER=<owner> /usr/local/lib/db-backup/restore.sh --host sworld --target sworld
```

`--at '2026-11-10 14:00'` restores an earlier state. The script restores the latest full snapshot and replaces the
rows of the hot tables with the latest hot snapshot after it. A foreign key fails when a hot row points at a row
missing from the full snapshot, such as a product made after it. The script prints such errors, and that constraint
is not created until the rows are fixed. Then point `DATABASE_URL` of every deployment at the new database and
restart uWSGI and Celery.

# Periodic maintenance

## Log rotation

The `logrotate` tag installs `/etc/logrotate.d/sewing-world` from the
[application log template](ansible/roles/server/templates/logrotate.j2). Update the template when a uWSGI, Celery
or Django log needs rotation. Debian rotates `/var/log/nginx/*.log` with `/etc/logrotate.d/nginx`. Ansible installs
[`/etc/logrotate.d/nginx-legacy`](ansible/roles/server/files/nginx-legacy.logrotate) for `*_legacy.jsonl`, rotating
those files monthly and keeping 12 rotations. The default application rules are:

```
/www/*/logs/*uwsgi*.log
/www/*/logs/celery*.log
/www/*/logs/django*.log
/www/*/logs/backup.log
/www/*/logs/beru.log
/www/*/logs/kassa.log
/www/*/logs/ozon.log
/www/*/logs/rarus.log
/www/*/logs/sber.log
/www/*/logs/wb.log
{
  su sworld www-data
  create 644 sworld www-data
  copytruncate
  daily
  rotate 7
  compress
  delaycompress
  missingok
  notifempty
}
```

## Docker cleanup

The `docker` tag enables `docker-prune.timer`. It runs weekly and removes unused Docker images and build cache
older than seven days. Keep any image you might need to roll back available in the registry.

## Development database syncronization

Simpliest way to sync development database with production is to recreate it.

First:

```sql
DROP DATABASE sworld_dev;
CREATE DATABASE sworld_dev OWNER andrey;
GRANT ALL PRIVILEGES ON DATABASE sworld_dev TO nikolays;
```

Then:

```sh
pg_dump sworld | psql sworld_dev
```

# Monitoring

## cAdvisor (Container Advisor)

Provides container usage metrics to Prometheus.

```sh
docker run \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=127.0.0.1:9324:8080 \
  --detach=true \
  --name=cadvisor \
  --privileged \
  --device=/dev/kmsg \
  ghcr.io/google/cadvisor:0.60.6
```

## celery-exporter

Provides celery usage metrics to Prometheus.

```sh
docker run \
  --publish=127.0.0.1:9808:9808 \
  --detach=true \
  --name=celery-exporter \
  --network="host" \
  danihodovic/celery-exporter:0.12.2 \
  --broker-url=redis://127.0.0.1:6379/0 \
  --broker-transport-option visibility_timeout=691200 \
  --retry-interval=5
```
