# Runbook: WALLIX Access Manager farm

Date: 2026-09-23. Sources: [Access Manager 5.2.4.0 Administration Guide](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) (AG),
[Access Manager 4.0.6.1 Installation Guide](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf) (IG),
[Access Manager release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html) (RN).
Quotes are verbatim.

Supporting role in this repository: Access Manager is the SAML service provider that Trustelem
authenticates for the web path. The farm settings that matter for that integration are the
trusted proxies (so the SAML redirect URL and audit logs carry the real client address), the
node-shared `crypto.install.key` (SAML keys and secrets are encrypted with it), and the
replication procedure (SAML identity providers are configuration data and replicate).

## 1. Appliance facts

- Minimum 4 GB RAM and 50 GB disk (RN 5.2.4.0); three interfaces in the installation guide
  (user access, HA, administration). Since 5.2 "The administration interface is now tied to the
  first interface (the only one required)" (RN WAB-13606).
- "Any network equipment (proxy or firewall) positioned in front of WALLIX Access Manager must
  support the WebSocket protocol." (RN)
- Embedded MariaDB; external MySQL, Oracle or Azure database possible; privileged database
  credentials "will not be stored and will be needed for every upgrade involving schema
  updates" (IG 3.1.2).
- Application runs in Docker: `docker restart access-manager_access_manager_1`; Apache in
  front: `systemctl restart apache2` (IG 3.4.1, AG 21.9).
- SSH administration on 2242: `ssh wabadmin@<admin_ip> -p 2242`, then `super`, then `sudo -i`.
- Default accounts: `wabadmin` (SecureWabAdmin), `wabsuper`, `wabupgrade`, GRUB `wabbootadmin`
  (SecureWabBoot), Access Manager global administrator `admin` / `admin` ("recommended to create a
  new global administrator and delete the default global administrator").

## 2. Install node 1

1. Boot the appliance image; wizard: keyboard, `wabadmin`, `wabsuper`, GRUB and `wabupgrade`
   passwords, network for the interfaces.
2. The summary shows the database administrator password (kept in
   `/var/wab/etc/access-manager.conf`); "The database setup and creation are handled
   automatically by the initialization of the appliance."
3. Web GUI `https://<admin_ip>/wabam/global`: change the default administrator password, create
   the organization, install the licence (About page, or CLI below).
4. Licence CLI (root):

```
/opt/wab/sbin/wabam-license-list
/opt/wab/sbin/wabam-context-file-download -c /tmp/licenses/wabam_context_file.json
/opt/wab/sbin/wabam-license-import -l /root/wallix_license.json
```

   "During the initial installation, Access Manager creates a 31-day evaluation license which
   allows up to 5 concurrent users."
5. Portal certificate with a SAN for the load-balanced FQDN: `wabam-certificate-update`
   (options seen in release notes: `--certificate`, `-r | --restore`,
   `-s | --subjectAlternativeNames`). WAMUT requires "at least one Subject Alternative Name
   field specified with the DNS used to connect" (AG 14.2).
6. Admin GUI session timeout: `SESSION_TIMEOUT` in `/etc/apache2/AM_variables.conf`, then
   `systemctl restart apache2`.

## 3. Add node 2 and replicate the database

AG 20.1: "The first instance has to be installed normally. However the following ones require
to manually edit their file wabam.properties. This file is under the configuration directory :
/var/wab/etc/wabam. The installation encryption key (crypto.install.key), the database settings
(all properties with a name starting with db.connections) and the installation administrator
credentials (values starting by user.admin) should be copied from the first installation."
"If the databases of the two appliances are replicated, there is no need to duplicate the
db.connections parameters." Restart the service after editing. Later administrator credential
changes are made on node 1 and copied.

Appliance database replication (release notes): script added in 5.0.0 (WAB-6124), with
`--prerequisite-check` (WAB-11782), a mandatory HA interface (WAB-11783), the node list in
`/root/sqlreplication/servers_list` (WAB-12957), fixes for offsets between nodes (WAB-15150)
and Azure (WAB-15457). "Before upgrading an Access Manager cluster to version 5.2.3,
replication must be uninstalled. Replication can be reinstalled after the upgrade."
(WAB-17588). The script's invocation is not documented publicly; use the vendor's System
Operations documentation for the exact command.

Per-node settings after replication:

- `purge.audit.active` "must be enabled only on one of the cluster nodes" (AG 21.7).
- `rdp.clientName` per node if targets must distinguish them (AG 21.1).
- SNMP, NTP, certificates and `wabam.vmoptions` heap on each node.

## 4. Load balancer settings

| Item | Value | Source |
|------|-------|--------|
| Listener | HTTPS 443 with WebSocket upgrade; HTTP 80 redirects | IG 2.4, RN |
| Persistence | source-IP affinity; cookie persistence on Citrix ADC "incompatible with Universal Tunneling for clusters" | RN WAB-6600 |
| Forwarded headers | `X-Forwarded-For/-Host/-Port/-Proto`, or RFC 7239 `Forwarded` (`web.proxy.header.forward.useRFC7239only`) | AG 21.6 |
| Trust | `web.proxy.trusted-proxies` = load balancer addresses; `web.proxy.trusted-proxies.enabled=true` ("On new installations, this parameter is enabled by default ... for upgrades, it remains disabled by default") | AG 21.5 |
| Health check | not documented; probe TCP 443 or an HTTPS GET of `/wabam/` | gap |
| Rate limits | `web.max.requests.perSec` (60), `web.rate.ipWhitelist` for many WAMUT tunnels | AG 21.5 |
| SNI | `web.sni.host.check` (true); certificate SAN must match the FQDN | AG 21.4 |

Why trusted proxies matter for SAML: the SAML URLs and audit logs use the client address seen
by Access Manager; without trusted proxies the load balancer's address is recorded, and on a
three-interface appliance the SAML URL may be auto-filled with the administration URL
(known issue WAB-4968).

## 5. wabam.properties parameters used by this design

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `crypto.install.key` | generated | encryption key, identical on all nodes |
| `db.connections.*` | | database connection |
| `user.admin.*` | | installation administrator |
| `bastion.cluster.identical.mode` | off | Bastion cluster with identical configuration and proxy certificates: sync from one node only |
| `bastion.connection.timeout` | 10 s | lower it to fail over faster inside a Bastion cluster |
| `restapi.connection.timeout` | 10 s | same for the REST API |
| `session.maxInactiveInterval` | | inactivity disconnect (minutes) |
| `session.keepAlive` | 0 | WebSocket ping (seconds, max 3600) |
| `sa.session.retention.days` | 30 | session audit retention in Elasticsearch |
| `purge.audit.active` | false | audit purge, one node only |
| `web.proxy.activated` | true | honour proxy headers |
| `web.proxy.trusted-proxies` | | allowed proxy addresses |
| `web.max.requests.perSec` | 60 | DoS filter |
| `web.sni.host.check` | true | SNI verification |
| `web.header.X-Frame-Options` | DENY | clickjacking protection |
| `ut.port.range` | | local ports for Universal Tunneling towards the Bastion |
| `approval.time.zone` | server TZ | approval workflow synchronisation |
| `rdp.clientName` | hostname | RDP client name per node |

Every change needs an Access Manager restart (AG, repeated warning). JVM heap: `-Xmx` in
`/var/wab/etc/wabam/wabam.vmoptions` (default 2373 MB on the appliance), verified in `tech.log`.

## 6. Backup and restore

```
wabam-backup -d <backup_directory> -n <backup_filename> -p <backup_password>
wabam-restore -b <backup_file> -p <backup_password>   # stop Access Manager first; same schema version
wabam-restore-admin -f /var/wab/etc/wabam/wabam.properties   # reset the global administrator
```

`wabam-backup` produces an AES-256 zip with the database, keystore and `wabam.properties`, and
"can be used in cron" since 5.1.4 (WAB-14534). A GUI restore with a different encryption key
broke SAML in an earlier release (WAB-14912): always restore with the same `crypto.install.key`.

## 7. Upgrade

```
wabadmin@wab:~$ sha256sum -c accessmanager-<ver>.iso.sha256sum
wabadmin@wab:~$ super
wabsuper@wab:~$ sudo -i
# mount -o loop /home/wabadmin/accessmanager-<ver>.iso /mnt
# cd /mnt && ./access-manager-upgrade.sh
# tail /root/migration-<PREVIOUS_VERSION>-<NEW_VERSION>.log
# systemctl reboot
```

"Access Manager can be updated to version 5.2.4.0 from any version with a release date earlier
than the release date of version 5.2.4.0." Uninstall replication before upgrading a cluster,
upgrade node by node, reinstall replication, then re-test the SAML login and the WAMUT
tunnel. Minimum target because of WSA-2026-07-0002: 5.2.7 or 6.0.4.

## 8. Elasticsearch (session audit)

Settings > Session Audit Settings: repository host, port 9300, cluster name, HTTPS credentials,
PKCS#12 certificate. After regenerating the appliance Elasticsearch certificates:

```
cp /etc/elasticsearch/certs/ca.crt /var/wab/etc/wabam/elasticsearch/ca.crt
docker exec access-manager_access_manager_1 /opt/wallix/wabam/bin/wabam-es-rootcertificate-update --certificate /etc/opt/wallix/wabam/elasticsearch/ca.crt
docker restart access-manager_access_manager_1
```

(RN WAB-14492). If authentication to Elasticsearch fails after an upgrade, read
`/etc/elasticsearch/.elastic_password` as root and re-enter it in the GUI (WAB-15707).

## 9. Metrics and monitoring

```
docker exec -it access-manager_access_manager_1 /opt/wallix/wabam/bin/wabam-audit-data -b <date> -a <date> -t ALL
/opt/wab/sbin/wabam-session-count       # JSON per node UUID across the cluster
/opt/wab/sbin/wabam-session-count -i    # this node only
snmpget -v3 -l authPriv -u wabsnmp -a SHA -A <authpass> -x AES -X <privpass> <ip> system.sysUpTime.0
```

SNMP v2c/v3 with disk and CPU traps (AG ch. 5). Logs in `/var/log/wallix/wabam` (`access.log`,
`error.log`, `tech.log`); per-module log levels in Settings > Logs; "The TRACE or ALL modes may
expose sensitive information, including passwords" (AG 15.2). No native syslog forwarder is
documented; ship the log directory with an OS-level agent.

## 10. Bastion objects and the Trustelem SAML domain

Checklist per Bastion object (AG 13): Host = Bastion user-interface address; API key with
profile `wallix_access_manager_session_audit` (Bastion 12.1+, "allows the use of only one API
key"); custom ports if changed; Cluster membership; Strip Domain OFF for federated users;
Approval Time Zone; Allow Session Search with the auditor login; Test Connection. SAML identity
provider settings are in `docs/trustelem/05-access-manager-integration.md`.
