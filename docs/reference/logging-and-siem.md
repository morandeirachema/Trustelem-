# Logging and SIEM reference for the Trustelem-Bastion-Access Manager platform

Date: 2026-09-23. Sources: [WALLIX Splunk add-on](https://github.com/wallix/Splunk-add-on)
(README and `default/props.conf`), [Sekoia WALLIX Bastion intake](https://docs.sekoia.com/integration/categories/iam/wallix/),
[Bastion 12.3.2 Functional Administration Guide](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
[Access Manager 5.2.4.0 Administration Guide](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf),
[Trustelem on-premise SIEM](https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem),
[Trustelem API](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api).

## 1. Sources and transport

| Source | Transport | Format | Retention at source |
|--------|-----------|--------|---------------------|
| Trustelem | push through Trustelem Connect to an on-premise target, every 30 s, queued on error | JSON (recommended) or syslog | 30 days in the console and API |
| Bastion nodes | System > SIEM integration: syslog UDP or TCP, RFC 3164 with ISO timestamps; categories configuration changes, authentication logs, account activities, SSH proxy events, RDP proxy events, SSH, RDP and VNC sessions; "only displayed when the SIEM functionality is associated with the license key" | key=value inside a bracketed event tag | local audit logs in the GUI; audit tables are not replicated between nodes |
| Access Manager nodes | no native forwarder; ship `/var/log/wallix/wabam/{access,error,tech}.log` with an OS agent | Apache-style access log, application logs | rotation on the appliance |
| Agents (ADConnect, Trustelem Connect) | OS logs only | | |

## 2. Bastion event format

Splunk sourcetype `WB:syslog` extracts the bracketed tag as `WB_Event` (values seen:
`wabauth`, `wabaudit`, `SSH Session`, `RDP Session`, `sshproxy`, `Vault Activity`) and
key=value pairs such as `action`, `user`, `client_ip`, `status`, `infos`, `type`, `object`,
`session_id`, `target_ip`, `device`, `service`, `account`, `duration`, `command_line`, `data`.

Examples (Sekoia samples):

```
[wabauth] action="authentify" user="admin" client_ip="1.1.1.1" status="success" infos="diagnostic [Authentication success: identified with local(LOCAL), authentified with: API key Bastion(APIKEY).]"
[wabauth] action="authentify" user="username123" client_ip="1.1.1.1" status="failure" infos="diagnostic [Authentication failed]
[SSH Session] session_id="1830cbf7a55a11dd005056b01296" client_ip="1.1.1.1" target_ip="ip-foo-bar-baz.corp.net" user="user1" device="DEVICE-FOO" service="SSH" account="username" type="SESSION_ESTABLISHED_SUCCESSFULLY"
[RDP Session] session_id="19662b5f..." client_ip="1.1.1.1" target_ip="192.0.2.1" user="test@test.fr" device="example.com" service="RDP" account="test@test.fr" type="NEW_PROCESS" command_line="\"C:\\Windows\\system32\\test_script.exe\""
[Vault Activity] type="Vault" action="checkin" user="test@test.fr" account="user1" vault="local" session="True" result="Checkin successful"
[wabaudit] action="add" type="LdapMapping" object="<QA_DOMAIN_1, OU=Group> in user_group_154954913825 GROUP" user="user1" client_ip="10.10.45.212" infos="ldapGroup [OU=Group], domain [QA_DOMAIN_1], group [user_group_154954913825]"
[wabaudit] action="add" type="UserAuth" object="QA_USER_AUTH_KERBEROS" user="admin" client_ip="10.10.45.212" infos="wabAuthType [KERBEROS], description [], port [88], host [10.10.45.148], kerDomControler [QA.IFR.LAN]"
[wabaudit] action="add" type="Apikey" object="apikey_154954880399" user="user1" client_ip="10.10.45.212" infos="cn [apikey_154954880399], apikey [********], ipLimitation []"
```

`wabaudit` `type` values include ConnectionPolicy, Ldapdomain, LdapMapping, UserAuth,
Usergroup, Profile, Apikey, Authorization, Approval, Backup/Restore, Cluster, Device,
sessionlog and more; actions add, edit, delete, list, backup, restore, download.

The `infos` diagnostic on `wabauth` names the identification source and the authentication
method (for example `identified with local(LOCAL), authentified with: API key`). A RADIUS
second factor appears in the same line as the method; a SAML user through Access Manager is
identified in the SAML domain.

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
| user | `userEmail` (local users) or the login attribute imported from AD (`uid`) | `user=` (login, or `login@DOMAIN` for federated users) | login in the audit log and `access.log` |
| client address | `ip` (public IP seen by Trustelem; for RADIUS the Framed-IP-Address sent by the Bastion) | `client_ip=` (the AM node address for portal sessions) | client address from `X-Forwarded-For` when trusted proxies are configured |
| session | Trustelem session id (console Sessions page) | `session_id=` | session in `access.log` |
| time | UTC in JSON | ISO timestamp with offset | server time zone |

Keep NTP on every node; SAML validation and correlation both depend on it.

## 5. Detection rules for the MFA design

| Rule | Logic |
|------|-------|
| MFA push fatigue | more than N Trustelem second-factor requests for one user in M minutes with rejections or timeouts, or N Bastion `wabauth` failures for the same user from the same `client_ip` |
| MFA silently disabled | Bastion `wabaudit` edit on type `Ldapdomain` whose `infos` no longer lists the RADIUS secondary authentication; Trustelem permission change to *Always allow* |
| Break-glass use | Bastion `wabauth` success for the local emergency account |
| Federation tampering | Access Manager audit entries for SAML identity provider changes; Bastion `wabaudit` on type `UserAuth` with `wabAuthType [SAML]` |
| API key misuse | `wabauth` success "authentified with: API key" from an address outside the Access Manager farm |
| Connector outage | absence of Trustelem RADIUS log records for more than five minutes during business hours while Bastion reports authentication failures with timeouts |
| Session anomalies | `RDP Session` `NEW_PROCESS` or `KBD_INPUT` matching restriction patterns; `SSH Session` `SESSION_DISCONNECTION` with very short `duration` |

Response hook: the Splunk add-on's kill action calls
`PUT https://<bastion>/api/sessions?session_id=<id>` with body `{"reason": "..."}` and headers
`X-Auth-Key` and `X-Auth-User`.

## 6. Parser and integration references

- Splunk add-on: https://github.com/wallix/Splunk-add-on (`[udp://514] sourcetype = WB:syslog`).
- Sekoia intake: https://docs.sekoia.com/integration/categories/iam/wallix/ (ECS mapping:
  source.ip, destination.ip, user.name, event.action, event.outcome, process.command_line).
- Google SecOps parser: https://docs.cloud.google.com/chronicle/docs/ingestion/default-parsers/wallix-bastion
- FortiSIEM: https://docs.fortinet.com/document/fortisiem/7.6.0/external-systems-configuration-guide/717035/wallix-bastion
- Cortex XSOAR: https://xsoar.pan.dev/docs/reference/integrations/wallix-bastion
