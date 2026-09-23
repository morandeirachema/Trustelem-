# Documentation index

The repository's main concern is **WALLIX Trustelem setup, configuration and integration**
with a WALLIX Bastion cluster and a WALLIX Access Manager cluster. Start in `trustelem/`.

## Trustelem (core)

| Document | Content |
|----------|---------|
| [trustelem/README.md](trustelem/README.md) | index and reading order of the eight Trustelem chapters |
| [01 Tenant setup](trustelem/01-tenant-setup.md) | tenant, console, identity-source decision, hardening, agent network flows |
| [02 ADConnect](trustelem/02-directory-sync-adconnect.md) | Active Directory synchronisation agent |
| [03 Trustelem Connect](trustelem/03-trustelem-connect.md) | LDAP and RADIUS agent, listeners, `connect check`, SIEM/SCIM targets |
| [04 Bastion integration](trustelem/04-bastion-integration.md) | RADIUS, LDAP and SAML scenarios with exact field values |
| [05 Access Manager integration](trustelem/05-access-manager-integration.md) | SAML template, RADIUS factor chains, linking to the Bastion domain |
| [06 MFA and access rules](trustelem/06-mfa-and-access-rules.md) | factors, passkey policy, enrollment, rescue codes, rule semantics and rule set |
| [07 Operations](trustelem/07-operations.md) | logs, SIEM export, API, certificate rotation, SSPR, delegation, outage handling |
| [08 Troubleshooting](trustelem/08-troubleshooting.md) | symptom tables and escalation data |
| [09 Worked example](trustelem/09-worked-example.md) | all fields filled in for a fictitious organisation |
| [10 Test plan](trustelem/10-test-plan.md) | test IDs, steps, expected results, log evidence |
| [11 User and help-desk guide](trustelem/11-user-and-helpdesk-guide.md) | end-user journeys and help-desk checklist |

## Architecture

| Document | Content |
|----------|---------|
| [Architecture report](trustelem-bastion-access-manager-architecture.md) | high-level and low-level design, identity flows, access-path coverage, cluster design, DR, ports, sizing, hardening, runbook summary, rollout plan, vendor questions, glossary |
| [diagrams/](diagrams/) | rendered ASCII diagrams (regenerate with `tools/diagrams/*.py`; `tools/check_docs.py` verifies them) |

## Supporting runbooks and references

| Document | Content |
|----------|---------|
| [Bastion HA Database Replication](runbooks/bastion-ha-replication.md) | node initialisation, replication install, commands, failover, upgrades, certificates, what replicates from the Trustelem integration |
| [Access Manager farm](runbooks/access-manager-farm.md) | node install, farm replication, load balancer settings, `wabam.properties`, backup, upgrade, monitoring |
| [Terraform for the Bastion side](reference/iac-terraform-bastion.md) | codifying the AD, RADIUS, SAML, mappings and API key objects |
| [Logging and SIEM](reference/logging-and-siem.md) | sources, formats, correlation keys, detection rules |
| [SAML assertion and naming](reference/saml-assertion-and-naming.md) | the three names that must match, illustrative assertion, what to verify in a SAML tracer |
| [Standards and compliance](reference/standards-and-compliance.md) | RFC and OASIS clauses, NIST assurance levels, NIS2, DORA, ISO 27001, IEC 62443, PCI DSS, ANSSI guides, vendor certifications, MITRE ATT&CK mapping |
| [archive/research-notes/](archive/research-notes/) | archived working notes (superseded by the chapters) |
