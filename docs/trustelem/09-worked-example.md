# Worked example: one tenant, one Bastion pair, one Access Manager farm

> - **Purpose:** every field of chapters 01 to 06 filled in for one fictitious organisation, so
>   that the values can be checked side by side and copied as a template.
> - **Audience:** PAM architects and the engineers who configure Trustelem, the Bastion and
>   Access Manager.
> - **Verified:** 2026-09-24, against the Trustelem applications book as read on 2026-09-24 and
>   the Bastion 12.4.3 and Access Manager 6.0.5 customer guides behind the doc.wallix.com login.
> - **Sources:** [Bastion app](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion),
>   [Access Manager app](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager),
>   [Bastion SAML](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml),
>   [Bastion Admin Guide](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
>   [AM Admin Guide](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf),
>   [doc.wallix.com](https://doc.wallix.com/) (Bastion 12.4.3 and Access Manager 6.0.5 guides).

All names, addresses and secrets are invented. The field names and rules come from the vendor
pages cited in the chapters. Each section links to the document that owns the rule behind the
values; the tests that validate them are in [10 Test plan](10-test-plan.md).

## 1. The organisation

Acme Industries runs one Trustelem tenant, one Bastion pair and one Access Manager farm.

| Item | Value |
|------|-------|
| Company | Acme Industries |
| Trustelem tenant | `acme` (`https://acme.trustelem.com`, `https://admin-acme.trustelem.com`) |
| Active Directory | forest `corp.acme.example`, domain controllers `dc1.corp.acme.example` (10.10.1.11) and `dc2` (10.10.1.12) |
| PAM groups in AD | `PAM-Admins`, `PAM-Operators`, `PAM-Auditors`, `PAM-Automation` |
| Partner users (no AD) | Trustelem group `Partners` |
| Bastion nodes | `bastion-1.corp.acme.example` 10.10.20.21 (primary master), `bastion-2` 10.10.20.22 |
| Bastion front-end name | `bastion.corp.acme.example` 10.10.20.20 (L4 load balancer, 22 and 3389, preserving the client source address so that the RADIUS Framed-IP-Address and the Trustelem MFA session see the user's own IP) |
| Access Manager nodes | `am-1` 10.10.20.31, `am-2` 10.10.20.32 on the administration interface, which also carries the replication tunnel (SSH 2242); user access interfaces 10.10.22.31 and .32 |
| Access Manager URL | `https://pam.acme.example/wabam` (L7 load balancer 10.10.20.30) |
| Trustelem Connect VMs | `tconnect-1` 10.10.21.41, `tconnect-2` 10.10.21.42 (administration network) |
| ADConnect VMs | `adconnect-1` 10.10.21.51, `adconnect-2` 10.10.21.52 |
| Federated domain name | `TRUSTELEM` (identical on the Bastion authentication domain, the Access Manager SAML domain and the Trustelem Access Manager app; rule in [SAML assertion and naming](../reference/saml-assertion-and-naming.md)) |
| Access Manager organization | identifier `acme` |

## 2. Trustelem console

The tenant has one AD directory, two Connect services (one per VM) with the same three
listeners, two apps and one rule set.

### Directories

Field meanings are in [02 Directory sync with ADConnect](02-directory-sync-adconnect.md).

| Field | Value |
|-------|-------|
| Directory name | `Acme AD` |
| Use a connector | checked |
| Synchronization ID | `2jy34wpcohrhdytr6hutym6qfi2l7nnw` (example format) |
| Connectors | `adconnect-1` priority 1, `adconnect-2` priority 2 |
| Service account | `svc-trustelem-ad@corp.acme.example`, read-only |
| Groups synchronised | `PAM-Admins`, `PAM-Operators`, `PAM-Auditors`, `PAM-Automation` |
| Custom attributes | `sAMAccountName`, `userPrincipalName`, `memberOf` |
| Login attribute | `sAMAccountName`, so the RADIUS User-Name and the SAML `uid` are both `jdoe`; with UPN logins set the Bastion primary-domain option ON instead (chapter 04) |
| Frequency | the shortest interval the domain controllers tolerate |

`config.ini` on `adconnect-1` (Linux):

```ini
sync_id = 2jy34wpcohrhdytr6hutym6qfi2l7nnw
state_dir = run/
ldap_addr = ldaps://dc1.corp.acme.example?tls_verify
ldap_port = 636
ldap_user = svc-trustelem-ad@corp.acme.example
ldap_password = <from the secret manager>
```

### Services (Trustelem Connect)

Listener ports follow [03 Trustelem Connect](03-trustelem-connect.md); the SIEM target follows
[07 Operations](07-operations.md), section 2.

| Service | VM | Applications and listeners |
|---------|----|----------------------------|
| `tconnect-1` | 10.10.21.41 | Bastion: RADIUS `*:1812`, LDAP `*:2001` (LDAPS off, StartTLS from the Bastion); Access Manager: RADIUS `*:2812` |
| `tconnect-2` | 10.10.21.42 | same listeners |

`config.ini` on `tconnect-1` (Linux), with the SIEM target:

```ini
service_id = 5kd82nwqzr7hxa4tm2ybc9ef3guvl6op
state_dir = run/
outgoing_allowed = "true"
[target.siem]
addr = "siem.corp.acme.example"
port = "5514"
```

### Apps

App settings follow [04 Bastion integration](04-bastion-integration.md) and
[05 Access Manager integration](05-access-manager-integration.md).

| App | Template | Settings |
|-----|----------|----------|
| `Acme Bastion` | WALLIX Bastion | LDAP on (service account `trustelem`, base DN `DC=acme,DC=trustelem,DC=com`), Radius on (secret `R1` from the model), MFA session 8 h |
| `Acme Access Manager` | WALLIX Access Manager | Root URL `https://pam.acme.example/wabam`, Organization identifier `acme`, Domain `TRUSTELEM`, SAML on, Radius on (secret `R2`), custom script below |

Access Manager app custom script:

```javascript
msg.setAttr("profile","User")
for (let group in groups) {
  if(group=="PAM-Admins"){msg.setAttr("profile","Administrator")}
  if(group=="PAM-Auditors"){msg.setAttr("profile","Auditor")}
}
for (let g in groups){ msg.addAttr("groups",g); }
```

### Security settings

Factor and passkey choices follow [06 MFA and access rules](06-mfa-and-access-rules.md),
sections 1 to 3.

| Setting | Value |
|---------|-------|
| Authentication factors | WALLIX Authenticator (Login on, User can reset token: `PAM-Operators` only), TOTP (Login on), Second-step passkey (Login on); SMS and e-mail off |
| Passkey policy | Strict for `PAM-Admins`, Recommended for others |
| Internal network | `203.0.113.0/24` (office egress) |
| Default authentication level for users | 2 factors |
| Password level (local users) | High, minimum 14 characters |
| Admin console | 2 factors |
| Application certificate | `acme-saml-2026`, expiry noted in the operations calendar |

### Access rules

The rule set of [06 MFA and access rules](06-mfa-and-access-rules.md), section 7, applied to
the Acme groups.

| App | Target | Web internal | Web external | LDAP | RADIUS |
|-----|--------|--------------|--------------|------|--------|
| Acme Access Manager | `PAM-Admins`, `PAM-Operators`, `PAM-Auditors` | 2 factors | 2 factors | | 2nd factor only |
| Acme Access Manager | everyone | Forbidden | Forbidden | | Forbidden |
| Acme Bastion | `PAM-Admins`, `PAM-Operators`, `PAM-Auditors` | | | | 2nd factor only |
| Acme Bastion | `PAM-Automation` | | | | Always allow |
| Acme Bastion | `Partners` | | | 1 factor | 2nd factor only |
| Acme Bastion | everyone | | | Forbidden | Forbidden |

## 3. Bastion (configured on `bastion-1`, replicated to `bastion-2`)

The Bastion has one AD domain with RADIUS as secondary authentication, one LDAP domain for
partners and one SAML domain for Access Manager ([04 Bastion integration](04-bastion-integration.md),
scenarios A, C and D).

### External authentications

| Name | Type | Values |
|------|------|--------|
| `CORP-AD` | Active Directory | server `dc1.corp.acme.example`, port 389, StartTLS with the corporate CA, bind `svc-bastion-ldap@corp.acme.example`, base DN `dc=corp,dc=acme,dc=example`, login attribute `sAMAccountName`, user name attribute `sAMAccountName`, timeout 30 |
| `Trustelem-RADIUS-1` | RADIUS | server 10.10.21.41, port 1812, timeout 50, secret `R1`, "Use mobile device for 2 factor authentication(2FA)" ON, "Use primary domain name for two-factor authentication (2FA)" OFF (logins are sAMAccountName, section 2) |
| `Trustelem-RADIUS-2` | RADIUS | server 10.10.21.42, same values |
| `Trustelem-LDAP` | Active Directory | server 10.10.21.41, port 2001, StartTLS, bind method simple, user `trustelem`, password from the Bastion app model, base DN `DC=acme,DC=trustelem,DC=com`, login and user name attribute `mail` |
| `Trustelem-SAML` | SAML | IdP metadata from the `Acme Access Manager` app; claims Username `uid`, Display name `displayname`, Email `email`, Group `groups`; SP entity ID left as generated (Access Manager is the front door); timeout 900 |

### Authentication domains

| Domain server name | Authentication domain name | Directory | Secondary authentication | Default domain | Notes |
|--------------------|----------------------------|-----------|--------------------------|:-:|-------|
| `CORP` | `corp.acme.example` | `CORP-AD` | `Trustelem-RADIUS-1`, `Trustelem-RADIUS-2` | yes | group attribute `memberOf`, default email domain `acme.example`; if Kerberos is enabled (test B-11) the Authentication domain name "must exactly match the Kerberos realm" in upper case, `CORP.ACME.EXAMPLE` (Bastion Administration Guide 7.2.1.2, 7.2.5.2) |
| `PARTNERS` | `partners` | `Trustelem-LDAP` | `Trustelem-RADIUS-1`, `Trustelem-RADIUS-2` | no | default email domain left empty |
| `TRUSTELEM` | `TRUSTELEM` | protocol `Trustelem-SAML` (Other IdPs) | none | no | label "Trustelem", default email domain `acme.example`, Force authentication off |

### Mappings

| Domain | External group value | Bastion user group | Profile |
|--------|----------------------|--------------------|---------|
| `CORP` | `CN=PAM-Admins,OU=Groups,DC=corp,DC=acme,DC=example` | `pam-admins` | `product_administrator` |
| `CORP` | `CN=PAM-Operators,OU=Groups,DC=corp,DC=acme,DC=example` | `pam-operators` | `user` |
| `CORP` | `CN=PAM-Auditors,OU=Groups,DC=corp,DC=acme,DC=example` | `pam-auditors` | `auditor` |
| `CORP` | `CN=PAM-Automation,OU=Groups,DC=corp,DC=acme,DC=example` | `pam-automation` | `user` |
| `PARTNERS` | `CN=Partners,OU=Groups,DC=acme,DC=trustelem,DC=com` (case as in Trustelem; the Bastion compares mappings case-insensitively, Administration Guide 7.2.1.3) | `partners` | `user` |
| `TRUSTELEM` | `PAM-Admins` | `pam-admins` | `product_administrator` |
| `TRUSTELEM` | `PAM-Operators` | `pam-operators` | `user` |
| `TRUSTELEM` | `PAM-Auditors` | `pam-auditors` | `auditor` |

### Other Bastion settings

| Item | Value |
|------|-------|
| API key for Access Manager | name `access-manager`, profile `wallix_access_manager_session_audit`, IP limitation `10.10.20.31,10.10.20.32` |
| Auditor login for AM session search | `am-auditor` (local, profile `auditor`, IP-restricted) |
| Break-glass | `bg-admin`, local password, profile `product_administrator`, source IP restricted to `10.10.21.0/24` |
| One time password ttl (each node: Configuration options do not replicate) | 30 s |
| SIEM integration (each node) | `siem.corp.acme.example`, TLS, RFC 5424, all filters enabled as WALLIX recommends ([System Operations Guide 12.4.3](https://doc.wallix.com/) 13.6) |

## 4. Access Manager (organization `acme`)

Access Manager uses Trustelem as its SAML identity provider, reaches both Bastions through one
cluster, and keeps RADIUS as a fallback for local administrators
([05 Access Manager integration](05-access-manager-integration.md)).

### SAML Identity Provider `Trustelem`

| Tab | Field | Value |
|-----|-------|-------|
| Service Provider | WALLIX-AM Entity ID | `WALLIX-AM` |
| Service Provider | Sign Messages / Encrypt Messages | OFF / OFF |
| Service Provider | Signed Response / Signed Assertion | ON / ON |
| Service Provider | Authent. Expir. Delay | 5 minutes |
| Identity Provider | metadata | imported from the `Acme Access Manager` app |
| Identity Provider | Redirect Logout Uri | `https://acme.trustelem.com/app/<ID>/on_logout` |
| Domain | Domain Name | `TRUSTELEM` |
| Domain | Login / Display Name / Email / Language / Profile | `uid` / `displayname` / `email` / `lang` / `profile` |
| Domain | Default Profile | User |

### Bastions

| Field | `bastion-1` | `bastion-2` |
|-------|-------------|-------------|
| Host | 10.10.20.21 | 10.10.20.22 |
| API key | `access-manager` | same key |
| Cluster | `acme-bastions` | `acme-bastions` |
| Strip Domain | OFF | OFF |
| Allow Session Search / Login | ON / `am-auditor` | ON / `am-auditor` |

**Settings > Application Settings**: `bastion.cluster.identical.mode` on,
`bastion.connection.timeout` 5.

### RADIUS server `Trustelem` (fallback path for local administrators)

Host 10.10.21.41 (and a second entry for 10.10.21.42), Protocol PAP, port 2812, timeout at the
default (raise to 45 to 60 s only if push in the factor chain is confirmed, gap A4),
Login type simple login, secret `R2`, NAS Identifier empty. Local domain: Local database
Factor 1, RADIUS Factor 2.

### Farm

The farm procedure is in the [Access Manager farm runbook](../runbooks/access-manager-farm.md).

Access Manager 6.0.5: `wallix-replication --create-conf-file` (Master/Master) on `am-1` with
`am-2` as the other node, then `--install` and `--monitoring`; the replication installation
copies what the manual farm procedure used to copy. On each node, because appliance
configurations are not replicated: Proxyma `trusted_proxies` set to the load balancer
10.10.20.30 in `/etc/proxyma/config.toml`, and "Limit the number of parallel connections per IP"
deactivated ([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) ch. 6, Administration Guide 8.4.5.1
and 8.5.2). On Access Manager 5.2 the same design used `web.proxy.trusted-proxies=10.10.20.30`
in `wabam.properties`, copied `crypto.install.key`, `db.connections*` and `user.admin*` by hand,
and set `purge.audit.active=true` on `am-1` only.

## 5. How the users log in

Each row is one population on one path; users such as `jdoe` use several paths. Only `bg-admin`
logs in without Trustelem. What users see is in
[11 User and help-desk guide](11-user-and-helpdesk-guide.md).

| User | Path | What happens |
|------|------|--------------|
| `jdoe` in `PAM-Operators` | browser to `https://pam.acme.example/wabam/acme` | redirect to `acme.trustelem.com`, AD password via ADConnect, push on the phone (passkey offered on the web), portal shows the `pam-operators` authorizations of `jdoe@TRUSTELEM`, RDP launches without a prompt |
| `jdoe` | `mstsc` to `bastion.corp.acme.example` | login `jdoe@corp.acme.example`, AD password checked by the Bastion, RADIUS request to `tconnect-1` with an empty password, push approved, session; next connection within 8 h on the same network is not prompted |
| `svc-backup` in `PAM-Automation` | scripted SFTP to the Bastion | AD password only, because its group rule is *Always allow* |
| `p.martin@partner.example` in `Partners` | browser to the portal | Trustelem password (local user) and push. Not covered by sections 2 and 4, which configure the AD path only: the vendor procedure for Trustelem local users is a second Access Manager app with Domain `partners` and Login `email` and a second Access Manager SAML identity provider (chapter 05 section 3). Native RDP/SSH: the Bastion `PARTNERS` LDAP domain (scenario C) with the Trustelem group DN mapping |
| `bg-admin` | Bastion web UI from the admin network | local password, no MFA, used only when Trustelem is unreachable |

## 6. Consistency checks before go-live

Check these values on all sides before the first test. The rules behind them are in
[SAML assertion and naming](../reference/saml-assertion-and-naming.md) and, for the egress
destinations, [01 Tenant setup](01-tenant-setup.md), section 4.

- `TRUSTELEM` appears identically in: Trustelem Access Manager app Domain; Access Manager SAML
  Domain Name; Bastion `Domain server name` and `Authentication domain name`.
- Trustelem Login attribute `uid` equals the Bastion SAML Username claim `uid`.
- The `groups` script is present on the Access Manager app and the values match the Bastion
  `TRUSTELEM` domain mappings exactly (case-insensitive on the Bastion side).
- RADIUS secrets `R1` and `R2` match the Bastion and Access Manager entries; listeners bound
  to `*`; ports 1812 and 2812 not in conflict on the Connect VMs.
- "Use mobile device for 2 factor authentication(2FA)" ON on both Bastion RADIUS entries.
- Access rules exist before any test (LDAP 1 factor for `Partners`, RADIUS 2nd factor only for
  the AD groups).
- Egress firewall allows the Connect and ADConnect VMs to `*.trustelem.com`,
  `relay-fr-01.wallix.com` and `relay-fr-02.wallix.com`, including 185.4.44.114 and
  185.4.44.117, with those destinations excluded from TLS inspection.
