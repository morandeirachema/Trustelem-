# Trustelem tenant setup

> - **Purpose:** harden a new Trustelem tenant and prepare its network flows before any
>   connector, application or access rule is added.
> - **Audience:** Trustelem administrator, PAM architect, network and firewall team.
> - **Verified:** 2026-09-24, against the Trustelem documentation books as read on 2026-09-24.
> - **Sources:** Trustelem administration book
>   ([summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary),
>   [local users](https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-local-users),
>   [password levels](https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-password-levels),
>   [connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows)),
>   [availability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability),
>   [WALLIX Authenticator setup instructions](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/setup-instructions).

## 1. What the tenant provides

A tenant gives two URLs:

- `https://<tenant>.trustelem.com`: the user dashboard.
- `https://admin-<tenant>.trustelem.com`: the admin console.

Source: [summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary).

The product names (WALLIX One IDaaS, WALLIX IDaaS in the Bastion guides) and the WALLIX
Authenticator licence limited to Bastion and Access Manager are described in the
[architecture overview, section 2](../architecture/01-overview.md#2-product-naming-and-versions).

Admin console areas used in a PAM deployment:

| Area | URL fragment | Used for |
|------|--------------|----------|
| Dashboard | `app#/dashboard` | user counts per directory with a health LED per directory, authentication statistics |
| Users, Groups | `app#/users` (Groups: menu entry, fragment not documented) | local users, imported AD users, group membership used by access rules and SAML scripts |
| Directories | `app#/directories` | Active Directory sync through ADConnect ([chapter 02](02-directory-sync-adconnect.md)) |
| Apps | menu entry (fragment not documented) | the Bastion and Access Manager applications ([chapter 04](04-bastion-integration.md) and [chapter 05](05-access-manager-integration.md)) |
| Services | menu entry (fragment not documented) | Trustelem Connect instances and their LDAP/RADIUS listeners ([chapter 03](03-trustelem-connect.md)) |
| Access rules | Access rules tab (fragment not documented) | who must present one or two factors ([chapter 06](06-mfa-and-access-rules.md)) |
| Security settings | `app#/security` | authentication factors, passkey policy, password management, internal network, application certificates |
| API / scripts | `app#/api-scripts` | automation ([chapter 07](07-operations.md)) |
| Logs, Alerts, Sessions | `app#/logs`, `app#/alert`, `app#/sessions` | operations ([chapter 07](07-operations.md)) |

## 2. Decide the identity sources first

Import Active Directory users with ADConnect. For everyone else the vendor recommends local
Trustelem users rather than local Bastion users; this design keeps local Bastion accounts only
for break-glass, automation and the Access Manager auditor login. The vendor's decision tree for WALLIX products:

- **Users in Active Directory:** import them with ADConnect and enrol their factors. "Are you
  mainly using account mapping?" If yes, use the AD login and password plus a Trustelem RADIUS
  second factor. If no, use Trustelem SAML (Access Manager).
- **Users not in Active Directory:** "it's best to go through local Trustelem users, and not
  local Bastion users. This way you only have one source of identity to maintain alongside the
  AD."
- **Local Trustelem accounts:** "Trustelem accounts should only be used for": "temporary users
  for testing purpose", "the definition of a backup administrator" and "users with no entry in
  directories such as partners, clients".

Sources: [setup instructions](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/setup-instructions),
[Bastion app page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion),
[local users](https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-local-users).

Check for duplicates before the first import. The merging rule: "if you synchronize a user who
has the same UPN/email as a local Trustelem account, then the 2 accounts will be merged and the
password to use will be the one from Active Directory".
Source: [ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect).

## 3. Day-zero checklist

Complete these eight items before the first connector is installed.

1. **Backup administrator.** Create one local Trustelem user with administration rights that is
   not linked to AD. Enrol two factors on it and store its rescue path offline. The
   backup-administrator role is documented; the two factors and the offline storage are
   recommendations.
2. **Admin console authentication level.** The project plan step is "Select 2 factors for
   Trustelem admin accesses". The exact setting location is not documented.
   Source: [summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary).
3. **Internal network.** "the internal IPs must be defined on Security settings / General /
   Internal network. Internal IPs are usually the public IPs of the company offices." This list
   sets the internal versus external zone of web access rules. IWA needs it too: "IWA is only
   enabled on the internal zone".
   Sources: [access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules),
   [IWA](https://trustelem-doc.wallix.com/books/trustelem-administration/page/integrated-windows-authentication).
4. **Default authentication level.** "Security settings / General / Default authentication level
   for users" is the value applied when an app rule says *Default*. Set it to 2 factors for a
   PAM tenant.
   Source: [access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules).
5. **Password policy** for Trustelem local users. There are "3 security levels : None - Medium -
   High". Medium is a zxcvbn score of 3 and High a score of 4. The policy also uses a minimum
   length you define and a vendor dictionary "which contains account information (login,
   domain, orga...)". Choose High.
   Source: [password levels](https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-password-levels).
6. **Authentication factors.** Enable WALLIX Authenticator, TOTP and second-step passkeys. Leave
   SMS (extra cost) and e-mail OTP (weak) off. Details are in
   [chapter 06, section 1](06-mfa-and-access-rules.md#1-factors-available).
   Source: [MFA](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication).
7. **Firewall and proxy rules for the agents.** See section 4.
8. **Alerts recipients.** "When a user requests help ... administrators receive an email", and
   "All administrators receive an email alerting that a rescue code is requested".
   Administrators are individual users, so give each one a monitored mailbox (recommendation).
   Sources: [summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary),
   [loss of a second factor](https://trustelem-doc.wallix.com/books/trustelem-administration/page/loss-of-a-second-factor).

## 4. Network prerequisites for every connector

Every connector needs outbound TCP 443 in TLS to the names below, and ADConnect also reaches the
domain controllers (last item of this section). If the connector exits through an HTTP proxy,
that proxy must not inspect TLS. This section is the repository's home for the Trustelem egress
destinations. All quotes are from the
[connectors network flows page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows).

### Flow rules

- "All traffic is outbound only, over TCP port 443, in TLS, and is always initiated by the
  connector".
- "Write your rules against these DNS names, not against IP addresses": `*.trustelem.com`,
  `relay-fr-01.wallix.com`, `relay-fr-02.wallix.com`.
- The older ADConnect and Trustelem Connect pages still list only `admin.trustelem.com`
  (185.4.44.22). The connectors network flows page is the complete list and takes precedence.

### IP addresses

- IP fallback list: 185.4.44.22, 185.4.46.20, 185.4.46.21, 185.4.46.22.
- Relays: 98.66.169.89 and 20.39.241.157.
- New addresses for `*.trustelem.com` "active on 29 September 2026": 185.4.44.114 and
  185.4.44.117. "Authorize them now, in addition to the addresses already in place: add them,
  do not replace the existing ones".

### Proxy and TLS inspection

The proxy "must allow the CONNECT method to these destinations on port 443, and the proxy must
not intercept the TLS session", because "The connector authenticates the server with a pinned
certificate".

### Checks after a change

1. `nslookup admin.trustelem.com` and `nslookup connect.trustelem.com`.
2. `./connect check <sync id> [http://proxy:3128]`, described in
   [chapter 03, section 8](03-trustelem-connect.md#8-connectivity-test). "A ping is not a valid
   test."
3. "After changing a firewall, proxy or DNS rule, restart the connector service to confirm that
   it can reconnect".

ADConnect has one more flow, towards a domain controller; see
[chapter 02, section 2](02-directory-sync-adconnect.md#2-prerequisites).

## 5. Availability and support

The vendor publishes an availability history and an incident log; it documents no contractual
SLA.

- Availability history: above 99.99 % for 2016 to 2022, and 99.94 % in 2023 with 50 minutes of
  planned maintenance for a datacenter migration.
  Source: [unavailability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability).
- Incident log with root causes, for example 2026-01-05, a storage failure at the hosting
  provider. Source: [incidents](https://trustelem-doc.wallix.com/books/trustelem-news/page/incidents).
- Not documented: contractual SLA, tenant export or backup, data retention policy, maintenance
  windows. There is no status page; the two pages above are the published record. Ask WALLIX
  for the rest (see the [open questions and gaps register](../reference/open-questions-and-gaps.md)).
- Enabled on request through WALLIX support or sales: the API, delegated administration and
  custom themes.
  Sources: [API](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api),
  [delegated administration](https://trustelem-doc.wallix.com/books/trustelem-administration/page/delegated-administration),
  [custom themes](https://trustelem-doc.wallix.com/books/trustelem-administration/page/custom-themes).

## 6. Order of work for a PAM tenant

Work in this order. It is this repository's plan, derived from the dependencies between
chapters.

1. Tenant hardening (this chapter).
2. ADConnect on two VMs and the AD directory sync ([chapter 02](02-directory-sync-adconnect.md)).
3. Factor enrollment campaign for the PAM groups ([chapter 06](06-mfa-and-access-rules.md)).
4. Trustelem Connect on two VMs, one service with the Bastion and Access Manager applications
   attached ([chapter 03](03-trustelem-connect.md)).
5. Bastion integration ([chapter 04](04-bastion-integration.md)) and Access Manager integration
   ([chapter 05](05-access-manager-integration.md)).
6. Access rules per group, pilot first ([chapter 06](06-mfa-and-access-rules.md)).
7. SIEM export, API keys, certificate expiry monitoring ([chapter 07](07-operations.md)).
