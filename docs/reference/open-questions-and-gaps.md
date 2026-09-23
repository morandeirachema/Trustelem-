# Open questions and gaps register

Date: 2026-09-23. One place for everything the public sources do not answer, with the chapter
that depends on it and the way to close it. "Vendor" means it needs a WALLIX answer or a login
to the customer documentation site; "lab" means it can be closed by testing.

## Trustelem

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| T1 | Contractual SLA, maintenance windows, tenant export or backup. Closed part: there is no status page; the [unavailability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability) and [incidents](https://trustelem-doc.wallix.com/books/trustelem-news/page/incidents) pages are the published record (checked 2026-09-23) | 01, 07 | vendor |
| T2 | Location of the admin console authentication level setting and of the RADIUS MFA session duration; allowed duration values | 01, 06 | vendor or console |
| T3 | Synchronisation frequency values for ADConnect; log file locations for ADConnect and Trustelem Connect | 02, 03, 08 | vendor or console |
| T4 | Whether Trustelem Connect answers CHAP; attributes returned in Access-Accept; Message-Authenticator support; BlastRADIUS statement; RadSec roadmap | 03, 04, standards | vendor |
| T5 | Exact SCIM payload, deprovisioning semantics, support for the WALLIX Bastion extension attributes | 12 | vendor |
| T6 | API representation of the RADIUS-only levels *Always allow* and *2nd factor only*: the documented `ZoneSecurityLevel` lists five values and the `EffectiveZoneSecurityLevel` type used by the effective-permission calls is referenced but never defined on the API page (checked 2026-09-23); rate limits | 07, API export | console script editor |
| T7 | Push number matching or rate limiting in WALLIX Authenticator: absent from all four Trustelem books (searched 2026-09-23), so treat as not offered unless WALLIX says otherwise | 06, standards | vendor |
| T8 | Browser "remember this device" or device trust: absent from all four Trustelem books (searched 2026-09-23); only the internal network zone and the RADIUS MFA session exist | 06 | vendor |
| T9 | Hosting provider, country, SecNumCloud or HDS status, ISO 27001 certificate number and statement of applicability | standards | vendor |
| T10 | Console URL fragments for Groups, Apps and Services (only Users, Directories, Security, API, Logs, Alerts, Sessions, Themes, Dashboard are documented) | 01 | console |

## Bastion

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| B1 | Bastion 12.4 release notes and the 12.3.x to 12.4.x change list (behind the doc login); 12.x sizing article | report, runbook | vendor login |
| B2 | Sample output of `bastion-replication --status`, `--monitoring`, `--prerequisite-check`; step-by-step `--elevate-master` failover and failback; restore on a replicated node; HA e-mail template names (System Operations Guide) | runbook | vendor login, lab |
| B3 | Closed for the NIC: eth1 may be used for replication like any other interface, and "When the eth1 interface is used for HA database replication, the associated administration features must be manually enabled from the System > Service control page for replication to work" ([Bastion release notes WAB-7947, WAB-17651](https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html)). Still open: latency limits for cross-site Master/Slaves | runbook, DR | vendor |
| B4 | SCIM API base path on the appliance, required attributes for user creation, Bearer support, cluster behaviour (scim.wallix.com timed out again on both 80 and 443 on 2026-09-23) | 12 | vendor |
| B5 | Closed: the provider source `resource_externalauth_radius.go` has only `authentication_name`, `host`, `port`, `secret`, `timeout`, `description`, `use_primary_auth_domain`, so the "Use mobile device" option must be set in the GUI after apply; no OIDC resources exist | IaC | provider issue tracker |
| B6 | Whether RADIUS accounting (1813) is used; `wabauth` diagnostic text for a RADIUS second factor and for SAML users through Access Manager | logging, test plan | lab |

## Access Manager

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| A1 | Access Manager 6.0 release notes and Debian 12 changes (doc.wallix.com answers 303 to the Trustelem SSO login for both the 6.0 and the Bastion 12.4 notes, checked 2026-09-23) | report, runbook | vendor login |
| A2 | Replication script name and invocation beyond `--prerequisite-check` and `/root/sqlreplication/servers_list`; replication port; maximum node count | runbook | vendor login |
| A3 | Health-check URL for the load balancer; TLS versions and cipher list | runbook | vendor, lab |
| A4 | SAML clock-skew tolerance and assertion replay cache; ACS URL pattern (only in the generated SP metadata); whether push (not only TOTP) works in the RADIUS factor chain | 05, standards | vendor, lab |
| A5 | PKCE on the OIDC client | standards | vendor |
| A6 | `wabam-config-database`, `wabam-init-database` and `wabam-certificate-update` full syntax; hotfix procedure | runbook | vendor login |

## Standards

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| S1 | Closed 2026-09-23: the official text of Implementing Regulation (EU) 2024/2690 was read (points 3.2.3, 11.3.1, 11.3.2, 11.4.1, 11.6.1, 11.7.1, 11.7.2) and the standards mapping now quotes it; an earlier paraphrase had attributed recital 23 wording to point 11.7.1 | standards | done |
| S2 | Closed 2026-09-23: DORA RTS 2024/1774 Article 21(1)(e)(ii) and (f)(ii) quoted from the official text | standards | done |
| S3 | Certification coverage of Bastion 12.3 and 12.4 versus the BSI-certified 12.0.14; ANSSI qualification status; Common Criteria plans | standards | vendor |

## How this register is maintained

Add a row when a chapter marks something "not documented" or "gap"; remove it when the answer
is written into the chapter and the source is cited. The vendor questions in section 9.1 of
the architecture report and section 6 of the SCIM chapter are the outbound form of this list.
