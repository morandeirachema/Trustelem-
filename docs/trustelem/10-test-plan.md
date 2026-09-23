# Test plan

Date: 2026-09-23. Each test has an identifier, preconditions, steps, the expected result and
the evidence to keep (the log line or screen that proves it). Values refer to the
[worked example](09-worked-example.md). Log formats are described in the
[logging and SIEM reference](../reference/logging-and-siem.md).

Evidence conventions: TL = Trustelem Logs page entry (or SIEM JSON record); WA = Bastion
syslog `[wabauth]` line; WD = Bastion `[wabaudit]` line; AM = Access Manager `access.log` or
audit log entry.

## 1. Connectivity and agents

| ID | Precondition | Steps | Expected | Evidence |
|----|--------------|-------|----------|----------|
| C-01 | Connect VM installed | `./connect check <service id>` on each Connect VM | `CommOK: true` ("The flows are correct"), neither `Network: false` nor `CanTLS: false`, `RemoteIP` shows the egress address | command output saved |
| C-02 | ADConnect installed | Directories page, connector table | both connectors listed with IP, server name and service account; LED green | screenshot |
| C-03 | Firewall rules applied | `nslookup admin.trustelem.com`, `nslookup connect.trustelem.com`; block 185.4.44.22 temporarily on a test VM | names resolve; the connector reconnects through the other addresses | firewall log |
| C-04 | Both Connect VMs on | Services page | both services on, listeners 1812, 2001, 2812 visible with the eye button | screenshot |
| C-05 | ADConnect running | Dashboard | user count per directory equals the members of the four PAM groups | screenshot |

## 2. Directory and enrollment

| ID | Precondition | Steps | Expected | Evidence |
|----|--------------|-------|----------|----------|
| D-01 | C-05 | open user `jdoe` in Users | attributes `sAMAccountName`, `userPrincipalName`, `memberOf` present | screenshot |
| D-02 | enrollment campaign on `PAM-Operators` | `jdoe` logs in to `https://acme.trustelem.com` | enrollment window appears; WALLIX Authenticator enrolled | TL enrollment event |
| D-03 | passkey policy Strict on `PAM-Admins` | admin enrols a YubiKey, then tries a synced passkey | hardware key accepted; synced passkey refused | TL events |
| D-04 | user in `PAM-Admins` and a local Trustelem account with the same e-mail | sync runs | accounts merged; AD password wins | TL, Users page |

## 3. Bastion RADIUS (native path)

| ID | Precondition | Steps | Expected | Evidence |
|----|--------------|-------|----------|----------|
| B-01 | chapter 04 scenario A configured | `jdoe` opens the Bastion web UI, domain `corp.acme.example`, AD password | page announces the push; push approved; session opened | WA `status="success"`, TL RADIUS 2nd factor |
| B-02 | B-01 | `mstsc` to `bastion.corp.acme.example`, login `jdoe@corp.acme.example` | RDP proxy login screen, push, target list | WA, TL |
| B-03 | B-01 | OpenSSH client to the proxy | keyboard-interactive prompt, push approved, shell | WA, TL |
| B-04 | B-02 within the MFA session (8 h, same network) | second `mstsc` connection | no push requested | TL shows no new 2nd-factor request |
| B-05 | B-01 | reject the push | Bastion refuses the login | WA `status="failure"`, TL rejected |
| B-06 | B-01 | wrong AD password | refused before any RADIUS request | WA failure, no TL RADIUS entry |
| B-07 | `svc-backup` rule *Always allow* | scripted SFTP | succeeds with the AD password only | WA success, TL "always allow" |
| B-08 | user in no PAM group | login attempt | refused (rule Forbidden or no rule) | TL forbidden or not found |
| B-09 | B-01 | stop `tconnect-1` | Bastion falls back to `tconnect-2` within the RADIUS timeout | WA success after delay, TL from Connect 2 |
| B-10 | B-09 | stop both Connect VMs | login fails at the second factor; `bg-admin` still logs in from the admin network | WA failure; WA success for `bg-admin` |
| B-11 | Kerberos enabled on the RDP proxy | `mstsc` without the `.rdp` parameters, then with `enablecredsspsupport:i:0` and `authentication level:i:2` | first attempt fails, second reaches the login screen | client screenshots |
| B-12 | scenario B local user with RADIUS only | login with the Trustelem password and TOTP | success; with both local password and RADIUS selected the password alone succeeds (documented behaviour) | WA |
| B-13 | scenario C `PARTNERS` domain | Bastion "Test authentication" on `Trustelem-LDAP` | "Authentication success" | screenshot |
| B-14 | B-13 | `p.martin@partners` logs in | Trustelem password, push, mapped to `partners` | WA, TL LDAP bind and RADIUS |
| B-15 | B-13 | mapping DN with wrong case | login fails | WA failure (then fix the case) |

## 4. Access Manager SAML (web path)

| ID | Precondition | Steps | Expected | Evidence |
|----|--------------|-------|----------|----------|
| A-01 | chapter 05 section 2 configured | open `https://pam.acme.example/wabam/acme?domain=TRUSTELEM` | redirect to `acme.trustelem.com/app/<ID>/sso` | browser address bar, SAML tracer |
| A-02 | A-01 | AD password and push (or passkey) | portal shows the authorizations of `jdoe@TRUSTELEM` | AM login entry; WA success "identified with" the SAML domain |
| A-03 | A-02 | launch RDP and SSH from the portal | sessions open without a Bastion prompt; audit shows the AM node address as client | Bastion session audit |
| A-04 | A-02 | user in `PAM-Admins` | lands with the Administrator profile | AM audit |
| A-05 | A-02 | log out | browser reaches the `on_logout` endpoint | address bar |
| A-06 | A-02 | SAML tracer capture | assertion signed by `acme-saml-2026`; attributes `uid`, `displayname`, `email`, `lang`, `profile`, `groups` | capture (signature redacted) |
| A-07 | skew test on a lab node with the clock 10 minutes off | login | fails; restores after NTP fix | AM SAML DEBUG log |
| A-08 | Signed Assertion switched OFF in a lab | login with a tampered assertion | must be refused on 5.2.7 / 6.0.4 and later; switch back ON | AM log |
| A-09 | stop `am-1` | new login through the load balancer | lands on `am-2`; sessions on `am-1` dropped | LB health log |
| A-10 | Strip Domain switched ON by mistake | login | authorizations empty (login without `@TRUSTELEM` does not match); switch OFF | AM, WA |
| A-11 | Access Manager RADIUS server | local administrator logs in | password then TOTP in the second "Password" field | AM login entry, TL |

## 5. Trustelem operations

| ID | Precondition | Steps | Expected | Evidence |
|----|--------------|-------|----------|----------|
| O-01 | SIEM target configured | perform B-01 | JSON record arrives within 30 s | SIEM index |
| O-02 | API enabled | call the `listPerms` script from an allowed IP and from a blocked IP | allowed returns JSON; blocked refused | HTTP responses |
| O-03 | new application certificate created | switch the AM app to it, re-import metadata on AM and Bastion | login works; old certificate retired | A-06 with the new certificate |
| O-04 | user lost the phone | request a rescue code, admin releases it from Alerts | one-time code accepted within 24 h; re-enrolment | TL, Alerts page |
| O-05 | RADIUS secret rotation | change on the app model, then on both Bastion entries and the AM server | B-01 passes; during the window Connect 2 still serves | WA |
| O-06 | ADConnect upgrade | install new version on a third path, reorder priority, disable old | sync continues; no failed logins | Dashboard, TL |

## 6. Cluster behaviour

| ID | Precondition | Steps | Expected | Evidence |
|----|--------------|-------|----------|----------|
| H-01 | Bastion replication installed | `bastion-replication --status` on `bastion-1` | both nodes in sync | command output |
| H-02 | H-01 | add a mapping on `bastion-1` | visible on `bastion-2` within seconds | WD on both nodes |
| H-03 | H-01 | `bastion-2` unreachable | logins via the load balancer continue on `bastion-1`; AM cluster stops using `bastion-2` after `bastion.connection.timeout` | AM log, LB log |
| H-04 | AM replication installed | create a SAML IdP on `am-1` | present on `am-2` | AM audit on both |

## 7. Exit criteria

All C, D, B (except B-11 if Kerberos is not enabled), A and H tests pass; O tests are
executed at least once before go-live and again after every rotation or upgrade. Failures are
triaged with [08 Troubleshooting](08-troubleshooting.md).
