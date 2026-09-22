# WALLIX Trustelem MFA for a Bastion and Access Manager PAM platform

Architecture research for a Privileged Access Management (PAM) platform built on
WALLIX products: **WALLIX Trustelem** (sold today as **WALLIX One IDaaS**) as the
cloud identity provider and MFA engine, a **WALLIX Bastion** cluster as the
session and password manager, and a **WALLIX Access Manager** cluster as the
user-facing web portal.

The main concern of this repository is **Trustelem itself: how to set it up,
configure it, and integrate it** with the Bastion cluster and the Access Manager
cluster. The Bastion and Access Manager material exists to make that integration
precise. The goal is a document set a PAM architect can hand to an integration
team: design, protocols, exact configuration paths on each product, and day-2
operations.

Last updated: 2026-09-22. Verified against WALLIX Bastion 12.3.2 and
WALLIX Access Manager 5.2.4.0 (public guides dated 2026-03-12). Newer builds exist:
Bastion 12.3.7 / 12.4.1 and Access Manager 5.2.7 / 6.0.4 carry the July 2026 security
fixes and are the minimum versions this design assumes.

## Scope

| Area | Covered |
|------|---------|
| Trustelem / WALLIX One IDaaS | tenant model, directory connector, authenticator app, MFA methods, SAML / OIDC / RADIUS services, access rules |
| WALLIX Bastion cluster | HA Database Replication modes, proxies (RDP, SSH, HTTPS), external authentication, authorization model, ports |
| WALLIX Access Manager cluster | multi-instance load balancing, shared database, Bastion clusters, SAML / OIDC / RADIUS domains, API keys |
| Integration | end-to-end login flows, attribute and group mapping, MFA on web portal versus native RDP/SSH clients, break-glass |
| Operations | certificate and secret rotation, logging and SIEM, upgrade order in HA, testing checklist |

## High-level architecture

```
                                  +---------------------------------------------+
                                  |        WALLIX Trustelem / One IDaaS         |
                                  |   (SaaS identity provider + MFA engine)     |
                                  |  SAML 2.0 IdP  |  OIDC OP  |  RADIUS  | AD  |
                                  +---------------------------------------------+
                                         |               |          |        |
        SAML / OIDC redirects            |               |          |        | outbound HTTPS
        (browser, HTTPS 443)             |               | RADIUS   |        | directory sync
                                         |               | 1812/udp |        |
+-------------+                   +------+---------------+-----+    |   +----+----------------+
| Privileged  | -- HTTPS 443 ---->|   Load balancer (L7 / L4)  |    |   | Directory connector |
| user        |                   +------+---------------+-----+    |   | agent (on-prem)     |
| (browser)   |                          |               |          |   +-----+---------------+
+-------------+                   +------+-----+  +------+-----+    |         |
       |                          | Access Mgr |  | Access Mgr |    |         |
       | native RDP 3389          |   node 1   |  |   node 2   |    |         | LDAP / AD
       | native SSH 22            +------------+  +------------+    |         |
       |                                 +-------+-------+          |         |
       |                          shared /       | REST API 443     |         |
       |                          replicated     | RDP 3389         |         |
       |                          MariaDB DB     | SSH 22           |         |
       |                          +--------------+-------------+    |         |
       |                          |  +----------+  +----------+|<---+         |
       |                          |  | Bastion 1|  | Bastion 2||            +-+---------+
       |                          |  | proxies  |==| proxies  || LDAP/AD    | Active    |
       |                          |  | vault    |  | vault    ||----------->| Directory |
       +------------------------->|  +----------+  +----------+|  389/636   +-----------+
                                  |                            |
                                  | HA Database Replication    |
                                  | (master/master or          |
                                  |  master/slaves)            |
                                  +------+---------------+-----+
                                         |               |
                                         | RDP, SSH, VNC,| HTTPS, Telnet
                                         |               |
                                  +------+------+ +------+---------+
                                  | Windows /   | | Linux / network|
                                  | jump hosts  | | / web targets  |
                                  +-------------+ +----------------+
```

Two access paths coexist:

1. **Web path.** The user opens Access Manager, is redirected to Trustelem
   (SAML or OIDC), completes MFA there, and launches HTML5 sessions. Access
   Manager talks to each Bastion over its REST API using an API key, and the
   Bastion trusts the federated identity because both products share the same
   authentication domain name and attribute mapping.
2. **Native client path.** The user points `mstsc` or an SSH client straight at
   the Bastion proxy. SAML and OIDC are not fully integrated in that path, so
   MFA is enforced with RADIUS challenge-response against Trustelem as a
   secondary authentication after the LDAP/AD bind, or with a one-time token
   issued by the web interface.

## Protocol matrix (verified)

| Component | Protocol | Role | Source |
|-----------|----------|------|--------|
| Access Manager | SAML 2.0 (HTTP-Redirect and HTTP-POST bindings, SP and IdP initiated) | Service Provider | [AM Admin Guide 5.2.4.0, ch. 10.3](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Access Manager | OpenID Connect, Authorization Code Flow, discovery URL | Relying Party | [AM Admin Guide 5.2.4.0, ch. 10.5](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Access Manager | RADIUS PAP / CHAP with challenge-response, port 1812 | RADIUS client | [AM Admin Guide 5.2.4.0, ch. 11](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Access Manager | REST API over HTTPS 443, RDP 3389, SSH 22 towards each Bastion | API client | [AM Admin Guide 5.2.4.0, ch. 10.4.3 and 13](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) |
| Bastion | SAML 2.0 Generic (only variant compatible with Access Manager) | Service Provider | [Bastion Admin Guide 12.3.2, ch. 7.3.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| Bastion | OpenID Connect, Authorization Code Flow, cluster-aware FQDNs | Relying Party | [Bastion Admin Guide 12.3.2, ch. 7.3.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| Bastion | RADIUS (RFC 2865 / RFC 8044, challenge-response, no VSAs, NAS-Identifier `WAB`) | RADIUS client, secondary factor | [Bastion Admin Guide 12.3.2, ch. 7.2.5.4](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| Bastion | LDAP / AD bind, Kerberos, TACACS+, X.509, SSH key and SSH CA, PingID | primary or secondary factors | [Bastion Admin Guide 12.3.2, ch. 7.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf) |
| Trustelem | SAML 2.0 IdP, OIDC provider, RADIUS service, directory synchronisation | Identity provider | see `docs/` report and its source list |

## Repository layout

```
.
+-- README.md          this file
+-- CLAUDE.md          conventions for maintaining the documents
+-- .gitignore         keeps downloaded vendor PDFs out of the repo
+-- docs/
|   +-- trustelem-bastion-access-manager-architecture.md   full architecture report
|   +-- diagrams/          rendered ASCII diagrams used by the report
|   +-- research-notes/    sourced working notes per product (Trustelem, Bastion,
|                          Access Manager, integration)
+-- tools/
    +-- asciigrid.py       grid helper for box and sequence diagrams
    +-- diagrams/*.py      one script per diagram; run to regenerate docs/diagrams
```

The report in `docs/` is organised as:

1. Executive summary, product naming and the security advisories that set minimum versions.
2. Component architecture of Trustelem, Bastion and Access Manager.
3. High-level design: decisions, web and native identity flows, access-path coverage matrix,
   administrator access model, OIDC alternative.
4. Cluster design: Bastion HA Database Replication, Access Manager farm, failure modes,
   disaster recovery.
5. Low-level design: naming and mapping rules, certificates and secrets, ports, timeouts,
   sizing, hardening checklist.
6. Setup runbook per product, acceptance tests, rollout and rollback plan.
7. Operations: monitoring, rotation, upgrades and backups.
8. Caveats, open gaps and the questions to put to WALLIX, then a glossary and sources.

## Primary sources

- WALLIX One PAM documentation index: <https://pam.wallix.one/documentation/administration/getting-started/documentation.html>
- WALLIX Bastion 12.3.2 Functional Administration Guide: <https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf>
- WALLIX Access Manager 5.2.4.0 Administration Guide: <https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf>
- WALLIX Bastion release notes: <https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html>
- WALLIX Access Manager release notes: <https://pam.wallix.one/documentation/release-notes/am-rn-en.html>
- Bastion and Access Manager compatibility matrix: <https://support.wallix.com/hc/en-us/articles/24928252714013-Compatibility-Between-Bastion-and-Access-Manager>
- WALLIX One IDaaS product page: <https://www.wallix.com/products/idaas/>

The WALLIX HTML documentation site at <https://doc.wallix.com/> sits behind a
Trustelem SAML login, which is itself a live example of the IdP in this design.
The PDF guides above are public and are the versions these notes cite.

## Working on the documents

- Every technical claim links to its source. Verified facts and inferences are
  kept in separate paragraphs or marked explicitly.
- Diagrams are plain ASCII drawn on a fixed grid so boxes stay aligned and render anywhere Markdown
  does, including GitHub and terminal viewers.
- To re-verify a chapter, download the PDF into a scratch folder and extract it
  with `pdftotext -layout`, then grep for the chapter title.
- Product versions and the "last updated" date at the top of each document are
  refreshed whenever a claim is re-checked against a newer release.

## Status

- [x] Repository conventions and source inventory
- [x] Architecture report in `docs/` (high-level and low-level design, flows, clusters)
- [x] Configuration runbook per product (section 7 of the report)
- [x] Test and acceptance checklist (section 7.5 of the report)
- [x] Gap review: access-path coverage, admin access model, DR, sizing, hardening, rollout plan
- [ ] Validate the design against Bastion 12.4 and Access Manager 6.0 release notes (need vendor login)
- [ ] Get answers to the vendor questions in section 9.1 of the report
