# SCIM provisioning from Trustelem to the Bastion: assessment

> - **Purpose:** whether Trustelem can provision users into the Bastion over SCIM 2.0: what each
>   side documents, what a configuration would look like, the risks and the questions for WALLIX.
> - **Audience:** PAM architects deciding how users outside Active Directory reach the Bastion.
> - **Verified:** 2026-09-24, against the Trustelem administration book as read on 2026-09-24
>   and the Bastion 12.3.2 Functional Administration Guide; the Bastion SCIM documentation host
>   was unreachable on 2026-09-23.
> - **Sources:** [Trustelem SCIM client](https://trustelem-doc.wallix.com/books/trustelem-administration/page/scim-client),
>   the Bastion SCIM API documentation at https://scim.wallix.com/scim/doc/,
>   the [Bastion 12.3.2 Functional Administration Guide](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
>   the [WALLIX SailPoint datasheet](https://www.wallix.com/wp-content/uploads/2020/06/WALLIX_SAILPOINT-Datasheet.pdf).

**Status: plausible but undocumented by WALLIX; not recommended for production until the vendor
answers the questions in section 6.**

The Bastion SCIM documentation host was unreachable on 2026-09-23. Statements from it come from
search-engine snippets and are marked as such.

## 1. Why it is interesting

SCIM would replace a directory lookup at login by accounts that Trustelem creates and removes.

- Today, [04 Bastion integration](04-bastion-integration.md) scenario C makes Trustelem-only
  users (partners, contractors) visible to the Bastion through the Trustelem LDAP listener.
- SCIM would instead create them as Bastion users in advance, driven by Trustelem access rules,
  with automatic removal when the rule is lost.
- It would also keep Trustelem as the single place where users outside Active Directory are
  managed.

## 2. What is documented on the Trustelem side

Trustelem documents the transport, the trigger and the scope, but not the payload.

- Role: "Trustelem is the SCIM client: it builds the provisioning
  requests and Trustelem Connect forwards them to the SCIM server (typically one that lives on
  the private network, but any reachable SCIM server works)."
- Target on the agent: `./TrustelemConnect set-target <name> <host:port>` writes
  `[target.<name>]` into `config.ini` and sets `outgoing_allowed = "true"`; options
  `-always-tls`, `-no-tls`, `-insecure-allow-skip-tls-check` ("must be combined with Skip TLS
  certificate check in the application setup"), `-override`; restart the service. "the generic
  agent only dials targets it has been explicitly configured with".
- Application settings: "Base Url for SCIM provisioning ... (e.g. https://scim.myapp.local/v2)",
  "Authentication Mode: Bearer Token or Basic", "Connector: select the service", "Connector
  target name: type the exact `<name>` you used with `./TrustelemConnect set-target`", "Skip TLS
  certificate check".
- Trigger and scope: "On a regular schedule (every 5 minutes), or when an administrator clicks
  Force SCIM Sync, Trustelem computes the users and groups that should exist on the
  application, based on its access rules, and prepares the corresponding SCIM requests
  (create / update / delete)." A forced sync "lists the resources already present on the SCIM
  server, reconciles them with the users and groups granted by the access rules, and applies
  the create / update / delete operations."
- Deprovisioning: "If a user loses the access-rule, Trustelem deletes (or deactivates) the user
  on the SCIM server." Whether it sends DELETE or `active=false` is not documented.
- Not documented: the attribute payload (which value becomes `userName`, `externalId`,
  `emails`, `name`), PATCH versus PUT, the Groups payload and membership format (groups
  are pushed: the connector "computes the users and groups that should exist on the
  application"), per-app attribute mapping, extension attributes.
- The WALLIX Bastion and WALLIX Access Manager app pages mention only LDAP, RADIUS and SAML;
  neither mentions SCIM.

## 3. What is documented on the Bastion side

The Bastion SCIM 2.0 API exists, but its public documentation could only be read through
search snippets, and the administration guide does not mention it.

- The Bastion exposes a SCIM 2.0 API documented at https://scim.wallix.com/scim/doc/ with
  pages Usage, Users, Groups, Schemas, Resource Type, Service Provider Config, Containers,
  Privileged Data, X509, Kerberos. WALLIX used it with SailPoint before 2020: "The integration
  set-up of the two solutions is done within a few minutes through the standard protocol SCIM
  2.0 REST API."
- From search snippets of those pages (unverified): authentication by `X-Auth-Key` plus
  `X-Auth-User` headers, HTTP Basic with a Bastion user, or X.509; "version is always equal to
  v2"; Service Provider Config advertises `patch`, `bulk` and `filter` as supported with
  `maxResults: 1000`; the User resource carries `userName`, `displayName`, `emails`, `active`,
  `externalId`, `groups`, `preferredLanguage`, plus a WALLIX extension
  `urn:ietf:params:scim:schemas:wallix:1.0:User` with `profile` (for example `user`,
  `WAB_administrator`) and `user_auths` (for example `local_password`, `local_sshkey`); the
  Group resource has `displayName` and `members`.
- The 12.3.2 Functional Administration Guide and the public release notes contain no
  occurrence of "SCIM"; the exact base path on an appliance and the required attributes for
  creating a user are not documented publicly. Creating a local user in the GUI requires a
  profile and at least one authentication method (Admin Guide 7.4.1), and local users are
  deleted permanently (7.4.7).

## 4. What the configuration would look like (untested)

The settings below combine both sides. None has been tested.

| Side | Setting | Value |
|------|---------|-------|
| Bastion | service user | dedicated local user with a profile allowed to manage users and groups; Basic authentication is the only mode both products document in common (Trustelem offers Bearer or Basic; the Bastion documents API key headers, Basic and X.509) |
| Bastion | endpoint | probably `https://<bastion>/scim/v2` (not verified); use the primary master or the front-end name |
| Trustelem Connect | target | `./TrustelemConnect set-target bastion-scim 10.10.20.21:443`, then restart; trusted certificate on the Bastion rather than skipping TLS checks |
| Trustelem | application | generic model with SCIM on: Base Url, Basic auth with the service user, connector and target name |
| Trustelem | access rules | SCIM rule per group (for example `Partners`), which defines who is created |
| Attributes | `userName` | must equal the login the Bastion will authenticate: the e-mail for Trustelem local users (RADIUS-only local users in scenario B, or the LDAP `mail` attribute) |
| Attributes | `profile`, `user_auths` | must be set for the user to log in; a generic SCIM client cannot send the WALLIX extension unless Trustelem supports it, so the Bastion would need defaults |

## 5. Risks

The main risks are unusable or duplicated accounts and irreversible deletions.

- **Users created without a profile or authentication method** cannot log in, or receive an
  unintended default profile.
- **Deletion is permanent on the Bastion.** If Trustelem sends DELETE when a rule is lost,
  authorizations and audit references to that user are affected; `active=false` would be
  reversible but is not confirmed.
- **Duplicate identities.** People already resolved through the `PARTNERS` LDAP domain
  (scenario C) or the AD domain would exist twice, once as directory users and once as SCIM-
  created local users, with different group mappings, and local users cannot authenticate by
  SAML (the Admin Guide 7.4.3 lists password, SSH key and X.509 as local and RADIUS, TACACS+
  and PingID as external methods for local users; SAML is absent).
- **Reconciliation scope.** The full synchronization that "lists the resources already present
  on the SCIM server" is described for Force SCIM Sync. The five-minute cycle "computes the
  users and groups that should exist" and prepares requests, so its listing scope is not
  documented. Whether it would touch Bastion local users it did not create (break-glass,
  `am-auditor`) is not documented either.
- **Cluster.** Which node should receive SCIM writes and whether created users replicate is not
  documented; the Master/Master rule that "API provisioning must not be performed
  simultaneously from both Bastions" applies ([Bastion HA runbook](../runbooks/bastion-ha-replication.md)).
- **Single connector.** Provisioning stops if the only Connect VM with the target is down.

## 6. Questions for WALLIX

These questions decide whether a proof of concept is worth running.

1. Is Bastion 12.3.x or 12.4.x a supported SCIM provisioning target of WALLIX One IDaaS, and is
   there a reference configuration or an app template?
2. Exact payload Trustelem sends for `POST` and `PATCH /Users` and `/Groups`: source of
   `userName` (e-mail or sAMAccountName), `externalId`, `active`, `name`, `groups`; can it emit
   the WALLIX extension `profile` and `user_auths`?
3. On loss of an access rule, `DELETE` or `PATCH active=false`, and is it configurable?
4. Does the Bastion SCIM server accept Bearer tokens, what is the exact base URL, and which
   profile rights does the service account need?
5. Behaviour of the Bastion on a `POST /Users` without `profile` and `user_auths`.
6. Do SCIM Groups map to Bastion user groups with their existing profile and authorization
   mappings, and does membership PATCH work?
7. Which node exposes the SCIM endpoint in an HA Database Replication cluster, and are
   SCIM-created users replicated?
8. Which Bastion version introduced SCIM 2.0, and is https://scim.wallix.com/scim/doc/ the
   canonical documentation (it was unreachable on 2026-09-23) or is it served from the
   appliance?
9. Is Access Manager also a SCIM target?

## 7. Recommendation

Keep [04 Bastion integration](04-bastion-integration.md) scenario C (Trustelem LDAP plus RADIUS) for users outside Active Directory.
Run a SCIM proof of concept in the lab only after WALLIX answers questions 2, 3 and 5, with a
dedicated Bastion user group and a `Partners-scim` Trustelem group so that reconciliation
cannot touch other accounts, and test deprovisioning before anything else.
