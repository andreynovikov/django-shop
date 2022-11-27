************
Server setup
************

Historically server is run under latest Devian Stable.

The following packages are required:
::
    apt install sudo
    apt install ntpdate
    apt install exim4
    apt install rsync
    apt install python3
    apt install python3-venv
    apt install postgresql
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
    apt install libtidy5deb1

The following packages are optional:
::
    apt install less
    apt install emacs-nox
    apt install dnsutils
    apt install htop

Master/slave cold redundancy server scheme is used for High Availability. It means that two servers are kept identical
but if one server fails manual actions should be performed to switch to another server (described below).

Create three users in this particular order (to preserve uids):
::
    adduser andrey
    adduser nikolays

Add users ``andrey`` and ``nikolays`` to ``sudu`` and ``www-data`` groups.

Disable ssh root login:
::
    PermitRootLogin no
    PasswordAuthentication yes

Optionaly adjust ssh keep-alives:
::
    ClientAliveInterval 60
    ClientAliveCountMax 8

Setup correct timezone:
::
    echo "Europe/Moscow" > /etc/timezone
    ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime
    dpkg-reconfigure -f noninteractive tzdata

Enable time syncronization. Create ``/etc/cron.daily/ntpdate`` file:
::
    #!/bin/sh
    /usr/sbin/ntpdate -u ru.pool.ntp.org

Reconfigure Exim for internet mode to be able to send mails:
::
    dpkg-reconfigure exim4-config

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
    ChallengeResponseAuthentication	yes

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
    
    include /etc/nginx/win-utf;

****************
PostgreSql setup
****************

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
    ListenStream=/var/run/uwsgi/%i.socket
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
            --socket /var/run/uwsgi/%i.socket
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

Install pm2 globally:
::
    npm install pm2 -g

Add ``export PM2_HOME=/www/.pm2`` to ``/etc/profile``

Create systemd service file:
::
    sudo mkdir /www/.pm2
    sudo chown www-data:www-data /www/.pm2
    sudo chmod g+w /www/.pm2
    sudo pm2 startup systemd -u www-data -hp /www --service-name pm2
    sudo systemctl enable pm2

*****************
Environment setup
*****************

All sites are located in ``/www`` folder. Replication should be configured for this folder (see below). The following
description is included for general reference.

All sites are kept in git on GitHub. Each site is configured as separate Python virtualenv and has its own ``requirements.txt``
file. So, general deployment scheme looks like this:
::
    cd /www
    git clone git@github.com:andreynovikov/django-shop.git janome.club
    cd janome.club
    git checkout janome
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    deactivate
    mkdir media
    mkdir static
    mkdir logs
    sudo chown nikolays:www-data logs
    mkdir st_search
    sudo chown nikolays:www-data st_search
    
For React sites:
::
    pm2 start npm --name "janome" -- start

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
