# Glossary

> - **Purpose:** the meaning of the WALLIX and Trustelem terms used across the repository.
> - **Audience:** anyone reading the documents in this repository.
> - **Verified:** 2026-09-24 against the documents of this repository, which cite the public Bastion 12.3.2 and Access Manager 5.2.4.0 guides, the Bastion 12.0.2 and 12.4.3 Deployment Guides, the Access Manager 6.0.5 guides and the Trustelem documentation books; every definition restates a fact sourced in those documents.
> - **Sources:** [Bastion Administration Guide 12.3.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Access Manager Administration Guide 5.2.4.0](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf), [Trustelem administration book](https://trustelem-doc.wallix.com/books/trustelem-administration/export/html).

## 1. Terms

| Term | Meaning |
|------|---------|
| ADConnect | Trustelem agent that synchronises AD users and validates AD passwords over an outbound websocket |
| Trustelem Connect | Trustelem agent exposing local LDAP (2001) and RADIUS (1812 Bastion, 2812 Access Manager) listeners that relay to the cloud |
| WALLIX Authenticator | the mobile and desktop push/TOTP app, and also the name of the Trustelem licence limited to Bastion and Access Manager |
| Authentication domain | Bastion object binding a user population (AD, SAML, OIDC) to primary and secondary authentication methods and group mappings |
| Domain server name | Bastion field that must equal the Access Manager SAML or OIDC domain name (Bastion 7.3.1, AM 10.3.2 and 10.5.2); the Authentication domain name of the same object is set identical, as WALLIX recommends |
| Strip Domain | Access Manager per-Bastion switch removing `@domain` from logins; must be off for federated users |
| HA Database Replication | Bastion 12 MariaDB replication over an autossh tunnel, Master/Master or Master/Slaves |
| Cluster (Access Manager) | group of Bastions with identical authorizations among which Access Manager balances sessions |
| Account mapping | Bastion secondary connection mode reusing the user's own credentials on the target |
| WAMUT | WALLIX Universal Tunneling client for raw TCP through the SSH proxy |
| Session Probe | agent injected into RDP sessions for process, clipboard and jump detection |
| Access rule | Trustelem per-application policy: number of factors required by zone (web), LDAP or RADIUS |
| MFA session | Trustelem option suppressing repeated RADIUS second factors for a duration on the same network |
