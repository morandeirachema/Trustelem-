# Open questions and gaps register

Date: 2026-09-24. One place for everything the public sources do not answer, with the chapter
that depends on it and the way to close it. "Vendor" means it needs a WALLIX answer; "lab" means
it can be closed by testing. On 2026-09-24 the customer guides behind the
[doc.wallix.com](https://doc.wallix.com/) login were obtained (Bastion 12.4.3 and 12.0.25 administration,
deployment, operation, SIEM, user and auditor guides; Access Manager 6.0.5 administration,
deployment, user and auditor guides) and the rows below were re-checked against them.

## Trustelem

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| T1 | Contractual SLA, maintenance windows, tenant export or backup. Closed part: there is no status page; the [unavailability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability) and [incidents](https://trustelem-doc.wallix.com/books/trustelem-news/page/incidents) pages are the published record (checked 2026-09-23); no customer-facing status or health API for the tenant and the agents is documented | 01, 07 | vendor |
| T2 | Location of the admin console authentication level setting and of the RADIUS MFA session duration; allowed duration values | 01, 06 | vendor or console |
| T3 | Synchronisation frequency values for ADConnect; log file locations for ADConnect and Trustelem Connect | 02, 03, 08 | vendor or console |
| T4 | Whether Trustelem Connect answers CHAP; attributes returned in Access-Accept; Message-Authenticator support; BlastRADIUS statement; RadSec roadmap; what happens to a pending push when the Bastion RADIUS timeout expires first, and the recommended timeout values on both sides; the Bastion 12.4.3 guides mention none of CHAP, Message-Authenticator, RadSec or accounting (only the release note WAB-16237 "Only the PAP protocol is supported"), and the Deployment Guide lists RADIUS as "1812/TCP and 1812/UDP" without explanation | 03, 04, standards | vendor |
| T5 | Exact SCIM payload, deprovisioning semantics, support for the WALLIX Bastion extension attributes; whether the five-minute reconciliation touches Bastion local users it did not create (break-glass, `am-auditor`). Closed part: Access Manager is not a SCIM target; SCIM appears in none of the 6.0.5 guides and "external users appear only after they sign in to the organization for the first time" ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) ch. 4) | 12 | vendor |
| T6 | API representation of the RADIUS-only levels *Always allow* and *2nd factor only*: the documented `ZoneSecurityLevel` lists five values and the `EffectiveZoneSecurityLevel` type used by the effective-permission calls is referenced but never defined on the API page (checked 2026-09-23); rate limits | 07, API export | console script editor |
| T7 | Push number matching or rate limiting in WALLIX Authenticator: absent from all four Trustelem books (searched 2026-09-23), so treat as not offered unless WALLIX says otherwise | 06, standards | vendor |
| T8 | Browser "remember this device" or device trust: absent from all four Trustelem books (searched 2026-09-23); only the internal network zone and the RADIUS MFA session exist | 06 | vendor |
| T9 | Hosting provider, country, SecNumCloud or HDS status, ISO 27001 certificate number and statement of applicability | standards | vendor |
| T10 | Console URL fragments for Groups, Apps and Services (only Users, Directories, Security, API, Logs, Alerts, Sessions, Themes, Dashboard are documented) | 01 | console |
| T11 | No WALLIX OIDC application template and no groups-claim guidance in the Trustelem books, so OIDC stays the alternative to SAML | report 4.1, 4.7 | vendor |
| T12 | Behaviour when the Trustelem cloud is unreachable: no documented offline mode for Trustelem Connect (RADIUS, LDAP) or cached factors; break-glass relies on local Bastion and Access Manager accounts | report 5.3, 07 | vendor |
| T13 | Throughput and sizing figures for ADConnect and Trustelem Connect ("minimal resources" and two VMs each is all that is published) | report 6.5 | vendor |
| T14 | Log retention: the API returns "the 30 previous days"; the console retention is not documented; whether a longer retention is available contractually or only through the on-premise SIEM push and the API export | 07, logging | vendor |
| T15 | Hardware TOTP tokens: supported models, seed import and bulk assignment to users | 06, 11 | vendor |
| T16 | Whether SMS and e-mail OTP work as the second factor over RADIUS and LDAP (the Trustelem Connect page describes push-wait and TOTP only) | 06 | vendor, lab |

## Bastion

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| B1 | Bastion 12.4 release notes and the 12.3.x to 12.4.x change list; end-of-support date for 12.3. Partly closed: the 12.4.3 guides were obtained; they contain no change list, and their HA chapters match 12.0.25 apart from renamed commands (`wallix-replication`, `wallix-luks-update`, `wallix-upgrade` from 12.3.5). Sizing now points to a support article ("What should be the sizing of my Wallix Bastion", login) | report, runbook | vendor login |
| B2 | Step-by-step `--elevate-master` failover and failback (only the one-line option description exists); sample output of `--monitoring` and `--prerequisite-check`. Closed parts, from the [Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 11.3 and 14.2.6: `--status` output and thread checks, the 10-day binlog buffer and `--dump-resync`, restore on a Master ("pauses the replication ... automatically resynchronizes all nodes") and no restore on a Slave; mail templates in Administration Guide 8.2.2 | runbook | vendor, lab |
| B4 | SCIM API base path on the appliance, required attributes for user creation, Bearer support, cluster behaviour (scim.wallix.com timed out again on both 80 and 443 on 2026-09-23); SCIM appears in none of the Bastion 12.4.3 customer guides (administration, deployment, operation, SIEM, user, auditor, WSM) | 12 | vendor |
| B6 | `wabauth` wording for a RADIUS second factor (success, failure, timeout), for API-key authentication, for Kerberos users and for logins brokered by Access Manager; whether RADIUS accounting (1813) is used (no 12.4.3 guide mentions it). Closed parts, from the [Bastion 12.4.3 SIEM Logs Guide](https://doc.wallix.com/) 2.1: SAML, OIDC, local and LDAP lines; failures carry no reason ("Authentication failed") | logging, test plan | lab |
| B9 | Password rotation after losing the primary master: "only the primary Bastion runs scheduled rotations ... if the primary Bastion becomes unavailable, password changes will not run until it is available again" ([Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) ch. 5); how to move rotation to the surviving node during a long outage, and whether `--dump-resync` from the primary discards changes made on the secondary master meanwhile | runbook | vendor |
| B10 | Whether the RADIUS secondary authentication still runs after an SSH key or FIDO2 hardware-key login on the SSH proxy ([Bastion 12.4.3 Administration Guide](https://doc.wallix.com/) 2.5 and 7.2.5.6 document the key login, not its interaction with secondary authentication) | 04, report 4.5 | lab, vendor |
| B11 | Trustelem MFA session behind a load balancer: the Bastion sends Framed-IP-Address so "RADIUS servers can use" it, but "when a load balancer sits in front of WALLIX Bastion, the address displayed is not the user's own" ([Bastion 12.4.3 Administration Guide](https://doc.wallix.com/) 7.2.5.4, 12.16.1.6); test whether the address Trustelem sees is the client's or the load balancer's, which would extend one user's MFA session to every source | 04, 06, report 4.3 | lab |

## Access Manager

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| A1 | Access Manager 6.0 release notes, OS and Java versions (the 6.0.5 guides refer to the release notes and never name Debian or Java), end-of-support date for 5.2. Closed part: migrating from 5.1 or 5.2 to 6 is a backup and restore into a new instance, and HA clusters use "a parallel cluster from a backup of the active cluster" ([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) ch. 7) | report, runbook | vendor |
| A3 | Health-check endpoint path (the HEALTH_VIEW right "Allows access to the API endpoint that provides the health check and status", path not given); TLS versions (*inference:* TLS 1.2 from the cipher names). Closed part: the default cipher list (four ECDHE AES-GCM suites) and `WABSecurityLevel` per node ([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 8.1, Administration Guide 8.5.3) | runbook | vendor, lab |
| A4 | SAML clock-skew tolerance and assertion replay cache (only "Authent. Expir. Delay" in minutes is documented); ACS URL pattern (only in the generated SP metadata); whether push, not only TOTP, works in the RADIUS factor chain: the 6.0.5 guide says the challenge-response mechanism allows "multiple challenge exchanges ... to implement multi-factor authentication" but names no push and no timeout default | 05, standards | vendor, lab |
| A5 | PKCE and exact redirect URI matching on the Bastion and Access Manager OIDC clients and on the Trustelem provider (not mentioned in the 6.0.5 guide, which documents the Authorization Code Flow and discovery) | standards | vendor |
| A7 | Syslog from Access Manager: the [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) table 4 lists "Syslog server integration 514/UDP ... Configurable in System > SIEM integration" (worded like the Bastion row), while the Administration Guide documents no such page; external agents are forbidden ("The installation of external components such as ... monitoring agents is forbidden"). Confirm the page exists and its format | logging | vendor, lab |

## Standards

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| S3 | Certification coverage of Bastion 12.3 and 12.4 versus the BSI-certified 12.0.14; ANSSI qualification status; Common Criteria plans; the 12.0.25 guides (certified branch) lack OIDC, the SAML dynamic flow, API key profiles and RDP Kerberos, so the certified branch cannot run this design's OIDC alternative or the `wallix_access_manager_session_audit` key profile | standards | vendor |

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
| B5 | Closed: the provider source `resource_externalauth_radius.go` has only `authentication_name`, `host`, `port`, `secret`, `timeout`, `description`, `use_primary_auth_domain`, so the "Use mobile device" option must be set in the GUI after apply; no OIDC resources exist | IaC | provider issue tracker |
| S1 | Closed 2026-09-23: the official text of Implementing Regulation (EU) 2024/2690 was read (points 3.2.3, 11.3.1, 11.3.2, 11.4.1, 11.6.1, 11.7.1, 11.7.2) and the standards mapping now quotes it; an earlier paraphrase had attributed recital 23 wording to point 11.7.1 | standards | done |
| S2 | Closed 2026-09-23: DORA RTS 2024/1774 Article 21(1)(e)(ii) and (f)(ii) quoted from the official text | standards | done |
| B3 | Closed 2026-09-24: replication needs "an interface with administration features" (SSH tunnel on 2242), "All Bastion nodes are on the same subnet and connected directly or through only one router", and "Replication across multiple time zones is not supported" ([Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.1); no latency figure is given, so cross-site replication is limited to a stretched subnet | runbook, DR | done |
| B7 | Closed 2026-09-24: "If SAML authentication is also configured in WALLIX Bastion, the domain name must match the name Domain server name used in WALLIX Bastion" ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.3.1; the same rule for OIDC and LDAP domains in 4.3.4.1 and 4.3.5.1), consistent with the Bastion guide. The Trustelem pages' Authentication domain name wording is satisfied by setting both fields to `TRUSTELEM` | 05, SAML reference | done |
| B8 | Closed 2026-09-24: "The key must be between 16 and 128 characters long" ([Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 4.3, 7.1, 7.2; System Operations Guide 14.2); only the pre-12 migration text keeps a 16-character key | runbook | done |
| A2 | Closed 2026-09-24: `wallix-replication` (create-conf-file, install, monitoring, status, resync, dump-resync, stop, start, uninstall), SSH tunnel maintained by autossh with ports 3307 and 3306, Master/Master "supporting two servers (nodes)", FQDN and IPv6 not supported, same subnet with at most one router ([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) ch. 6) | runbook | done |
| A6 | Closed 2026-09-24: `wabam-init-database` and `wabam-config-database` syntax ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 8.3.1, 8.3.2); `wabam-certificate-update` is replaced by `wallix-proxyma-rotate-tls-certificate` (8.5.4.4); no hotfix procedure, minor upgrades use `wallix-upgrade` (Deployment Guide 8.1) | runbook | done |

## How this register is maintained

Add a row when a chapter marks something "not documented" or "gap"; move it to *Closed* when the
answer is written into the chapter and the source is cited. The outbound form of this list is
the [vendor meeting script](vendor-meeting-script.md); section 9.1 of the architecture report,
section 6 of the SCIM chapter and section 5 of the standards reference are the per-document
question lists and point here.
