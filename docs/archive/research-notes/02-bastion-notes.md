# Research notes 02: WALLIX Bastion architecture, HA and external authentication

Working notes gathered on 2026-09-22 from the Bastion 12.3.2 Functional Administration Guide,
the 12.0.2 Deployment Guide, the 12.3.2 Users and Auditor guides, the 10.0.6 Quick Start,
the 9.0.2 legacy administration guide, release notes, AWS Marketplace listings and WALLIX
advisories. Facts are tagged verified, inference or gap.

## Versions and editions

- Verified: current on-premises line is 12.4.x; 12.4.3 on AWS Marketplace on Debian 12.15 (https://aws.amazon.com/marketplace/pp/prodview-up3f6pn7fybfi); 12.3.6 on Debian 12.13 (https://aws.amazon.com/marketplace/pp/prodview-y5hi5ceigyrwo). Public release notes cover 12.0.1 to 12.3.2 without per-version dates (https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html). 12.4 release notes sit behind the SSO-protected doc site.
- Verified (https://www.wallix.com/support-services/alerts/): WSA-2026-07-0001 (CVSS 10, unauthenticated REST API privilege escalation, affects 12.3.0 to 12.3.6 and 12.4.0, fixed in 12.3.7 and 12.4.1, published 2026-07-20); WSA-2026-07-0002 SAML SP bypass in Access Manager fixed in 5.1.10, 5.2.7, 6.0.4; 2025-03 AD discovery credential leaks fixed in 12.0.9.
- Verified release highlights: 12.0.1 Kerberos default for NLA; 12.1 API keys with profiles; 12.2 Web Session Manager, OIDC, unified WAMUT client, FIDO2 for SSH proxy users, Debian 12.11; 12.3 redesigned target groups, Kerberos-Password deprecated; 12.3.1 Kerberos primary authentication on the RDP proxy; 12.3.2 dynamic SAML/OIDC URLs, legacy DRBD code removed, eth1 becomes a standard NIC, Debian 12.13.
- Verified: Session Manager and Password Manager are licence-gated features inside Bastion (admin guide 1.1); Access Manager is a separate appliance. Marketing brands the product "WALLIX PAM" with PASM, PEDM, Secure Remote Access and MFA pillars (https://www.wallix.com/products/privileged-access-management/).
- Verified: WALLIX One PAM (SaaS) drops X.509 user authentication, IPv6 targets, session invite, transparent mode, custom plugins, on-premises remote storage; HA documentation "to be disregarded" (https://pam.wallix.one/documentation/deployment/getting-started/limitations.html); connectivity by IKEv2 IPsec tunnel (https://pam.wallix.one/documentation/deployment/getting-started/prerequisites.html).
- Gap: no "Essential/Advanced" editions found in public sources.

## Internal architecture

- Verified: Debian 12; the database is MariaDB/MySQL, not PostgreSQL (the upgrade procedure stops `mariadb`; replication uses ports 3306/3307) (Deployment Guide https://marketplace-wallix.s3.amazonaws.com/bastion_12.0.2_en_deployment_guide.pdf; https://www.varnostne-resitve.si/wp-content/uploads/2025/03/TECHDOC360_Classic-WALLIX-Bastion-Architecture-OT.pdf).
- Verified (Deployment Guide 2.1, ch. 7): system accounts `admin` (GUI), `wabadmin` (SSH admin console TCP 2242), `wabsuper` (sudo), `wabupgrade` (CLI upgrades with `BastionSecureUpgrade`), `wabbootadmin` (GRUB); factory IP 192.168.10.5/24.
- Verified: web UI at `https://<bastion>/ui`; REST API under `/api` with documentation at `https://<bastion>/api/doc/Usage.html`; API keys bound to profiles and IP-restrictable; headers `X-Auth-User` and `X-Auth-Key` (https://github.com/wallix/wbrest_samples); SCIM 2.0 API (https://scim.wallix.com/scim/doc/Usage.html); Terraform provider (https://github.com/wallix/terraform-provider-wallix-bastion).
- Verified (admin guide 12.1, 12.16.4): SSH/SFTP/SCP/TELNET/RLOGIN proxy on TCP 22; RDP/VNC proxy on 3389 (RDP proxy configuration called "sesman"); RAW TCP/IP = Universal Tunneling (SSH tunnel from the workstation with WALLIX-PuTTY, WAMUT or OpenSSH; sessions recorded as PCAP). Inference: the RDP proxy engine is the open-source "redemption" project (https://github.com/wallix/redemption). No HTML5 gateway in Bastion itself; HTML5 is delivered by Access Manager. Web Session Manager is a separate server linked by hostname and JWS/JWE keys (admin guide 12.2).
- Verified: Session Probe runs inside the RDP session, collects window, process, clipboard and drive metadata for SIEM, blocks TCP jump connections, masks password input (admin guide 12.16.1.4).
- Verified (Auditor guide https://pam.wallix.one/documentation/user-doc/bastion_en_auditor_guide.pdf): RDP video with OCR of title bars, MP4 export; SSH/TELNET as .txt/.ttyrec; embedded player; 4-eyes and 4-hands.
- Verified (TECHDOC360; Deployment Guide 2.2): remote recording storage on SMB/CIFS, NFS or Amazon EFS, moved after session end, kept locally if the share is down; NFS 2049, CIFS 445.
- Verified: vault with global domains (local or external vault via REST API), local domains per device, password change plugins, SSH CA per domain, checkout/check-in, Break Glass; discovery scans (network, AD, Azure AD); ICAP AV/DLP scanning.

## High availability and clustering

Legacy design (Bastion 11 and earlier, hardware appliances only), verified from the 9.0.2 guide (https://archive.smile.ci/assets/Bastion-admin-guide-fr.pdf) and 10.0.6 Quick Start (https://marketplace-wallix.s3.amazonaws.com/Bastion-quickstart-en.pdf):

- Two-appliance active/passive failover sharing a virtual IP; DRBD replicates configuration, logs and recordings; crossover cable on eth1; identical version and hotfix; `WABHASetup`, `systemctl start wabha`, `/opt/wab/bin/WABHAStatus`. Split-brain: passive promotes itself, DRBD detects divergence when the link returns, the cluster stops and the admin picks the reference master. Not supported on virtual appliances.

Current design (Bastion 12.x) "HA Database Replication", verified from the Deployment Guide 12.0.2 chapter 5 and the 12.3.2 release notes:

- DRBD removed in 12; restoring a DRBD-era backup yields a standalone node.
- Replication is MariaDB replication over an SSH tunnel kept up by `autossh`; slaves pull (outbound 3307 to inbound 3306 through the tunnel); the database is never exposed. Inference: the tunnel rides the 2242 admin SSH channel.
- Modes: Master/Slave(s) (one active master, N passive slaves, no changes on slaves) and Master/Master (bidirectional, exactly two nodes with primary and secondary master; partner doc: "limited to 2 Bastions max").
- Prerequisites: identical versions; encryption initialised on every node; IPv4 addresses only; do not clone VMs (UUID conflicts); the primary master's database overwrites the others; SMTP on the master; same timezone; configuration in `/etc/sqlreplication`.
- Tooling: `bastion-replication --create-conf-file | --prerequisite-check | --install | --monitoring | --install-monitoring | --install-notification | --status | --resync | --dump-resync | --add-slave | --elevate-master | --stop | --start | --uninstall`. Mail templates ha_master_fault, ha_master_up, ha_slave_missing.
- Not replicated: audit and session tables (each node keeps its own history), recording options, configuration options, connection messages, licence, audit logs, network, time service, SNMP, SMTP, service control, SIEM integration, GPG fingerprints, device certificates. Limitations: no simultaneous API provisioning in Master/Master; password operations and scheduled rotation only from the primary master; "change password at check-in" not in Master/Slave; approvals replicated only in Master/Master.
- No VIP or heartbeat in 12.x: failover is administrative (`--elevate-master`) or handled by front-end routing. The glossary defines a "Bastion cluster" as a set of Bastions allowing load balancing and HA; the SAML SP Entity ID can be set to a load balancer FQDN; OIDC works with any FQDN in a cluster; Access Manager supports clustered Bastions with failover and load balancing. Partner reference: load balancer in front of two Access Managers on 443 with WebSocket upgrade, cookie persistence and X-Forwarded-For (TECHDOC360). Inference: active proxy sessions on a failed node are dropped because the proxies terminate TCP locally.
- DR: a DR Bastion refreshed by non-real-time backup/restore; centralised, hybrid and distributed architectures documented for OT (TECHDOC360). Gap: integration node HA.
- Upgrade in HA: all nodes on compatible versions; minor upgrades with `wabupgrade` starting with slaves; "parallel cluster" method (clone cluster, upgrade, `bastion-replication --stop/--start`); snapshot before upgrade (Deployment Guide ch. 6 and 7).

## External authentication and MFA

- Verified (admin guide 7.1): LDAP/AD bind password, Kerberos ticket, Kerberos-Password (deprecated), local password, RADIUS, TACACS+, PingID, SAML 2.0, OIDC, SSH key and SSH CA, X.509 certificate, FIDO2 for SSH proxy users.
- Verified (7.1.3): single-factor or two-factor only; a primary authentication on the authentication domain plus a secondary authentication (RADIUS, TACACS+, PingID, Kerberos-Password); extra factors live in the IdP.
- Verified (7.2.5.2, 12.16.1.2): Kerberos keytab upload; SPN `host/` for the SSH proxy and `TERMSRV/` for the RDP proxy with NLA; RDP target authentication matrix (NLA Kerberos, NLA NTLM, TLS only, RDP legacy).
- Verified (7.2.5.4, 7.4.3.4): RADIUS per RFC 2865 and 8044, challenge-response supported, standard attributes only (User-Name, User-Password, State, NAS-Identifier=WAB, Framed-IP-Address), port 1812, timeout 5 s default, "Use mobile device for 2FA" and "Use primary domain name for 2FA" options; sole method for local users or secondary for LDAP/AD. Third-party guides confirm (https://www.protectimus.com/guides/wallix-mfa/, https://www.wallix.com/wp-content/uploads/2020/12/Okta-WALLIX-Integration-Guide.pdf).
- Verified (7.3.1): SAML IdP-initiated and SP-initiated flows; "SAML dynamic flow"; IdP metadata upload prefills claims; default timeout 900 s; SP entity ID changeable to the load balancer FQDN; NameID must be an e-mail address whose domain equals the authentication domain name; Force authentication native for Entra ID and Okta; variants SAML Generic and SAML for Entra ID (Graph API); only SAML Generic works through Access Manager and, once SAML is fronted by AM, direct SAML logon to Bastion is impossible. SAML end to end since Bastion 10.4 with AM 4.4.
- Verified (7.3.2): OIDC native since 12.2, Authorization Code Flow only, discovery, username and group claims mandatory.
- Verified (2.3): X.509 is GUI only; proxy users are redirected to the GUI.
- Verified (7.1.1, 12.4, 12.5, Users guide https://pam.wallix.one/documentation/user-doc/bastion_en_user_guide.pdf): the matrix marks SAML and OIDC on SSH and RDP proxies as supported but not fully integrated (copy a link into a browser, get a token, paste it in the client); practical pattern is to authenticate in the web UI and download an instant-access connection file carrying a one-time password (default TTL 30 s, configurable). With Kerberos enabled on the RDP proxy, SAML/OTP/RADIUS users must set `enablecredsspsupport:i:0` and `authentication level:i:2` in mstsc or `/sec:tls` in FreeRDP. SSH primary connection uses keyboard-interactive prompts, which is how a RADIUS challenge reaches an SSH client. Approval requests can be raised from the RDP and SSH clients.

## Authorization model

- Verified (6.1, 13.1 to 13.3, 12.6, 11.3 to 11.7): permission profiles (product_administrator, operation_administrator, read-only and custom; API keys intersect user and key profiles); user groups with external mappings, restrictions and time frames; target groups with accounts, account mappings and interactive targets; authorizations = user group x target group with sub-protocol flags (SSH_SHELL_SESSION, SSH_REMOTE_COMMAND, SFTP_SESSION, RDP, RDP_CLIPBOARD_UP/DOWN, RDP_DRIVE...), recording and critical flags, approval settings with quorum and time frame; global, local and authentication domains; connection and checkout policies; Protected Users group; AD authentication silo.

## Network ports (Deployment Guide 2.2, Quick Start 5.2)

- Inbound: 22 (SSH/SFTP/TELNET/RLOGIN proxy), 3389 (RDP/VNC proxy), 443 (web UI and REST API), 2242 (SSH admin console), 161 (SNMP).
- Outbound: 22, 3389, 80/443, 25/465/587 (SMTP), 123 (NTP), 53 (DNS), 88 (Kerberos), 389/636 (LDAP), 1812 (RADIUS), 49 (TACACS+), 2049 (NFS), 445 (CIFS), 139/445 (SMB password management), 514 (syslog), 162 (SNMP traps). Replication between nodes: 3306/3307 inside the autossh tunnel. Gap: RADIUS accounting 1813 not mentioned.

## Deployment, sizing, licensing

- Verified (Deployment Guide 3.2; AWS listing): ISO, Hyper-V vhdx, KVM/OpenStack qcow2 (also Nutanix AHV), VMware OVA; AWS AMI (BYOL), Azure Marketplace, GCP and Alibaba on request; hardware appliances. Disk is LUKS-encrypted with a default passphrase that must be changed except on AWS.
- Verified (Quick Start 10.0.6): minimum 2 vCPU, 4 GB RAM, 50 GB; 25 RDP/110 SSH sessions = 4 CPU/8 GB; 25/240 = 4/16; 40/240 = 8/16; 50/480 = 8/32; 75/480 = 16/32. The 12.x sizing KB requires a support login (https://support.wallix.com/s/article/Wallix-Bastion-sizing).
- Verified: licence key issued from a context file; Session Manager, Password Manager, External Vaults and WAAPM are gated features. Gap: per-user versus per-target metrics not public.

## Logging, SIEM, audit, certifications

- Verified: System > SIEM integration with syslog UDP or TCP, RFC 3164 with ISO timestamps, selectable categories (configuration, authentication, accounts, proxies, sessions) (https://docs.sekoia.com/integration/categories/iam/wallix/); parsers for Splunk (https://github.com/wallix/Splunk-add-on), Google SecOps, FortiSIEM, Sekoia, Cortex XSOAR (https://xsoar.pan.dev/docs/reference/integrations/wallix-bastion). Audit tables are node-local.
- Verified: ANSSI CSPN first-level certification for Bastion 6.0.102 (2020-01) (https://www.wallix.com/wp-content/uploads/2020/08/20200113-CSPN_EnglishVersion.pdf); a German BSI certification reported (https://www.solutions-numeriques.com/wallix-obtient-la-certification-du-bsi-et-accelere-sur-la-scene-europeenne/). Gap: no ANSSI qualification or Common Criteria evidence.
