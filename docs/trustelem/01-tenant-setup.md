# Trustelem tenant setup

Date: 2026-09-23. Sources: the Trustelem administration book
([summary page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary),
[local users](https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-local-users),
[password levels](https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-password-levels),
[connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows),
[availability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability)) and the
[WALLIX Authenticator setup instructions](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/setup-instructions).
Quotes are verbatim.

## 1. What you receive

A tenant gives two URLs: `https://<tenant>.trustelem.com` (user dashboard) and
`https://admin-<tenant>.trustelem.com` (admin console). The product is sold today as WALLIX One
IDaaS; the licence limited to Bastion and Access Manager is called WALLIX Authenticator, and
"can be extended for the authentication of other apps: with only a license change".
Sources: [summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary),
[WALLIX Authenticator presentation](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/presentation).

Admin console areas you will use for a PAM deployment:

| Area | URL fragment | Used for |
|------|--------------|----------|
| Dashboard | `app#/` | user counts per directory with a health LED per connector, authentication statistics |
| Users, Groups | `app#/users`, `app#/groups` | local users, imported AD users, group membership used by access rules and SAML scripts |
| Directories | `app#/directories` | Active Directory sync through ADConnect (chapter 02) |
| Apps | `app#/apps` | the Bastion and Access Manager applications (chapters 04 and 05) |
| Services | `app#/services` | Trustelem Connect instances and their LDAP/RADIUS listeners (chapter 03) |
| Access rules | per app | who must present one or two factors (chapter 06) |
| Security settings | `app#/security` | authentication factors, passkey policy, password management, internal network, application certificates |
| API / scripts | `app#/api-scripts` | automation (chapter 07) |
| Logs, Alerts, Sessions | `app#/logs`, `app#/alert`, `app#/sessions` | operations (chapter 07) |

## 2. Decide the identity sources first

The vendor's own decision tree for WALLIX products:

- Users in Active Directory: import them with ADConnect, enrol their factors, then use RADIUS
  as second factor on the Bastion AD domain, or SAML for Access Manager.
- Users not in Active Directory: create Trustelem local users rather than Bastion local
  users, "to maintain a single source of identity".
- "Trustelem accounts should only be used for" partners, external users and "the definition of
  a backup administrator".

Sources: [setup instructions](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/setup-instructions),
[Bastion app page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion),
[local users](https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-local-users).

Merging rule to remember before importing: "if you synchronize a user who has the same
UPN/email as a local Trustelem account, then the 2 accounts will be merged and the password to
use will be the one from Active Directory".
Source: [ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect).

## 3. Day-zero checklist

1. **Backup administrator.** Create one local Trustelem user with administration rights that is
   not linked to AD, enrol two factors on it, store its rescue path offline.
2. **Admin console authentication level.** The project plan step is "Select 2 factors for
   Trustelem admin accesses" (the exact setting location is not documented; it sits with the
   security settings). Source: [summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary).
3. **Internal network.** "the internal IPs must be defined on Security settings / General /
   Internal network. Internal IPs are usually the public IPs of the company offices." This
   drives the internal versus external zone of web access rules and is required for IWA.
   Source: [access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules).
4. **Default authentication level.** "Security settings / General / Default authentication level
   for users" is the value applied when an app rule says *Default*. Set it to 2 factors for a
   PAM tenant. Source: [access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules).
5. **Password policy** for Trustelem local users: "3 security levels : None - Medium - High";
   Medium is a zxcvbn score of 3, High a score of 4, plus a minimum length you define and a
   dictionary of tenant-specific words. Choose High.
   Source: [password levels](https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-password-levels).
6. **Authentication factors.** Enable WALLIX Authenticator, TOTP and second-step passkeys; leave
   SMS (extra cost) and e-mail OTP (weak) off. Details in chapter 06.
7. **Firewall and proxy rules for the agents** (section 4).
8. **Alerts recipients.** All administrators receive alert e-mails (rescue codes, help
   requests); make sure the admin group is a distribution list that is monitored.
   Source: [summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary).

## 4. Network prerequisites for every connector

Verbatim rules from the
[connectors network flows page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows):

- "All traffic is outbound only, over TCP port 443, in TLS, and is always initiated by the
  connector".
- "Write your rules against these DNS names, not against IP addresses": `*.trustelem.com`,
  `relay-fr-01.wallix.com`, `relay-fr-02.wallix.com`.
- IP fallback list: 185.4.44.22, 185.4.46.20, 185.4.46.21, 185.4.46.22; relays 98.66.169.89 and
  20.39.241.157.
- New addresses for `*.trustelem.com` "active on 29 September 2026": 185.4.44.114 and
  185.4.44.117. "Authorize them now, in addition to the addresses already in place: add them, do
  not replace the existing ones".
- Proxy: it "must allow the CONNECT method to these destinations on port 443, and the proxy must
  not intercept the TLS session" because "The connector authenticates the server with a pinned
  certificate".
- Checks: `nslookup admin.trustelem.com`, `nslookup connect.trustelem.com`, then
  `./connect check <sync id> [http://proxy:3128]` (see chapter 03). "A ping is not a valid test."
- "After changing a firewall, proxy or DNS rule, restart the connector service to confirm that
  it can reconnect".

ADConnect additionally needs TCP 389 or 636 to a domain controller when the VM is not a
domain-joined Windows server.
Source: [ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect).

## 5. Availability and support facts

- Availability history published by the vendor: above 99.99 % for 2016 to 2022, 99.94 % in 2023
  with 50 minutes of planned maintenance for a datacenter migration.
  Source: [unavailability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability).
- Incident log with root causes (for example 2026-01-05, storage failure at the hosting
  provider). Source: [incidents](https://trustelem-doc.wallix.com/books/trustelem-news/page/incidents).
- Not documented: contractual SLA, tenant export or backup, data retention policy, maintenance
  windows, status page. Ask WALLIX (see the vendor questions in the architecture report).
- Features enabled on request through WALLIX support or sales: the API, delegated
  administration and custom themes.
  Sources: [API](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api),
  [delegated administration](https://trustelem-doc.wallix.com/books/trustelem-administration/page/delegated-administration),
  [custom themes](https://trustelem-doc.wallix.com/books/trustelem-administration/page/custom-themes).

## 6. Order of work for a PAM tenant

1. Tenant hardening (this chapter).
2. ADConnect on two VMs and the AD directory sync (chapter 02).
3. Factor enrollment campaign for the PAM groups (chapter 06).
4. Trustelem Connect on two VMs with the Bastion and Access Manager services (chapter 03).
5. Bastion integration (chapter 04) and Access Manager integration (chapter 05).
6. Access rules per group, pilot first (chapter 06).
7. SIEM export, API keys, certificate expiry monitoring (chapter 07).
