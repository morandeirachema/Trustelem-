# Logging and SIEM reference for the Trustelem-Bastion-Access Manager platform

Date: 2026-09-24. Verified against Bastion 12.4.3 (SIEM Logs Guide, Operation Guide, Deployment
Guide, Auditor Guide), the Bastion 12.0.25 SIEM Logs Guide for version differences, and Access
Manager 6.0.5 (Administration and Deployment Guides); older Access Manager 5.2 statements are
labelled as such. The guides linked to https://doc.wallix.com/ are WALLIX customer documentation
behind the doc.wallix.com login (WALLIX Trustelem SSO); section numbers are given so they can be
found. Other sources: [WALLIX Splunk add-on](https://github.com/wallix/Splunk-add-on)
(README and `default/props.conf`), [Sekoia WALLIX Bastion intake](https://docs.sekoia.com/integration/categories/iam/wallix/),
[Bastion 12.3.2 Functional Administration Guide](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
[Access Manager 5.2.4.0 Administration Guide](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf),
[Trustelem on-premise SIEM](https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem),
[Trustelem API](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api).
The SIEM Logs Guide "lists log examples and is not exhaustive" (1).

## 1. Sources and transport

| Source | Transport | Format | Retention at source |
|--------|-----------|--------|---------------------|
| Trustelem | push through Trustelem Connect to an on-premise target, every 30 s, queued on error | JSON (recommended) or syslog | 30 days through the API ("List all the logs of the 30 previous days"); console retention not documented |
| Bastion nodes | System > SIEM integration, one row per destination: address, "transmission protocol (UDP, TCP, or TLS)", port, "log format (standard RFC 5424 or RFC 3164)"; with RFC 3164 "the timestamp can be in RFC 3164 or ISO (YYYY-MM-DD-HH:MM:SS±TZ)". "Using TLS is strongly recommended" (PEM file with the CA chain). "This feature is only available when the SIEM feature is associated with the license key." Each filter of the SIEM Logs Guide can be enabled or disabled; "WALLIX recommends that you enable all logs and that you filter out the events on your SIEM solution directly." ([Bastion 12.4.3 Operation Guide](https://doc.wallix.com/) 13.6; same text in 12.0.25, 13.5) | syslog, key=value inside a bracketed event tag (section 2) | "The logs are also stored on the local file system" (Operation Guide 13.6): `syslog`, `wabaudit.log`, `wabauth.log` under `/var/log`, purged by "Remove user logs older than", "The maximum retention time for the logs is 365 days or 52 weeks" (Operation Guide 6.5.2); Audit > Authentication history for proxy logins ([Bastion 12.4.3 Auditor Guide](https://doc.wallix.com/) 10); "The audit tables are not replicated" ([Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5, Limitations) |
| Access Manager nodes | see section 1.1 | Apache-style access log, application logs | files for the "ongoing day (static 24h)", downloaded as an archive |
| Agents (ADConnect, Trustelem Connect) | OS logs only | | |

### 1.1 Access Manager log files and forwarding

- Access Manager 6.0.5: "The access log file (access.log) which records connections from
  external clients", "The technical log files (error.log, cli.log, and tech.log)" and the Java
  `hs_err_pid` file, "stored in the following directory: /var/log/wabam"; download from
  Settings > Application Settings, Logs tab ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 9.7, 9.7.1).
- Access Manager 5.2 (older path): `/var/log/wallix/wabam/{access,error,tech}.log`
  ([AM 5.2.4.0 Administration Guide](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)).
- Forwarding is contradictory in the 6.0.5 guides (gap A7). The Deployment Guide network table
  (2.2, Table 4) has a row "Syslog server integration", port "514/UDP", required when "Syslog
  message routing is enabled.", "Configurable in System > SIEM integration."
  ([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 2.2), but the Administration Guide has no SIEM integration page (its System chapter 8.4
  covers Network, context path, time zone and NTP, SNMP and Service control). The table row is
  worded exactly as the Bastion 12.4.3 Deployment Guide row, so it may be a template carry-over
  (*inference*). Until WALLIX confirms, plan to ship the files with an OS agent.

## 2. Bastion event format

Messages carry a bracketed tag followed by key=value pairs ([Bastion 12.4.3 SIEM Logs Guide](https://doc.wallix.com/)).
The Splunk sourcetype `WB:syslog` extracts the tag as `WB_Event` (the add-on dashboards use
`wabauth`, `sshproxy`, `rdpproxy`, `SSH Session`, `RDP Session`). Tags in the guide:

| Tag | Purpose | Key fields | SIEM Logs Guide |
|-----|---------|------------|-----------------|
| `[wabauth]` | primary user authentication | `type="UserAuth"`, `action="authentify"`, `user`, `client_ip`, `status` (started, success, failure, cancel), `infos="diagnostic [...]"` | 2.1 |
| `[Vault Activity]` | account checkout and check-in, credential change | `action` (checkout, checkout extension, checkin, force checkin, credential change), `user`, `account`, `session`, `result`, `reason` | 2.2 |
| `[sessionexport]`, `[sessionimport]` | session log export and import scripts | `action`, `sessions`, `files` | 2.4 |
| `[boot]`, `[wallixplugins]`, `[WABWATCHDOG]` | boot, WindowsService plugin rotation, watchdog | `action`; `account`, `type="SecretRotation"`, `device`, `service`, `result`; free text | 2.5 to 2.7 |
| `[wabaudit]` | configuration changes from the web interface and API | `action`, `type` (object type), `object`, `user`, `client_ip`, `infos` | 3 |
| `[CLI Audit]` | command line tools | `action`, `type` (Backup/Restore, Crypto, Database, SecurityLevel, System), `user`, `infos` | 4 |
| `[sshproxy]`, `[rdpproxy]` | proxy connection and login steps | `psid`, `user`, `type` (INCOMING_CONNECTION, AUTHENTICATION_TRY, AUTHENTICATION_SUCCESS, AUTHENTICATION_FAILURE, TARGET_CONNECTION, TARGET_CONNECTION_FAILED, TARGET_DISCONNECTION, TARGET_ERROR, DISCONNECTION or DISCONNECT, LOGOUT, TIME_METRICS), `method` (Password, SSH Key, OTP), `src_ip`, `session_id`, `target`, `reason`, `primary_authentication` | 5, 7 |
| `[SSH Session]`, `[RDP Session]`, `[VNC Session]` | session content | `type`, `session_id`, `client_ip`, `target_ip`, `user`, `device`, `service`, `account`, plus `duration`, `data`, `command_line`, `pattern`, `command` | 6, 8, 9 |
| `[Web Session]` | Web Session Manager sessions (12.4.3 only) | `type`, `session_id`, `user`, `client_ip`, `target`, `url` | 10 |
| `[sysaudit]` | System menu changes | `action`, `type` (network, remote-storage, route, security-level, service-mapping, siem-dest, smtp, time-service), `object`, `infos` | 11 |
| `[integrity]` | session recording integrity check | `session_uid`, `status` (OK, failed), `type`, `user`, `target`, `begin`, `end` | 12 |

No RADIUS event and no replication event is documented. Approvals appear as `wabaudit` types
`Approval` and `Answer`.

### 2.1 Authentication (`wabauth`)

Format and examples (SIEM Logs Guide 2.1; wrapped lines joined, typographic quotes straightened):

```
[wabauth] type="UserAuth" action="authentify" user="[USER NAME]" client_ip="[USER IP ADDRESS]" status="[AUTHENTICATION STATUS]" infos="diagnostic [INFOS]"
[wabauth] type="UserAuth" action="authentify" user="user_name" client_ip="192.0.2.0" status="started" infos="diagnostic [Authentication started: identified with local(LOCAL).]"
[wabauth] type="UserAuth" action="authentify" user="user_name" client_ip="192.0.2.0" status="success" infos="diagnostic [Authentication success: identified with local(LOCAL).]"
[wabauth] type="UserAuth" action="authentify" user="user_name" client_ip="192.0.2.0" status="success" infos="diagnostic [Authentication success: identified with external-auth-ad(LDAP), authentified with: external-auth-ad(LDAP).]"
[wabauth] type="UserAuth" action="authentify" user="user_name" client_ip="192.0.2.0" status="started" infos="diagnostic [Authentication started: identified with SAML-Trustelem(SAML).]"
[wabauth] type="UserAuth" action="authentify" user="user_name" client_ip="192.0.2.0" status="success" infos="diagnostic [Authentication success: identified with SAML-Trustelem(SAML), authenticated with: SAML-Trustelem(SAML).]"
[wabauth] type="UserAuth" action="authentify" user="user_name" client_ip="192.0.2.0" status="failure" infos="diagnostic [Authentication failed]"
[wabauth] type="UserAuth" action="authentify" user="test" client_ip="172.18.0.1" status="failure" infos="diagnostic [Authentication failed: account locked due to too many failed login attempts]"
[wabauth] type="UserAuth" action="authentify" user="user_name" client_ip="192.0.2.0" status="canceled" infos="diagnostic [Authentication canceled]"
```

What the guide establishes:

- A login produces a `started` line (identification: `identified with {name}({TYPE})`) and then
  a `success`, `failure` or `canceled` line. The status list says `cancel`, the example prints
  `canceled`; match both.
- `user` is "the user name when used as login" or "the value [unknown X username] if the user
  name is not used as login. For example, when authenticating through a X.509 certificate,
  through a Kerberos ticket, or through a provider."
- Failures carry no reason ("Authentication failed"), except the lockout text. The reason for a
  refused second factor must come from Trustelem (section 3).
- Spelling differs by method: "authentified with" (LDAP) and "authenticated with" (SAML, OIDC).
- 12.4.3 adds the same lines for OIDC (`OIDC-Trustelem(OIDC)`).
- The flow examples omit `type="UserAuth"` and may be prefixed by the program name
  (`wabengine: [wabauth] ...` in the SSH flow, 6.9); the RDP flow (8.14) also shows a per-method
  line before the `started` line:
  `[wabauth] action="authentify" user="user_name" client_ip="192.0.2.0" status="success" infos="diagnostic [\'Active Directory\' -password- authentication succeeded]"`
  Parsers must not require `type="UserAuth"` or the prefix.
- The RDP proxy logs a failed one-time password separately:
  `[rdpproxy] psid="154937229523480" user="user_name" type="AUTHENTICATION_FAILURE" method="OTP"` (7).
- Audit > Authentication history lists "the authentication attempts on the RDP and SSH proxy
  interfaces (respectively on ports 3389 and 22)" with a Diagnosis column and CSV export;
  "Authentication attempts with an expired OTP are not attributed to a user and are logged as
  [unknown username]." (Auditor Guide 10). It does not cover web interface logins.

Not documented (gap B6, lab capture needed): the `wabauth` wording for a RADIUS secondary
authentication (success, reject or timeout), for API-key authentication, for Kerberos users and
for Access Manager portal logins. *Inference:* a RADIUS factor adds either a second
"authentified with:" entry or a per-method line similar to the `'Active Directory' -password-`
one. The API-key form is known only from a Sekoia sample:

```
[wabauth] action="authentify" user="admin" client_ip="1.1.1.1" status="success" infos="diagnostic [Authentication success: identified with local(LOCAL), authentified with: API key Bastion(APIKEY).]"
```

### 2.2 Configuration changes (`wabaudit`)

Format: `[wabaudit] action="[ACTION]" type="[OBJTYPE]" object="[UID/CN/NAME]" user="[WHO]" infos="[INFOS]"`
(SIEM Logs Guide 3, quotes straightened); the examples also carry `client_ip`. Values in `infos` are quoted lists and
edits show old and new values (`description ['' to 'DESCRIPTION']`). Examples relevant to this
design:

```
[wabaudit] action="add" type="AuthDomain" object="DOMAIN_1" user="user_name" client_ip="192.0.2.0" infos="cn ['DOMAIN_1'], description [''], auth_domain_name ['domain1'], defaultLanguage ['en'], defaultEmailDomain ['wallix'], groupAttribute ['memberOf'], snAttribute ['displayName'], emailAttribute ['mail'], languageAttribute ['preferredLanguage'], isDefaultDomain [True], client_key_cert [{'certificate': '********', 'private_key': '********'}], enable_ca [False]"
[wabaudit] action="add" type="AuthDomainMapping" object="18dc7079eed7bc40005056b621fb" user="user_name" client_ip="192.0.2.0" infos="local_group ['user_group_154954913825'], external_group ['OU=Group'], is_fallback [False], domain ['DOMAIN_1']"
[wabaudit] action="add" type="UserAuth" object="user_nameUTH_KERBEROS" user="user_name" client_ip="192.0.2.0" infos="wabAuthType ['KERBEROS'], description [''], port [88], host ['10.10.45.148'], kerDomControler ['DOMAIN.IFR.LAN']"
[wabaudit] action="add" type="Apikey" object="apikey_154954880399" user="user_name" client_ip="192.0.2.0" infos="cn ['apikey_154954880399'], apikey ['********'], ipLimitation['']"
```

Object types include Account, Answer, Apikey, Approval, AuthDomain (Auth domain),
AuthDomainMapping, authlog, Authorization, Backup/Restore, Cluster (a cluster of targets, not
the Bastion HA pair), ConfigOptions, ConnectionPolicy, Crypto, Device, Profile, Restriction,
session, sessionlog, SiemLog, User, UserAuth (External authentication), Usergroup; actions
include add, edit, delete, list, view, save, backup, download, restore, terminate, log, Unlock
and Change. The types `Ldapdomain` and `LdapMapping` seen in older Sekoia samples do not appear
in the 12.0.25 or 12.4.3 guides; use `AuthDomain` and `AuthDomainMapping`.

### 2.3 Sessions

Examples (SIEM Logs Guide 6.2, 8.4, 8.6; the Sekoia samples show the same shapes):

```
[SSH Session] session_id="session_identifier" client_ip="192.0.2.0" target_ip="192.0.2.255" user="user_name" device="device_name" service="service_name" account="account_name" type="SESSION_ESTABLISHED_SUCCESSFULLY"
[SSH Session] type="SESSION_DISCONNECTION" session_id="session_identifier" client_ip="192.0.2.0" target_ip="192.0.2.255" user="user_name" device="device_name" service="service_name" account="account_name" duration="9:12:12"
[RDP Session] type="NEW_PROCESS" session_id="session_identifier" client_ip="192.0.2.0" target_ip="192.0.2.255" user="user_name" device="device_name" service="service_name" account="account_name" command_line="C:\\Windows\\system32\\DllHost.exe /Processid:{49F171DD- B51A-40D3-9A6C- 2D674CC729D}"
[RDP Session] type="KBD_INPUT" session_id="session_identifier" client_ip="192.0.2.0" target_ip="192.0.2.255" user="user_name" device="device_name" service="service_name" account="account_name" data=" to connect to remote TCP host."
[Vault Activity] action="checkin" user="user_name" account="account_name" session="False" result="Checkin successful"
```

`duration` "follows the h:mm:ss format" (examples "0:00:07", "16:23:16", "157:45:59"): parse it,
do not compare it as a string. The Sekoia `[Vault Activity]` sample also carries `type="Vault"`
and `vault="local"`, which the guide does not show.

## 3. Trustelem event format

Record fields from the API `Log` type: `id, date, level, msg, details, userID, userEmail, ip,
useragent`. Second-factor events (push accepted or rejected, TOTP, passkey, including
`webauthn_duplicate_credential`) are forwarded with the other events. The LDAP and RADIUS
requests relayed by Trustelem Connect are logged with the application name, which is the way
to correlate a Bastion `wabauth` failure with a Trustelem decision (user not found, no access
rule, no second factor).

## 4. Correlation keys

| Field | Trustelem | Bastion | Access Manager |
|-------|-----------|---------|----------------|
| user | `userEmail` (local users) or the login attribute imported from AD (`uid`) | `user=` (login, or `login@DOMAIN` for federated users); "[unknown X username]" when the user name is not the login (X.509, Kerberos ticket, provider) | login in the audit log and `access.log` |
| client address | `ip` (public IP seen by Trustelem; for RADIUS the Framed-IP-Address sent by the Bastion) | `client_ip=` (the AM node address for portal sessions, *inference*; for Web Session Manager the guide warns it can be the load balancer or reverse proxy) | client address from `X-Forwarded-For` when trusted proxies are configured |
| session | Trustelem session id (console Sessions page) | `session_id=` in session and proxy events; `psid=` is "the same for all actions logged during the same session" of a proxy connection (SIEM Logs Guide 6.9) | session in `access.log` |
| time | UTC in JSON | RFC 5424 timestamp, or RFC 3164 with an RFC 3164 or ISO (±TZ) timestamp, as set per destination | server time zone |

Keep NTP on every node; SAML validation and correlation both depend on it.

## 5. Detection rules for the MFA design

| Rule | Logic |
|------|-------|
| MFA push fatigue | more than N Trustelem second-factor requests for one user in M minutes with rejections or timeouts, or N Bastion `wabauth` `status="failure"` for the same user from the same `client_ip`; `wabauth` gives no reason, so take it from Trustelem; on RDP also `[rdpproxy]` `AUTHENTICATION_FAILURE` `method="OTP"` |
| MFA silently disabled | Bastion `wabaudit` `action="edit"` or `delete` on type `AuthDomain` or `UserAuth` (the RADIUS external authentication); the `infos` attribute that carries the secondary authentication is not documented (*gap*, capture in the lab); Trustelem permission change to *Always allow* |
| Break-glass use | Bastion `wabauth` `status="success"` with `identified with local(LOCAL)` for the local emergency account |
| Federation tampering | Access Manager audit entries for SAML identity provider changes; Bastion `wabaudit` on type `UserAuth` or `AuthDomain`, any action; the SAML value is expected as `wabAuthType ['SAML']` (*inference*, the guide shows only KERBEROS and LDAP) |
| API key misuse | `wabaudit` type `Apikey` add or delete, and `Profile` add or edit (the add example shows `ip_limitation`) (SIEM Logs Guide 3); `wabauth` success "authentified with: API key" from an address outside the Access Manager farm (Sekoia sample only, not in the guide) |
| Connector outage | absence of Trustelem RADIUS log records for more than five minutes during business hours while Bastion `wabauth` failures rise; the guide documents no timeout message, *inference*: proxy `TIME_METRICS` `primary_authentication` durations grow |
| Session anomalies | `RDP Session` `NEW_PROCESS` (`command_line`) or `KBD_INPUT` (`data`); prefer `KILL_PATTERN_DETECTED` and `NOTIFY_PATTERN_DETECTED` (`pattern`, `data`) raised by session restrictions; `SSH Session` `SESSION_DISCONNECTION` with a very short parsed `duration` |

Response hook: the Splunk add-on's kill action calls
`PUT https://<bastion>/api/sessions?session_id=<id>` with body `{"reason": "..."}` and headers
`X-Auth-Key` and `X-Auth-User`; the helper hard-codes `X-Auth-User: admin`, so the key must be
valid for that user. A kill is audited as `wabaudit` `action="terminate"` `type="sessionlog"`
with "reason ['Killed by admin']" in `infos` (SIEM Logs Guide 3).

## 6. Version differences (SIEM Logs Guide 12.0.25 to 12.4.3)

- 12.4.3 adds the OIDC `wabauth` examples and chapter 10, WEBAPP session filters (`[Web Session]`).
- 12.4.3 adds `data=` to RDP and VNC `KILL_PATTERN_DETECTED` and `NOTIFY_PATTERN_DETECTED`,
  VNC clipboard file transfer and ICAP events, and makes `target` optional on `[rdpproxy]`
  `TARGET_ERROR`.
- The 12.4.3 RDP flow example drops the `wabengine:` prefix before `[wabauth]`.
- The System > SIEM integration procedure is the same in both Operation Guides.

## 7. Parser and integration references

- Splunk add-on: https://github.com/wallix/Splunk-add-on (`[udp://514] sourcetype = WB:syslog`).
- Sekoia intake: https://docs.sekoia.com/integration/categories/iam/wallix/ (ECS mapping:
  source.ip, destination.ip, user.name, event.action, event.outcome, process.command_line).
- Google SecOps parser: https://docs.cloud.google.com/chronicle/docs/ingestion/default-parsers/wallix-bastion
- FortiSIEM: https://docs.fortinet.com/document/fortisiem/7.6.0/external-systems-configuration-guide/717035/wallix-bastion
- Cortex XSOAR: https://xsoar.pan.dev/docs/reference/integrations/wallix-bastion
