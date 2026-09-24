# Deployment and rollout

> - **Purpose:** the prerequisites, the order of the setup steps with a pointer to the document that holds each procedure, the sign-off tests and the phased rollout with its rollback.
> - **Audience:** PAM architect, project manager, Trustelem administrator, Bastion and Access Manager operators.
> - **Verified:** 2026-09-24 against the public Bastion 12.3.2 and Access Manager 5.2.4.0 guides, the Bastion 12.4.3 and Access Manager 6.0.5 customer guides and the Trustelem documentation books, with the WALLIX security advisories.
> - **Sources:** [WALLIX security advisories](https://www.wallix.com/support-services/alerts/), Bastion 12.4.3 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), Access Manager 6.0.5 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), [Bastion Administration Guide 12.3.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Trustelem administration book](https://trustelem-doc.wallix.com/books/trustelem-administration/export/html), [test plan](../trustelem/10-test-plan.md).

Order matters: directory first, then agents, then Bastion cluster, then Access Manager farm,
then federation, then MFA enforcement. Test after each block.

## 1. Prerequisites

1. AD read-only service account for ADConnect (UPN format) and, if self-service password reset
   is wanted, the "Reset user password" delegation.
   Source: [ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect).
2. Four small VMs (two ADConnect, two Trustelem Connect), Windows Server or Linux, with
   outbound TCP 443 to the Trustelem FQDNs and IPs, TLS inspection excluded.
   Source: [Connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows).
3. Two Bastion appliances at 12.4.3 (target; at least 12.3.7 or 12.4.1 per the advisories),
   identical version and hotfix, IPv4 addresses on the same subnet with at most one router
   between them, an interface with administration features on each node, encryption
   initialised, a licence for each node, an SMTP server on each node, NTP to the same time zone.
   Sources: [WALLIX advisories](https://www.wallix.com/support-services/alerts/),
   [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5 and 5.1.
4. Two Access Manager appliances at 6.0.5 (target; at least 6.0.4 or 5.2.7 per the advisories,
   SAML forgery fix), identical version, two interfaces each (Administration on the first, User
   Access on the second), IPv4 addresses on the same subnet with at most one router between
   them, NTP to the same time zone, at least 2 cores, 4 GB RAM and 50 GB disk (DG 2.3 for
   session sizing), one Access Manager licence file.
   Sources: [WALLIX advisories](https://www.wallix.com/support-services/alerts/),
   [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 1.2, 2.3, 4.3 and 6.
5. A load balancer with WebSocket support and session affinity (Layer 7 cookie affinity) in front
   of Access Manager and, optionally, an L4 balancer or DNS name for the Bastion proxies.
   Sources: [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 5 and 10.1, [AM release notes header](https://pam.wallix.one/documentation/release-notes/am-rn-en.html).

## 2. Trustelem tenant

Each step is documented in full, with its sources, in the Trustelem chapters; this list gives
the order.

1. Register the AD directory, install ADConnect on both VMs, select the groups and the
   frequency: [chapter 02](../trustelem/02-directory-sync-adconnect.md#3-register-the-directory-in-the-console), sections 3 to 6.
2. Enable the factors and the passkey policy, then launch the enrollment campaign:
   [chapter 01, section 3](../trustelem/01-tenant-setup.md#3-day-zero-checklist) and
   [chapter 06](../trustelem/06-mfa-and-access-rules.md#2-enable-factors), sections 2 to 4.
3. Create the **Access Manager** application:
   [chapter 05, section 2](../trustelem/05-access-manager-integration.md#2-saml-for-ad-users-step-by-step)
   (RADIUS on the same app only for the alternative flow, section 5).
4. Create the **WALLIX Bastion** application with RADIUS; the generic SAML2 app only for native
   SAML without Access Manager:
   [chapter 04](../trustelem/04-bastion-integration.md#2-common-prerequisite-the-bastion-application-and-trustelem-connect),
   sections 2 and 6.
5. Download and install Trustelem Connect on both VMs, add the applications and their listeners,
   then run `./connect check`:
   [chapter 03](../trustelem/03-trustelem-connect.md#2-create-the-service-in-the-console),
   sections 2 to 5 and 8.
6. Set the access rules:
   [chapter 06, section 7](../trustelem/06-mfa-and-access-rules.md#7-rule-set-for-the-pam-design).
7. Create one local Trustelem backup administrator not linked to AD:
   [chapter 01, section 3](../trustelem/01-tenant-setup.md#3-day-zero-checklist).

## 3. Bastion cluster

The replication procedures are in the [Bastion HA runbook](../runbooks/bastion-ha-replication.md)
and the Trustelem settings in [chapter 04](../trustelem/04-bastion-integration.md).

1. Initialise both appliances and apply the settings that do not replicate:
   [HA runbook](../runbooks/bastion-ha-replication.md#3-node-initialisation-both-nodes), sections 3
   and 12.
2. Install the replication from the primary master:
   [HA runbook](../runbooks/bastion-ha-replication.md#4-install-the-replication), sections 4 and 5.
3. Create the AD external authentication and the AD authentication domain with its group
   mappings: [chapter 04, scenario A prerequisite](../trustelem/04-bastion-integration.md#prerequisite-ad-external-authentication-and-domain).
4. Create the RADIUS external authentication twice, one per Trustelem Connect VM:
   [chapter 04, section 3](../trustelem/04-bastion-integration.md#bastion-settings-for-scenario-a),
   steps 1 to 5, and its [worksheet](../trustelem/04-bastion-integration.md#7-configuration-worksheet).
5. Set both RADIUS methods as **Secondary authentication** of the AD domain:
   [chapter 04, section 3](../trustelem/04-bastion-integration.md#bastion-settings-for-scenario-a), step 6.
6. Create the SAML external authentication:
   [chapter 04, section 6](../trustelem/04-bastion-integration.md#standalone-saml-procedure), step 2,
   with the changes listed under
   [Behind Access Manager](../trustelem/04-bastion-integration.md#behind-access-manager).
7. Create the SAML **Other IdPs** authentication domain and its group mappings:
   [chapter 04, section 6](../trustelem/04-bastion-integration.md#standalone-saml-procedure), steps 3
   and 5, with the names of the [naming rules](05-low-level-design.md#1-naming-and-mapping-rules).
8. Create the API key and the auditor login for Access Manager:
   [farm runbook, section 10](../runbooks/access-manager-farm.md#10-bastion-objects-and-the-trustelem-saml-domain).
9. Keep one local, IP-restricted break-glass administrator and delete the default `admin`
   account: [administrator access model](03-design-and-flows.md#6-administrator-access-model) and
   [HA runbook](../runbooks/bastion-ha-replication.md#3-node-initialisation-both-nodes), section 3.

## 4. Access Manager farm

The farm procedures are in the [Access Manager farm runbook](../runbooks/access-manager-farm.md)
and the Trustelem settings in [chapter 05](../trustelem/05-access-manager-integration.md).

1. Install and secure node 1:
   [farm runbook, section 2](../runbooks/access-manager-farm.md#2-install-node-1).
2. Install node 2, replicate from node 1 and repeat the per-node settings:
   [farm runbook, section 3](../runbooks/access-manager-farm.md#3-add-node-2-and-replicate-the-database).
3. Set the Proxyma trusted proxies and the appliance firewall option behind the load balancer on
   each node: [farm runbook, section 4](../runbooks/access-manager-farm.md#4-load-balancer-settings).
4. Create the organization and declare both Bastion nodes as one Cluster:
   [farm runbook, sections 5 and 10](../runbooks/access-manager-farm.md#10-bastion-objects-and-the-trustelem-saml-domain),
   and [chapter 05, section 4](../trustelem/05-access-manager-integration.md#4-linking-the-access-manager-saml-domain-to-the-bastion).
5. Add the Trustelem SAML identity provider:
   [chapter 05, section 2](../trustelem/05-access-manager-integration.md#access-manager-saml-identity-provider).
6. Optional alternative flow, RADIUS servers and the LDAP domain with RADIUS as factor 2:
   [chapter 05, section 5](../trustelem/05-access-manager-integration.md#access-manager-radius-server-and-domain),
   with the timeout of the [timeouts table](05-low-level-design.md#4-timeouts-to-align).
7. Set the organization default domain:
   [chapter 05, section 2](../trustelem/05-access-manager-integration.md#organization-default-domain).

## 5. Acceptance tests

The full test plan with IDs, preconditions, steps and the evidence to keep is
[chapter 10](../trustelem/10-test-plan.md); the table below is the sign-off summary.

| Test | Expected result |
|------|-----------------|
| AD user opens Access Manager | redirect to Trustelem, AD password, push approval, portal shows Bastion authorizations of `user@TRUSTELEM` |
| Launch RDP and SSH from the portal | session opens with no Bastion prompt; Bastion audit shows the AM node IP as client |
| Same user with `mstsc` to the Bastion proxy | AD password, push prompt on the phone, session opens; second connection within the MFA session window is not re-prompted |
| SSH client with keyboard-interactive | challenge received; approve push or type TOTP |
| Stop Trustelem Connect VM 1 | Bastion falls back to VM 2 within the RADIUS timeout |
| Stop AM node 1 | load balancer drains, new logins land on node 2 |
| `wallix-replication --status` on the primary master | IO and SQL threads "YES" for each replica ([System Operations Guide](https://doc.wallix.com/) 11.3); create a test authorization on the master and see it on the other node |
| SAML tracer on the browser | assertion signed by the current Trustelem certificate, `groups` and `profile` attributes present |
| Break-glass | local Bastion admin logs in from the admin network with Trustelem Connect stopped |

Tools: Bastion "Test authentication" on LDAP domains, Access Manager "Test Connection" on
Bastions and RADIUS servers, `./connect check`, and a SAML tracer browser extension.
Sources: [AM 11 and 13](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf),
[AM app in Trustelem](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager).

## 6. Rollout and rollback

| Phase | Scope | Exit criteria | Rollback |
|-------|-------|---------------|----------|
| 0. Build | clusters, agents, federation on a pilot organization | all [acceptance tests](#5-acceptance-tests) pass on the pilot | none needed |
| 1. Pilot | one AD group of administrators; Trustelem access rule *2 factors* for the Access Manager app on that group only, RADIUS rule *2nd factor only* on the same group, *Always allow* for everyone else | two weeks without authentication incidents; SIEM dashboards populated | set the group rule back to *Default* / *Always allow* |
| 2. Native clients | enable RADIUS secondary authentication on the AD domain for all groups; automation accounts moved to a separate AD domain object without secondary authentication | no failed scripted transfers; push timeout tuned | remove the secondary authentication from the domain (one field) |
| 3. Everyone on the web path | Access Manager access rule *2 factors* for all PAM groups | help-desk volume normal; rescue-code process exercised | rule back to *1 factor* |
| 4. Hardening | delete default accounts, close direct SAML to the Bastion, restrict 2242, passkey policy Strict for admins | [hardening checklist](05-low-level-design.md#6-security-hardening-checklist) complete | re-enable individual controls |

Trustelem access rules apply per group, and "A user access rule wins over a group access rule,
whether it is more restrictive or not", so the pilot and the
rollback stay within the Trustelem console without touching the Bastion or Access Manager.
Source: [Access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules).
The MFA session (same network, tenant-defined duration, example given as one hour) softens the
prompt frequency for native clients during phase 2.
Source: [Trustelem new features](https://trustelem-doc.wallix.com/books/trustelem-news/page/new-features).
