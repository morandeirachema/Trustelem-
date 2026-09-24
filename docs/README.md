# Documentation index

Every document opens with its purpose, audience, verification date and sources. The writing
rules are in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Trustelem setup, configuration and integration

The core of the repository, in reading order for a new deployment.

| Chapter | Answers |
|---------|---------|
| [01 Tenant setup](trustelem/01-tenant-setup.md) | what the tenant is, day-zero hardening, egress rules for the agents |
| [02 Directory sync with ADConnect](trustelem/02-directory-sync-adconnect.md) | how AD users reach Trustelem and how their passwords are checked |
| [03 Trustelem Connect](trustelem/03-trustelem-connect.md) | how the Bastion and Access Manager reach Trustelem over RADIUS and LDAP |
| [04 Bastion integration](trustelem/04-bastion-integration.md) | how to add MFA to the Bastion, field by field, for each user population |
| [05 Access Manager integration](trustelem/05-access-manager-integration.md) | how to federate Access Manager over SAML, and the RADIUS fallback |
| [06 MFA and access rules](trustelem/06-mfa-and-access-rules.md) | which factors, how users enrol, which rule each group gets |
| [07 Operations](trustelem/07-operations.md) | logs, SIEM, API, certificates, change management, outages |
| [08 Troubleshooting](trustelem/08-troubleshooting.md) | symptom, cause and fix for each failing login |
| [09 Worked example](trustelem/09-worked-example.md) | every field filled in for one sample organisation |
| [10 Test plan](trustelem/10-test-plan.md) | test IDs, steps, expected results and evidence |
| [11 User and help-desk guide](trustelem/11-user-and-helpdesk-guide.md) | what users see, enrollment, lost phone, help-desk checklist |
| [12 SCIM provisioning](trustelem/12-scim-provisioning.md) | whether to provision Trustelem users into the Bastion over SCIM |

## Architecture

| Document | Answers |
|----------|---------|
| [Architecture set](architecture/README.md) | index and reading order of the design documents |
| [01 Overview](architecture/01-overview.md) | the design in brief, product names, versions, certifications |
| [02 Components](architecture/02-components.md) | what Trustelem, the Bastion and Access Manager each do |
| [03 Design and flows](architecture/03-design-and-flows.md) | design decisions, web and native login flows, access-path coverage |
| [04 Clusters and DR](architecture/04-clusters-and-dr.md) | Bastion and Access Manager clusters, failure modes, disaster recovery |
| [05 Low-level design](architecture/05-low-level-design.md) | naming, certificates, ports, timeouts, sizing, hardening |
| [06 Deployment and rollout](architecture/06-deployment-and-rollout.md) | prerequisites, order of work, acceptance, rollout and rollback |
| [07 Operations](architecture/07-operations.md) | monitoring, rotation, upgrades and backups |
| [08 Caveats and questions](architecture/08-caveats-and-questions.md) | limits of the design and the questions for WALLIX before sign-off |

## Runbooks

| Runbook | Answers |
|---------|---------|
| [Bastion HA Database Replication](runbooks/bastion-ha-replication.md) | Bastion 12.4.3: build, check, fail over, upgrade and back up the cluster |
| [Access Manager farm](runbooks/access-manager-farm.md) | Access Manager 6.0.5 (with 5.2 differences): build, load-balance, upgrade and monitor the farm |

## Reference

| Document | Answers |
|----------|---------|
| [Open questions and gaps](reference/open-questions-and-gaps.md) | what the sources do not answer, and how to close each item |
| [Vendor meeting script](reference/vendor-meeting-script.md) | the brief and the questions to put to WALLIX |
| [SAML assertion and naming](reference/saml-assertion-and-naming.md) | the names that must match on the three products |
| [Logging and SIEM](reference/logging-and-siem.md) | log sources, formats, correlation keys, detection rules |
| [Standards and compliance](reference/standards-and-compliance.md) | RFCs, OASIS, NIST, NIS2, DORA, ISO 27001, ANSSI, MITRE mapping |
| [Terraform for the Bastion side](reference/iac-terraform-bastion.md) | codifying the AD, RADIUS, SAML, mapping and API key objects |
| [Trustelem API export](reference/trustelem-api-export.md) | nightly export of permissions, identities, logs and alerts |
| [Glossary](reference/glossary.md) | the terms used across the documents |
| [Sources](reference/sources.md) | every vendor guide, page and standard cited, and where to get it |

## Archive

[Research notes](archive/research-notes/README.md): the first working notes, kept for
provenance; the chapters supersede them.
