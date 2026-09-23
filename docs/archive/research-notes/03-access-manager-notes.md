# Research notes 03: WALLIX Access Manager architecture, clustering and authentication

Working notes gathered on 2026-09-22 from the Access Manager 5.2.4.0 Administration Guide
(AG), the 5.2.4.0 User Guide (UG), the 4.0.6.1 Installation Guide (IG), the Access Manager
release notes (RN), the Bastion 12.3.2 Functional Administration Guide (BAG) and the WALLIX
security advisories page. Facts are tagged verified, inference or gap.

## Product and versions

- Verified (AG ch. 3): Access Manager "provides connection services between web browsers and targets... Target accesses are performed through Wallix Bastion appliances. The connections are done using HTML5 clients; no browser plug-in is required." Users with rights can display or copy target passwords.
- Verified (AG ch. 8): multi-tenancy through Organizations; a user and a Bastion belong to a single organization; built-in `global` organization for administrators, deletable `default` organization.
- Verified (AG 14.2, UG ch. 5, RN WAB-6270/6558): sessions use the bundled SSH, RDP and WAMUT (Universal Tunneling, formerly RAWTCPIP) clients; SFTP/SCP, RemoteApp, VNC via Session Invite; Seamless Connection mode from Bastion 12.2 with AM 5.2.
- Inference: no native-client launch (`.rdp` files, mstsc, PuTTY) is described; the only non-HTML5 path is the WAMUT tunnelling client.
- Verified (RN): 5.0.0 on 2024-01-22 (MySQL replication script, X.509 as first factor, trusted-proxy anti-spoofing); 5.1.0 on 2024-10-24 (Debian 10 extended LTS, SameSite cookie for SAML); 5.1.1 on 2024-11-12 (CVSS 9.1 disabled-account bypass fix); 5.1.3 on 2025-04-18 (hardware appliance); 5.2.0 on 2025-06-03 (Java 17, Jetty 11, OIDC, Elasticsearch 8.18); 5.2.4.0 on 2026-03-12.
- Verified but thin: advisory WSA-2026-07-0002 (2026-07-20) lists fixed versions "5.1.10, 5.2.7, 6.0.4 and higher", so a 6.0 line exists; RN WAB-16660 says versions before 6.0 are incompatible with Dell R660 hardware; a partner states AM 6.0 is based on Debian 12 (https://sns-security.fr/bastion-administration-deploiement-points-de-vigilance/). Gap: 6.0 release notes sit behind the SSO-protected doc site.
- Verified: WALLIX One PAM (SaaS) "includes the functionalities of WALLIX Bastion and WALLIX Access Manager" (https://pam.wallix.one/documentation/deployment/release-notes/1.6.0.html); WALLIX One Console (2026-04) manages Bastion and AM appliances centrally (https://www.ironie.fr/wallix-one-console-la-tour-de-controle-de-lecosysteme-wallix/). Inference: AM is not being merged into Bastion; it stays a separate appliance.

## Internal architecture

- Verified (RN WAB-10062, WAB-17644, WAB-9889, WAB-16998, WAB-2850; AG ch. 16, 17, 21): Java 17 on Jetty 11; GWT/React front end and Xterm.js; FreeRDP 3.x as the RDP engine; OpenSAML, jose4j / oauth2-oidc-sdk, TinyRadius, Apache LDAP API; Elasticsearch 8.18 as session audit repository; MariaDB 10.5 embedded on the appliance or external MySQL, Oracle or Azure database.
- Verified (IG 3.4.1, AG 21.9): the application runs as the Docker container `access-manager_access_manager_1` behind Apache2 on the appliance; configuration in `/var/wab/etc/wabam/wabam.properties`, JVM options in `wabam.vmoptions` (default heap 2373 MB).
- Verified (AG 1.1, RN WAB-9787, WAB-4132, WAB-1876): Debian 10 extended LTS for 5.x; appliance images for Alibaba, AWS, GCP, KVM, Azure, Hyper-V, Nutanix AHV, OpenStack, VMware, plus a physical appliance since 5.1.3. The standalone installer of the 4.0 era is discontinued.
- Verified (AG ch. 13, 10.4.3; BAG 6.1.2): each Bastion object holds Host (Bastion user interface IP), a REST API key, certificate and SSH/RDP fingerprint pinning, cluster membership, Strip Domain, time zone and custom ports (SSH 22, RDP 3389, REST 443). Bastion 12.1+ API key profiles: `wallix_access_manager_session_audit` (recommended), `wallix_access_manager_session`, `wallix_access_manager_audit`; AM allows only one API key per Bastion.
- Verified (IG 2.4.1, AG 15.1.1.4, BAG Universal Tunneling auditing): AM opens SSH 22, RDP 3389, HTTPS 443, LDAP 389/636 and Elasticsearch 9300 outbound; the Bastion sees the AM IP as the client. Inference: the HTML5 gateway lives on AM; browser to AM over HTTPS/WebSocket, AM to Bastion proxies as an ordinary client, Bastion to target. Any proxy in front of AM must support WebSocket (RN header).
- Verified (AG ch. 8, 10, 12.2, 14): organization identifier in the URL path (`https://<host>/wabam/<org>`) or FQDN prefix; domain selected with `?domain=<name>`; user login "should match the WALLIX Bastion user login in order to properly retrieve user's authorizations"; AM profiles (Global Administrator, Administrator, Approver, Auditor, User) matched by name; authorizations pulled from every active Bastion at login.

## High availability and clustering

- Verified (AG 20.1): "it is possible to deploy several Access Manager instances. Such a deployment will also provide high-availability by preventing Access Manager to be a single point of failure. The load-balancing itself should be implemented in front of the instances." Active/active farm behind an external load balancer; no active/passive VIP mode documented. Gap: maximum node count.
- Verified (AG 20.1): install node 1 normally; on each additional node copy `crypto.install.key`, all `db.connections*` properties and `user.admin*` credentials from node 1 into `wabam.properties`, restart the service. "If the databases of the two appliances are replicated, there is no need to duplicate the db.connections parameters."
- Verified (RN WAB-6124, WAB-11782, WAB-11783, WAB-12957, WAB-15150, WAB-15457, WAB-17588; AG 21.7, 21.1): appliance MySQL/MariaDB replication script since 5.0.0 with `--prerequisite-check`, a mandatory HA interface and `/root/sqlreplication/servers_list`; "Before upgrading an Access Manager cluster to version 5.2.3, replication must be uninstalled. Replication can be reinstalled after the upgrade."; `purge.audit.active` on one node only; `rdp.clientName` per node. Gap: replication port and master/master versus master/slave are not public (MariaDB 3306 assumed).
- Verified (AG 21.5, 21.6; RN WAB-4975, WAB-8043): AM expects an HTTP proxy in front (`web.proxy.activated=true`), honours `X-Forwarded-For/-Host/-Port/-Proto/-Server` and RFC 7239 `Forwarded`; `web.proxy.trusted-proxies` with `web.proxy.trusted-proxies.enabled` prevents header spoofing. Inference: TLS termination at the load balancer is supported; TLS pass-through works since AM listens on 443 with its own certificate (`wabam-certificate-update`, `web.sni.host.check`).
- Verified (RN WAB-6600): Citrix ADC/NetScaler cookie-based persistence is incompatible with Universal Tunneling for AM clusters. Inference: web sessions are Jetty in-memory and WebSocket sessions are pinned to the node that opened the RDP/SSH connection, so source-IP affinity is the safe choice. Gap: no published health-check URL; Elasticsearch status on 9200.
- Verified (AG 13, 20.2, 15.1.1.1, 15.1.1.5; RN WAB-17043): Bastions with identical authorizations can form an AM Cluster; each connection goes to the Bastion with the fewest sessions; enable `bastion.cluster.identical.mode` when nodes share configuration and proxy certificates; clusters are incompatible with password display (external vault is fine); keep `bastion.connection.timeout` and `restapi.connection.timeout` low; known issue where AM keeps trying an unreachable member (disable it on the Bastion page). Inference: a Bastion HA pair with a VIP can be declared once with the VIP as Host; an AM cluster of Bastions is the alternative for active/active spreading.
- Verified (AG 10.1 to 10.3): authenticators and identifiers carry Factor and Priority; equal priority means random round robin, otherwise failover; within a SAML domain each IdP server is equivalent.

## Authentication

- Verified (AG ch. 10, 11): domain types local, LDAP/AD (recursive AD group search), SAML, BASTION, OIDC; RADIUS servers attach as authenticators. Kerberos is absent from the AM guide.
- Verified (AG 10.1; RN WAB-6292, WAB-6397): multi-factor is an ordered chain of authenticators that must all succeed; "Factor Used for Account Mapping" picks which factor's password is forwarded to the Bastion for account mapping; X.509 client certificate can be the first factor followed by RADIUS. No built-in TOTP; MFA is delegated to RADIUS (PAP/CHAP, challenge-response, IPv6 unsupported) or to the SAML/OIDC IdP. WALLIX Authenticator: "Access Manager is compatible with SAML (recommended), LDAP and Radius"; FIDO2 keys with AM via SAML only.
- Verified (AG 10.3; RN WAB-8861, WAB-4968, WAB-11153): SAML SP tab (Entity ID up to 256 chars, Sign Messages, Encrypt Messages, Signed Response, Signed Assertion, Force Authent., expiry delay), IdP tab (metadata import, bindings, logout URIs, validation certificate), Domain tab (Login, Display Name, Email, Language, Profile). Known issues: 3-NIC appliances auto-fill the SAML URL with the admin interface URL; missing `SigAlg` with signed Redirect. Gap: ACS URL pattern and NameID format only appear in the generated SP metadata; login URL pattern `https://<host>/wabam/<org>?domain=<DOMAIN>`.
- Verified (AG 10.5): OIDC since 5.2.0, Authorization Code Flow, IdP Redirect URL auto-populated and must be changed when users reach AM through another hostname (load balancer), discovery with Match, scope must include `openid`, RS256, certificate verification, 5 s timeout.
- Verified (RN WAB-3405; AG 10.3.2, 10.5.2; BAG 7.3.1): integrated SAML workflow since Bastion 10.4 with AM 4.4 using the same IdP on both; requirements: AM domain name equals Bastion "Domain server name", AM Login attribute equals Bastion Username claim, Encrypt Messages disabled, Strip Domain disabled so `user@domain` is kept. "Only SAML Generic is compatible with WALLIX Access Manager. The configuration of a SAML authentication with WALLIX Access Manager means that it is impossible to authenticate directly to WALLIX Bastion in SAML." Inference: AM opens Bastion sessions through the REST API key on behalf of `login@domain`, so the user is never re-prompted; MFA at the IdP is the only interactive authentication. Account-mapping targets need a saved password in preferences (UG ch. 4) or Bastion vault transformation rules.
- Verified (AG 8.3, 12.2, 15.1.1.8, 21.5; IG 3.4.2): `session.maxInactiveInterval`, `session.keepAlive`, per-organization password policies and lockout, restricted source IPs per user, DoS filter `web.max.requests.perSec=60`, Apache `SESSION_TIMEOUT`.
- Verified (https://www.wallix.com/support-services/alerts/): WSA-2026-07-0002 (2026-07-20, CVSS 8.7) SAML SP bypass allowing a forged SAML response to log in "under an attacker-chosen identity and privilege level", fixed in 5.1.10, 5.2.7 and 6.0.4; WSA-2026-02-0001 credentials in logs, fixed in 5.1.7 and 5.2.4; 2024-11 CVSS 9.1 disabled or expired account bypass, fixed in 5.1.1 and 4.0.8.

## Network ports

- Verified (IG 2.4; AG ch. 5, 11, 15.1.1.13; IG 3.2; RN WAB-13606): inbound HTTP 80 (redirect), HTTPS 443 (UI and WebSocket sessions), 9300 Elasticsearch intra-cluster, optional 9200, SSH admin 2242, SNMP 161/162. Outbound 22, 3389, 443 (Bastion REST API and IdP endpoints), 389/636, 1812/udp, 9300, plus `ut.port.range` for Universal Tunneling. Appliance NICs: user access, HA (database replication), administration; since 5.2.4.0 the admin service binds to the first interface.

## Deployment and operations

- Verified (IG 3.2, 2.1.3; RN; AG 21.2): appliance minimum 2 vCPU, 4 GB RAM, 40 GB disk; 5.2.4.0 asks for 4 GB RAM and 50 GB disk; legacy table 100 users/10 sessions = 1 CPU 2 GB, 500/50 = 3 CPU 3 GB, 1000/100 = 6 CPU 4 GB.
- Verified (AG ch. 4; AWS Marketplace https://aws.amazon.com/marketplace/pp/prodview-6gdcxmn2wyj5s): licence key from the About page or CLI; BYOL on AWS; evaluation licence 31 days and 5 concurrent users.
- Verified (IG 3.6; RN): upgrade by mounting the ISO and running `./access-manager-upgrade.sh`; `wabupgrade` user for hotfixes; uninstall replication before a cluster upgrade.
- Verified (AG 15.3): `wabam-backup -d -n -p` produces an AES-256 zip with database, keystore and `wabam.properties`; `wabam-restore`; GUI backup limited to 10 MB; MySQL/MariaDB only.
- Verified (AG 15.2, 18, 19, 21.7; AG ch. 5): `access.log`, `error.log`, `tech.log` in `/var/log/wallix/wabam`; per-module log levels; audit log of all user actions per organization; session audit pulled from Bastions into Elasticsearch with `sa.session.retention.days` (30 days default) and GDPR purge; SNMP v2c/v3 with traps. Gap: no native syslog forwarder documented for AM.

## Sources

- https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf
- https://pam.wallix.one/documentation/release-notes/am-rn-en.html
- https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf
- https://pam.wallix.one/documentation/user-doc/am-user-guide_en.pdf
- https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf
- https://pam.wallix.one/documentation/deployment/release-notes/1.6.0.html
- https://www.wallix.com/support-services/alerts/
- https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager
- https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml
- https://trustelem-doc.wallix.com/books/wallix-authenticator/page/presentation
- https://docs.trustbuilder.com/mfa/wallix-access-manager-saml-2-0-configuration
- https://aws.amazon.com/marketplace/pp/prodview-6gdcxmn2wyj5s
- https://www.wallix.com/wp-content/uploads/2020/07/WALLIX_BASTION_ACCESS_MANAGER_EN.pdf
- https://www.ironie.fr/nouveautes-wallix-bastion-12-2-access-manager-5-2/
- https://www.ironie.fr/wallix-one-console-la-tour-de-controle-de-lecosysteme-wallix/
- https://sns-security.fr/bastion-administration-deploiement-points-de-vigilance/
