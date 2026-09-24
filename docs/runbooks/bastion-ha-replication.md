# Runbook: WALLIX Bastion HA Database Replication

Date: 2026-09-24. Verified against the [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) and the
[Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/), which are customer documentation
behind the doc.wallix.com login (Trustelem SSO); section numbers below refer to those editions.
Where a statement is unchanged since 12.0.2, the public
[Bastion 12.0.2 Deployment Guide](https://marketplace-wallix.s3.amazonaws.com/bastion_12.0.2_en_deployment_guide.pdf)
supports it too. Other sources: the [Bastion Functional Administration Guide](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
the [Bastion release notes](https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html) and the
[Bastion Quick Start](https://marketplace-wallix.s3.amazonaws.com/Bastion-quickstart-en.pdf).
Quotes are verbatim. Items neither guide covers are marked "not documented"; inferences are
marked *inference*.

**12.0.x note.** The HA chapters of the 12.0.25 and 12.4.3 guides are identical except for command
names. The 12.0.x guides (12.0.2, 12.0.25) use `bastion-replication` and `bastion-luks-update`
where 12.4.3 uses `wallix-replication` and `wallix-luks-update`; the version that introduced the
new names is not stated. Upgrades use `BastionSecureUpgrade` up to 12.3.4 and `wallix-upgrade` from
12.3.5 ([Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 7.1 step 6).

Supporting role in this repository: the Trustelem integration (RADIUS secondary authentication,
SAML domains, mappings) is configuration data, so it replicates between the nodes; the SIEM,
network, SNMP, SMTP, time and configuration-option settings do not, and must be set on each node
(section 12).

## 1. Facts

Source: [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) chapter 5 and
[Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) chapter 11 (same text).

- "WALLIX Bastion 12 removed the High-Availability File System Replication (DRBD) feature. To
  use High-Availability abilities in your infrastructure, you must use the Database Replication
  feature detailed in this section."
- "an SSH tunnel with port forwarding is established between Bastions to secure communication
  between the databases. This tunnel is managed by the autossh service that keeps the tunnel
  permanently running. The port forwarding allows the databases to communicate without having
  to open a remote access to the database."
- The tunnel runs over the SSH administration port. Deployment Guide 2.2, row "CLI-based
  administration 2242/TCP": required when "The sshadmin service is enabled (System > Service
  control). HA Database Replication relies on this port being open." The port is "Not
  configurable". Ports 3306 and 3307 are not in the port tables: they are local ends of the tunnel.
- Slaves (and both masters in Master/Master) "request updates from the Master node using the
  outbound port 3307 (source) and the inbound port 3306 (destination)"; the tunnel end is
  `127.0.0.1:3307` on the slave or secondary master (System Operations Guide 11.3).
- Modes: Master/Slave(s) ("No modification must be performed by the Slaves") and Master/Master
  ("there is a primary Master and a secondary Master. The primary Master is the Master Bastion
  on which the replication is installed").
- Not replicated: Audit; Session Management > Recording Options; Configuration > Configuration
  Options; Configuration > Connection Messages; Configuration > Audit Logs; System > Network;
  System > Time Service; System > SNMP; System > SMTP Server; System > Service Control; System >
  SIEM Integration; Users > Accounts: the GPG fingerprint; Targets > Devices: the certificates for
  the device.
  12.0.x note: the 12.0.2 list also named Configuration > License; the 12.0.25 and 12.4.3 lists do
  not (see section 12 for the licence).
- No virtual IP, heartbeat or automatic failover appears in either 12.4.3 guide (*inference* from
  absence): node loss is handled by the front end and by the operator (section 7).

Limitations table (verbatim excerpts, Deployment Guide 5):

| Feature | Limitation |
|---------|------------|
| Audit | "The audit tables are not replicated ... all Bastions have their own audit session tables." |
| SMTP server | "To receive notifications, an SMTP server must be configured on each node of the Database Replication." |
| API provisioning | "In Master/Master mode, API provisioning must not be performed simultaneously from both Bastions." |
| Cloning VMs | "Do not clone virtual machines and use them to set the replication. This leads to errors related to the universally unique identifier (uuid)." |
| Passwords | "all password actions must always be performed from the (primary) Master node." |
| Password changes | "Always schedule password changes on the (primary) Master node. Password rotation crons are not automatically replicated between nodes, so only the primary Bastion runs scheduled rotations. As a result, if the primary Bastion becomes unavailable, password changes will not run until it is available again." |
| Check-in | "In Master/Slaves mode, do not use the Change password at check-in option." |
| Approvals | "In Master/Master mode, approvals are replicated between both Bastions. In Master/Slaves mode, approvals must be requested and validated only on the Master." |

Post-installation rules (Deployment Guide 5.1): "In Master/Master mode, changes can be made on
both nodes." and "In Master/Slaves mode, changes must be made only on the Master node. Any changes
to replicated elements on Slave nodes will cause errors and break the replication."

## 2. Prerequisites

Requirements before installation ([Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.1):

| Requirement | Reason given |
|-------------|--------------|
| "All Bastion nodes are on the same subnet and connected directly or through only one router." | "Prevents latency and HA issues caused by extra network devices." |
| "All Bastion nodes run the same WALLIX Bastion version." | "Prevents replication errors and inconsistent behavior." |
| "All Bastion nodes have encryption initialized." | "Ensures secure replication and protects data integrity." |
| "All Bastion nodes are synchronized via NTP to the same timezone. Configure the primary (Master) Bastion first, then synchronize all other nodes to the same server." | "Replication across multiple time zones is not supported." |
| "All Bastion nodes have an interface with administration features." | "Allows establishing an SSH tunnel between nodes." |

- No latency figure is given. The subnet rule means cross-site replication is only within the
  documented requirements when both sites share one subnet with at most one router between the
  nodes (*inference*); otherwise a disaster-recovery Bastion is restored from backup.
- Interface: WALLIX "recommends dedicating an interface to administration on each node to
  separate administrative traffic from user traffic" (Deployment Guide 5.1). The tunnel uses the
  interface that carries the administration features (port 2242), whatever its name. Since DRBD
  was removed "the eth1 network interface can now be configured and used like any other"
  interface, and "When the eth1 interface is used for HA database replication, the associated
  administration features must be manually enabled from the System > Service control page for
  replication to work" ([release notes WAB-7947 and WAB-17651](https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html)).
  Firewalls and the 2242 access list must admit the peer nodes.
- "Before installing the replication, back up all critical data on each node. During setup, the
  primary (Master) Bastion’s database replaces the databases of the other Bastion nodes,
  resulting in the loss of their existing data." (Deployment Guide 5.1.1 and 5.1.2)
- "FQDN and IPv6 are not supported in the HA feature configuration. You must only use the IPv4
  address for Bastions." (5.1.1 and 5.1.2)
- SMTP on each node and NTP to the same time zone are requirements (limitations table and
  requirement table above). 12.0.x note: the 12.0.2 guide only recommended "a SMTP server on the
  (primary) Master" and the same timezone.
- Both nodes fully initialised as in section 3, including the per-node settings of section 12.
- 12.0.x note: the 12.0.2 guide names the configuration file `/etc/sqlreplication`; the 12.4.3
  guides do not name it.

Ports to open between nodes and to the outside are in the architecture report, section 6.3.

## 3. Node initialisation (both nodes)

Source: [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.1, 2.3, 4.1, 4.2 and 4.3.

Factory state: eth0 `192.168.10.5/24`, "SSH TCP port for administration: 2242", "Web interface
port: 443 (HTTPS)". "RSA private keys (SSH 2242, HTTPS, and RDP) inserted in WALLIX Bastion must
be greater than or equal to 3072bits." (chapter 2)

| Account | Role | Factory value (2.1) |
|---------|------|---------------------|
| `admin` | GUI super administrator | admin / admin (AWS: `admin-{instanceID}`, 3.2.1.2) |
| `wabadmin` | CLI connection user on 2242 | SecureWabAdmin, "You must create a new password during the initial configuration phase" |
| `wabsuper` | sudo user (`super`, then `sudo -i`) | "No default. You must create a password during the initial configuration phase." |
| `wabupgrade` | upgrades from the CLI | "No default. You must create a password during the initial configuration phase." |
| `wabbootadmin` | GRUB user | SecureWABBoot, "you must create a new password during the initial configuration phase" |

Privilege escalation used by every procedure:

```
wabadmin$ super
[sudo] password for wabsuper:
wabsuper$ sudo -i
[sudo] password for wabsuper:
```

First boot wizard (4.1): keyboard, new `wabadmin` password, then passwords for `wabsuper`,
`wabbootadmin` (the wizard offers to reuse the `wabsuper` password; "The wabbootadmin account
accepts only ASCII characters for the password") and `wabupgrade`, then hostname, eth0 static
address and FQDN.

Secure the system (4.2), as root:

```
# on-premises or virtual machine: new passphrase, interactive boot
wallix-luks-update --interactive --change-passphrase
# cloud platform other than AWS: new passphrase and new volume key
wallix-luks-update --reencrypt
```

12.0.x note: the command is `bastion-luks-update` in the 12.0.x guides.

- "Add the public keys for wabadmin and wabupgrade in their dedicated ~/.ssh/authorized_keys
  folder." (4.2 step 3), before any change that disables password login on 2242.
- Run `WABSecurityLevel` and "For all security levels, select your preferred cryptography
  profile"; "Whenever possible, choose the same security level for all services" (4.2 step 4).
  This design keeps the SOG-IS profile. Profiles are listed in System Operations Guide 6.4.5, and
  "If your system is configured in High-Availability (HA), you must manually apply the security
  level changes to each node to ensure consistency" (System Operations Guide 6.4.6).
  12.0.x note: the 12.0.2 guide named "SOG-IS CES 1.3 Agreed Cryptographic Mechanisms up to 2030".

GUI initial configuration (4.3):

1. Log in as `admin` / `admin` and change the password.
2. Initialise encryption with a custom passphrase: "The minimum length for a passphrase is 12
   characters, with at least one of each: uppercase, lowercase, number, special character."
   Quick Start 5.3.2 adds "once a passphrase has been set, it cannot be deleted" (not restated in
   12.4.3; System Operations Guide 6.4.3 documents only changing it).
3. Licence: Configuration > License > Download context file, send it to WALLIX support, upload
   `wallix_license.json`.
4. System > Network; add the load balancer FQDN and any DNS alias to "Trusted hostnames for
   HTTP_HOST header" (section 12).
5. System > Time service: time zone and NTP servers (same time zone on every node).
6. Configuration > Notifications: recipients for "Not enough space on filesystem (90% full)" and
   "Disk space is full (< 100MiB), emergency shutdown of all proxy servers" (section 11).
7. Create a named user with the `product_administrator` profile.
8. System > Backup/Restore: first backup. "The key must be between 16 and 128 characters long."
9. Log in as the new administrator; "Recommended: Delete the default administrator account."

12.0.x note: the 12.0.2 guide gave the backup key as "at least 16" (4.3) and "must be exactly 16
characters long" (chapters 6 and 7), and ended 4.3 with "Change the default password of the SQL
database using the WABChangeDbRootPassword command". 12.4.3 drops that step, and the System
Operations Guide 11.3 uses `WABChangeDbRootPassword` to "retrieve the database password"; do not
run it as a change step on replicated nodes without WALLIX confirmation.

## 4. Install the replication

Source: [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.1.1 and 5.1.2.

Master/Master, on the node that will be the primary master, as root:

```
wallix-replication --create-conf-file
**********CREATE CONF FILE**********
creation of initial configuration file
What kind of SQL replication do you want to implement?
1. Master/Master
2. Master/Slave(s)
Enter the number of your choice: 1
What is the ip address of your Bastion No 1 (This node)? 10.10.XX.XX
what is the wabadmin password of your bastion 10.10.XX.XX?
what is the wabsuper password of your bastion 10.10.XX.XX?
What is the ip address of your Bastion No 2 (Other master node)? 10.10.YY.YY
what is the wabadmin password of your bastion 10.10.YY.YY?
what is the wabsuper password of your bastion 10.10.YY.YY?
What is your passphrase? leave blank, if there is none ?
**********SCRIPT EXECUTION SUCCESSFUL**********
```

Then:

```
wallix-replication --prerequisite-check     # optional, listed in 5.2, not a 5.1.1 step
wallix-replication --install
wallix-replication --monitoring
wallix-replication --install-monitoring     # optional: cron for replication status (log files)
wallix-replication --install-notification   # optional: e-mail when replication is down
```

Master/Slaves (5.1.2) is the same sequence on the Master with choice `2`; the dialogue adds
"How many slave(s) do you have? 1" and labels the other node "(Slave node)".

12.0.x note: the 12.0.2 transcript also asked "Do you want to disable the password rotation on
the bastion ...?" for each node; 12.4.3 no longer asks. The question remains in `--add-slave`
("Decide if you want to disable password rotation for the Slave Bastion", System Operations Guide
11.2.1).

## 5. Command reference

Source: [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.2.

```
wallix-replication --create-conf-file | --prerequisite-check | --install | --status
                   | --monitoring | --install-monitoring | --uninstall-monitoring
                   | --install-notification | --uninstall-notification | --notification NOTIFICATION
                   | --resync | --dump-resync | --add-slave | --elevate-master
                   | --stop | --start | --uninstall | --version | --debug
```

- `--status`: "Check the replication status from a log file".
- `--monitoring`: "Show SQL replication status on all Bastions".
- `--resync`: "Resynchronize all slave with the Master".
- `--dump-resync`: "Create a SQL dump (without the auth/session history) send it to Slave node
  and resync the slave with the Master".
- `--elevate-master`: "Elevate a slave bastion from an existing cluster master/slave".
- `--uninstall`: "Uninstall replication on every node, to run on Master".
- Not runnable on a slave in Master/Slave mode: `--resync`, `--dump-resync`,
  `--install-monitoring`, `--install-notification`, `--notification`, `--monitoring`.

Impact (5.2; for the last column "Not all tables from the database are affected"):

| Option | Restarts primary master DB | Restarts slaves / secondary master DB | Erases DB data on all nodes except the primary master |
|--------|:-:|:-:|:-:|
| `--install` | yes | yes | yes |
| `--dump-resync` | no | yes | yes |
| `--resync` | no | yes | no |
| `--uninstall` | yes | yes | no |

Lifecycle rules ([Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 11.1, 11.2 and 11.4):

- Re-IP: "If you change the IP address of any of the Bastion nodes in the cluster (Masters or
  Slaves), you must re-install the replication": `--create-conf-file`, then `--install`, which
  erases the database of the non-primary nodes.
- Add a slave: `--add-slave` on the (primary) Master.
- "You cannot remove a slave node from the database replication. However, you can uninstall and
  reinstall the replication without the Slave node."
- Uninstall: "Ensure that no users are connected to any of the Bastions before executing this
  procedure", run `--uninstall` from the (primary) Master, then `--uninstall-monitoring` and
  `--uninstall-notification` if they were installed: "If both options are not uninstalled, you
  will generate errors."

## 6. Daily checks and troubleshooting

Source: [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 11.3 and 13.

1. `wallix-replication --status` on the (primary) Master. Truncated sample from 11.3:

   ```
   {'Binlog_Do_DB': 'wallix',
   'Binlog_Ignore_DB': 'mysql',
   'File': 'mysql-bin.000001',
   'Position': '938'}
   [...]
   'Slave_Transactional_Groups': '1',
   'Until_Condition': 'None',
   'Until_Log_File': '',
   'Until_Log_Pos': '0',
   'Using_Gtid': 'No'}
   ```

   "If you are using a Master/Master mode, there are two sets of output for each node displayed.
   You must inspect the IO and SQL threads to ensure the value is YES. If the value reads
   Connecting, there might a network issue between the nodes." In Master/Slaves "only the output
   for the Slaves nodes are returned".
2. `wallix-replication --monitoring` on the (primary) Master. Sample output of `--monitoring`
   and `--prerequisite-check` is not documented.
3. Replication e-mails arriving at the operations mailbox. The templates are `ha_master_fault.txt`,
   `ha_master_up.txt` and `ha_slave_missing.txt`; "The list of recipients is configured with the
   related script." ([Administration Guide 8.2.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
   same section in 12.4.3)
4. Create a test object (for example a time frame) on the primary master, confirm it on the
   other node within seconds, delete it.
5. `WB_Event=wabaudit` lines in the SIEM from both nodes. The syslog (System > Syslog) shows "all
   operations on HA Database Replication" (13.1), and the debug archive includes the
   `status_replication` log (13.4).

Deeper checks (11.3), on the node named:

| Check | Command | Expected |
|-------|---------|----------|
| Tunnel reaches the Master database (slave or secondary master) | `mysql -h127.0.0.1 -P3307 -uroot -p$(WABChangeDbRootPassword)` | login succeeds |
| Replication configuration (master) | `cat /etc/mysql/conf.d/replic.cnf` | present |
| SSH tunnel (slave or secondary master) | `netstat -antp`, filtered on 3307 | `127.0.0.1 :3307 ... ESTABLISHED PID/ssh` |
| autossh service | `systemctl status autossh` | "Active: active (running)" |
| autossh parameters | `cat /etc/default/autossh` and `cat /etc/systemd/system/autossh.service` | review |

Replication position, on the slave nodes and then on the master:

```
mysql -uroot -p{DB_PASSWORD} -e "show slave status\G" | grep Master_Log
mysql -uroot -p{DB_PASSWORD} -e "show master status"
netstat -antp | grep 3307
```

`{DB_PASSWORD}` is the database password returned by `WABChangeDbRootPassword`, with no space
after `-p`.

## 7. Failover, failback and restore

Master/Master: *inference:* both masters accept logins at all times ("In Master/Master mode,
changes can be made on both nodes", Deployment Guide 5.1), so a node loss is handled by the front
end (load balancer, DNS or Access Manager cluster). Keep administration and API provisioning on
the surviving node only. If the primary master is the node lost, scheduled password rotations
stop: "if the primary Bastion becomes unavailable, password changes will not run until it is
available again" (Deployment Guide 5). How to move rotation to the secondary during a long outage
is not documented (*inference:* reinstalling the replication with the survivor as primary; ask
WALLIX first).

Master/Slaves: promote with `wallix-replication --elevate-master` ("Elevate a slave bastion from
an existing cluster master/slave"; *inference:* run on the surviving slave), then repoint the
front end. Neither 12.4.3 guide gives the step-by-step failover or failback procedure; rehearse it
on the test cluster and record your own runbook.

Failback ([Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 11.3):

- "There is a 10-day buffer on the master where data is automatically replicated when the faulty
  node comes back online. If the 10 days passed (or other non-network problems such writing issue
  or faulty state occurred), a manual re-sync is required."
- Manual re-sync, on the (primary) Master: `wallix-replication --dump-resync`. "This command
  overwrites the Slave/Secondary Master database with the Master database."
- `--resync` is for a failed restart: "If a problem occurs during the "start" command (such as
  wrong log_file number), you can use the following command from the Master node to restart the
  synchronization."
- *Inference:* in Master/Master, if the primary was the node lost and changes were made on the
  secondary, a `--dump-resync` from the primary discards them. Check `--status` first and ask
  WALLIX before overwriting.

Restore on a replicated cluster (System Operations Guide 14.2.6):

- "You cannot restore a backup on a Slave Bastion."
- "When you restore the backup configuration on a Master Bastion, whether in Master/Master or
  Master/Slaves mode, WALLIX Bastion automatically reinstates the HA Replication process.
  Concretely, when you restore the backup file, WALLIX Bastion pauses the replication. Then,
  after the restoration procedure is complete, WALLIX Bastion automatically resynchronizes all
  nodes and resumes replication."

Disable the failed node in Access Manager (Bastions page, Active Bastion off) so the cluster
stops trying it ([AM release note WAB-17043](https://pam.wallix.one/documentation/release-notes/am-rn-en.html)).

## 8. Upgrades

Source: [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) chapter 7.

Minor upgrade in HA mode (7.2). "Your WALLIX Bastion will be unavailable and unusable by all users
during the update procedure", and "Steps must be carried out in their given order to ensure a
proper upgrade of the cluster."

1. Snapshot each node, or back up each node (System > Backup/Restore, key of 16 to 128
   characters). "In case of a Master/Slaves setup, start with the Slaves. In case of a
   Master/Master setup, you can start with any node."
2. Optional, local recording storage only: export recordings with `WABSessionLogExport`.
3. Download the ISO, `.iso.sha256sum` and `.iso.sha256sum.sig` from the support portal.
4. Copy the three files to each node (same order as step 1):

   ```
   scp -P 2242 <BASTION_ISO_NAME>.iso wabupgrade@<BASTION_IP_ADDRESS>:/home/wabupgrade/<BASTION_ISO_NAME>.iso
   scp -P 2242 <BASTION_ISO_NAME>.iso.sha256sum.sig wabupgrade@<BASTION_IP_ADDRESS>:/home/wabupgrade/<BASTION_ISO_NAME>.iso.sha256sum.sig
   scp -P 2242 <BASTION_ISO_NAME>.iso.sha256sum wabupgrade@<BASTION_IP_ADDRESS>:/home/wabupgrade/<BASTION_ISO_NAME>.iso.sha256sum
   ```

5. On the (primary) Master, as root: `wallix-replication --stop` ("stop the replication for all
   nodes").
6. On each node ("To save time, you can perform this operation in parallel on all nodes"):

   ```
   ssh -p 2242 wabupgrade@<BASTION_IP_ADDRESS>
   # 12.3.5 and later
   wallix-upgrade -i /home/wabupgrade/<BASTION_ISO_NAME>.iso -c /home/wabupgrade/<BASTION_ISO_NAME>.iso.sha256sum -s /home/wabupgrade/<BASTION_ISO_NAME>.iso.sha256sum.sig
   # 12.3.4 and earlier
   BastionSecureUpgrade -i /home/wabupgrade/<BASTION_ISO_NAME>.iso -c /home/wabupgrade/<BASTION_ISO_NAME>.iso.sha256sum -s /home/wabupgrade/<BASTION_ISO_NAME>.iso.sha256sum.sig
   ```

7. Reboot all nodes (as `wabadmin`, elevate to root, `reboot`).
8. On the (primary) Master: `wallix-replication --dump-resync`.
9. On the (primary) Master: `wallix-replication --start`.
10. On the (primary) Master: `wallix-replication --monitoring`.
11. Check `WABSecurityLevel` on each node ("check that the selection of the cryptographic
    algorithms accepted by both the SSH and the HTTP servers still meets your requirements").

Plan a full-cluster outage window: *inference* from steps 5 to 8, since every node is locked
down during its upgrade and `--dump-resync` overwrites anything written on the non-primary nodes
after `--stop`.

Signature check. Optional before step 4: "You can check the integrity and signature of the
downloaded ISO image if you want. However, the WALLIX update script does this automatically."
Manual check (3.2.1.1.1): `gpg --import <CA_NAME>.pub.gpg`, then
`gpg --verify <BASTION_ISO_NAME>.iso.sha256sum.sig <BASTION_ISO_NAME>.iso.sha256sum`, expecting
`Good signature from "WALLIX PAM R&D Team - Bastion 12 / AM 6 (Key used to sign WALLIX repositories and plugins) <dev@wallix.com>"`,
then compare the SHA-256 of the ISO with the `.sha256sum` file.

Upgrade failure (7.3): answer `N` to "Do you wish to deactivate the 'Protective System Lockdown'?
(y/N)", reboot (rescue mode), audit the system, then `/opt/wab/bin/wallix-upgrade --unlock-system`
and reboot. 12.0.x note: `/opt/wab/bin/BastionSecureUpgrade --unlock-system`.

Rollback (7.4): "On a virtual appliance or in the cloud, restore the snapshot of the previous
version of WALLIX Bastion." On physical appliances: back up the configuration
(`/opt/wab/bin/wallix-config-backup.py`, 6.2.3) and the recordings (`WABSessionLogExport`) before
upgrading; to roll back, reinstall the previous ISO from a bootable USB key, run
`wallix-config-restore.py`, upload the recordings archive and run `WABSessionLogImport`.
*Inference:* for a cluster, roll back all nodes to snapshots taken at the same point, then check
`--status`.

Chapter 6 ("WALLIX Bastion 12.X migration") applies only to migrations from a pre-12 Bastion; the
supported backup sources are 9.0, 9.1.0, 10.0, 10.1.0, 10.3.0, 10.4.3 and 11.0.0 (6.1). It does not
apply to a cluster installed on 12.x. 12.0.x note: the 12.0.2 guide's controlled-deployment steps
(`wallix-config-restore.py --testing-mode`, `systemctl mask --now cron`) are not in 12.4.3.

Because of WSA-2026-07-0001, any cluster on 12.3.0 to 12.3.6 or 12.4.0 must be taken to
12.3.7 or 12.4.1 and later ([advisories](https://www.wallix.com/support-services/alerts/)).

## 9. Backups

Source: [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 14.2.

- "Every backup has a key to encrypt the backup. The key must be between 16 and 128 characters
  long." "Session recordings are not saved during a backup/restore operation."
- Automatic backup: "By default, this is performed every day at 6:50 p.m. in the time zone in
  which WALLIX Bastion is located." "The files are stored in the directory /var/wab/backups."
  The schedule is the `WABExecuteBackup` line in `/etc/cron.d/wabcore` (14.2.3.1).
- "All automatic backups are encrypted with the same key." Replace the default key under
  Configuration > Configuration options > Global > Backup key (14.2.3.2). Set it on each node:
  *inference* from the exclusion of Configuration > Configuration Options from the replication.
- Copy the backup files off the appliance; the recovery point of a disaster-recovery Bastion is
  the interval between copies.

## 10. Certificates and keys per node

Source: [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 8.1.2, 8.2 and 8.3.

- GUI and API: replace `ca.crt`, `server.pem`, `server.key` in `/var/wab/apache2/ssl.crt`, then
  `systemctl restart apache2`; self-signed regeneration `WABGuiCertificate selfsign -f`
  ([Quick Start 5.4](https://marketplace-wallix.s3.amazonaws.com/Bastion-quickstart-en.pdf); not in
  the 12.4.3 guides).
- RDP proxy: `rdpcert --key --inkey=<RDP_private_key_file>.key --x509 --inx509=<X509_certificate_file>.pem --force`,
  then `systemctl restart redemption`. "Your certificate must contain all of the FQDNs of the
  WALLIX Bastion in SubjectAltName properties."
- SSH proxy host keys: `/var/wab/etc/ssh/server_rsa.key` ("A minimum 4,096-bit length is also
  recommended") and `/var/wab/etc/ssh/server_ed25519.key`, regenerated with
  `WABSshServerGenRsaKey.sh`.
- Access Manager pins the Bastion certificate and fingerprints: after any change, toggle
  "Reset Bastion Certificate", "Reset SSH Fingerprint" and "Reset RDP Fingerprint" on the AM
  Bastions page ([AM Admin Guide 13](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)).

## 11. Services, disk space and disk expansion

Source: [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.3 and 3.2.3.

Disk space (2.3):

- Notification when `/`, `/var/log` or `/var/wab` reaches 90%, repeated every 2 hours.
- Below 100 MiB free on `/` or `/var/wab` (or 100 MiB of free quota on `/var/log`): "The SSH and
  RDP proxy servers are shut down to prevent further issues. This terminates all current
  sessions". The proxies come back at 500 MiB.
- Quotas: `/var/log` 10 GB, `/home` 4 GB.
- "The system sends notifications only if they are activated" (section 3, step 6).

Disk expansion (3.2.3): increasing the existing virtual disk is the recommended method ("keeping
a single virtual disk simplifies maintenance and ensures full compatibility with the snapshot and
backup features of the hosting environment"): resize the disk in the hypervisor and reboot; "the
system automatically detects and allocates most of the additional space to the /var/wab
partition" (3.2.3.1). "Disk resizing is not supported on physical appliances." Add a second disk
only if the existing one cannot be resized (3.2.3.2). That procedure encrypts the new disk with
LUKS, extends `vg00`, stops the services below, resizes LV `vg00/lvwab` mounted at `/var/wab`, and
reboots:

`wabwatchdog`, `wabrestapi`, `wabgui`, `redemption` (RDP proxy), `sashimi` (SSH proxy),
`wallix-validator`, `superset`, `wallix-discovery`, `wallixsession`, `wallixcelery`,
`wabsystemconfiguration`, `syslog-ng`, `acpid`, `cron`, `wab-backupdaemon`, `mariadb`.

autossh, used by replication, is not in that list. The AWS procedure (3.2.3.3) has its own list.
GUI equivalent for the proxies and the administration console: System > Service control.

## 12. What replicates, and what to set on each node

What replicates: the status output shows `'Binlog_Do_DB': 'wallix'` and
`'Binlog_Ignore_DB': 'mysql'` ([Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 11.3):
the `wallix` database replicates, minus the exclusion list of section 1. "In HA Database
Replication mode, all Bastion nodes in a cluster share the same encryption key, even in
master/master mode", but "session metadata remains local to the Bastion of origin. As a result,
sessions can only be viewed on the Bastion of origin through its GUI" (System Operations Guide
6.5.3). The rows below are an *inference* from the exclusion list, except where a quote is given.

| Object | Replicated | Action on the second node |
|--------|:-:|---------------------------|
| External authentications (AD, RADIUS to Trustelem Connect, SAML) | yes | none |
| Authentication domains, secondary authentication, mappings | yes | none |
| User groups, profiles, authorizations | yes | none |
| API keys for Access Manager | yes | none |
| SIEM integration, SMTP, SNMP, NTP, network | no | configure on each node |
| Configuration options: trusted hostnames for HTTP_HOST, automatic backup key | no | set on each node |
| Service control: service mapping, "Limit the number of parallel connections per IP" | no | set on each node |
| Security level (`WABSecurityLevel`) | no | "manually apply the security level changes to each node" (System Operations Guide 6.4.6) |
| Recording options and storage | no | configure on each node, with the NFS rules below |
| Audit data and session recordings | no | view them on the node that recorded them |
| Device certificates and GPG fingerprints | no | re-accept on each node; in Master/Master "you must upload the GPG key to both master nodes, even if the second node displays the fingerprint after uploading the GPG key to the first node" ([Administration Guide 4.5](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf)) |
| Licence | not stated | *inference:* one licence per node until WALLIX confirms |

Per-node settings in detail ([Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/)):

- Trusted hostnames (7.1.2): the GUI and REST API check the HTTP_HOST header, and "If you need
  to access WALLIX Bastion through additional hostnames, FQDNs, or IP addresses, you must manually
  add them to the trusted list. This is typically required when connecting through SSH tunnels,
  DNS aliases, or reverse proxies." Add the load balancer FQDN under Configuration > Configuration
  Options > Global > Trusted hostnames for HTTP_HOST header.
- Parallel connections (7.2): for a Bastion "configured with any of the following: WALLIX Access
  Manager, load balancer, Web Application Filter (WAF), reverse proxy, or other", "Deactivate the
  Limit the number of parallel connections per IP option" (System > Service control, advanced
  mapping options).
- Service mapping (7.2): keep the administration features (GUI and SSH on 2242) on the dedicated
  admin interface on each node; the replication tunnel depends on them.
- NFS recording storage (10.2): "ensure that the owner users and owner groups are identical on
  all WALLIX Bastion instances (for example, if the all_squash option is set by the NFS server on
  a single WALLIX Bastion, replication will not work)" and "use an identical NFS export
  configuration for all WALLIX Bastion instances."
- Licence: the 12.4.3 exclusion list no longer names Configuration > License, but neither guide
  says the licence replicates. Each appliance is activated with its own context file, and "A
  context file that has already been used to activate a license cannot be reused" (5.1).
