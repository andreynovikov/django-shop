# Server setup with Ansible

`site.yml` sets up the production server and the backup host as [deploy/README.md](../README.md) describes. Each task
describes a state, such as "this package is installed" or "this line is in that file", and Ansible changes a server
only where it differs. So a run is safe to repeat: on a server that is already set up it changes nothing, and after a
failure you fix the cause and run the same command again.

There are two ways to run it:

- On the new server itself, as root, with [setup-server.sh](setup-server.sh). This is the quick setup at the top of
  [deploy/README.md](../README.md#quick-setup-with-ansible): it needs nothing but ssh on your computer.
- From your own computer over ssh, see [New production server](#new-production-server). This is the usual way to apply
  changes of the playbook to a running server, and the only way for the backup host.

## First rollout and later runs

A run sets up what the server lacks, so the same command sets up a new server and keeps a running one in order. There
is no switch between the two, each part looks at what is there:

- A backend site of the vault without a commit is cloned from `server_git_repository`, gets its venv, its database
  migrated and its static files collected. Later runs leave its code and venv alone: `deploy-backend` updates them,
  from GitHub Actions or by hand, see "Backend deployment" in [deploy/README.md](../README.md#backend-deployment).
- A storefront without a container is started, see "Storefront service user" in
  [deploy/README.md](../README.md#storefront-service-user). Later deploys come from GitHub Actions.
- A storefront with XML feeds whose directory has no feed templates gets those of its branch.
- A certificate that an enabled site lacks is requested, and one that lacks an alias of the inventory is expanded,
  see "TLS certificates" in [deploy/README.md](../README.md#tls-certificates).

The secret files are the exception: every run writes them from the vault, see below.

The run ends with a `Summary` of what it couldn't finish, such as certificates whose names don't reach the server yet.

## Secrets

The secret files of the server are kept in `group_vars/production/secrets.yml`, encrypted with
[Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html). Ansible reads that file by itself for
the production server, and decrypts it in memory when the run is given the vault password: `setup-server.sh` asks for
it, other commands ask with `-J` (`--ask-vault-pass`). The file is gitignored, because the repository is public. Keep
it in the password manager with `inventory.yml` and the vault password, which nobody can recover.

The commands of `ansible-vault`, run in this directory, all ask for the vault password:

- `ansible-vault edit group_vars/production/secrets.yml` opens a decrypted copy in your editor (`$EDITOR`) and
  encrypts it again when you save;
- `ansible-vault view group_vars/production/secrets.yml` shows it;
- `ansible-vault rekey group_vars/production/secrets.yml` changes the password.

It holds the files whole, as YAML block scalars:

```yaml
vault_backend_files:                # the backend sites to set up, with their secret files
  www.sewing-world.ru:
    .env: |
      SECRET_KEY=...
    .env.admin: |
      ALLOWED_HOSTS=...
vault_storefront_env:               # .env.storefront by deployment name; stage gets sworld's unless it has its own
  sworld: |
    API_SERVER=...
  janome: |
    ...
vault_nginx_htpasswd: |             # /etc/nginx/htpasswd
  user:$apr1$...
vault_restic_password: ...          # the backup repository's password, see "Database backups"
vault_ssh_host_keys:                # optional: the server's ssh host keys, so that a new server keeps its identity
  ed25519: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    ...
```

The vault is the source of the files: a run replaces a file edited on the server with the vault's, and keeps the old
one next to it with a date in its name. When a file changes, the run restarts what reads it: the site's uWSGI apps and
Celery for a backend site, the container for a storefront. So to change a secret, edit the vault, then run the
playbook, `--tags backend` or `--tags deployment` is enough. The tasks that handle secrets don't print them, also not
with `--diff`.

A backend site is set up only if `vault_backend_files` has its files, so a server without `dev.sigalev.ru` in the
vault doesn't get one.

### Making the vault from a running server

`export-secrets.sh` reads the secret files of a server set up by hand and writes them into an encrypted
`group_vars/production/secrets.yml`, asking for a new vault password. It also prints two settings of the server for
`inventory.yml`: the deploy account's public key and the aliases of the certificates.

```sh
./export-secrets.sh -K --limit server.example.ru
```

Then run the playbook with `--check --diff -J`: it shows no change in the secret files when the vault matches the
server.

### GitHub's copies of the storefront configuration

The `ENV_FILE` secret of each storefront's GitHub environment must be the same as its `.env.storefront`, see "Storefront
configuration" in [deploy/README.md](../README.md#storefront-configuration). After changing `vault_storefront_env`,
set them from the vault with [GitHub's CLI](https://cli.github.com), signed in with access to the repository:

```sh
ansible-playbook -i inventory.yml github-env.yml -J
```

Then build new images, with a push or by re-running the last push's workflow, if the build uses what changed.

## What is left to do by hand

- each user's OTP codes (`google-authenticator`), see "Two factor authentication";
- the uploaded files in `media/` of a new server, see the quick setup;
- outside the server: the database server's allowed addresses, DNS, and GitHub's settings when they change;
- the backup host, whose repository password then goes into the vault.

PostgreSQL runs on a separate server.

## Nginx sites

The `nginx` tag installs [the bundled configuration](roles/server/files/nginx/) with the main `nginx.conf`,
the production sites, their custom includes, and `/etc/nginx/htpasswd` from the vault. Debian supplies the standard
files and the Brotli module. The role enables the sites in `server_nginx_sites_enabled` whose certificates are present,
and gets the missing ones, see "TLS certificates" in [deploy/README.md](../README.md#tls-certificates). Move a site to
`server_nginx_sites_disabled` to remove only its `sites-enabled` entry. To also delete its installed config, remove the
bundled file and move the site to `server_nginx_sites_removed`. The dev site is disabled. The stats site (Grafana and
Prometheus) is in `server_nginx_monitoring_sites`, enabled with the `prometheus` section and disabled without it.

Review and apply from this directory:

```sh
ansible-playbook -i inventory.yml site.yml --limit server.example.ru -K -J --tags nginx --check --diff
ansible-playbook -i inventory.yml site.yml --limit server.example.ru -K -J --tags nginx,logrotate
```

The playbook runs `nginx -t` on the assembled configuration before reloading nginx. If validation fails,
Ansible stops before reload. Correct the on-disk files or restore their timestamped backups before retrying.
Check mode previews file and link changes. Validation runs on an apply because nginx needs the installed files.
The `logrotate` tag installs the rule for the legacy redirect log alongside the application log rotation rules.

The uWSGI and Celery apps are listed in `roles/server/defaults/main.yml`. The playbook writes their configuration
on every run, but starts their units only once the site is cloned into `/www` and has its `.venv`. That run also
hands the site's `logs`, `media`, `static`, `.cache` and `import` to the service user, and makes `.env` and
`.env.admin` readable by root and the service user only. It stops before that if an nginx site still writes its logs
into `/www`: they belong in `/var/log/nginx`, see "Nginx setup" in [deploy/README.md](../README.md#nginx-setup).

sshd lets in only the users of `server_users` and `server_ssh_extra_users`. If GitHub Actions deploys as another
user (the `DEPLOY_USER` secret), add it to `server_ssh_extra_users` before the run, or the deploys stop working.

The `firewall` tag turns on nftables. Keep an ssh session open on the first run of it. If something else connects
to the server, for example over the private network, add a rule for it to `server_firewall_rules`. Where the
hosting's firewall filters the traffic instead, set `server_firewall: false` in `inventory.yml`, and let that firewall
allow the same: tcp 22, 80 and 443, udp 443, and tcp 10050 from the hosting's Zabbix servers. The playbook then
skips the section, but it does not turn off nftables that an earlier run turned on.

The `prometheus` tag installs Prometheus and node-exporter, their scrape jobs and alert rules, Docker's metrics and
the cAdvisor and celery-exporter containers, see "Prometheus" in [deploy/README.md](../README.md#prometheus).
`promtool` checks the configuration before Prometheus reloads it. It writes the whole of `/etc/docker/daemon.json`,
and a change of it restarts Docker. Set `server_prometheus: false` in `inventory.yml` where the server is monitored
otherwise; the playbook then leaves whatever monitoring there is alone.

## Preparation

Install Ansible on your computer. Debian's `ansible` package includes the collections the playbook uses, the
smaller `ansible-core` does not:

```sh
sudo apt install ansible
```

Copy the example inventory, the list of servers and their settings. `inventory.yml` is ignored by git, because it
holds password hashes:

```sh
cd deploy/ansible
cp inventory.example.yml inventory.yml
```

Put the real host names in place of `server.example.ru` and `backup.example.ru`, and fill in the settings it
describes. All the commands below run in `deploy/ansible`.

## New production server

The quick setup at the top of [deploy/README.md](../README.md#quick-setup-with-ansible) runs the playbook on the server
itself. To run it from your computer instead:

The playbook creates the users and disables ssh login as root. On a new server none of the users exists yet, so the
first run connects as root, and every later run connects as your own user. That only works if you can log in as your
user and use sudo once root is locked out, so give yourself an ssh key and a password before the first run.

1. Make a hash of your password. It asks for the password twice and prints a line that starts with `$6$`:

   ```sh
   openssl passwd -6
   ```

2. Add the hash and your public key (`cat ~/.ssh/id_ed25519.pub`) to your user in `inventory.yml`:

   ```yaml
   server_users:
     - name: andrey
       groups: [adm, docker, sudo, www-data]
       password: '$6$...'
       ssh_keys:
         - ssh-ed25519 AAAA... andrey@laptop
   ```

   The password is set only when the user is created. If you change it later with `passwd`, later runs keep it.

3. Let your key log in as root, and install what Ansible itself needs on the server. A minimal Debian install may lack
   `sudo` and `python3`, and without them every task fails:

   ```sh
   ssh-copy-id root@server.example.ru
   ssh root@server.example.ru 'apt update && apt install -y sudo python3'
   ```

   Check that Ansible reaches the server. It should answer `"ping": "pong"`:

   ```sh
   ansible -i inventory.yml server.example.ru -u root -m ping
   ```

4. Run the first section, "Server setup" with tag `server`, as root. It installs the packages, creates the users and
   disables root login. `--limit` keeps the run to this server, `-u root` connects as root, `-J` asks for the vault
   password:

   ```sh
   ansible-playbook -i inventory.yml site.yml --limit server.example.ru -u root -J --tags server
   ```

   Ansible prints every task with its result, then a summary for each server:

   ```text
   TASK [server : Install packages] ***********************************************
   changed: [server.example.ru]
   ...
   PLAY RECAP *********************************************************************
   server.example.ru          : ok=21   changed=19   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
   ```

   `ok` means that nothing had to change, `changed` that the task changed the server. The run succeeded when
   `failed` and `unreachable` are 0.

5. Keep the root session open and check from another terminal that your user can log in and use sudo:

   ```sh
   ssh -t andrey@server.example.ru sudo -v
   ```

6. Run the whole playbook as your user. `-K` asks for your sudo password, the one hashed in step 1:

   ```sh
   ansible-playbook -i inventory.yml site.yml --limit server.example.ru -K -J
   ```

   Ansible logs in with your local login name. If yours differs on the servers, add `-u andrey`.

7. Each user runs `google-authenticator -t -d -f -r 3 -R 30 -W`. Until then they can log in with an ssh key only,
   because ssh logins with a password also ask for an OTP code now.

The production server takes the backup repository password from `vault_restic_password` of the vault. Without it, a
run from your computer copies it from the backup host, so set up that one first if it is new. `-K` gives the same sudo
password to both servers. Until there is a backup host, leave the `backup` group of `inventory.yml` empty: the
production server then skips its "Database backups" section.

## New backup host

The backup host is a machine of ours where you already log in as your user, so it needs only one run:

```sh
ansible-playbook -i inventory.yml site.yml --limit backup.example.ru -K -J
```

Then save the repository password in the password manager, and in `vault_restic_password` of the vault. Without it
the backups cannot be read:

```sh
ssh -t backup.example.ru sudo cat /etc/db-backup/restic-password
```

The production server logs in to the backup host with `backup_host_login_password`. Keep it encrypted with
ansible-vault rather than as plain text in `inventory.yml`. This command asks for the vault password, then for the
variable name, answer `backup_host_login_password`, then for the password itself:

```sh
ansible-vault encrypt_string --prompt
```

Paste its output under `vars` of the `backup` group.

## Later runs

After you change the playbook or the inventory, run the same command as in step 6. Some useful options:

- `--check --diff` shows what a run would change, without changing anything. Use it on a server that is already set
  up, on a new one tasks fail because the packages they configure are not installed yet.
- `--tags nginx` runs one section only. `--list-tags` and `--list-tasks` show what there is.
- `--limit` picks the servers, without it the run covers every server in the inventory.
