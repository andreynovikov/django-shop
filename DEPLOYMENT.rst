************
Server setup
************

Historically server is run under latest Devian Stable.

The following packages are required:
::
    apt install sudo
    apt install rsync
    apt install python3-dev
    apt install postgresql
    apt install nginx
    apt install uwsgi
    apt install uwsgi-plugin-python3
    apt install memcached
    apt install redis-server
    apt install letsencrypt

The following packages are optional:
::
    apt install emacs-nox
    apt install dnsutils
    apt install htop

Master/slave cold redundancy server scheme is used for High Availability. It means that two servers are kept identical
but if one server fails manual actions should be performed to switch to another server (described later).

Server should have SMTP daemon running. For Debian it's Exim and it does not need any specific configuration.

Three users should be created in this particular order (to preserve uids):
::
    adduser andrey
    adduser nikolays
    adduser import1c

Users andrey and nikolays should be added to suduers and www-data groups. User import1c should not be able to login
interactively (shell set to ``/bin/false``).

****************
PostgreSQL setup
****************

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

All sites are located in ``/www`` folder.

All sites are kept in git on GitHub. Each site is configured as separate Python virtualenv and has its own ``requirements.txt``
file. So, general deployment scheme looks like this:
::
    
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
