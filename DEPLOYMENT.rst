************
Server setup
************

The Ansible playbook ``deploy/ansible/site.yml`` does the steps of this guide that need neither files from the old
server nor secrets: packages, users, system configuration and the files listed here, on the production server and on
the backup host. It leaves out PostgreSQL, the sites in ``/www``, replication and failover.
``deploy/ansible/README.rst`` tells how to run it and what is left to do by hand.

Historically server is run under latest Debian Stable.

The following packages are required:
::
    apt install sudo
    apt install exim4
    apt install rsync
    apt install python3
    apt install postgresql-client
    apt install nginx
    apt install uwsgi
    apt install uwsgi-plugin-python3
    apt install memcached
    apt install redis-server
    apt install certbot
    apt install git

The following packages are required for building python packages:
::
    apt install build-essential
    apt install python3-dev
    apt install libmemcached-dev
    apt install libpq-dev
    apt install libjpeg-dev
    apt install tidy

Python packages are installed with uv, which Debian does not package:
::
    curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh

The following packages are optional:
::
    apt install less
    apt install emacs-nox
    apt install bind9-dnsutils
    apt install htop

Install Docker (https://docs.docker.com/engine/install/debian/#install-using-the-repository)

Master/slave cold redundancy server scheme is used for High Availability. It means that two servers are kept identical
but if one server fails manual actions should be performed to switch to another server (described below).

Create users in this particular order (to preserve uids):
::
    adduser andrey
    adduser nikolays
    adduser maria
    adduser egor

Add user ``andrey`` to ``adm`` and ``docker`` groups.
Add users ``andrey`` and ``nikolays`` to ``sudu`` and ``www-data`` groups.
Add users ``maria`` and ``egor`` to ``www-data`` group.

Disable ssh root login:
::
    PermitRootLogin no

Optionaly adjust ssh keep-alives:
::
    ClientAliveInterval 60
    ClientAliveCountMax 8

Setup correct timezone:
::
    timedatectl set-timezone Europe/Moscow

Enable time syncronization. Edit ``/etc/systemd/timesyncd.conf`` file:
::
    NTP=ru.pool.ntp.org

then restart time service:
::
    systemctl restart systemd-timesyncd
    timedatectl set-ntp true

Reconfigure Exim for internet mode to be able to send mails:
::
    dpkg-reconfigure exim4-config

Increase memcached limits in ``/etc/memcached.conf`` file:
::
   -m 256

Two factor authentication
*************************

Install required package:
::
    apt install libpam-google-authenticator

Execute ``google-authenticator -t -d -f -r 3 -R 30 -W`` for every interactive user to generate OTP codes.

Add the following line to the bottom of the ``/etc/pam.d/sshd``:
::
    auth required pam_google_authenticator.so

Enable challenge response:
::
    ChallengeResponseAuthentication    yes

***********
Nginx setup
***********

Copy ``/etc/nginx/basic_auth`` and ``/etc/nginx/htpasswd`` from old server to new.
Copy ``/etc/nginx/sites-available/*`` from old server to new. Set links to all configs in ``sites-enabled``.

Adjust ``/etc/nginx/nginx.conf``:
::
    tcp_nodelay on;
    keepalive_timeout 65;
    server_names_hash_bucket_size 64;

    log_format upstream '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                        'rt="$request_time" uct="$upstream_connect_time" uht="$upstream_header_time" urt="$upstream_response_time" '
                        '"$http_referer" "$http_user_agent"';

    log_format errored  '[$time_local] $status "$request" "$http_referer"';

    map $status $moved {
      ~^[3]   1;
      default 0;
    }

    map $status $notfound {
      ~^[4]   1;
      default 0;
    }

    map $status $errored {
      ~^[5]   1;
      default 0;
    }

****************
PostgreSql setup*
****************

* currently we use separate postgresql server, so this step should be skipped

Create necessary roles and databases:
::
    CREATE ROLE andrey SUPERUSER LOGIN;
    CREATE ROLE nikolays SUPERUSER LOGIN;
    CREATE ROLE sworld LOGIN;
    CREATE DATABASE sworld OWNER andrey;
    CREATE DATABASE sworld_dev OWNER andrey;

Permit database login without password to ``sworld`` in ``/etc/postgresql/*.*/main/pg_hba.conf``:
::
    local   all             sworld                                  trust

Import data from backup:
::
    cat sworld.db | psql sworld

***********
UWSGI setup
***********

Create ``/etc/systemd/system/uwsgi@.socket``:
::
    [Unit]
    Description=Socket for uWSGI app %i

    [Socket]
    ListenStream=/run/uwsgi/%i.socket
    SocketUser=nikolays
    SocketGroup=www-data
    SocketMode=0660

    [Install]
    WantedBy=sockets.target

Create ``/etc/systemd/system/uwsgi@.service``:
::
    [Unit]
    Description=%i uWSGI app
    After=syslog.target

    [Service]
    ExecStart=/usr/bin/uwsgi \
            --ini /etc/uwsgi/apps-available/%i.ini \
            --socket /run/uwsgi/%i.socket
    User=nikolays
    Group=www-data
    Restart=on-failure
    KillSignal=SIGQUIT
    Type=notify
    StandardError=syslog
    NotifyAccess=all

    [Install]
    WantedBy=multi-user.target

Copy ``/etc/uwsgi/apps-available/*`` from old server to new. **Do not** set any links in ``apps-enabled``.

Typical application setup looks as follows:
::
    [uwsgi]
    master = true
    plugins = python3,logfile
    chdir = /www/www.sewing-world.ru
    virtualenv = /www/www.sewing-world.ru/env
    module = sewingworld.wsgi:application
    processes = 2
    threads = 4
    buffer-size = 8192
    uid = nikolays
    gid = www-data
    chmod-socket = 660
    env = PYTHONIOENCODING=UTF-8
    env = DJANGO_SETTINGS_MODULE=sewingworld.settings.production
    harakiri = 120
    vacuum = true
    max-requests = 5000
    req-logger = file:/www/www.sewing-world.ru/logs/uwsgi_access.log
    logger = file:/www/www.sewing-world.ru/logs/uwsgi_error.log
    log-date = true

Each application should be:
::
    systemctl enable uwsgi@app.socket
    systemctl start uwsgi@app.socket
    systemctl enable uwsgi@app
    systemctl start uwsgi@app

where ``app`` is the name of the uwsgi configuration file.

************
Celery setup
************

``/etc/systemd/system/celery@.service``
::
    [Unit]
    Description=Celery worker for %I
    Wants=redis-server.service
    After=network.target redis-server.service

    [Service]
    User=nikolays
    Group=www-data
    Type=forking
    EnvironmentFile=-/etc/celery/%I_worker
    PIDFile=/run/celery/%I_worker.pid
    ExecStart=/bin/sh -c "$$VIRTUALENV/bin/celery multi start $CELERYD_NODES --pidfile=/run/celery/%I_worker.pid $CELERYD_OPTS"
    ExecStop=/bin/sh -c "$$VIRTUALENV/bin/celery multi stopwait $CELERYD_NODES --pidfile=/run/celery/%I_worker.pid"
    ExecReload=/bin/sh -c "$$VIRTUALENV/bin/celery multi restart $CELERYD_NODES --pidfile=/run/celery/%I_worker.pid $CELERYD_OPTS"

    [Install]
    WantedBy=multi-user.target

``/etc/systemd/system/celery_beat@.service``:
::
    [Unit]
    Description=Celery beat for %I
    Wants=redis-server.service
    After=network.target redis-server.service

    [Service]
    User=nikolays
    Group=www-data
    Type=forking
    EnvironmentFile=-/etc/celery/%I_beat
    PIDFile=/var/run/celery/%I_beat.pid
    ExecStart=/bin/sh -c "($$VIRTUALENV/bin/celery beat --pidfile=/run/celery/%I_beat.pid $CELERYD_OPTS)& echo $!"
    ExecStop=/bin/kill -s TERM /run/celery/%I_beat.pid

    [Install]
    WantedBy=multi-user.target

``/etc/tmpfiles.d/celery.conf``:
::
    d /run/celery 0755 nikolays www-data -

Set proper permissions, otherwise services will fail to start:
::
    mkdir /run/celery
    chown nikolays:www-data /run/celery

*************
Node.js setup
*************

Install Node (replace XX.X with actual version):
::
    mkdir /www/.nvm
    export NVM_DIR="/www/.nvm"
    wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.XX.X/install.sh | bash
    nvm install node

*****************
Environment setup
*****************

All sites are located in ``/www`` folder. Replication should be configured for this folder (see below). The following
description is included for general reference.

All sites are kept in git on GitHub. Each site has its own Python virtualenv in ``env``, which uv fills
from the ``uv.lock`` of its branch. So, general deployment scheme looks like this:
::
    cd /www
    git clone git@github.com:andreynovikov/django-shop.git janome.club
    cd janome.club
    git checkout janome
    UV_PROJECT_ENVIRONMENT=env uv sync --locked --no-dev
    mkdir media
    mkdir static
    mkdir logs
    sudo chown nikolays:www-data logs
    mkdir st_search
    sudo chown nikolays:www-data st_search

The Next.js frontends run in Docker, see `Frontend deployment`_.

*******************
Frontend deployment
*******************

The Next.js frontends are branches of this repository, one per site. They run on the server as Docker containers,
built by GitHub Actions:

=========  ===========================  =========  ====
Branch     Directory                    NAME       Port
=========  ===========================  =========  ====
sworld     /www/www.sewing-world.ru     sworld     4104
sworld     /www/cartzilla.sigalev.ru    stage      4004
family     /www/familysew.ru            family     4101
janome     /www/janome.club             janome     4103
singer     /www/singer.ru               singer     4102
dortak     /www/dor-tak.ru              dortak     4105
=========  ===========================  =========  ====

The second sworld line is the stage site. Each directory holds the branch's ``docker-compose.yaml`` and its
``templates/``, which is mounted into the container for the XML feeds. At start the container copies its static files
into ``.docker/``, where nginx serves them from. nginx proxies everything else to ``127.0.0.1:<port>``.

Each branch has its own ``.github/workflows/frontend.yml``. Every push to the branch runs lint and type checks, builds
the image with the frontend's ``.env``, and pushes it to ``ghcr.io/andreynovikov/<branch>``. The image is tagged with
the commit's date in Moscow time and its short hash, such as ``2026.11.11-7f57710``, and with ``latest``. sworld also
runs the Playwright tests and deploys every push to stage.

To deploy a frontend to production, open Actions → Frontend CI → Run workflow on GitHub and choose its branch. The run
deploys the image of the branch's last commit, and fails if that commit's build has not finished or has failed. To roll
back, re-run an earlier deploy run (GitHub allows re-runs for 30 days), or start an older image on the server.
``docker images`` lists the ones it has; pulling another one needs ``docker login ghcr.io`` with a token that can read
packages:

::

    cd /www/janome.club
    NAME=janome PORT=4103 IMAGE=ghcr.io/andreynovikov/janome:2026.11.10-eb964ab docker compose up -d

The ``frontend.yml`` on ``main`` only puts the Run workflow button on the Actions page: GitHub shows it only for workflows
on the default branch. Run on ``main``, it fails.

GitHub settings
***************

* Environments ``sworld``, ``family``, ``janome``, ``singer`` and ``dortak``, one per branch, each limited to its
  branch. Each holds the secret ``ENV_FILE``, the frontend's ``.env``. Next.js builds it into the image, so the build
  job reads it too, and sworld's stage runs the production image. Don't add required reviewers: they would also hold
  up the build job, which reads the environment without deploying to it.
* No repository secret ``ENV_FILE``: a job falls back to it when its environment has none, and would build a frontend
  with another one's ``.env``.
* Repository secrets ``DEPLOY_HOST``, ``DEPLOY_USER`` and ``SSH_PRIVATE_KEY``: the ssh login of the deploy jobs.
* The ``Protected branches`` ruleset lists the frontend branches by name. Update it when a branch is added or renamed.

************************
Master/slave replication
************************

There are two separate replication processes: file replication and database replication. Only site files (``/www``)
are replicated automatically. All server configuration and maintenance should be replicated manually. Servers distinguish
who is master by presence of the ``/primary_server`` file.

File replication
****************

Files are replicated by ``rsync`` executed by ``cron`` on hourly basis. Create ``/etc/cron.hourly/rsync``:
::
    #!/bin/sh
    test -f /primary_server && rsync -a -s -S -u --exclude "*.pyc" --exclude "logs/" --exclude "__pycache__/" -e "ssh -i /home/andrey/.ssh/id_rsa" --rsync-path="sudo rsync" --numeric-ids /www/ andrey@duo.sigalev.ru:/www/

Disable sudo password for rsync - create file ``/etc/sudoers.d/rsync`` on slave:
::
    andrey  ALL=NOPASSWD:/usr/bin/rsync

Set proper permissions:
::
    chmod 440 /etc/sudoers.d/rsync

Database replication
********************

Configure PostgreSql on master:
::
    listen_addresses = '*'
    wal_level = replica
    max_wal_senders = 3
    wal_keep_size = 256

Permit replication connection in ``/etc/postgresql/X.X/main/pg_hba.conf`` on master:
::
    host     replication     replicator      217.25.88.165/32        md5
and on slave:
::
    host     replication     replicator      92.53.104.6/32          md5

Create ``replicator`` user on master:
::
    CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD '***';
    SELECT pg_reload_conf();

Configure PostgreSql on slave:
::
    listen_addresses = '*'
    wal_level = replica
    max_wal_senders = 3
    wal_keep_size = 256
    hot_standby = on
    promote_trigger_file = '/primary_server'

Stop postgresql on slave, copy current database state from master to slave (should be executer on slave):
::
    systemctl stop postgresql
    rm -rf /var/lib/postgresql/X.X/main/*
    pg_basebackup -h 92.53.104.6 -U replicator -p 5432 -D /var/lib/postgresql/X.X/main -P -Xs -R

This will also create required configuration files. Start postgresql to begin replication.

****************
Failover actions
****************

Terms *master* and *slave* apply to **current** server status. It means that these actions should be taken
to switch **from** *master* **to** *slave*. Actions on **master** should be taken if the server is accessible
**preserving** original order.

#. On **master**: ``sudo systemctl stop postgresql``
#. On **master**: ``sudo rm /primary_server``
#. On **slave**: ``sudo touch /primary_server``
#. On **slave**: ``sudo systemctl start nginx``
#. ...
#. Switch DNS IP records for all sites in order of importance.

****************
Database backups
****************

The database provider keeps its own backups, these are ours in case the provider is lost. Every hour the production
server runs ``manage.py backup_db``, which streams ``pg_dump`` output into a `restic <https://restic.net>`_ repository
on our backup host. restic encrypts, compresses and deduplicates it, so a daily full dump costs only what changed.
The production server can only add snapshots to the repository. ``deploy/backup/maintain.sh`` on the backup host
applies the retention policy, checks the repository, test-restores it weekly and raises alarms.

The repository is encrypted with its password. Keep it in the password manager and on paper: without it the backups
cannot be read.

There are three kinds of snapshots, with settings in ``sewingworld/settings/backup.py``:

* **full**: once a day at 03:00, or on the first run after it, and after migrations. It holds the whole database with
  its schema, but not the rows of the ``errors`` and ``django_celery_results`` tables. Kept 14 days, 8 weeks and
  12 months.
* **hot**: every other hour. It holds only the rows of orders, order items, boxes, users, serials and favorites.
  Kept 48 hours.
* **config**: ``.env``, ``.env.admin`` and ``sewingworld/settings/integrations.py``, saved with each full snapshot.
  Kept 14 days and 12 months.

Backup host
***********

Any Debian machine of ours with enough disk for about twice the database. Besides the server it needs the tools for
maintenance and restore tests, and a mail transport for ``mail``. ``postgresql`` must be at least the major version
of the production server, take it from apt.postgresql.org if Debian's is older:

::

    apt install restic-rest-server restic jq apache2-utils bsd-mailx postgresql

The packaged service runs as the ``restic-rest-server`` user. Maintenance runs as the same user, so that it can delete
what the server writes. Create the repository, its password, and the login of the production server. With
``--private-repos``, the login name is the repository directory:

::

    mkdir -p /srv/restic /etc/db-backup
    chown restic-rest-server: /srv/restic
    openssl rand -base64 30 > /etc/db-backup/restic-password  # save it in the password manager
    chown restic-rest-server: /etc/db-backup/restic-password && chmod 400 /etc/db-backup/restic-password
    sudo -u restic-rest-server restic init --no-cache --repo /srv/restic/sworld --password-file /etc/db-backup/restic-password
    htpasswd -B /etc/restic-rest-server/users.htpasswd sworld
    sudo -u postgres createuser --createdb restic-rest-server  # for restore tests

Set ``/etc/default/restic-rest-server`` as follows and run ``systemctl restart restic-rest-server``. The TLS
certificate is for the host name and must be readable by ``restic-rest-server``. Open the port only to the
production server:

::

    LISTEN = :8000
    BACKUP_DIR = /srv/restic/
    ARGS = "\
      --htpasswd-file /etc/restic-rest-server/users.htpasswd \
      --append-only --private-repos \
      --tls --tls-cert /etc/restic-rest-server/cert.pem --tls-key /etc/restic-rest-server/key.pem \
    "

Copy ``deploy/backup/*.sh`` into ``/usr/local/lib/db-backup/`` and create ``/etc/default/db-backup``. ``DB_HOSTS``
lists the database names, ``CONFIG_HOSTS`` the project directory names of the deployments:

::

    RESTIC_REPOSITORY=/srv/restic/sworld
    RESTIC_PASSWORD_FILE=/etc/db-backup/restic-password
    DB_HOSTS="sworld"
    CONFIG_HOSTS="www.sewing-world.ru"
    ALERT_EMAIL=admin@sewing-world.ru
    PGHOST=/var/run/postgresql
    TMPDIR=/var/tmp  # restore tests unpack a full dump here, /tmp is in memory on Debian 13

``/etc/systemd/system/db-backup@.service``:

::

    [Unit]
    Description=Database backup maintenance: %i

    [Service]
    Type=oneshot
    User=restic-rest-server
    CacheDirectory=db-backup
    Environment=RESTIC_CACHE_DIR=%C/db-backup
    ExecStart=/usr/local/lib/db-backup/maintain.sh %i

Three timers start it: ``db-backup@fresh.timer`` with ``OnCalendar=*:30``, ``db-backup@prune.timer`` with
``OnCalendar=12:00`` and ``db-backup@verify.timer`` with ``OnCalendar=Sun 13:00``. Each one looks like this:

::

    [Unit]
    Description=Database backup maintenance: %i

    [Timer]
    OnCalendar=*:30
    Persistent=true

    [Install]
    WantedBy=timers.target

Enable them with ``systemctl enable --now db-backup@fresh.timer db-backup@prune.timer db-backup@verify.timer``.

Production server
*****************

#. ``apt install restic``. It must be 0.17 or later, and ``pg_dump --version`` must not be older than the database
   server.

#. Copy the password file from the backup host into ``/etc/db-backup/`` with owner ``nikolays`` and mode ``400``,
   and add to ``.env`` of the deployment that owns the database:

   ::

       RESTIC_REPOSITORY=rest:https://sworld:<htpasswd password>@backup.example.ru:8000/sworld/
       RESTIC_PASSWORD_FILE=/etc/db-backup/restic-password

   With a self-signed certificate, copy it too and add ``RESTIC_CACERT=/etc/db-backup/cert.pem``.

#. Check that the production server cannot delete. Save a test snapshot and try to forget it. restic exits with 0
   even when the server refuses, so look at the output instead: ``forget`` must print ``403 Forbidden``, and the
   snapshot must still be listed:

   ::

       export $(grep '^RESTIC_' .env)
       echo test | restic backup --stdin --host append-test
       restic forget --host append-test latest
       restic snapshots --host append-test

   If the snapshot is gone, check ``--append-only`` on the backup host. Remove the test snapshot there:
   ``sudo -u restic-rest-server restic forget --prune --host append-test latest``, with the settings of
   ``/etc/default/db-backup``.

#. Check which tables are the largest, and add logs that need no backup to ``EXCLUDE_DATA_APPS`` or
   ``EXCLUDE_DATA_TABLES``:

   ::

       SELECT relname, pg_size_pretty(pg_total_relation_size(oid)) FROM pg_class
       WHERE relkind = 'r' ORDER BY pg_total_relation_size(oid) DESC LIMIT 20;

#. Run ``python manage.py backup_db --dry-run``, then ``time python manage.py backup_db --kind full``.

#. Create ``/etc/systemd/system/db_backup@.service``:

   ::

       [Unit]
       Description=Database backup for %I
       Wants=network-online.target
       After=network-online.target

       [Service]
       Type=oneshot
       User=nikolays
       Group=www-data
       WorkingDirectory=/www/%I
       ExecStart=/www/%I/env/bin/python manage.py backup_db
       Nice=10
       IOSchedulingClass=idle

   and ``/etc/systemd/system/db_backup@.timer``:

   ::

       [Unit]
       Description=Hourly database backup for %I

       [Timer]
       OnCalendar=hourly
       Persistent=true

       [Install]
       WantedBy=timers.target

   Enable the timer for the deployment that owns the database: ``systemctl enable --now db_backup@www.sewing-world.ru.timer``.
   Do this for only one deployment per database. Another deployment with its own ``.env`` saves its config daily with
   copies of these units named ``db_backup_config@``, with ``backup_db --kind config`` and ``OnCalendar=daily``. Add
   its directory name to ``CONFIG_HOSTS`` on the backup host.

Failures are logged to ``logs/backup.log`` and mailed to ``ADMINS``. The backup host raises its own alarm when
snapshots stop coming, even if the production server is down.

Restore
*******

On the backup host, or any machine with restic, jq and the PostgreSQL client tools, take the password from the
password manager. ``TMPDIR`` needs room for an uncompressed full dump:

::

    export RESTIC_REPOSITORY=/srv/restic/sworld RESTIC_PASSWORD_FILE=/etc/db-backup/restic-password TMPDIR=/var/tmp
    restic snapshots
    restic restore latest --tag config --host www.sewing-world.ru --target /var/tmp/config
    PGHOST=<new server> PGUSER=<owner> /usr/local/lib/db-backup/restore.sh --host sworld --target sworld

``--at '2026-11-10 14:00'`` restores an earlier state. The script restores the latest full snapshot and replaces the
rows of the hot tables with the latest hot snapshot after it. A foreign key fails when a hot row points at a row
missing from the full snapshot, such as a product made after it. The script prints such errors, and that constraint
is not created until the rows are fixed. Then point ``DATABASE_URL`` of every deployment at the new database and
restart uWSGI and Celery.

********************
Periodic maintenance
********************

Log rotation
************

Create ``/etc/logrotate.d/sewing-world``:
::
    /www/*/logs/nginx*.log
    {
      daily
      missingok
      rotate 7
      compress
      delaycompress
      notifempty
      su www-data www-data
      create 0640 www-data www-data
      sharedscripts
      prerotate
        if [ -d /etc/logrotate.d/httpd-prerotate ]; then \
          run-parts /etc/logrotate.d/httpd-prerotate; \
        fi \
      endscript
      postrotate
        invoke-rc.d nginx rotate >/dev/null 2>&1
      endscript
    }

    /www/*/logs/uwsgi*.log
    /www/*/logs/django*.log
    /www/*/logs/backup.log
    {
      su nikolays www-data
      create 644 nikolays www-data
      copytruncate
      daily
      rotate 7
      compress
      delaycompress
      missingok
      notifempty
    }

Development database syncronization
***********************************

Simpliest way to sync development database with production is to recreate it.

First:
::
    DROP DATABASE sworld_dev;
    CREATE DATABASE sworld_dev OWNER andrey;
    GRANT ALL PRIVILEGES ON DATABASE sworld_dev TO nikolays;

Then:
::
    pg_dump sworld | psql sworld_dev

****
TODO
****

#. SSL certificates syncronization.
