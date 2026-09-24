# Open questions and gaps register

Date: 2026-09-24. One place for everything the public sources do not answer, with the chapter
that depends on it and the way to close it. "Vendor" means it needs a WALLIX answer or a login
to the customer documentation site; "lab" means it can be closed by testing.

## Trustelem

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| T1 | Contractual SLA, maintenance windows, tenant export or backup. Closed part: there is no status page; the [unavailability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability) and [incidents](https://trustelem-doc.wallix.com/books/trustelem-news/page/incidents) pages are the published record (checked 2026-09-23); no customer-facing status or health API for the tenant and the agents is documented | 01, 07 | vendor |
| T2 | Location of the admin console authentication level setting and of the RADIUS MFA session duration; allowed duration values | 01, 06 | vendor or console |
| T3 | Synchronisation frequency values for ADConnect; log file locations for ADConnect and Trustelem Connect | 02, 03, 08 | vendor or console |
| T4 | Whether Trustelem Connect answers CHAP; attributes returned in Access-Accept; Message-Authenticator support; BlastRADIUS statement; RadSec roadmap; what happens to a pending push when the Bastion RADIUS timeout expires first, and the recommended timeout values on both sides | 03, 04, standards | vendor |
| T5 | Exact SCIM payload, deprovisioning semantics, support for the WALLIX Bastion extension attributes; whether the five-minute reconciliation touches Bastion local users it did not create (break-glass, `am-auditor`); whether Access Manager is also a SCIM target | 12 | vendor |
| T6 | API representation of the RADIUS-only levels *Always allow* and *2nd factor only*: the documented `ZoneSecurityLevel` lists five values and the `EffectiveZoneSecurityLevel` type used by the effective-permission calls is referenced but never defined on the API page (checked 2026-09-23); rate limits | 07, API export | console script editor |
| T7 | Push number matching or rate limiting in WALLIX Authenticator: absent from all four Trustelem books (searched 2026-09-23), so treat as not offered unless WALLIX says otherwise | 06, standards | vendor |
| T8 | Browser "remember this device" or device trust: absent from all four Trustelem books (searched 2026-09-23); only the internal network zone and the RADIUS MFA session exist | 06 | vendor |
| T9 | Hosting provider, country, SecNumCloud or HDS status, ISO 27001 certificate number and statement of applicability | standards | vendor |
| T10 | Console URL fragments for Groups, Apps and Services (only Users, Directories, Security, API, Logs, Alerts, Sessions, Themes, Dashboard are documented) | 01 | console |
| T11 | No WALLIX OIDC application template and no groups-claim guidance in the Trustelem books, so OIDC stays the alternative to SAML | report 4.1, 4.7 | vendor |
| T12 | Behaviour when the Trustelem cloud is unreachable: no documented offline mode for Trustelem Connect (RADIUS, LDAP) or cached factors; break-glass relies on local Bastion and Access Manager accounts | report 5.3, 07 | vendor |
| T13 | Throughput and sizing figures for ADConnect and Trustelem Connect ("minimal resources" and two VMs each is all that is published) | report 6.5 | vendor |
| T14 | Log retention beyond the 30 days of the console and API: whether a longer retention is available contractually or only through the on-premise SIEM push and the API export | 07, logging | vendor |
| T15 | Hardware TOTP tokens: supported models, seed import and bulk assignment to users | 06, 11 | vendor |

## Bastion

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| B1 | Bastion 12.4 release notes and the 12.3.x to 12.4.x change list (behind the doc login; the [public release notes](https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html) stop at 12.3.2, checked 2026-09-24); 12.x sizing article; end-of-support date for 12.3 and the upgrade path to 12.4 | report, runbook | vendor login |
| B2 | Sample output of `bastion-replication --status`, `--monitoring`, `--prerequisite-check`; step-by-step `--elevate-master` failover and failback; restore on a replicated node; HA e-mail template names (System Operations Guide) | runbook | vendor login, lab |
| B3 | Closed for the NIC: eth1 may be used for replication like any other interface, and "When the eth1 interface is used for HA database replication, the associated administration features must be manually enabled from the System > Service control page for replication to work" ([Bastion release notes WAB-7947, WAB-17651](https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html)). Still open: latency limits for cross-site Master/Slaves | runbook, DR | vendor |
| B4 | SCIM API base path on the appliance, required attributes for user creation, Bearer support, cluster behaviour (scim.wallix.com timed out again on both 80 and 443 on 2026-09-23) | 12 | vendor |
| B6 | Whether RADIUS accounting (1813) is used; `wabauth` diagnostic text for a RADIUS second factor and for SAML users through Access Manager | logging, test plan | lab |
| B7 | Which Bastion domain the Access Manager SAML Domain Name must match: the Trustelem [Access Manager app page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager) says "the Authentication domain name of your Active Directory Authentication domain", the Trustelem [Bastion SAML page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml) says "AM Domain Name = Bastion Authentication domain name" of the SAML domain; this design binds `TRUSTELEM` to a separate SAML *Other IdPs* domain (report 7.3 step 7) | 05, SAML reference | vendor, lab |

## Access Manager

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| A1 | Access Manager 6.0 release notes and Debian 12 changes (doc.wallix.com answers 303 to the Trustelem SSO login for both the 6.0 and the Bastion 12.4 notes, checked 2026-09-23; the [public release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html) stop at 5.2.4.0, checked 2026-09-24); end-of-support date for 5.2 and the upgrade path to 6.0 on Debian 12 | report, runbook | vendor login |
| A2 | Replication script name and invocation beyond `--prerequisite-check` and `/root/sqlreplication/servers_list`; replication port; maximum node count | runbook | vendor login |
| A3 | Health-check URL for the load balancer; TLS versions and cipher list | runbook | vendor, lab |
| A4 | SAML clock-skew tolerance and assertion replay cache; ACS URL pattern (only in the generated SP metadata); whether push (not only TOTP) works in the RADIUS factor chain | 05, standards | vendor, lab |
| A5 | PKCE and exact redirect URI matching on the Bastion and Access Manager OIDC clients and on the Trustelem provider | standards | vendor |
| A6 | `wabam-config-database`, `wabam-init-database` and `wabam-certificate-update` full syntax; hotfix procedure | runbook | vendor login |
| A7 | No native syslog forwarder on Access Manager: log files under `/var/log/wallix/wabam` need an agent to reach the SIEM | logging | vendor, lab |

## Standards

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| S3 | Certification coverage of Bastion 12.3 and 12.4 versus the BSI-certified 12.0.14; ANSSI qualification status; Common Criteria plans | standards | vendor |

## Commercial and delivery

Not documentation gaps, but answers only WALLIX can give; asked in the
[vendor meeting script](vendor-meeting-script.md).

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| C1 | Licensing units and price: WALLIX Authenticator versus full WALLIX One IDaaS, Bastion per node or per user, Access Manager concurrent users, agents and SIEM push included or not, SMS cost, behaviour when the licence lapses | meeting block 2 | vendor |
| C2 | Deployment durations and Professional Services scope; the timeline in the meeting script is the repo's own estimate | meeting block 3 | vendor |
| C3 | Whether any on-premise edition of Trustelem exists, and the supported third-party RADIUS TOTP servers for a fully on-premise design | meeting block 1 | vendor |
| C4 | Contractual SLA, support hours and severity response times, single or separate support contracts for the three products | meeting block 4, T1 | vendor |

## Closed

Kept for the record; the answer is written into the chapter named in "Depends".

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| S1 | Closed 2026-09-23: the official text of Implementing Regulation (EU) 2024/2690 was read (points 3.2.3, 11.3.1, 11.3.2, 11.4.1, 11.6.1, 11.7.1, 11.7.2) and the standards mapping now quotes it; an earlier paraphrase had attributed recital 23 wording to point 11.7.1 | standards | done |
| S2 | Closed 2026-09-23: DORA RTS 2024/1774 Article 21(1)(e)(ii) and (f)(ii) quoted from the official text | standards | done |
| B5 | Closed: the provider source `resource_externalauth_radius.go` has only `authentication_name`, `host`, `port`, `secret`, `timeout`, `description`, `use_primary_auth_domain`, so the "Use mobile device" option must be set in the GUI after apply; no OIDC resources exist | IaC | provider issue tracker |

## How this register is maintained

Add a row when a chapter marks something "not documented" or "gap"; move it to *Closed* when the
answer is written into the chapter and the source is cited. The outbound form of this list is
the [vendor meeting script](vendor-meeting-script.md); section 9.1 of the architecture report,
section 6 of the SCIM chapter and section 5 of the standards reference are the per-document
question lists and point here.
