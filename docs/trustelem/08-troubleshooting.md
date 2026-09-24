# Trustelem troubleshooting

> - **Purpose:** find the cause of a failed Trustelem, Bastion or Access Manager authentication
>   from its symptom, and collect the data WALLIX support needs.
> - **Audience:** Trustelem administrators, Bastion and Access Manager operators, and the PAM
>   support team.
> - **Verified:** 2026-09-24, against the Trustelem administration and applications books as read
>   on 2026-09-24, the Bastion 12.4.3 guides and the Access Manager 6.0.5 Administration Guide
>   (WALLIX customer documentation behind the doc.wallix.com login).
> - **Sources:** the Debug chapter of
>   [LDAP-Radius - Trustelem Connect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect),
>   [ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect),
>   [connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows),
>   the [WALLIX Bastion](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion) and
>   [WALLIX Access Manager](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager)
>   application pages, the Bastion 12.4.3 and Access Manager 6.0.5 guides on
>   [doc.wallix.com](https://doc.wallix.com/).

## 1. First question: is there a log line in Trustelem?

Open the Trustelem **Logs** page first. A log line means the connector works and the entry
gives the reason for the failure. No log line means the request never reached the cloud.

The vendor text: "Go on your Trustelm [sic] Logs page and see if you have LDAP or Radius logs. If
yes, the connector is working and you should know why the authentication failed:

- if the user is not found, is the login attribute correct?
- if the user doesn't have the permission for the app, is your access rule correct?
- if the user doesn't have a 2nd factor, is your enrollment process correct?"

Without a log line, check the connector, the listener, the port and the firewall (section 2).
One documented exception: "If your application tries to do a LDAP search and doesn't have
access rule (LDAP 1 or 2 factors), no users will be found but you will not see any logs because
it is not a bug".

## 2. Connector and network

Most connector failures are a blocked or inspected outbound flow. The required destinations are
listed in [01 Tenant setup](01-tenant-setup.md), section 4.

| Symptom | Check (verbatim where quoted) |
|---------|-------------------------------|
| Connector not listed in the console | "verify the synchronization ID", "verify the proxy setup", on Windows "verify that you clicked on Validate"; run `./connect check <sync id> [http://proxy:3128]` |
| `Network: false` | "The connection could not be opened at all: the traffic is blocked or not routed." |
| `Network: true`, `CanTLS: false` | "The connection reaches the server but the TLS session fails: proxy or TLS inspection." The connector pins the server certificate; exclude every destination listed in chapter 01, section 4, from inspection |
| `CommOK: true` but service shows off | turn the service on in the console ("Turn on the service by clicking on No") |
| Worked yesterday, fails today | DNS or IP change; "After changing a firewall, proxy or DNS rule, restart the connector service"; check that the new `*.trustelem.com` addresses active from 2026-09-29 are allowed (chapter 01, section 4) |
| Listener not reachable from the Bastion | "verify if the listen address is correct (should be * if the VM is dedicated to Trustelem)"; "see the port defined and the setup information clicking on the eye button"; local firewall on the VM |
| Need packet evidence | "use Wireshark on Windows or tcpdump on Linux. /!\ tcpdump displays the flow received, before applying local firewall rules." |

## 3. Directory synchronisation

Sync problems come from the flow to the domain controllers or the rights of the ADConnect
service account.

| Symptom | Check |
|---------|-------|
| No groups in "Sync groups" | open the "i" icon: if Server Link shows an error, "verify the flows from the VM running the connector to the Active Directory; verify the service account used for Trustelem AD Connect (UserPrincipalName and password); verify if you have a replication delay between the DC"; otherwise "verify if the service account has the right to search groups" |
| Group appears empty | "If your group is Domain users, it's normal, it can't be used because it is not a real group"; the service account may not read those user objects; DC replication delay |
| User merged with a local account | expected: same UPN or e-mail merges them and "the password to use will be the one from Active Directory" |
| 4th LED red on the Windows installer | expected when a `config.ini` is used on a non-domain host |

## 4. Bastion RADIUS

Bastion RADIUS failures come from the **Use mobile device** option, the method order, the
timeout or the access rule. The values to set are in
[04 Bastion integration](04-bastion-integration.md), sections 3, 4 and 8.

| Symptom | Check |
|---------|-------|
| Password prompt loops or immediate failure for AD users | "verify if you checked the option Use mobile device on the Radius external authentication" (must be ON for AD users, scenario A) |
| Local user authenticates without MFA | both local password and RADIUS selected: "the Bastion will try the first method (local password)"; select only RADIUS |
| Local user fails with logs in Trustelem | "if the login of the local user is unknown by Trustelem the authentication won't work" (login must be the Trustelem e-mail) |
| Push never arrives, Bastion times out | RADIUS timeout too short for a push: test and raise it (defaults and vendor advice in the [low-level design, section 4](../architecture/05-low-level-design.md#4-timeouts-to-align)); user has no enrolled WALLIX Authenticator; access rule missing |
| User never prompted | user or group rule *Always allow*, or inside the MFA session window on the same network ([06 MFA and access rules](06-mfa-and-access-rules.md), sections 7 and 8) |
| mstsc fails before the login screen | Kerberos enabled on the RDP proxy: add `enablecredsspsupport:i:0` and `authentication level:i:2` to the `.rdp` file, or `/sec:tls` with FreeRDP |

## 5. Bastion LDAP (Trustelem users)

Bastion LDAP failures for Trustelem users come from the bind values, a missing access rule or
the case of the group DN. The field values are in
[04 Bastion integration](04-bastion-integration.md), section 5.

| Symptom | Check |
|---------|-------|
| "Test authentication" fails | bind user `trustelem` and password from the app model; base DN from the app model; port 2001 (the LDAP listener, [03 Trustelem Connect](03-trustelem-connect.md)); StartTLS or LDAPS consistent on both sides |
| Users not found | "Trustelem users will not be found by the Bastion before having an access rule (1 or 2 factors)"; login attribute and user name attribute set to `mail` |
| Mapping does not apply | group DN case: "if you don't respect the case, the authentication won't work"; DN pattern `CN=<group>,OU=Groups,DC=<tenant>,DC=trustelem,DC=com` |

## 6. Access Manager RADIUS

Access Manager RADIUS failures come from the protocol or the factor order.

- "Verify if the protocol is set to PAP".
- "if the password is not handle [sic] by Trustelem, the authentication is login + password
  (AD, local...) then Trustelem TOTP even if the input name is Password again".
- Factor order on the domain: AD (or local database) Factor 1, RADIUS Factor 2. Trustelem rule:
  *2nd factor only*.

## 7. Access Manager SAML

SAML failures come from a copy-paste error, clock skew, an existing user or a name mismatch.
Work through the vendor list, then the additional checks, then capture a trace.

### 7.1 Vendor checks

Verbatim:

- "Verify if the setup is correct: there is a lot of information to copy and paste, and an
  error can quickly happen."
- "Verify the time on Access Manager: SAML assertion are [sic] valid for a short period."
- "Verify if the user doesn't already exist. For instance if the SAML domain was used before
  for LDAP authentication, the users may already exist. In these case [sic] the authentication
  will not work and it has to be deleted first."
- "Verify the attributes mapped in Access Manager --> reminder: a local Trustelem user must
  have an uid set to email".
- "Verify if the domain used in the SAML setup is the same used on the Bastion for the
  Authentication domain name".

### 7.2 Additional checks

From the Access Manager guide and release notes:

- Service provider options as set in
  [05 Access Manager integration](05-access-manager-integration.md), section 2: Signed Response
  and Signed Assertion ON, Encrypt Messages OFF, Sign Messages OFF (the Access Manager 5.2.4.0
  release notes list known issue WAB-11153: SAML authentication "can fail due to a missing
  "SigAlg" query param" when it is ON with the "Redirect" binding).
- On a three-interface appliance the SAML URL may be auto-filled with the administration
  interface URL (known issue WAB-4968,
  [Access Manager release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html)).
  Correct it to the user-facing FQDN.
- Strip Domain OFF on the Bastion object, so that `login@domain` reaches the Bastion
  ([SAML assertion and naming, section 1.2](../reference/saml-assertion-and-naming.md#12-strip-domain)).
- Access Manager below 5.2.7 or 6.0.4 is vulnerable to a SAML response forgery
  (WSA-2026-07-0002, [WALLIX advisories](https://www.wallix.com/support-services/alerts/)).
  Failures after an upgrade are not a reason to downgrade.

### 7.3 Trace

1. "Download the browser plugin SAML tracer".
2. Set the Access Manager SAML module to DEBUG on the **Logs** tab of **Settings > Application
   Settings** (Access Manager 6.0.5; the Trustelem page names the older path **Settings >
   Application Settings > Configuration > SAML**), as in
   [chapter 05, section 9](05-access-manager-integration.md).
3. Reproduce the failure.
4. Download the log archive.

## 8. Escalation data to collect

Collect evidence from all three systems for the same attempt before opening a case.

1. **Trustelem**: the Logs page filtered on the user, a screenshot of the service page
   (listener, port, status), and the `./connect check` output.
2. **Bastion**:
   - the `wabauth` lines of the attempt, from the SIEM or from the node (local files or
     `WABJournalCtl`);
   - the **Audit > Authentication history** rows with their Diagnosis (RDP and SSH proxy logins
     only);
   - the RADIUS external authentication settings and the domain's secondary authentication.

   A failure line only says "Authentication failed"; the reason is on the Trustelem side. Where
   the Bastion logs live and their formats are in the
   [logging and SIEM reference](../reference/logging-and-siem.md#12-bastion-nodes), sections 1.2
   and 2.1.
3. **Access Manager**:
   - the log archive with SAML at DEBUG, never TRACE or ALL (files and levels in the
     [logging and SIEM reference, section 1.3](../reference/logging-and-siem.md#13-access-manager-log-files-and-forwarding);
     procedure in [05 Access Manager integration](05-access-manager-integration.md#saml-debug-logs), section 9);
   - the SAML Identity Provider settings;
   - a SAML tracer capture (redact the assertion signature if shared outside the team).
4. **All systems**: timestamps and NTP status.
5. **Support**: open a WALLIX support case at https://support.wallix.com. Themes are enabled by
   support-trustelem@wallix.com, and the delegated administration tool through "your WALLIX
   sales contact".
