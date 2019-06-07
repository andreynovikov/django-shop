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
    apt install python3-dev
    apt install python3-virtualenv
    apt install postgresql
    apt install nginx
    apt install uwsgi
    apt install uwsgi-plugin-python3
    apt install memcached
    apt install redis-server
    apt install letsencrypt
    apt install git

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
    adduser import1c

Add users ``andrey`` and ``nikolays`` to ``suduers`` and ``www-data`` groups. Disable interactive login for user ``import1c``
(set shell to ``/bin/false``). Rename ``import1c`` group to ``sftponly``.

Setup correct timezone:
::
    echo "Europe/Moscow" > /etc/timezone
    ln -fs /usr/share/zoneinfo/Europe/Moscow /etc/localtime
    dpkg-reconfigure -f noninteractive tzdata

Enable time syncronization. Create ``/etc/cron.daily/ntpdate`` file:
::
    !#/bin/sh
    /usr/sbin/ntpdate -u ru.pool.ntp.org

***********
Nginx setup
***********

***********
UWSGI setup
***********

************
Celery setup
************

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
    python3 -m virtualenv -p python3 env
    source env/bin/activate
    pip install -r requirements.txt
    deactivate
    mkdir media
    mkdir static
    mkdir logs
    sudo chown nikolays:www-data logs
    mkdir st_search
    sudo chown nikolays:www-data st_search

Import
******

Disable interactive login for user ``import1c``: set shell to ``/bin/false``.

Create import folder ``/home/import1c/import``.

Log rotation
************

************************
Master/slave replication
************************

There are two separate replication processes: file replication and database replication. Only site files (``/www``)
are replicated automatically. All server configuration and maintenance should be replicated manually. Servers distinguish
who is master by presence of the ``/primary_server`` file.

File replication
****************

Files are replicated by ``rsync`` executed by ``cron`` on hourly basis.

Database replication
********************

Configure PostgreSql on master:
::
    listen_addresses = '*'
    wal_level = replica
    max_wal_senders = 3
    wal_keep_segments = 16
    hot_standby = on

Permit replication connection in ``/etc/postgresql/9.6/main/pg_hba.conf``:
::
    host     replication     replicator      193.19.119.252/32       md5

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

****
TODO
****

#. SSL certificates syncronization.
