# Trustelem setup, configuration and integration

This folder is the core of the repository: how to set up WALLIX Trustelem (WALLIX One IDaaS),
configure MFA and access rules, and integrate it with a WALLIX Bastion cluster and a WALLIX
Access Manager cluster. Every chapter quotes the vendor documentation verbatim and links to it.

| Chapter | Content |
|---------|---------|
| [01 Tenant setup](01-tenant-setup.md) | tenant URLs, console areas, identity-source decision, day-zero hardening, network flows for the agents, availability facts, order of work |
| [02 Directory sync with ADConnect](02-directory-sync-adconnect.md) | how ADConnect works, prerequisites, Windows and Linux install, config keys, activation, custom attributes, rolling upgrades, health |
| [03 Trustelem Connect](03-trustelem-connect.md) | the LDAP and RADIUS agent: install, config keys, listeners per application, emulated LDAP tree, RADIUS behaviour, `connect check`, SIEM and SCIM targets |
| [04 Bastion integration](04-bastion-integration.md) | four scenarios (RADIUS for AD users, RADIUS-only local users, Trustelem LDAP plus RADIUS, SAML), field-by-field values, worksheet, verification, common mistakes |
| [05 Access Manager integration](05-access-manager-integration.md) | SAML template for AD and Trustelem users, linking to the Bastion domain, RADIUS as factor 2, worksheet, verification, debug |
| [06 MFA and access rules](06-mfa-and-access-rules.md) | factors, passkey policy, enrollment campaigns, rescue codes, access-rule semantics and priority, the rule set for the PAM design, MFA session |
| [07 Operations](07-operations.md) | logs, alerts, sessions, SIEM export, API and scripts, certificate rotation, self-service reset, delegated administration, change management, outage handling |
| [08 Troubleshooting](08-troubleshooting.md) | symptom tables for connectors, directory sync, Bastion RADIUS and LDAP, Access Manager RADIUS and SAML, escalation data |
| [09 Worked example](09-worked-example.md) | every field filled in for a fictitious organisation: tenant, agents, apps, access rules, Bastion, Access Manager, user journeys, consistency checks |
| [10 Test plan](10-test-plan.md) | test IDs with preconditions, steps, expected results and the log evidence to keep |
| [11 User and help-desk guide](11-user-and-helpdesk-guide.md) | what users see on each path, enrollment, lost phone, help-desk checklist, emergency |
| [12 SCIM provisioning](12-scim-provisioning.md) | assessment of provisioning Trustelem users into the Bastion over SCIM 2.0: documented halves, untested configuration, risks, vendor questions |

Reading order for a new deployment: 01, 02, 06 (enrollment), 03, 04, 05, 06 (rules), 07, then 09 as
the template to fill in and 10 to validate. Chapter 11 is for the help desk.

The surrounding design (clusters, flows, ports, sizing, runbooks for the appliances) is in the
[architecture report](../trustelem-bastion-access-manager-architecture.md) and the
[runbooks](../runbooks/).
