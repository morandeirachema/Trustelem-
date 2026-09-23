# Open questions and gaps register

Date: 2026-09-23. One place for everything the public sources do not answer, with the chapter
that depends on it and the way to close it. "Vendor" means it needs a WALLIX answer or a login
to the customer documentation site; "lab" means it can be closed by testing.

## Trustelem

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| T1 | Contractual SLA, maintenance windows, status page, tenant export or backup | 01, 07 | vendor |
| T2 | Location of the admin console authentication level setting and of the RADIUS MFA session duration; allowed duration values | 01, 06 | vendor or console |
| T3 | Synchronisation frequency values for ADConnect; log file locations for ADConnect and Trustelem Connect | 02, 03, 08 | vendor or console |
| T4 | Whether Trustelem Connect answers CHAP; attributes returned in Access-Accept; Message-Authenticator support; BlastRADIUS statement; RadSec roadmap | 03, 04, standards | vendor |
| T5 | Exact SCIM payload, deprovisioning semantics, support for the WALLIX Bastion extension attributes | 12 | vendor |
| T6 | API representation of the RADIUS-only levels *Always allow* and *2nd factor only* (the documented `ZoneSecurityLevel` lists five values); rate limits | 07, API export | console script editor |
| T7 | Push number matching or rate limiting in WALLIX Authenticator (push fatigue) | 06, standards | vendor |
| T8 | Browser "remember this device" or device trust beyond the internal network zone | 06 | vendor |
| T9 | Hosting provider, country, SecNumCloud or HDS status, ISO 27001 certificate number and statement of applicability | standards | vendor |
| T10 | Console URL fragments for Groups, Apps and Services (only Users, Directories, Security, API, Logs, Alerts, Sessions, Themes, Dashboard are documented) | 01 | console |

## Bastion

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| B1 | Bastion 12.4 release notes and the 12.3.x to 12.4.x change list (behind the doc login); 12.x sizing article | report, runbook | vendor login |
| B2 | Sample output of `bastion-replication --status`, `--monitoring`, `--prerequisite-check`; step-by-step `--elevate-master` failover and failback; restore on a replicated node; HA e-mail template names (System Operations Guide) | runbook | vendor login, lab |
| B3 | Which NIC carries the replication tunnel in 12.3.2 and later (eth1 became a standard interface when DRBD was removed); latency limits for cross-site Master/Slaves | runbook, DR | vendor |
| B4 | SCIM API base path on the appliance, required attributes for user creation, Bearer support, cluster behaviour (scim.wallix.com unreachable on 2026-09-23) | 12 | vendor |
| B5 | Terraform: whether the RADIUS option "Use mobile device for 2 factor authentication(2FA)" is exposed by the provider; no OIDC resources | IaC | provider issue tracker, lab |
| B6 | Whether RADIUS accounting (1813) is used; `wabauth` diagnostic text for a RADIUS second factor and for SAML users through Access Manager | logging, test plan | lab |

## Access Manager

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| A1 | Access Manager 6.0 release notes and Debian 12 changes (behind the doc login) | report, runbook | vendor login |
| A2 | Replication script name and invocation beyond `--prerequisite-check` and `/root/sqlreplication/servers_list`; replication port; maximum node count | runbook | vendor login |
| A3 | Health-check URL for the load balancer; TLS versions and cipher list | runbook | vendor, lab |
| A4 | SAML clock-skew tolerance and assertion replay cache; ACS URL pattern (only in the generated SP metadata); whether push (not only TOTP) works in the RADIUS factor chain | 05, standards | vendor, lab |
| A5 | PKCE on the OIDC client | standards | vendor |
| A6 | `wabam-config-database`, `wabam-init-database` and `wabam-certificate-update` full syntax; hotfix procedure | runbook | vendor login |

## Standards

| # | Gap | Depends | Close by |
|---|-----|---------|----------|
| S1 | Exact annex numbering and wording of Implementing Regulation (EU) 2024/2690 (EUR-Lex refused automated retrieval; numbering taken from a secondary summary) | standards | read the Official Journal text |
| S2 | DORA RTS 2024/1774 sub-point lettering for Article 21 | standards | read the Official Journal text |
| S3 | Certification coverage of Bastion 12.3 and 12.4 versus the BSI-certified 12.0.14; ANSSI qualification status; Common Criteria plans | standards | vendor |

## How this register is maintained

Add a row when a chapter marks something "not documented" or "gap"; remove it when the answer
is written into the chapter and the source is cited. The vendor questions in section 9.1 of
the architecture report and section 6 of the SCIM chapter are the outbound form of this list.
