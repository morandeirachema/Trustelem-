# Trustelem operations

Date: 2026-09-23. Sources: [On-premise SIEM](https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem),
[API](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api),
[Application scripts](https://trustelem-doc.wallix.com/books/trustelem-administration/page/application-scripts),
[Certificate renewal](https://trustelem-doc.wallix.com/books/trustelem-administration/page/certificate-renewal),
[Self-service password reset](https://trustelem-doc.wallix.com/books/trustelem-administration/page/self-service-password-reset),
[Delegated administration](https://trustelem-doc.wallix.com/books/trustelem-administration/page/delegated-administration),
[Custom themes](https://trustelem-doc.wallix.com/books/trustelem-administration/page/custom-themes),
[Summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary),
[SCIM client](https://trustelem-doc.wallix.com/books/trustelem-administration/page/scim-client).
Quotes are verbatim.

## 1. Logs, alerts and sessions in the console

- **Logs** (`app#/logs`): "Every interaction with Trustelem from administrators, users or
  directories is visible here". LDAP and RADIUS authentications relayed by Trustelem Connect
  appear here; their absence is the first debugging signal (chapter 08).
- **Alerts** (`app#/alert`): help requests, rescue code requests, temporary passwords;
  "administrators receive an email... The admin can generate a code/link required to unlock the
  user".
- **Sessions** (`app#/sessions`): "The red trash allows the administrators to kill the session.
  Note: killing a Trustelem session doesn't mean users will be disconnected from their
  applications." A Bastion or Access Manager session already opened stays open; terminate it on
  the Bastion.
- Retention shown in the API: logs and alerts for "the 30 previous days"; sessions are paged
  ("By default, a page contains maximum 10000 sessions") and deleted sessions are listed for the
  30 previous days. Export to a SIEM for longer retention.

## 2. SIEM export through Trustelem Connect

"Trustelem sends new events every 30s, and has a queuing system if an error is detected during
transmission."

1. "Install Trustelem Connect... you don't need to add any applications to the Trustelem
   Service" (an existing Connect VM can be reused).
2. "Add or edit the config.ini file":

```ini
outgoing_allowed = "true"
[target.siem]
addr = "siem.example.local"
port = "5514"
```

   The vendor page spells the section `[targert.choose_a_name]`; the SCIM page and the
   `set-target` CLI use `[target.<name>]`, which is the correct key.

3. Restart the Trustelem Connect service.
4. On the Trustelem **Service** page: "Under Send logs, choose the date from which you'll get
   the logs. Click Add send logs tasks. Click enabled. Under Target name, enter the name choose
   on the config.ini file. Under format, choose JSON (strongly recommended, as Trustelem logs are
   not properly designed for syslog). Under types of logs to send, choose ALL or a specific type
   of logs. Click Save".

Test receiver: `nc -l -k <vm_ip> <port>` on Linux or `.\ncat.exe -l -k --allow <vm_ip> <port>`
from `C:\Program Files (x86)\Nmap\` on Windows.

Record schema: *inference*, the SIEM page does not document the JSON fields; they are expected
to follow the API `Log` type (`id, date, level, msg, details, userID, userEmail, ip, useragent`).
Check against a captured record. Second-factor events, including `webauthn_duplicate_credential`, are included.

SIEM use cases for the PAM design:

| Detection | Signal |
|-----------|--------|
| push fatigue attack | repeated RADIUS second-factor requests for one user with rejections or timeouts |
| MFA bypass attempt | a user switched to *Always allow* (the event name is not documented; compare nightly `listPerms` exports, reference API export) |
| factor reset abuse | rescue code issued, factor reset, then login from a new IP |
| connector outage | directory LED not green in the dashboard (the LED is documented for directories only) and no LDAP/RADIUS logs while the Bastion reports RADIUS timeouts |
| SAML certificate expiry | expiry e-mail from Trustelem and Access Manager SAML errors |

## 3. API and scripts

"APIs are available in the API / scripts tab: https://admin-mydomain.trustelem.com/app#/api-scripts.
Note: if you don't have access to this feature, please contact WALLIX Trustelem support."

Steps: "1-Add a new script 2-Add a new API key if required 3-Edit the API key 4-Provide the
allowed IPs and select the new script 5-Click on the script to see a sample command".

```bash
curl -X POST -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <api-key>' \
  -d '{"email":"jdoe@test.com","firstname":"John","lastname":"Doe"}' \
  https://admin.trustelem.com/api/script/{script-path-id}/create_user
```

Scripts are TypeScript handlers:

```ts
const input = req.ReadJSON(true);
const result = api.createUser({
  email: input.email, firstName: input.firstname, lastName: input.lastname,
  passwordInit: { kind: 'temporaryPassword' }
});
if (isError(result)) { w.JSON({ error: result.error }) } else { w.JSON({ password: result.temporaryPassword }); }
```

Objects: Users (create, get, update, delete, search, attributes, resetPassword), Groups,
Applications, Permissions (`listPerms`, `setGroupPerm`, user permissions; zones
`internalZone, externalZone, ldapZone, radiusZone` with values `'' | 'default' | '1_factor' |
'2_factors' | 'forbidden'`), Logs (`listLogs`, 30 days, page size 1000, RFC 3339 dates),
Alerts, Sessions, AuthToken (`listAuthTokens`, `issueAuthToken`, `verifyAuthToken` with status
`success | waiting | rejected | timeout | failed`). Rate limits are not documented.

Useful automations for this design:

- nightly export of permissions to detect user-level exemptions (*Always allow*);
- joiner/leaver reconciliation between AD groups, Trustelem groups and Bastion mappings;
- pulling 30 days of logs as a backup of the SIEM feed.

Scripts for these three exports and a nightly job are in the
[Trustelem API export reference](../reference/trustelem-api-export.md).

Application scripts (SAML and OIDC claim customisation) use `msg.setAttr`, `msg.addAttr` and,
for OIDC, `claims["Groups"] = JSON.stringify(groups)`; the Bastion and Access Manager scripts
are in chapters 04 and 05.

## 4. Application certificates (SAML signing)

Expiry alert e-mail: "The following applications are federated using the certificate -Name of
the certificate- that has expired on...". Renewal:

1. "Go to your Trustelem admin page, then Security settings, then Application certificates and
   click on +Create."
2. Edit the Access Manager (and Bastion SAML) application and select the new certificate.
3. On the service provider re-import the metadata, "not necessary if the certificate is
   recovered using the Trustelem metadata URL". Access Manager and Bastion import a metadata
   file, so re-import it on both.
4. "The consequence will be a short indisponibility between the change on Trustelem and the
   change on the application." Schedule it and keep the RADIUS path as the fallback for
   administrators.

Track the expiry date in the operations calendar: the e-mail says the certificate "will expired
soon or has already expired" [sic], so it can arrive late.

## 5. Self-service password reset (Trustelem and AD passwords)

User URL `https://<tenant>.trustelem.com/forgot`. Setup: **Security settings > Password
management** ("Self-service password reset for users"); "the administrator can select the
number of required factors then select which factors will be required". For AD passwords:
enable "Password recovery" on the directory and delegate "Reset user password and force
password change at next logon" to the ADConnect service account. Consider leaving AD writeback
off for privileged accounts and keeping the reset in the help-desk process.

## 6. Delegated administration and custom consoles

"To enable this tool, you need to send an email to your WALLIX sales contact". Delegates are
granted through access rules and the user attribute `groupManager`, for example
`Supplier1;max:10`, `regexp:.*`, `Supplier2;assignableGroups:Google,SalesForce;max:10`. The
delegated administration tool also grants "Reset factors of administered users"; a "Custom
Admin Console" built on the API can restrict an external provider to managing its own group's
membership (the public API has no factor-reset call).

## 7. Branding and user communication

Themes (`app#/themes`) are "not activate by default" and enabled by
support-trustelem@wallix.com; Login, Dashboard and Common files, plus `favicon.ico`. Use the
theme to make the Trustelem login page recognisable to privileged users, which reduces the
success of look-alike phishing pages.

## 8. Change management

| Change | Where | Impact |
|--------|-------|--------|
| ADConnect upgrade | agent VMs | none with the documented parallel install, new connector listed first (chapter 02) |
| Trustelem Connect upgrade | agent VMs | no documented procedure; upgrade one VM at a time while the other serves (*inference*) |
| New Trustelem IP ranges | egress firewall | connectors reconnect; restart them after the change |
| Access rule change | console | expected at the next authentication (*inference*, not documented) |
| Factor policy change | console | applies at next enrollment and login |
| SAML certificate rotation | console plus SP re-import | short interruption |
| RADIUS secret rotation | Trustelem app model, Bastion, Access Manager | coordinate; do the two Connect listeners one at a time |
| Tenant feature enablement (API, delegation, themes) | WALLIX support or sales | lead time |

## 9. Availability and incident handling

Published history and incident log: [unavailability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability),
[incidents](https://trustelem-doc.wallix.com/books/trustelem-news/page/incidents). No status
page or maintenance calendar is documented. When the tenant is unreachable:

1. Bastion administrators use the local break-glass account (IP-restricted).
2. Existing Bastion and Access Manager sessions keep running; new native logins are expected to
   fail at the RADIUS step once the Bastion timeout expires (*inference*).
3. If the outage is long, temporarily remove the RADIUS secondary authentication from the AD
   domain on the Bastion (one field, documented rollback) and record the decision.
4. Re-enable and verify with `./connect check` and a test login when the tenant is back.
