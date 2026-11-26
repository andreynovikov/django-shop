# Server setup with Ansible

`site.yml` sets up the production server and the backup host as [deploy/README.md](../README.md) describes. Ansible
runs on your own computer and does its work on the servers over ssh. Each task describes a state, such as "this
package is installed" or "this line is in that file", and Ansible changes a server only where it differs. So a run is
safe to repeat: on a server that is already set up it changes nothing, and after a failure you fix the cause and run
the same command again.

## What is left to do by hand

These steps stay manual, as [deploy/README.md](../README.md) describes them:

- the nginx `htpasswd` file (copy privately or provision separately with ansible-vault);
- users' OTP codes (`google-authenticator`);
- TLS certificates of the sites and of the backup host;
- the backend checkout and site configuration, including `.env` files, the storefronts' `.env.storefront` and their
  feed templates;
- saving the backup repository password in the password manager.

PostgreSQL runs on a separate server.

## Nginx sites

The `nginx` tag installs [the bundled configuration](roles/server/files/nginx/) with the main `nginx.conf`,
the production sites, and their custom includes. Debian supplies the standard files and the Brotli module.
The role enables the sites in `server_nginx_sites_enabled`. Move a site to `server_nginx_sites_disabled` to
remove only its `sites-enabled` entry. To also delete its installed config, remove the bundled file and move
the site to `server_nginx_sites_removed`. The dev site is disabled and the stats site is removed.

Provision the TLS certificates and their keys at the paths referenced in the enabled site files. Also install
`/etc/nginx/htpasswd` with `root:www-data` ownership and `0640` permissions. Provision these files before
applying the `nginx` tag. Keep the password hashes and keys outside git.

Review and apply from this directory:

```sh
ansible-playbook -i inventory.yml site.yml --limit server.example.ru -K --tags nginx --check --diff
ansible-playbook -i inventory.yml site.yml --limit server.example.ru -K --tags nginx,logrotate
```

The playbook runs `nginx -t` on the assembled configuration before reloading nginx. If validation fails,
Ansible stops before reload. Correct the on-disk files or restore their timestamped backups before retrying.
Check mode previews file and link changes. Validation runs on an apply because nginx needs the installed files.
The `logrotate` tag installs the rule for the legacy redirect log alongside the application log rotation rules.

The uWSGI and Celery apps are listed in `roles/server/defaults/main.yml`. The playbook writes their configuration
on every run, but starts their units only once the site is cloned into `/www` and has its `.venv`. Run it again
after you deploy a site. That run also hands the site's `logs`, `media`, `static`, `.cache` and `import` to
the service user, and makes `.env` and `integrations.py` readable by root and the service user only. It stops before
that if an nginx site still writes its logs into `/www`: they belong in `/var/log/nginx`, see "Nginx setup" in
[deploy/README.md](../README.md#nginx-setup).

sshd lets in only the users of `server_users` and `server_ssh_extra_users`. If GitHub Actions deploys as another
user (the `DEPLOY_USER` secret), add it to `server_ssh_extra_users` before the run, or the deploys stop working.

The `firewall` tag turns on nftables. Keep an ssh session open on the first run of it. If something else connects
to the server, for example over the private network, add a rule for it to `server_firewall_rules`. Where the
hosting's firewall filters the traffic instead, set `server_firewall: false` in `inventory.yml`, and let that firewall
allow the same: tcp 22, 80 and 443, udp 443, and tcp 10050 from the hosting's Zabbix servers. The playbook then
skips the section, but it does not turn off nftables that an earlier run turned on.

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

Put the real host names in place of `server.example.ru` and `backup.example.ru`. All the commands below run in
`deploy/ansible`.

## New production server

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
   disables root login. `--limit` keeps the run to this server, `-u root` connects as root:

   ```sh
   ansible-playbook -i inventory.yml site.yml --limit server.example.ru -u root --tags server
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

6. Provision the TLS files and nginx `htpasswd` as described in [Nginx sites](#nginx-sites), then run the whole
   playbook as your user. `-K` asks for your sudo password, the one hashed in step 1. If you need to bootstrap
   the rest of the server before the TLS files are ready, use `--skip-tags nginx` and apply the `nginx` tag
   after provisioning them.

   ```sh
   ansible-playbook -i inventory.yml site.yml --limit server.example.ru -K
   ```

   Ansible logs in with your local login name. If yours differs on the servers, add `-u andrey`.

7. Each user runs `google-authenticator -t -d -f -r 3 -R 30 -W`. Until then they can log in with an ssh key only,
   because ssh logins with a password also ask for an OTP code now.

The production server copies the backup repository password from the backup host, so set up that one first if it is
new. `-K` gives the same sudo password to both servers. Until there is a backup host, leave the `backup` group of
`inventory.yml` empty: the production server then skips its "Database backups" section.

## New backup host

The backup host is a machine of ours where you already log in as your user, so it needs only one run:

```sh
ansible-playbook -i inventory.yml site.yml --limit backup.example.ru -K
```

Then save the repository password in the password manager. Without it the backups cannot be read:

```sh
ssh -t backup.example.ru sudo cat /etc/db-backup/restic-password
```

The production server logs in to the backup host with `backup_host_login_password`. Keep it encrypted with
ansible-vault rather than as plain text in `inventory.yml`. This command asks for a vault password, then for the
variable name, answer `backup_host_login_password`, then for the password itself:

```sh
ansible-vault encrypt_string --prompt
```

Paste its output under `vars` of the `backup` group and add `-J` to every `ansible-playbook` command, so that
Ansible asks for the vault password.

## Later runs

After you change the playbook or the inventory, run the same command as in step 6. Some useful options:

- `--check --diff` shows what a run would change, without changing anything. Use it on a server that is already set
  up, on a new one tasks fail because the packages they configure are not installed yet.
- `--tags nginx` runs one section only. `--list-tags` and `--list-tasks` show what there is.
- `--limit` picks the servers, without it the run covers every server in the inventory.
