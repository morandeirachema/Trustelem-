# Operations

> - **Purpose:** what to monitor and log on each component, how secrets and users are rotated, and how the two clusters are upgraded and backed up.
> - **Audience:** Bastion and Access Manager operators, Trustelem administrator, SOC.
> - **Verified:** 2026-09-24 against the Bastion 12.4.3 and Access Manager 6.0.5 customer guides, the public Bastion 12.3.2 and Access Manager 5.2.4.0 guides and release notes, and the Trustelem documentation books.
> - **Sources:** [On-premise SIEM](https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem), [Certificate renewal](https://trustelem-doc.wallix.com/books/trustelem-administration/page/certificate-renewal), Bastion 12.4.3 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), Access Manager 6.0.5 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), [Access Manager Administration Guide 5.2.4.0](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf).

## 1. Monitoring and logging

| Component | What to collect | How | Source |
|-----------|-----------------|-----|--------|
| Trustelem | authentication success/failure, factor enrollments, admin changes; directory health from the dashboard LED | Logs page, API (30 days), on-premise SIEM push through Trustelem Connect every 30 s in JSON | [On-premise SIEM](https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem), [API](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api) |
| Bastion | `wabauth` events, session start/stop, approvals, SNMP | System > SIEM integration: UDP, TCP or TLS; RFC 5424 or RFC 3164; filters selectable one by one; SIEM licence feature ([Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 13.6; catalogue in the [Bastion 12.4.3 SIEM Logs Guide](https://doc.wallix.com/)); parsers for Splunk, Google SecOps, FortiSIEM, Sekoia | [Splunk add-on](https://github.com/wallix/Splunk-add-on), [Google SecOps](https://docs.cloud.google.com/chronicle/docs/ingestion/default-parsers/wallix-bastion), [FortiSIEM](https://docs.fortinet.com/document/fortisiem/7.6.0/external-systems-configuration-guide/717035/wallix-bastion), [Sekoia](https://docs.sekoia.com/integration/categories/iam/wallix/) |
| Access Manager | log files, audit log per organization, SNMP traps | log files and their forwarding, which is unconfirmed (gap A7), are in the [logging and SIEM reference, section 1.3](../reference/logging-and-siem.md#13-access-manager-log-files-and-forwarding); the vendor forbids external agents on the appliance; SNMP in the [farm runbook, section 9](../runbooks/access-manager-farm.md#9-metrics-logs-and-monitoring) | [Access Manager 6.0.5 Sessions Audit Guide](https://doc.wallix.com/) 5, [AM 15.2, 18, ch. 5](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |

## 2. Rotation and lifecycle

- **SAML certificate**: create the new certificate in Security settings > Application
  certificates, assign it to the Access Manager (and Bastion) app, re-import the IdP metadata
  on the SP side and verify the authentication; removing the old certificate afterwards is a
  recommendation, not a documented step.
  Source: [Certificate renewal](https://trustelem-doc.wallix.com/books/trustelem-administration/page/certificate-renewal).
- **RADIUS secret and API key**: change in Trustelem (or Bastion) and immediately in the
  Bastion RADIUS entries, the Shared Secret field of each AM RADIUS server (the 5.2 guide names
  a "Change Shared Secret" toggle, the 6.0.5 guide only the field) and the "Change API Key"
  option of the AM Bastion object.
  Sources: [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 3.2.4 and 4.3.6, [AM 11 and 13](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf).
- **Agents**: ADConnect upgrades by installing the new connector in parallel and listing it
  first; no procedure is documented for Trustelem Connect (upgrade one VM at a time).
  Source: [ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect).
- **Users**: joiners and leavers flow from AD through ADConnect; Bastion and Access Manager
  resolve groups at login, so removing the AD group removes access at the next login. Active
  sessions are not cut by mapping changes.
  Source: [Bastion 7.3.1.1.3](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf).
- **Lost phone**: user requests a rescue code, an administrator releases it from Alerts, the
  user re-enrols.
  Source: [Loss of a second factor](https://trustelem-doc.wallix.com/books/trustelem-administration/page/loss-of-a-second-factor).

## 3. Upgrades and backups

- **Bastion HA**: minor upgrades follow "Minor upgrade in HA mode": snapshot or back up each
  node ("In case of a Master/Slaves setup, start with the Slaves"), copy the ISO and signature
  files to each node, `wallix-replication --stop` on the primary master, upgrade every node as
  `wabupgrade` with `wallix-upgrade` (`BastionSecureUpgrade` up to 12.3.4; "you can perform this
  operation in parallel on all nodes"), reboot all nodes, then `--dump-resync`, `--start` and
  `--monitoring` on the primary master. "Your WALLIX Bastion will be unavailable and unusable by
  all users during the update procedure": plan a full-cluster outage window (*inference* from
  the procedure). Rollback: restore the snapshots (virtual appliances) or reinstall the previous
  ISO and restore the configuration backup (physical appliances). The "controlled deployment"
  and "auto deployment" approaches of chapter 6 apply only to migrations from a pre-12 Bastion.
  Backups: the key "must be between 16 and 128 characters long"; restore only on a master, which
  pauses and resumes the replication by itself ("You cannot restore a backup on a Slave
  Bastion"). Procedure in the [HA runbook](../runbooks/bastion-ha-replication.md) section 8.
  Sources: [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 6, 7.2 and 7.4, [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 14.2 and 14.2.6.
- **Access Manager farm**: minor upgrades within 6.x follow "Minor upgrade in HA mode": back up
  with `wabam-backup` on the primary master, copy the ISO and signature files to each node,
  `wallix-replication --stop`, `wallix-upgrade -i ... -c ... -s ...` as `wabupgrade` on both
  nodes (parallel allowed), reboot both, then `--dump-resync`, `--start` and `--monitoring` on
  the primary master; replication is stopped, not uninstalled. "Your WALLIX Access Manager will
  be unavailable and unusable by all users during the update procedure." Moving from 5.1 or 5.2
  to 6.x is a migration: "You must import your existing data into a new instance using the
  backup/restore functionality", on a parallel cluster (`wabam-backup`, fresh 6.x nodes,
  `wabam-restore`, `wabam-init-database`, replication reinstalled) switched over after tests.
  Procedure in the [Access Manager farm runbook](../runbooks/access-manager-farm.md) section 7.
  *Access Manager 5.2:* uninstall replication before upgrading (required for 5.2.3, WAB-17588)
  and upgrade with `./access-manager-upgrade.sh`.
  Sources: [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 7, 7.3, 8.1 and 8.2, [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.3.3.4,
  [AM release notes WAB-17588](https://pam.wallix.one/documentation/release-notes/am-rn-en.html), [AM Install Guide 3.6](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf).
- **Compatibility**: check the Bastion and Access Manager compatibility matrix before any
  upgrade (support login required); the versions the guides state are in the
  [overview, section 2](01-overview.md#2-product-naming-and-versions).
  Source: [Compatibility article](https://support.wallix.com/hc/en-us/articles/24928252714013-Compatibility-Between-Bastion-and-Access-Manager).
