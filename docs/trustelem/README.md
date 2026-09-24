# Trustelem setup, configuration and integration

How to set up WALLIX Trustelem (WALLIX One IDaaS), configure MFA and access rules, and integrate
it with a WALLIX Bastion cluster and a WALLIX Access Manager cluster. Each chapter quotes the
vendor documentation and links to it.

## Chapters

| Chapter | Question it answers |
|---------|---------------------|
| [01 Tenant setup](01-tenant-setup.md) | What do I get with a tenant, and what must be decided, hardened and opened in the firewall before anything else? |
| [02 Directory sync with ADConnect](02-directory-sync-adconnect.md) | How do AD users and groups reach Trustelem, and how is the ADConnect agent installed, upgraded and monitored? |
| [03 Trustelem Connect](03-trustelem-connect.md) | How does the on-premise LDAP and RADIUS agent work, and how is it installed, tested and pointed at SIEM or SCIM targets? |
| [04 Bastion integration](04-bastion-integration.md) | Which Bastion scenario fits each population, and what goes in every field? |
| [05 Access Manager integration](05-access-manager-integration.md) | How does Access Manager use Trustelem over SAML or RADIUS, and how is it linked to the Bastion domain? |
| [06 MFA and access rules](06-mfa-and-access-rules.md) | Which factors, enrollment method and access rules does the PAM design use? |
| [07 Operations](07-operations.md) | How is the tenant run day to day: logs, SIEM export, API, certificates, changes, outages? |
| [08 Troubleshooting](08-troubleshooting.md) | A login fails: where is the cause, and what does WALLIX support need? |
| [09 Worked example](09-worked-example.md) | What does a complete configuration look like, with every value filled in? |
| [10 Test plan](10-test-plan.md) | Which tests prove the integration works, and what evidence is kept? |
| [11 User and help-desk guide](11-user-and-helpdesk-guide.md) | What do users see, and what does the help desk do when they call? |
| [12 SCIM provisioning](12-scim-provisioning.md) | Can Trustelem provision users into the Bastion over SCIM 2.0? |

## Reading order for a new deployment

1. 01 Tenant setup.
2. 02 Directory sync with ADConnect.
3. 06 MFA and access rules, enrollment sections.
4. 03 Trustelem Connect.
5. 04 Bastion integration, then 05 Access Manager integration.
6. 06 MFA and access rules, access rule sections.
7. 07 Operations.
8. 09 Worked example as the template to fill in, then 10 Test plan to validate.

Chapter 11 is for the help desk. Chapter 12 is an assessment, not a procedure.

## Related documents

- [Architecture](../architecture/README.md): clusters, flows, ports, sizing and design
  decisions.
- [Runbooks](../runbooks/): Bastion HA replication and the Access Manager farm.
- [Reference](../reference/): logging and SIEM, SAML naming, API export, standards, open
  questions and gaps.
