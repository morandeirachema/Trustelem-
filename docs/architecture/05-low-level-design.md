# Low-level design

> - **Purpose:** the naming and mapping rules, certificates and secrets, the network flow and port matrix, the timeouts to align, sizing and the security hardening checklist.
> - **Audience:** PAM architect, network and security engineers, Bastion and Access Manager operators.
> - **Verified:** 2026-09-24 against the public Bastion 12.3.2 and Access Manager 5.2.4.0 guides, the Bastion 12.4.3 and Access Manager 6.0.5 customer guides and the Trustelem documentation books.
> - **Sources:** [Bastion Administration Guide 12.3.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Access Manager Administration Guide 5.2.4.0](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf), Bastion 12.4.3 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), Access Manager 6.0.5 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), [Connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows), [WALLIX security advisories](https://www.wallix.com/support-services/alerts/).

## 1. Naming and mapping rules

| Item | Value in this design | Rule |
|------|---------------------|------|
| Bastion authentication domain (SAML) | `Domain server name` = `TRUSTELEM`, `Authentication domain name` = `TRUSTELEM` | The Domain server name must equal the AM SAML Domain Name ("the server domain name must be identical to the Domain Name field in the domain configuration on WALLIX Access Manager"); "WALLIX recommends to insert the same name as for Domain server name" in the Authentication domain name ([Bastion 7.3.1.1.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf)) |
| Trustelem SAML NameID | e-mail address | "select email address. The domain of the e-mail address must be the same as the authentication domain name" ([Bastion 7.3.1.1.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf)); *inference:* the Default domain toggle (which "strips the domain part (that is @domain) from the user login") and the Default email domain may reconcile a mismatch, but the guide does not say so; test it |
| Login attribute | `uid` for AD users, `email` for Trustelem local users | Trustelem AM template ([AM app](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager)) |
| Bastion Username claim | same attribute as the AM Login attribute | [Bastion 7.3.1.1.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| Group claim | `groups`, filled by the Trustelem script `for (let g in groups){ msg.addAttr("groups",g); }` | one value per Bastion mapping, case-insensitive ([Bastion 7.3.1.1.3](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Bastion SAML app](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml)) |
| AM profile | `profile` attribute set by script, matched by name to AM profiles; Default Profile = User | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.3.1, [AM 10.3.1](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| AM Entity ID | `WALLIX-AM` (Trustelem template) or `https://<am-fqdn>/wabam/<org>?domain=TRUSTELEM` | [AM app](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager), [TrustBuilder guide](https://docs.trustbuilder.com/mfa/wallix-access-manager-saml-2-0-configuration) |
| Bastion SP Entity ID | load balancer FQDN when native SAML is used through an LB | [Bastion 7.3.1.1.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| Bastion API key for AM | profile `wallix_access_manager_session_audit`, IP limitation to the AM nodes | profile per [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 3.2.1 and [AM 13](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf); IP limitation set on the Bastion, one address per field, no subnets ([Bastion 6.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 12.1) |
| RADIUS NAS-Identifier | `WAB` from Bastion; AM sets its own NAS Identifier field | [Bastion 7.2.5.4](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.6, [AM 11](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |

## 2. Certificates, keys and secrets

| Object | Where it lives | Rotation impact |
|--------|---------------|-----------------|
| Trustelem SAML signing certificate | Security settings > Application certificates, one per app | Re-import IdP metadata in AM (and Bastion if native SAML); brief interruption ([Certificate renewal](https://trustelem-doc.wallix.com/books/trustelem-administration/page/certificate-renewal)) |
| AM SP signing key (optional) and metadata | SAML Identity Providers page, generated or pasted PEM ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.3.2.1) | Sign Messages is off in the Trustelem template; the Access Manager 5.2.4.0 release notes list known issue WAB-11153, SAML authentication "can fail due to a missing "SigAlg" query param" when it is on with the Redirect binding ([AM release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html); not mentioned in the 6.0.5 guides) |
| AM portal TLS certificate | `wallix-proxyma-rotate-tls-certificate -c` (certificate) `-k` (unencrypted key) on each node, since server certificates do not replicate; SAN lists every client and load-balancer hostname (strict SNI). Access Manager 5.2: `wabam-certificate-update` (WAB-9894, WAB-14102) | LB re-pins if pass-through ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.2.1 and 8.5.4.4, [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 6, [AM release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html)) |
| Bastion TLS certificate and proxy certificates | Bastion web UI | Toggle "Reset Bastion Certificate" and fingerprints in AM after change ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 3.2.4, [AM 13](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)) |
| RADIUS shared secret | Trustelem Bastion app model; Bastion and AM RADIUS entries | Change on both ends at once; in AM edit the Shared Secret field of each RADIUS server ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.6 lists no "Change Shared Secret" toggle; the 5.2 guide, [AM 11](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf), names one) |
| Bastion API key | Bastion Configuration > API keys page ([Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) ch. 12; profile and IP limitations cannot be changed, so rotation means a new key); AM Bastion object | "Change API Key" option in AM ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 3.2.4, [AM 13](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)) |
| Trustelem Connect and ADConnect sync IDs | Trustelem console (Services, Directories) and agent config | Re-register the agent if revoked ([Trustelem Connect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect)) |
| AM `crypto.install.key` | `/etc/wabam/wabam.properties` on every node | Must be identical across the farm: copied from node 1, or set up by the replication installation ([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 5.1, [AM 20.1](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)) |

## 3. Network flows and ports

| From | To | Port | Purpose | Source |
|------|----|------|---------|--------|
| Users | Load balancer / Access Manager | TCP 443 (the 6.0.5 inbound list has no port 80; the 5.2 web-application install redirected 80 to 443) | HTML5 portal, WebSocket sessions | [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 2.2, [AM Install Guide 2.4](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf) |
| Users | Bastion nodes or LB | TCP 22, 3389 | native SSH/RDP proxies | [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2 |
| Users | Trustelem | TCP 443 | SAML/OIDC login pages | [Applications export](https://trustelem-doc.wallix.com/books/trustelem-applications/export/html) |
| Access Manager | Bastion nodes | TCP 443, 22, 3389 | REST API, proxies | [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 2.2, [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 3.2.2, [AM 10.4.3](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Access Manager | Trustelem Connect | UDP 2812 | RADIUS (alternative flow; 2812 is the Access Manager listener, 1812 the Bastion listener, one port per application; the Access Manager default is 1812) | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.6, [AM 11](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf), [AM app in Trustelem](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager) |
| Access Manager | Trustelem | TCP 443 | OIDC discovery, token, userinfo and JWKS; SAML metadata is a file import and the assertion travels through the browser | [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 2.2, [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.4.2, [AM 10.5](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Access Manager | Domain controllers | TCP 389/636 | LDAP domains | [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 2.2, [AM Install Guide 2.4](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf) |
| AM node 1 <-> AM node 2 | | TCP 2242 on the administration interface: SSH tunnel maintained by autossh carrying the database ports 3307 (outbound) and 3306 (inbound) ("HA Database Replication relies on this port being open"); two nodes at most, same subnet, at most one router. Access Manager 5.2 used a dedicated HA NIC | HA Database Replication | [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 2.2 and 6, [AM Install Guide 2.4 and 3.2](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf) |
| Bastion node <-> Bastion node | | TCP 2242 on the admin interface: SSH tunnel managed by autossh carrying local 3307 to 3306 ("HA Database Replication relies on this port being open"); nodes on the same subnet, at most one router | HA Database Replication | [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2, 5 and 5.1 |
| Bastion nodes | Trustelem Connect | UDP 1812; the Bastion port table lists RADIUS as "1812/TCP and 1812/UDP", "Configurable per authentication method", and the Trustelem Connect listener is UDP ("udp port 1812 for Radius", [Trustelem Connect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect)), so open 1812/tcp only if a test shows it is used | RADIUS secondary authentication | [Bastion 7.2.5.4](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2 |
| Bastion nodes | Trustelem | TCP 443 | OIDC alternative only ([OIDC alternative](03-design-and-flows.md#7-openid-connect-as-the-alternative-to-saml)): token and metadata requests ("Allow WALLIX Bastion outbound network access to your IdP to request tokens and retrieve metadata"); the port table also lists SAML on 443, although the SAML metadata is imported as a file | [Bastion 12.4.3 Administration Guide](https://doc.wallix.com/) 7.3.2.1, [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2 |
| Bastion nodes | Domain controllers | TCP 389/636, 88 | LDAP/AD bind, Kerberos | [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2 |
| Bastion nodes | Targets | 22, 3389, 80/443; VNC 5900, Telnet 23, rlogin 513, Universal Tunneling any TCP port | sessions | [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2 |
| Bastion nodes | SIEM, NTP, SMTP, DNS, NFS/CIFS | 514/UDP, 123/UDP, 25/465/587, 53, 2049/445 | operations | [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2 |
| ADConnect, Trustelem Connect | Trustelem cloud and relays (FQDNs and IPs in [tenant setup, section 4](../trustelem/01-tenant-setup.md#4-network-prerequisites-for-every-connector)) | TCP 443 outbound only | websocket relay; certificate pinned, no TLS inspection; HTTP CONNECT proxy allowed | [Connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows) |
| ADConnect | Domain controllers | TCP 389/636 | sync and password validation | [ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect) |
| Authenticator app | Trustelem, and WNS for the Windows app | TCP 443 | push | [MFA methods](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication) |
| Admins | Bastion, Access Manager | TCP 2242, 443, SNMP 161/UDP (162/UDP for traps) | administration | [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2, [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 1.2 and 2.2, [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.4.4, [AM Install Guide 3.3 and 3.5](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf), [AM 5](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |

## 4. Timeouts to align

| Setting | Default | Recommendation | Source |
|---------|---------|----------------|--------|
| Bastion RADIUS timeout | 5 s ("By default, the timeout is 5 seconds"); entries "inherited from an earlier version of WALLIX Bastion keep the former timeout value defined", so check them after an upgrade | 45 to 60 s so a push can be approved. The Trustelem Bastion page says "let the default value, unless you have latency on your network"; an HID guide hosted by WALLIX (2019) says to "increase the Timeout to at least 45-50 seconds" for HID Approve push. Test the push round trip and raise the timeout if it does not fit | [Bastion 7.2.5.4](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Bastion app in Trustelem](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion), [HID guide](https://www.wallix.com/wp-content/uploads/2020/07/HID_ActivID_Appliance_Wallix_RADIUS_ConfigGuide_FINAL.pdf) |
| AM RADIUS Connection Timeout | field per server, no default stated | same as Bastion | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.6, [AM 11](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Bastion SAML/OIDC timeout | 900 s from clicking the IdP button | keep | [Bastion 7.3.1.1.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| AM "Authent. Expir. Delay" | minutes, no default stated | align with the IdP assertion validity | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.3.2.1, [AM 10.3.2](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| AM `restapi.connection.timeout` and `bastion.connection.timeout` | 10 s each in 5.2; no default stated in 6.0.5 | as low as the network allows: "WALLIX recommends using the lowest practical value to reduce waiting times when a cluster node is unreachable" (REST API); in 6.0.5 `bastion.connection.timeout` is the wait for the target over SSH or RDP | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.5.5.1 and 8.5.5.3, [AM 15.1.1.1](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Bastion one-time password TTL | 30 s | keep | [Bastion 12.5](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| Trustelem RADIUS MFA session | tenant setting | 8 h same network is a common choice (*inference*) | [Trustelem new features](https://trustelem-doc.wallix.com/books/trustelem-news/page/new-features) |
| Clock skew | not published (not in the 6.0.5 guides either) | NTP on every node; Trustelem says time sync is essential for SAML | [AM app in Trustelem](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager) |

## 5. Sizing

Bastion (per node, from the 10.0.6 Quick Start; these are legacy figures. The 12.4.3 Deployment
Guide gives no table and points to the 12.x sizing article, behind the support login):

| Concurrent sessions RDP / SSH | SFTP/SCP throughput | vCPU | RAM to reserve |
|------------------------------:|--------------------:|-----:|---------------:|
| 25 / 110 | 1.6 Gbit/s | 4 | 8 GB |
| 25 / 240 | 1.6 Gbit/s | 4 | 16 GB |
| 40 / 240 | 3.2 Gbit/s | 8 | 16 GB |
| 50 / 480 | 3.2 Gbit/s | 8 | 32 GB |
| 75 / 480 | 5.0 Gbit/s | 16 | 32 GB |

Minimum 4 GB RAM and 50 GB disk (Quick Start only; not restated in the 12.4.3 guides); on
vSphere use one socket, shares High and a CPU reservation, because "The number of concurrent
sessions can only be guaranteed if the appropriate numbers of CPU Mhz and the appropriate memory
size are reserved". For recordings, enlarge the existing virtual disk and reboot (the method
WALLIX recommends; "the system automatically detects and allocates most of the additional space
to the /var/wab partition") or use remote storage. Below 100 MiB free, "The SSH and RDP proxy
servers are shut down"; enable the disk-space notifications on each node.
Sources: [Quick Start 3.3](https://marketplace-wallix.s3.amazonaws.com/Bastion-quickstart-en.pdf),
[Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.3, 3.2.2.1 and 3.2.3.1,
[Bastion sizing article (login)](https://support.wallix.com/hc/en-us/articles/22098207347613-What-should-be-the-sizing-of-my-Wallix-Bastion).

Access Manager, per node (measured by WALLIX with Access Manager 6.0.3 and Bastion 12.3.4 of the
same size; sessions without / with video recording):

| Access Manager vCPU | Access Manager RAM | RDP sessions | SSH sessions |
|--------------------:|-------------------:|-------------:|-------------:|
| 4 | 8 GB | 85 / 80 | 110 / 100 |
| 8 | 16 GB | 200 / 190 | 220 / 210 |
| 8 | 32 GB | 305 / 300 | 510 / 500 |
| 16 | 32 GB | 320 / 310 | 620 / 600 |

Replicated nodes need at least "RAM: 4 GB", "CPU: 2 cores" and "Disk: 50 GB". On vSphere the
Access Manager guide gives the same settings as the Bastion guide: one socket, shares High and a
reservation (Access Manager 6.0.5 Deployment Guide 3.2.2.1). Two interfaces: Administration mandatory
on the first, User Access optional on the second; replication runs over the administration
interface. The Java heap defaults to 70% of the RAM (`-XX:MaxRAMPercentage` in
`/etc/wabam/wabam.vmoptions`).
Sources: [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 1.2, 2.3, 3.2.2.1, 4.3 and 6, [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.5.1.
*Access Manager 5.2:* 2373 MB heap default, 50 GB disk (40 GB in the 4.0.6.1 install guide), one
required interface plus an HA interface (three in the install guide), legacy table 6 vCPU / 4 GB
for 1000 registered users and 100 concurrent sessions.
Sources: [AM Install Guide 2.1.3 and 3.2](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf),
[AM 21.2](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf), [AM release notes WAB-13606](https://pam.wallix.one/documentation/release-notes/am-rn-en.html).

Agents: Trustelem documents "minimal resources" and two VMs each; *gap:* no throughput figures.
Size for the RADIUS timeout window: each pending push holds a request for up to the configured
timeout. Source: [Trustelem Connect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect).

Both clusters are sized for one node carrying the full load, because failover in both products
is a node loss, not a capacity share.

## 6. Security hardening checklist

| Control | Where | Source |
|---------|-------|--------|
| Run Bastion 12.3.7 / 12.4.1 or later and Access Manager 5.2.7 / 6.0.4 or later | both clusters | [WALLIX advisories](https://www.wallix.com/support-services/alerts/) |
| Change all factory credentials (`admin`, `wabadmin`, `wabsuper`, `wabupgrade`, GRUB) and change the LUKS disk passphrase (`wallix-luks-update`; `bastion-luks-update` in 12.0.x); add SSH public keys for `wabadmin` and `wabupgrade` before disabling password SSH; apply the same `WABSecurityLevel` profile on each node | Bastion | [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.1, 4.1 and 4.2, [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 6.4.6 |
| Keep Signed Response and Signed Assertion on; Encrypt Messages off; import only the Trustelem signing certificate | Access Manager SAML | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.3.2.1, [AM 10.3.2](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Change the Access Manager factory credentials and the LUKS passphrase (`wallix-luks-update --interactive --change-passphrase`, or `--reencrypt` on clouds other than AWS); apply `WABSecurityLevel` on each node ("manually apply the security level to each node"); the default HTTP level allows only ECDHE-ECDSA/RSA-AES256-GCM-SHA384 and ECDHE-ECDSA/RSA-AES128-GCM-SHA256 | Access Manager | [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 2.1, 4.2 and 8.1, [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.5.3 |
| Restrict API keys by profile and source IP; one key per consumer; re-create keys made before 12.1, which "have the product_administrator profile applied by default"; deactivate the "Deprecated resources" option (Configuration > Configuration options > REST API; WALLIX "recommends modifying the default behavior to forbid the use of all these deprecated API endpoints") on each node once no client needs them | Bastion | [Bastion 6.1 and 6.1.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 6.6, 12 and 12.2 |
| Set Proxyma `trusted_proxies` to the load balancer addresses so only it may set forwarded headers (Access Manager 5.2: `web.proxy.trusted-proxies`) | Access Manager | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.5.2, [AM 21.5](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Keep the Proxyma DoS filter (`dos_filter_activated`) and SNI hostname verification (`verify_server_cert_hostname`, default true) enabled; deactivate "Limit the number of parallel connections per IP" behind the load balancer (Access Manager 5.2: `web.max.requests.perSec=60`, `web.sni.host.check`) | Access Manager | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.2, 8.4.5.1 and 8.5.2, [AM 21.4 and 21.5](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Avoid TRACE or ALL log levels, which "may expose sensitive information, including passwords"; switch to DEBUG before generating an archive | Access Manager | [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 9.7.1, [AM 15.2](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Restrict 2242 and the admin interface to the administration network and the peer node of each cluster (the replication tunnels use 2242); use the dedicated admin interface | both | [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 1.2 and 6, [AM Install Guide 3.2](https://marketplace-wallix.s3.amazonaws.com/am-install_en.pdf), [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 2.2 and 5.1, [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 7.2 |
| Add the load balancer FQDN to the trusted HTTP_HOST names, and deactivate "Limit the number of parallel connections per IP" behind Access Manager or a load balancer, on each node | Bastion | [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 7.1.2 and 7.2 |
| Use StartTLS or LDAPS towards AD and towards Trustelem Connect (Trustelem: "The best way to encrypt the LDAP flows is simply to check startTLS on the Bastion") | Bastion, Access Manager | [Bastion app in Trustelem](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion) |
| Exclude Trustelem FQDNs from TLS inspection (certificate pinning) | egress proxy | [Connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows) |
| Passkey policy Strict or Custom with attestation for administrator groups | Trustelem | [MFA methods](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication) |
| Require 2 factors on the Trustelem admin console; keep SMS and e-mail OTP disabled | Trustelem | [Access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules) |
| Keep Session Probe enabled in RDP connection policies (process, clipboard and jump detection) | Bastion | [Bastion 12.16.1.4](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| Forward Bastion syslog and Trustelem JSON logs to the SIEM, and Access Manager logs once WALLIX confirms the method (gap A7; no agents on the appliance), with alerts on `wabauth` failures (the Bastion logs no RADIUS timeout message) | all | [monitoring and logging](07-operations.md#1-monitoring-and-logging) |
