# Runbook: WALLIX Access Manager farm

Date: 2026-09-24. Verified against Access Manager 6.0.5 (design baseline) and, on the Bastion
side, Bastion 12.3.2. Primary sources: [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) (AG),
[Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) (DG) and
[Access Manager 6.0.5 Users and Approvers Guide](https://doc.wallix.com/) (UG). These three guides are
customer documentation behind the doc.wallix.com login; section numbers refer to the 6.0.5
editions. Section 11 keeps the Access Manager 5.2.4.0 facts that no longer apply, with their
public sources. Quotes are verbatim; *inference* marks what the guides do not state.

Supporting role in this repository: Access Manager is the SAML service provider that Trustelem
authenticates for the web path. The farm settings that matter for that integration are the
trusted proxies (so the audit logs carry the real client address rather than the proxy's), the
node-shared `crypto.install.key` (copied between nodes, DG 5.1), and the replication
procedure (SAML identity providers are database content and replicate; `wabam.properties`,
appliance settings and server certificates do not, DG 6).

## 1. Appliance facts

- Appliance only: "WALLIX Access Manager cannot be installed on third-party hardware" (DG 3.1).
  Virtual images exist for KVM, Hyper-V, Nutanix AHV, OpenStack, Proxmox and VMware vSphere, and
  cloud images for AWS, Azure, Outscale, GCP and Alibaba Cloud (DG 3.2.1).
- Services: the web application is the systemd service `wabam` (`systemctl restart wabam`);
  the front proxy is Proxyma, configured in `/etc/proxyma/config.toml` (`systemctl reload
  proxyma`), a Pingora-based service that also lists a "Local Apache endpoint" (AG 8.4.2,
  8.5.2). Configuration lives in `/etc/wabam`: "By default, the wabam.properties file is
  located in /etc/wabam" (DG 5.1). The web server is "typically Jetty" (AG 8.2). The guides
  do not state the Debian or Java version: "Refer to the Release Notes document to learn more
  about the technical requirements of this version" (DG ch. 2).
- Interfaces: "By default, WALLIX Access Manager requires at least two network interfaces for
  security and role separation" (DG 1.2). At initialisation the Administration service is
  "Mandatory" on the 1st interface ("This service cannot be deactivated") and User Access is
  "Optional" on the 2nd ("This service can be deactivated") (DG 4.3). Global organization URL:
  `https://INTERFACE_1/CONTEXT_PATH/global`; organization URL on either interface; appliance
  administration `https://INTERFACE_1/accounts/login` as `wabsuper` (DG 1.2). "In case of Fully
  Qualified Domain Name (FQDN), there can only be one FQDN for all interfaces." (DG 1.2).
- SSH administration: "SSH administration is available using INTERFACE_1 on port 2242, with
  the wabadmin account", then `super` and `sudo -i` (DG 1.2, 4.2).
- Default accounts (DG 2.1): `wabadmin` (SecureWabAdmin), `wabsuper`, `wabupgrade`, GRUB user
  `wabbootadmin` (SecureWABBoot), Access Manager `admin` / `admin` (on AWS "admin-{instanceID}").
  The guides contradict each other on the default administrator: "This account can be deleted
  and can be restored if deleted" (DG 2.1) against "The default administrator account for the
  global organization (admin) cannot be deleted" (AG 4.2.7). Create a named global administrator
  and log in with it (DG 4.4 steps 4 and 6) whichever holds.
- Database: embedded MariaDB; for an external database "Only MySQL is supported", with an
  "Azure database" option and a "Secure" (TLS) option; the privileged account "is not saved"
  (AG 8.3). The appliance commands "only support MySQL Community Server and MariaDB Server
  databases" (AG 11.2).
- Vendor rule on the appliance: "The installation of external components such as Endpoint
  Detection and Response (EDR), backup, or monitoring agents is forbidden." (DG 1.3, AG 1.3).
- Disk quotas: `/var/log` "is limited to 10GB" and `/home` "is limited to 4GB" (DG 2.4).
- Compatibility: "WALLIX Access Manager 6.0.5 is compatible with: ... WALLIX Bastion 12.0 and
  above" (DG 10.1). "Any network equipment (proxy or firewall) positioned in front of WALLIX
  Access Manager must support the WebSocket protocol." (DG 10.1).

### Sizing (DG 2.3)

Measured by WALLIX with Access Manager 6.0.3 and Bastion 12.3.4 at identical sizes; sessions
without / with video recording:

| Access Manager vCPU | Access Manager RAM | RDP sessions | SSH sessions |
|--------------------:|-------------------:|-------------:|-------------:|
| 4 | 8 GB | 85 / 80 | 110 / 100 |
| 8 | 16 GB | 200 / 190 | 220 / 210 |
| 8 | 32 GB | 305 / 300 | 510 / 500 |
| 16 | 32 GB | 320 / 310 | 620 / 600 |

Minimum for each replicated node: "RAM: 4 GB", "CPU: 2 cores", "Disk: 50 GB" (DG 6). On
vSphere use one socket, shares High and a reservation (DG 3.2.2.1). Java heap: the
`wabam.vmoptions` default "allocates 70% of the system’s total physical memory (RAM) to the JVM"
(`-XX:MaxRAMPercentage`, or a fixed `-Xmx`), in `/etc/wabam/wabam.vmoptions`, checked in
`tech.log` (AG 8.5.1).

## 2. Install node 1

1. Verify the image signature (`gpg --verify`, `sha256sum -c`) and deploy it (DG 3.2.1).
2. Console wizard: installation, keyboard, `wabadmin` password change, `wabsuper`,
   `wabbootadmin` and `wabupgrade` passwords, hostname, `eth0` address, FQDN (DG 4.1). Static
   addresses outside cloud platforms ("we strongly discourage configuring DHCP").
3. Harden the system (DG 4.2): `wallix-luks-update --interactive --change-passphrase` on premises
   (the default disk passphrase "is common to all appliances and stored in a file in clear") or
   `wallix-luks-update --reencrypt` on clouds other than AWS; store SSH public keys for
   `wabadmin` and `wabupgrade`; run `WABSecurityLevel` for every service. With the interactive
   mode the passphrase must be typed at every boot from the hypervisor console.
4. Appliance interface `https://INTERFACE_1/accounts/login` as `wabsuper`: network, time zone
   and NTP, service mapping (Administration on the 1st interface, User Access on the 2nd)
   (DG 4.3).
5. Global organization: change the password, install the licence, create a named global
   administrator, take a backup, log in as the new administrator, reboot (DG 4.4).
6. Licence. "During the initial installation, Access Manager creates a 31-day evaluation license
   which allows up to 5 concurrent users." (AG 8.1). GUI: About > Access Manager License >
   Download context file, send it to support, upload `wallix_license.json`. CLI as root (AG 8.1.3):

```
wabam-license-list
wabam-context-file-download -c /tmp/licenses/wabam_context_file.json
wabam-license-import -l /root/wallix_license.json
```

   Revocation is `wabam-revoke-license` in AG 8.1.3 but `wabam-license-revoke` in the AG 11.2
   command table; check which exists on the node. "Connections of the administrator of the
   global organization are not counted." (AG 8.1).
7. Portal certificate with a SAN for every name clients and the load balancer use (section 4),
   uploaded as PEM with an unencrypted key (AG 8.5.4.4):

```
wallix-proxyma-rotate-tls-certificate -c <path_to_certificate.pem> -k <path_to_private_key.pem>
```

   The guide prints the first option with an en dash (`–c`); type a hyphen. Server certificates
   are not replicated (DG 6): repeat on node 2. WAMUT requires "at least one Subject Alternative
   Name field specified with the DNS used to connect" (UG 4.5).
8. Inactivity timeout: application setting `session.maxInactiveInterval` in minutes, 0
   disables it; "Users must log out of their current session for the changes to take effect."
   (AG 7.3).

## 3. Add node 2 and replicate the database

HA Database Replication (DG 6):

- "In WALLIX Access Manager, communication between databases is secured via an SSH tunnel with
  port forwarding. This tunnel is maintained by the autossh service".
- "Replication is configured in Master/Master mode, supporting two servers (nodes) that
  synchronize data bidirectionally. Both nodes communicate using outbound port 3307 and inbound
  port 3306". *Inference:* 3306 and 3307 stay inside the tunnel, so the only port to open
  between the nodes is SSH 2242 on the administration interfaces ("HA Database Replication
  relies on this port being open", DG 2.2).
- Maximum two nodes. The primary Master is the node where the setup is run.
- Requirements: same subnet, "connected directly or through only one router"; same version; NTP
  to the same time zone ("Replication across multiple time zones is not supported"); an
  interface with administration features on every node. "Both Access Manager nodes must have
  two network interfaces: 1. User Access to handle standard user connections. 2.
  Administration for SSH management between nodes. It must allow SSH connections on port 2242
  for secure replication setup." In the cloud "only one network interface is required" (DG 6.1).
- "FQDN and IPv6 are not supported in the HA feature configuration. You must only use the IPv4
  address for Access Managers." (DG 6.1).
- "Be cautious when cloning virtual machines, as this can cause UUID conflicts in MySQL."
- Not replicated: "wabam.properties file", "Appliance configurations", "Server certificates".
  "Several parameters such as some application settings or log levels can be modified through
  the web interface. However, these values are stored in the wabam.properties file. Because this
  file is excluded from replication, these parameters are not replicated."

Procedure (DG 6.1), as root on the primary Master, after backing up both nodes ("During setup,
the primary Master Access Manager’s database replaces the databases of the other Access Manager
node, resulting in the loss of their existing data."):

```
wallix-replication --prerequisite-check
wallix-replication --create-conf-file     # 1 = Master/Master, then IPv4 address, wabadmin and wabsuper passwords of each node
wallix-replication --install
wallix-replication --monitoring
wallix-replication --install-monitoring   # optional: cron that collects the replication status
```

Other options (DG 6.2): `--resync`, `--dump-resync`, `--status`, `--uninstall` ("Uninstall
replication on every node, to run on Master"), `--stop`, `--start`, `--version`,
`--uninstall-monitoring`, `--debug`. `--install` and `--dump-resync` restart both databases and
erase the secondary's data ("Not all tables from the database are affected"); `--resync` restarts nothing; `--uninstall` restarts both without
erasing. The `--create-conf-file` prompt also offers "2. Master/Slave(s)", which the guide does
not document further.

When replication is used, the manual `wabam.properties` copy of section 3.1 "is not required.
The replication installation automatically performs all necessary steps." (DG 5.1).

Authentication priority: authenticators with the same factor are tried in Priority order for
high availability (AG 4.4.2).

### 3.1 Two nodes without replication (shared external database)

DG 5.1: deploy node 1, deploy node 2, then copy from node 1 into node 2's
`/etc/wabam/wabam.properties` "The installation encryption key (crypto.install.key)", "The
database settings (all properties with a name starting with db.connections)" and "The
administrator credentials (all properties beginning with user.admin)", then
`systemctl restart wabam` on node 2.

### 3.2 Per-node settings

Because `wabam.properties` does not replicate, set on each node: `rdp.clientName` if targets must
tell the nodes apart ("As the wabam.properties file is not replicated, you assign a unique RDP
client name to each WALLIX Access Manager", AG 7.7.2), any application setting or log level
stored there, `WABSecurityLevel` ("manually apply the security level to each node", AG 8.5.3),
the TLS certificate, `/etc/proxyma/config.toml`, network, NTP and SNMP.

## 4. Load balancer settings

| Item | Value | Source |
|------|-------|--------|
| Listener | HTTPS 443 with WebSocket; the inbound port list has 443, 2242 and SNMP only, no HTTP 80 | DG 2.2, 10.1 |
| Persistence | "it requires stateful load balancing ... session affinity (sticky sessions)"; "X.509 authentication is not compatible with Layer 7 load balancers (cookie-based mechanism). For all other types of authentication, WALLIX recommends implementing Layer 7 load balancing whenever possible." | DG 5 |
| TLS | "Use TLS passthrough when possible because it ensures that WALLIX Access Manager receives the original client SNI value"; with termination and re-encryption, add the internal hostname to the certificate SAN or forward the client SNI (for example `proxy_ssl_server_name`). *Inference:* L7 cookie affinity needs termination, so this design terminates on the load balancer and forwards the client SNI | AG 8.2.1 |
| Ciphers | default HTTP security level allows only ECDHE-ECDSA-AES256-GCM-SHA384, ECDHE-RSA-AES256-GCM-SHA384, ECDHE-ECDSA-AES128-GCM-SHA256, ECDHE-RSA-AES128-GCM-SHA256; the TLS versions are not stated (*inference:* TLS 1.2 suites); the load balancer's backend profile must offer one of them | DG 8.1 |
| SNI | strict since 5.2: a missing or wrong hostname returns "HTTP ERROR 400 Invalid SNI"; Proxyma `verify_server_cert_hostname` "Default value: true"; clients must use a hostname, "Using an IP address bypasses SNI and causes validation to fail" | AG 8.2, 8.2.1, 8.5.2 |
| Forwarded headers | Proxyma `trusted_proxies` = load balancer addresses ("used to validate client IP addresses from the X-Forwarded-For header"); `prefer_forwarded_header` to prefer `Forwarded` over `X-Forwarded-For` | AG 8.5.2 |
| Rate limits | Proxyma `dos_filter_activated`, `max_proxy_request_per_second`, `overrate_delay_requests`, `overrate_delay_ms` (above the extra allowance, HTTP 429), `ip_whitelist`, `max_concurrent_connections_per_ip`, `max_concurrent_connections_global` (0 = no limit); no defaults are stated | AG 8.5.2 |
| Appliance firewall | behind a load balancer, WAF or reverse proxy: "Deactivate the Limit the number of parallel connections per IP option" (default 30 per IP) | AG 8.4.5.1 |
| Health check | a HEALTH_VIEW right "Allows access to the API endpoint that provides the health check and status of the WALLIX Access Manager"; the endpoint path is not given (gap A3). Until WALLIX gives it, probe with an HTTPS GET of `/wabam/` using the portal FQDN as SNI and Host (*inference:* an IP-based probe gets the 400 Invalid SNI answer) | AG ch. 1 |
| Host header | trusted host names in `http_host_trusted_hostnames` of `/var/wab/etc/wabengine.conf`; `web.host.header.https` in `wabam.properties` for HTTP 1.0 requests | AG 8.5.4.1, 8.5.4.2 |

Why trusted proxies matter: *inference* from AG 8.5.2 and the 5.2 guide (section 11): without
them the audit logs carry the load balancer's address instead of the user's.

## 5. Parameters used by this design

`/etc/wabam/wabam.properties` (edit, then `systemctl restart wabam`; not replicated):

| Parameter | Default | Purpose | Source |
|-----------|---------|---------|--------|
| `crypto.install.key` | generated at install | encryption key, identical on all nodes | DG 5.1 |
| `db.connections.*` | | database connection | DG 5.1 |
| `user.admin.*` | | installation administrator | DG 5.1 |
| `web.contextPath` | `wabam` | URL context path; then `systemctl reload proxyma` | AG 8.4.2 |
| `web.host.header.https` | | host name returned for HTTP 1.0 requests | AG 8.5.4.2 |
| `web.header.X-Frame-Options` | DENY | clickjacking protection | AG 8.5.6.3 |
| `web.client.certificate.subhostname` | | X.509 host name (for example `x509`) | AG 8.5.4.5 |
| `rdp.clientName` | hostname | RDP client name per node | AG 7.7.2 |
| `wabam.uuid` | | node identifier in `wabam-sessions-count` | AG 9.6 |

`/etc/proxyma/config.toml` (AG 8.5.2): `trusted_proxies`, `prefer_forwarded_header`,
`verify_server_cert_hostname`, `verify_wsm_cert`, `verify_wsm_cert_hostname`, the DoS
parameters of section 4, and log levels `level`, `pingora_level`, `pingora_http_level`
(error to trace). Leave `am_endpoint` and `apache_endpoint` alone: "This parameter should only
be modified upon instruction from WALLIX support."

Application settings (Settings > Application Settings > Application tab):

| Parameter | Default | Purpose | Source |
|-----------|---------|---------|--------|
| `bastion.cluster.identical.mode` | not stated | Bastion cluster with identical configuration: sync from one node; "Copy the proxy certificates manually to every WALLIX Bastion in the cluster" | AG 3.3.3, 8.5.5.2 |
| `bastion.connection.timeout` | not stated | wait for the target over SSH or RDP; "This does not affect webapp sessions." | AG 8.5.5.3 |
| `restapi.connection.timeout` | not stated | Bastion REST API; "WALLIX recommends using the lowest practical value to reduce waiting times when a cluster node is unreachable" | AG 8.5.5.1 |
| `session.maxInactiveInterval` | | inactivity disconnect in minutes, 0 disables | AG 7.3 |
| `session.keepAlive` | | WebSocket ping in seconds, 0 disables, maximum 3600; restart needed | AG 7.1 |
| `sa.session.retention.days` | not stated | session audit retention | AG 9.1 |
| `purge.audit.active` | disabled | automatic purge of user audit data; `purge.audit.hourOfDayToExec` 3, `purge.audit.purgeOlderThanInDays` 270 | AG 9.4 |
| `ut.port.range` | | local ports for Universal Tunneling towards the Bastion | AG 7.9.2 |

## 6. Backup and restore

CLI (AG 8.3.3.2, 8.3.3.4), as root:

```
wabam-backup -d <backup_directory> -n <backup_filename> -p <backup_password>
systemctl stop wabam
wabam-restore -b <backup_file> -p <backup_password> -a <db_admin_password>
systemctl start wabam
```

- `wabam-backup` saves "the database, key store, and wabam.properties file" in an AES-256 zip;
  default name `backup_yyyyMMdd-hhmmss.wambk`.
- `wabam-restore` options: `-p` backup password, `-a` database administrator password, `-P` file
  holding that password, `-u` database administrator (default root). "The database restore
  operation can only be performed on a WALLIX Access Manager instance whose database schema
  version is the same." The AG 8.3.3 comparison table says the CLI is "Compatible with all
  supported versions"; treat the schema rule as binding.
- On a replicated Master, "WALLIX Access Manager pauses the replication. Then, after the
  restoration procedure is complete, WALLIX Access Manager automatically resynchronizes all
  nodes and resumes replication." (AG 8.3.3.4).
- GUI (Settings > Application Settings > Database tab): one organization or all, "Maximum 10 MB",
  "Backup/restore only possible on the same X.Y.Z version" (AG 8.3.3). Use the CLI for the farm.
- The GUI backup asks for an Encryption Key that protects "sensitive data (such as API keys
  used with WALLIX Bastion instances)" (AG 8.3.3.1). Keep `crypto.install.key` unchanged across
  a restore (*inference* from the 5.2 issue WAB-14912 in section 11).
- Global administrator reset: `wabam-restore-admin` (AG 4.8.1), or
  `wabam-restore-admin -f <configuration_file_path>` for the baseline organization administrator,
  with the service stopped first (AG 8.4.6).

Database commands (AG 8.3.1, 8.3.2), then `systemctl restart wabam`:

```
wabam-init-database -u root -a $(/opt/wab/sbin/WABChangeDbRootPassword)   # add --resetDbAccount to recreate the account
wabam-config-database --unixSocketAddress <unix_socket_file_path> -s <schema> -u <db_user> -p <db_user_password> -m <min_pool_size> -M <max_pool_size>
wabam-config-database -H <host> -P <port> -s <schema> -u <db_user> -p <db_user_password> -m <min_pool_size> -M <max_pool_size>
```

## 7. Upgrade

### 7.1 Minor upgrade in HA (6.x to 6.y, DG 8.2)

"Steps must be carried out in their given order to ensure a proper upgrade of the cluster."

1. Snapshot both nodes; `wabam-backup` on the primary Master.
2. Copy the ISO, `.iso.sha256sum` and `.iso.sha256sum.sig` to `/home/wabupgrade/` on each node
   (`scp -P 2242`).
3. On the primary Master, as root: `wallix-replication --stop`.
4. On both nodes (parallel allowed), as `wabupgrade`:

```
wallix-upgrade -i /home/wabupgrade/<ISO>.iso -c /home/wabupgrade/<ISO>.iso.sha256sum -s /home/wabupgrade/<ISO>.iso.sha256sum.sig
```

5. Reboot the primary Master, then the second node.
6. On the primary Master: `wallix-replication --dump-resync`, `wallix-replication --start`,
   `wallix-replication --monitoring`.
7. Check `WABSecurityLevel` on each node, then re-test the SAML login and a WAMUT tunnel.

Standalone is the same without steps 3 and 6 (DG 8.1). If the upgrade aborts, keep the
"Protective System Lockdown", audit in rescue mode, then `/opt/wab/bin/wallix-upgrade
--unlock-system` (DG 8.3). Rollback: restore the snapshot, or on a physical appliance reinstall
the previous ISO and run `wallix-config-restore.py` (DG 8.4).

### 7.2 Migration from 5.x to 6.x (DG 7)

"Due to significant changes introduced in version 6 to enhance performance and stability,
migrating to WALLIX Access Manager 6 requires a different approach from a standard upgrade. You
must import your existing data into a new instance using the backup/restore functionality."
Sources: "WALLIX Access Manager 5.1" and "WALLIX Access Manager 5.2" (DG 7.2). For a farm, build
a parallel 6.x cluster and switch over after validation (DG 7.1):

1. `wabam-backup` on the primary Master of the 5.x cluster.
2. Install 6.x on two new appliances.
3. On the new primary Master: `systemctl stop wabam`,
   `wabam-restore -b <backup_file> -u root -a $(/opt/wab/sbin/WABChangeDbRootPassword)`,
   `wabam-init-database -u root -a $(/opt/wab/sbin/WABChangeDbRootPassword)`,
   `systemctl start wabam`.
4. Install replication (section 3), re-apply the per-node settings of section 3.2 and the
   Proxyma settings of section 4 (the 5.x `web.proxy.*` values do not carry over, *inference*
   from the changed parameter names), test, switch the load balancer, decommission the 5.x farm.

If a DR Access Manager exists, "Update the WALLIX Access Manager dedicated to the DRP last";
its "DRP configuration script is erased" and must be redeployed (DG 7.3). Minimum version
because of WSA-2026-07-0002: 6.0.4, met by 6.0.5 ([WALLIX advisories](https://www.wallix.com/support-services/alerts/)).

## 8. Session audit repository

Settings > Session Audit Settings (global administrator only): repository hostname, port,
cluster name, HTTPS login and password, all "configured by default to work with the repository
embedded in the appliance"; change them only on WALLIX request (AG 9.3). "IPv6 is not
supported for session audits." Audit visibility is controlled by `sa.session.user.filter` and
`sa.session.user.prefilter` (AG 9.1).

## 9. Metrics, logs and monitoring

```
wabam-audit-data -b <date> -a <date> -t ALL   # licence and sizing data (AG 9.2)
wabam-sessions-count                          # JSON per node wabam.uuid across the cluster (AG 9.6)
wabam-sessions-count -i                       # this node only
snmpget -v3 -l authPriv -u wabsnmp -a SHA -A <authpass> -x AES -X <privpass> <ip> system.sysUpTime.0
```

- SNMP v2c/v3 with disk and CPU traps; v2c is disabled on a fresh install; "When Access Managers
  are configured in HA mode, the SNMP agent monitors all the nodes via the virtual IP address."
  (AG 8.4.4).
- Logs: `access.log`, `error.log`, `cli.log`, `tech.log` and the Java `hs_err_pid` file "are
  stored in the following directory: /var/log/wabam" (AG 9.7). Log levels and the archive are
  on Settings > Application Settings > Logs tab. "The TRACE or ALL modes may expose sensitive
  information, including passwords." Switch to DEBUG before generating an archive (AG 9.7.1).
- SIEM: the Deployment Guide lists "Syslog server integration 514/UDP", "Configurable in
  System > SIEM integration" (DG 2.2, table 4), and DG 2.4.1 suggests to "implement a SIEM
  solution so as not to lose any event logs". The Administration Guide has no SIEM integration
  section and does not describe the message content, so the forwarder exists but is not
  documented beyond the port (vendor inconsistency, ask WALLIX). A file-shipping agent is not an
  option because external agents are forbidden (section 1).
- Support tools: `wabam-debug-config` (runs once; `--reset` to force again) and
  `wabam-debug-export -p <PASSWORD>` (writes `troubleshooting_info__DATE-TIME` in `/root`)
  (AG 10.1, 10.2). Services: `WABServices`, `WABServices disable gui` (AG 8.4.5.2).

## 10. Bastion objects and the Trustelem SAML domain

Checklist per Bastion object (Configuration > Bastions, AG 3.2.1):

- Host = the IP address "used for the user service of WALLIX Bastion".
- API key with profile `wallix_access_manager_session_audit` ("recommended"); "For versions
  prior to 12.1, a single API key covers all features."
- Cluster membership, then `bastion.cluster.identical.mode` (AG 3.3.3).
- Strip Domain OFF: "WALLIX recommends not enabling this option unless there is a specific
  need." (AG 3.2.1) and, for SAML, "disable the Strip Domain option in the Bastion configuration
  window. This keeps the login format as user@domain, which is required for proper user mapping
  and authorization." (AG 4.3.3.2).
- Approval Time Zone (updated automatically on test or save).
- Allow Session Search with a Search Start Date and the Bastion login "linked to the Auditor
  profile".
- Custom SSH, RDP and REST API ports under Advanced Options (AG 3.2.2); Test TCP Connections.
- After a Bastion certificate change: Reset Bastion Certificate (AG 3.2.4).

SAML identity provider settings are in `docs/trustelem/05-access-manager-integration.md`.

## 11. Access Manager 5.2 differences

Facts from the [Access Manager 5.2.4.0 Administration Guide](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) (AG52),
[Access Manager 4.0.6.1 Installation Guide](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf) (IG)
and [Access Manager release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html) (RN) that
do not apply to 6.0.5. Use them only for a 5.x farm still in service or during the migration.

- Stack: application in Docker (`docker restart access-manager_access_manager_1`,
  `docker exec ...`), Apache in front (`systemctl restart apache2`), configuration in
  `/var/wab/etc/wabam`, logs in `/var/log/wallix/wabam` (IG 3.4.1, AG52 15.2, 21.9). Debian 10
  base (RN WAB-9787). Admin session timeout `SESSION_TIMEOUT` in `/etc/apache2/AM_variables.conf`.
- Database: external MySQL, Oracle or Azure listed (IG 3.1.2); database administrator password
  in `/var/wab/etc/access-manager.conf`.
- Interfaces: three in the installation guide (user access, HA, administration); since 5.2
  "The administration interface is now tied to the first interface (the only one required)"
  (RN WAB-13606). Replication over a dedicated HA interface (RN WAB-11783).
- Replication script added in 5.0.0 (RN WAB-6124) with `--prerequisite-check` and
  `/root/sqlreplication/servers_list` (RN WAB-11782, WAB-12957). "Before upgrading an Access
  Manager cluster to version 5.2.3, replication must be uninstalled. Replication can be
  reinstalled after the upgrade." (RN WAB-17588).
- Upgrade with `./access-manager-upgrade.sh` from the mounted ISO, log in
  `/root/migration-PREVIOUS_VERSION-NEW_VERSION.log` (IG 3.6).
- Proxy and DoS settings in `wabam.properties`: `web.proxy.activated` (true),
  `web.proxy.trusted-proxies`, `web.proxy.trusted-proxies.enabled` (on for new installations,
  off after an upgrade), `web.proxy.header.forward.useRFC7239only`, `web.max.requests.perSec`
  (60), `web.rate.ipWhitelist`, `web.sni.host.check` (true) (AG52 21.4 to 21.6). Without trusted
  proxies "the information contained in the audit logs is that of the proxy" (AG52 21.6).
- `purge.audit.active` "must be enabled only on one of the cluster nodes" (AG52 21.7).
- Defaults stated in 5.2: `bastion.connection.timeout` and `restapi.connection.timeout` 10 s,
  `sa.session.retention.days` 30, OIDC timeout 5 s, Java heap 2373 MB on the appliance
  (AG52 15.1.1, 16, 10.5.2, 21.2); `approval.time.zone` in `wabam.properties` (AG52 13).
- Portal certificate: `wabam-certificate-update` (`--certificate`, `-r | --restore`,
  `-s | --subjectAlternativeNames`) (RN WAB-9894, WAB-14102).
- Session audit in Elasticsearch 8.18 ("Session audit repository: 9300", "Session audit service
  status: 9200" in IG 2.4), PKCS#12 certificate, `wabam-es-rootcertificate-update` after regenerating the certificates, password in
  `/etc/elasticsearch/.elastic_password` (AG52 16, RN WAB-17644, WAB-14492, WAB-15707).
- `/opt/wab/sbin/wabam-session-count` (singular) (AG52 ch. 6).
- Load balancer: cookie persistence on Citrix ADC "incompatible with Universal Tunneling for
  clusters", so source-IP affinity was advised (RN WAB-6600); HTTP 80 "is redirected to the
  HTTPS one" in the web-application install mode (IG 2.2.3).
- "Clusters are not compatible with the feature allowing the display of the target passwords.
  However it can be used with an external vault." (AG52 13); the 6.0.5 guides no longer state it.
- X.509 "is not possible on the administration interface of an appliance" (AG52 10.2.4).
- Known issues: SAML URL auto-filled with the administration URL on a three-interface appliance
  (RN WAB-4968); GUI restore with a different encryption key broke SAML (RN WAB-14912);
  `wabam-backup` from cron fixed in 5.1.4 (RN WAB-14534); API key profiles from Bastion 12.2
  in RN WAB-11577 against 12.1 in AG52 13.
