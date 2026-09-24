# Architecture overview

> - **Purpose:** what the design is, the three WALLIX products and their names, the versions the set was verified against, the target versions and the certifications.
> - **Audience:** PAM architect, project sponsor, security officer.
> - **Verified:** 2026-09-24 against the public Bastion 12.3.2 and Access Manager 5.2.4.0 guides, the Bastion 12.4.3 and Access Manager 6.0.5 customer guides and the Trustelem documentation books, with the public release notes and the WALLIX security advisories.
> - **Sources:** [Bastion Administration Guide 12.3.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Access Manager Administration Guide 5.2.4.0](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf), Bastion 12.4.3 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), Access Manager 6.0.5 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), [WALLIX security advisories](https://www.wallix.com/support-services/alerts/), [Trustelem administration book](https://trustelem-doc.wallix.com/books/trustelem-administration/export/html).

## 1. Executive summary

WALLIX sells three products that together give MFA-protected privileged access:

- **WALLIX Trustelem**, now marketed as **WALLIX One IDaaS**, is a French SaaS
  identity provider with SSO (SAML 2.0, OpenID Connect, OAuth 2.0) and MFA, plus two on-premise
  agents: **Trustelem ADConnect** (directory synchronisation and AD password validation) and
  **Trustelem Connect** (a local LDAP and RADIUS server that relays to the cloud).
  Sources: [Trustelem summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary),
  [WALLIX One IDaaS product page](https://www.wallix.com/products/idaas/).
- **WALLIX Bastion** is the PAM appliance (session proxies for RDP, SSH, VNC, Telnet and raw
  TCP, password vault, recording). It runs on Debian 12 ([release notes WAB-17140](https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html): Debian 12.13) with a MariaDB database and clusters
  through **HA Database Replication** (Master/Master or Master/Slaves).
  Sources: [Bastion Admin Guide 12.3.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
  [Bastion 12.0.2 Deployment Guide](https://marketplace-wallix.s3.amazonaws.com/bastion_12.0.2_en_deployment_guide.pdf),
  [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.
- **WALLIX Access Manager** is the HTML5 web portal in front of one or more Bastions. It scales
  out as an active/active farm behind a load balancer sharing or replicating a MariaDB database.
  Source: [AM Admin Guide 5.2.4.0, chapter 20](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf).

The recommended design in this architecture set:

1. **Active Directory stays the source of truth.** Trustelem ADConnect imports AD users and
   groups and validates AD passwords without storing them. Bastion and Access Manager keep
   their own LDAP/AD domains for authorization (group mapping).
2. **Web access goes through Access Manager with SAML 2.0 from Trustelem.** Trustelem enforces
   the second factor (push, TOTP, passkey). Access Manager and Bastion share the same SAML
   domain name and login attribute, so the Bastion trusts the Access Manager session and the
   user is never re-prompted. Only the "SAML Generic" variant of Bastion works with Access
   Manager, and once it is configured the Bastion web UI no longer accepts direct SAML logins.
3. **Native RDP and SSH clients that connect straight to the Bastion proxies get MFA through
   RADIUS** against Trustelem Connect, configured on the Bastion as the *secondary
   authentication* of the AD domain, with the "Use mobile device for two-factor authentication"
   option so the proxy waits for a push approval. SAML and OIDC are not fully integrated in
   the native client path.
4. **Two Trustelem Connect VMs and two ADConnect VMs** provide agent failover; the Bastion lists
   both RADIUS servers as primary and backup.
5. **Clusters:** a two-node Bastion HA Database Replication pair (Master/Master) fronted by a
   load balancer or by the Access Manager "Cluster" object, and a two-node Access Manager farm
   behind a Layer 7 load balancer with WebSocket support and source-IP affinity.

Three things a PAM architect must not miss:

- **Patch levels.** WSA-2026-07-0001, a CVSS 10 unauthenticated privilege escalation in the
  REST API, affects Bastion 12.3.0 to 12.3.6 and 12.4.0 (fixed in 12.3.7 and 12.4.1).
  WSA-2026-07-0002, a CVSS 8.7 unauthenticated bypass of the SAML service provider, affects every
  Access Manager with SAML configured before 5.1.10, 5.2.7 and 6.0.4. Both were published on
  2026-07-20. WSA-2026-02-0001 (passwords written to logs when the "Default" or REST API log level is
  DEBUG, TRACE or ALL and users perform password checkouts; fixed in 5.1.7 and 5.2.4) is the
  reason to keep those log levels off in production.
  Source: [WALLIX security advisories](https://www.wallix.com/support-services/alerts/).
- **No cloud, no MFA.** Trustelem Connect only relays to the cloud, so RADIUS and LDAP through it
  stop working if the tenant is unreachable. Keep a local, IP-restricted Bastion administrator
  with a local password as break-glass. Trustelem publishes its availability history
  (above 99.99 % from 2016 to 2022, 99.94 % in 2023).
  Source: [Trustelem availability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability).
- **New Trustelem IP addresses.** Two new addresses become active on 2026-09-29 and must be
  allowed on outbound firewalls now, alongside the existing ranges; the list and its source are
  in [tenant setup, section 4](../trustelem/01-tenant-setup.md).

## 2. Product naming and versions

| Product | Current public name | Version verified | Newer builds seen | Base |
|---------|--------------------|------------------|-------------------|------|
| Trustelem | WALLIX One IDaaS ("also known as Trustelem", vault documentation quick start in the sources) | SaaS, no version | continuous | SaaS "Hosted in European Data Centers" ([product page](https://www.wallix.com/products/idaas/)); multi-tenancy is an inference |
| Bastion | WALLIX Bastion / WALLIX PAM | 12.3.2 (2026-03-12, public guide) and 12.4.3 (customer guides) | 12.3.7, 12.4.3 | Debian 12, MariaDB |
| Access Manager | WALLIX Access Manager | 5.2.4.0 (2026-03-12, public guide) and 6.0.5 (customer guides) | 5.2.7, 6.0.4 | 5.x: Debian 10, Java 17 / Jetty 11 (release notes); 6.0.5: Debian and Java versions not stated in the guides ("Refer to the Release Notes document"), web server "typically Jetty", systemd service `wabam` behind the Proxyma proxy, embedded MariaDB or external MySQL |
| MFA bundle | WALLIX Authenticator | offer name | | Trustelem licence limited to Bastion and Access Manager |

Names and compatibility stated in the vendor documents:

- Trustelem is sold today as WALLIX One IDaaS ([product page](https://www.wallix.com/products/idaas/)).
  The Bastion guides call it "WALLIX IDaaS (ex Trustelem)" in the list of supported SAML
  identity providers ([Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 8.1,
  "Supported SAML identity providers"; same entry in 12.0.25), and give "WALLIX IDaaS" as an
  example provider for "SAML Generic with any Identity Provider"
  ([Bastion Admin Guide 7.3.1.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
  12.3.2 and 12.4.3).
- The WALLIX Authenticator licence, limited to Bastion and Access Manager, "can be extended for
  the authentication of other apps: with only a license change"
  ([WALLIX Authenticator presentation](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/presentation)).
- "WALLIX Access Manager 6.0.5 is compatible with: ... WALLIX Bastion 12.0 and above"
  ([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 10.1). The 12.0 branch
  lacks four features this design uses (below).

Assurance: Bastion 12.0.14 holds BSI certificate BSZ-0020-2025 (2025-09-29, valid to
2027-09-28; WALLIX states it is recognised by ANSSI through the CSPN-BSZ mutual recognition agreement,
which is not reflected in the ANSSI catalogue); the older ANSSI CSPN 2019/15 for Bastion 6.0 is listed as no
longer maintained; WALLIX holds ISO/IEC 27001:2022 and states it covers the WALLIX One SaaS platform in scope.
Sources: [BSI BSZ-0020-2025](https://www.bsi.bund.de/SharedDocs/Zertifikate_BSZ/Bestaetigt/BSZ-0020-2025.html),
[ANSSI catalogue](https://messervices.cyber.gouv.fr/visas/catalogue-produits-services-profils-de-protection-sites-certifies-qualifies-agrees-anssi.pdf),
[WALLIX ISO 27001 press release](https://www.wallix.com/wp-content/uploads/2025/01/250901_-WALLIX-ISO270012022_FINAL_VFR.pdf).
The certified 12.0 branch lacks four features this design uses: Generic OpenID Connect, the SAML
dynamic flow (SP entity ID set to a load balancer FQDN), API keys bound to a profile, and
Kerberos on the RDP proxy (12.0.25 customer guides on [doc.wallix.com](https://doc.wallix.com/));
the RADIUS and SAML rules used here read the same in 12.0.25 and 12.4.3. Details in
[chapter 04 section 11](../trustelem/04-bastion-integration.md#11-bastion-120-branch-bsi-certified-12014).

Sources: [Enterprise Vault quick start naming note](https://vault-doc.wallix.com/books/enterprise-vault-administration/page/quick-start-guide),
[Bastion release notes](https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html),
[Access Manager release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html),
[AWS Marketplace Bastion 12.4](https://aws.amazon.com/marketplace/pp/prodview-up3f6pn7fybfi),
[WALLIX advisories](https://www.wallix.com/support-services/alerts/),
[WALLIX Authenticator presentation](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/presentation).

WALLIX One is the SaaS umbrella launched on 2023-12-14 (One IDaaS, One PAM, One Remote Access,
One Enterprise Vault). WALLIX One PAM bundles Bastion and Access Manager as a service, and the
WALLIX One Console announced in 2026 manages on-premise Bastion and Access Manager appliances
centrally. Nothing public suggests Access Manager is being merged into Bastion.
Sources: [WALLIX One launch](https://www.wallix.com/press/2023/introducing-wallix-one-the-cybersecurity-saas-platform-designed-to-meet-the-digital-and-economic-challenges-of-companies-aiming-to-safeguard-their-access-and-identities/),
[WALLIX One PAM 1.6.0 notes](https://pam.wallix.one/documentation/deployment/release-notes/1.6.0.html),
[WALLIX One Console](https://www.wallix.com/press/wallix-launches-wallix-one-console-to-boost-operational-efficiency-and-simplify-cybersecurity-for-enterprises-and-organizations/).

## 3. Verification baseline

The set was verified on 2026-09-24 against WALLIX Bastion 12.3.2 (Functional Administration
Guide dated 2026-03-12), WALLIX Access Manager 5.2.4.0 (Administration Guide dated 2026-03-12),
the public release notes of both products, and the WALLIX Trustelem documentation portal as read
on the same day.
Newer builds exist (Bastion 12.4.3 as listed on the
[AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-up3f6pn7fybfi), Access Manager
5.2.7 and 6.0.4 per the [WALLIX advisories](https://www.wallix.com/support-services/alerts/))
whose release notes sit behind the SSO-protected documentation site; where a newer build matters
for security, the documents say so.

Bastion statements were re-checked on 2026-09-24 against the Bastion 12.4.3 customer guides
(Functional Administration, Deployment, System Operations and SIEM Logs guides), which sit behind
the [doc.wallix.com](https://doc.wallix.com/) login; they are cited as, for example,
"[Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.1". Access Manager statements were
re-checked on 2026-09-24 against the Access Manager 6.0.5 customer guides (Administration,
Deployment, Users and Approvers, and Sessions Audit guides), behind the same login and cited as,
for example, "[Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.3.1"; facts
that hold only for Access Manager 5.2 are labelled as such.

The target versions for the deployment are Bastion 12.4.3 and Access Manager 6.0.5.

Every factual statement links to its source. Statements marked *inference* are the author's
deduction from the sources; statements marked *gap* could not be confirmed publicly.
