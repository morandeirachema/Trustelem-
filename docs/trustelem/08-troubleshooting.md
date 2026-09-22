# Trustelem troubleshooting

Date: 2026-09-23. Sources: the Debug chapter of
[LDAP-Radius - Trustelem Connect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect),
[ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect),
[connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows),
[WALLIX Bastion](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion) and
[WALLIX Access Manager](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager) application pages.
Quotes are verbatim.

## 1. First question: is there a log line in Trustelem?

"Go on your Trustelm Logs page and see if you have LDAP or Radius logs. If yes, the connector
is working and you should know why the authentication failed:

- if the user is not found, is the login attribute correct?
- if the user doesn't have the permission for the app, is your access rule correct?
- if the user doesn't have a 2nd factor, is your enrollment process correct?"

No log line at all means the request never reached the cloud: connector, listener, port or
firewall. One documented exception: "If your application tries to do a LDAP search and doesn't
have access rule (LDAP 1 or 2 factors), no users will be found but you will not see any logs
because it is not a bug".

## 2. Connector and network

| Symptom | Check (verbatim where quoted) |
|---------|-------------------------------|
| Connector not listed in the console | "verify the synchronization ID", "verify the proxy setup", on Windows "verify that you clicked on Validate"; run `./connect check <sync id> [http://proxy:3128]` |
| `Network: false` | "The connection could not be opened at all: the traffic is blocked or not routed." |
| `Network: true`, `CanTLS: false` | "The connection reaches the server but the TLS session fails: proxy or TLS inspection." The connector pins the server certificate; exclude `*.trustelem.com` from inspection |
| `CommOK: true` but service shows off | turn the service on in the console ("Turn on the service by clicking on No") |
| Worked yesterday, fails today | DNS or IP change; "After changing a firewall, proxy or DNS rule, restart the connector service"; check the new 185.4.44.114 and .117 addresses active from 2026-09-29 |
| Listener not reachable from the Bastion | "verify if the listen address is correct (should be * if the VM is dedicated to Trustelem)"; "see the port defined and the setup information clicking on the eye button"; local firewall on the VM |
| Need packet evidence | "use Wireshark on Windows or tcpdump on Linux. /!\ tcpdump displays the flow received, before applying local firewall rules." |

## 3. Directory synchronisation

| Symptom | Check |
|---------|-------|
| No groups in "Sync groups" | open the "i" icon: if Server Link shows an error, "verify the flows from the VM running the connector to the Active Directory; verify the service account used for Trustelem AD Connect (UserPrincipalName and password); verify if you have a replication delay between the DC"; otherwise "verify if the service account has the right to search groups" |
| Group appears empty | "If your group is Domain users, it's normal, it can't be used because it is not a real group"; the service account may not read those user objects; DC replication delay |
| User merged with a local account | expected: same UPN or e-mail merges them and "the password to use will be the one from Active Directory" |
| 4th LED red on the Windows installer | expected when a `config.ini` is used on a non-domain host |

## 4. Bastion RADIUS

| Symptom | Check |
|---------|-------|
| Password prompt loops or immediate failure for AD users | "verify if you checked the option Use mobile device on the Radius external authentication" (must be ON for AD users, scenario A) |
| Local user authenticates without MFA | both local password and RADIUS selected: "the Bastion will try the first method (local password)"; select only RADIUS |
| Local user fails with logs in Trustelem | "if the login of the local user is unknown by Trustelem the authentication won't work" (login must be the Trustelem e-mail) |
| Push never arrives, Bastion times out | RADIUS timeout too short (default 5 s); user has no enrolled WALLIX Authenticator; access rule missing |
| User never prompted | user or group rule *Always allow*, or inside the MFA session window on the same network |
| mstsc fails before the login screen | Kerberos enabled on the RDP proxy: add `enablecredsspsupport:i:0` and `authentication level:i:2` to the `.rdp` file, or `/sec:tls` with FreeRDP |

## 5. Bastion LDAP (Trustelem users)

| Symptom | Check |
|---------|-------|
| "Test authentication" fails | bind user `trustelem` and password from the app model; base DN from the app model; port 2001; StartTLS or LDAPS consistent on both sides |
| Users not found | "Trustelem users will not be found by the Bastion before having an access rule (1 or 2 factors)"; login attribute and user name attribute set to `mail` |
| Mapping does not apply | group DN case: "if you don't respect the case, the authentication won't work"; DN pattern `CN=<group>,OU=Groups,DC=<tenant>,DC=trustelem,DC=com` |

## 6. Access Manager RADIUS

- "Verify if the protocol is set to PAP".
- "if the password is not handle by Trustelem, the authentication is login + password (AD,
  local...) then Trustelem TOTP even if the input name is Password again".
- Factor order on the domain: AD (or local database) Factor 1, RADIUS Factor 2; Trustelem rule
  *2nd factor only*.

## 7. Access Manager SAML

Vendor list, verbatim:

- "Verify if the setup is correct: there is a lot of information to copy and paste, and an
  error can quickly happen."
- "Verify the time on Access Manager: SAML assertion are valid for a short period."
- "Verify if the user doesn't already exist. For instance if the SAML domain was used before
  for LDAP authentication, the users may already exist. In these case the authentication will
  not work and it has to be deleted first."
- "Verify the attributes mapped in Access Manager --> reminder: a local Trustelem user must
  have an uid set to email".
- "Verify if the domain used in the SAML setup is the same used on the Bastion for the
  Authentication domain name".
- Then "Download the browser plugin SAML tracer" and enable Access Manager SAML logs at DEBUG
  (Settings > Application Settings > Configuration > SAML), reproduce, download the log
  archive.

Additional checks from the Access Manager guide and release notes:

- Signed Response and Signed Assertion must be ON, Encrypt Messages OFF, Sign Messages OFF
  (a 5.2.x issue drops `SigAlg` when it is ON).
- On a three-interface appliance the SAML URL may be auto-filled with the administration
  interface URL (known issue WAB-4968); correct it to the user-facing FQDN.
- Strip Domain OFF on the Bastion object so `login@domain` reaches the Bastion.
- Access Manager below 5.2.7 or 6.0.4 is vulnerable to a SAML response forgery
  (WSA-2026-07-0002); failures after an upgrade are not a reason to downgrade.

## 8. Escalation data to collect

1. Trustelem: Logs page filtered on the user, service page screenshot (listener, port,
   status), `./connect check` output.
2. Bastion: authentication log lines (`wabauth` events in syslog), the RADIUS external
   authentication settings, the domain's secondary authentication.
3. Access Manager: log archive with SAML at DEBUG, the SAML Identity Provider settings, a SAML
   tracer capture (redact the assertion signature if shared outside the team).
4. Timestamps from all three systems and their NTP status.
5. WALLIX support case at https://support.wallix.com; Trustelem theme or feature requests go
   to support-trustelem@wallix.com.
