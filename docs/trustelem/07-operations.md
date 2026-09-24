# Trustelem operations

> - **Purpose:** how to run the Trustelem tenant day to day: console logs, SIEM export, API
>   scripts, certificate rotation, password reset, delegation, changes and outages.
> - **Audience:** Trustelem administrators and the PAM operations team.
> - **Verified:** 2026-09-24, against the Trustelem administration book as read on 2026-09-24 and
>   the log formats in [logging and SIEM](../reference/logging-and-siem.md).
> - **Sources:** [On-premise SIEM](https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem),
>   [API](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api),
>   [Application scripts](https://trustelem-doc.wallix.com/books/trustelem-administration/page/application-scripts),
>   [Certificate renewal](https://trustelem-doc.wallix.com/books/trustelem-administration/page/certificate-renewal),
>   [Self-service password reset](https://trustelem-doc.wallix.com/books/trustelem-administration/page/self-service-password-reset),
>   [Delegated administration](https://trustelem-doc.wallix.com/books/trustelem-administration/page/delegated-administration),
>   [Custom themes](https://trustelem-doc.wallix.com/books/trustelem-administration/page/custom-themes),
>   [Summary](https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary),
>   [SCIM client](https://trustelem-doc.wallix.com/books/trustelem-administration/page/scim-client).

Bastion and Access Manager event formats and the detection rules are in the
[logging and SIEM reference](../reference/logging-and-siem.md). This chapter covers the
Trustelem side.

## 1. Logs, alerts and sessions in the console

Three console pages show what happened and let administrators act on it. The API returns 30
days of logs and alerts; export them to a SIEM (section 2) for longer retention.

- **Logs** (`app#/logs`): "Every interaction with Trustelem from administrators, users or
  directories is visible here". LDAP and RADIUS authentications relayed by Trustelem Connect
  appear here. Their absence is the first debugging signal
  ([08 Troubleshooting](08-troubleshooting.md), section 1).
- **Alerts** (`app#/alert`): help requests, rescue code requests and temporary passwords.
  "administrators receive an email... The admin can generate a code/link required to unlock the
  user".
- **Sessions** (`app#/sessions`): "The red trash allows the administrators to kill the session.
  Note: killing a Trustelem session doesn't mean users will be disconnected from their
  applications." A Bastion or Access Manager session already opened stays open. Terminate it on
  the Bastion.
- **Retention** as shown in the API: logs and alerts for "the 30 previous days". Sessions are
  paged ("By default, a page contains maximum 10000 sessions"), and deleted sessions are listed
  for the 30 previous days.

## 2. SIEM export through Trustelem Connect

Trustelem Connect pushes the tenant's events to an on-premise target: "Trustelem sends new
events every 30s, and has a queuing system if an error is detected during transmission."

### 2.1 Set up the export

1. "Install Trustelem Connect... you don't need to add any applications to the Trustelem
   Service". An existing Connect VM can be reused.
2. "Add or edit the config.ini file": enable outgoing connections and declare the SIEM target
   as in [chapter 03, section 9](03-trustelem-connect.md#9-outbound-targets-siem-and-scim); use
   `[target.<name>]`, not the vendor page's `[targert.choose_a_name]` [sic]
   ([chapter 03, section 4](03-trustelem-connect.md#4-install-on-linux)).
3. Restart the Trustelem Connect service.
4. On the Trustelem **Service** page: "Under Send logs, choose the date from which you'll get
   the logs. Click Add send logs tasks. Click enabled. Under Target name, enter the name choose
   [sic] on the config.ini file. Under format, choose JSON (strongly recommended, as Trustelem
   logs are not properly designed for syslog). Under types of logs to send, choose ALL or a
   specific type of logs. Click Save".
5. Test the flow with a listener on the receiving VM: `nc -l -k <vm_ip> <port>` on Linux, or
   `.\ncat.exe -l -k --allow <vm_ip> <port>` from `C:\Program Files (x86)\Nmap\` on Windows.

### 2.2 Record content

The SIEM page does not document the JSON record fields. *Inference:* they follow the API `Log`
type listed in the [logging and SIEM reference](../reference/logging-and-siem.md), section 3,
which also lists the second-factor events forwarded. Check against a captured record.

### 2.3 Trustelem signals for detection

The detection rules for the MFA design, including the Trustelem-side signals (*Always allow*
changes, factor reset abuse, connector outage, SAML certificate expiry), are in the
[logging and SIEM reference, section 5](../reference/logging-and-siem.md#5-detection-rules-for-the-mfa-design).

## 3. API and scripts

The API runs TypeScript scripts on the tenant, called over HTTPS with an API key bound to
allowed IPs. "APIs are available in the API / scripts tab: https://admin-mydomain.trustelem.com/app#/api-scripts.
Note: if you don't have access to this feature, please contact WALLIX Trustelem support."

### 3.1 Create a script and a key

The vendor steps, verbatim: "1-Add a new script 2-Add a new API key if required 3-Edit the API
key 4-Provide the allowed IPs and select the new script 5-Click on the script to see a sample
command".

Sample call:

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

### 3.2 Objects available

- **Users**: create, get, update, delete, search, attributes, resetPassword.
- **Groups**, **Applications**, **Alerts**, **Sessions**.
- **Permissions**: `listPerms`, `setGroupPerm`, user permissions; zones
  `internalZone, externalZone, ldapZone, radiusZone` with values
  `'' | 'default' | '1_factor' | '2_factors' | 'forbidden'`.
- **Logs**: `listLogs`, 30 days, page size 1000, RFC 3339 dates.
- **AuthToken**: `listAuthTokens`, `issueAuthToken`, `verifyAuthToken` with status
  `success | waiting | rejected | timeout | failed`.

Rate limits are not documented.

### 3.3 Automations for this design

- Nightly export of permissions, to detect user-level exemptions (*Always allow*).
- Joiner and leaver reconciliation between AD groups, Trustelem groups and Bastion mappings.
- Pulling 30 days of logs as a backup of the SIEM feed.

Scripts for these three exports and a nightly job are in the
[Trustelem API export reference](../reference/trustelem-api-export.md).

### 3.4 Application scripts

Application scripts customise SAML and OIDC claims. They use `msg.setAttr`, `msg.addAttr` and,
for OIDC, `claims["Groups"] = JSON.stringify(groups)`. The Bastion and Access Manager scripts
are in [04 Bastion integration](04-bastion-integration.md) and
[05 Access Manager integration](05-access-manager-integration.md).

## 4. Application certificates (SAML signing)

Rotate the SAML signing certificate before it expires. The change causes a short interruption
on each service provider.

Trustelem sends an expiry alert e-mail: "The following applications are federated using the
certificate -Name of the certificate- that has expired on...". The e-mail says the certificate
"will expired soon or has already expired" [sic], so it can arrive late. Track the expiry date
in the operations calendar.

Renewal:

1. "Go to your Trustelem admin page, then Security settings, then Application certificates and
   click on +Create."
2. Edit the Access Manager application (and the Bastion SAML application) and select the new
   certificate.
3. Re-import the metadata on the service provider. It is "not necessary if the certificate is
   recovered using the Trustelem metadata URL". Access Manager and Bastion import a metadata
   file, so re-import it on both.
4. "The consequence will be a short indisponibility between the change on Trustelem and the
   change on the application." Schedule the change. Keep the RADIUS path as the fallback for
   administrators.

## 5. Self-service password reset (Trustelem and AD passwords)

Users reset their own password at `https://<tenant>.trustelem.com/forgot`. For privileged
accounts, consider leaving AD writeback off and keeping the reset in the help-desk process.

1. Open **Security settings > Password management** ("Self-service password reset for users").
   "the administrator can select the number of required factors then select which factors will
   be required".
2. For AD passwords, enable "Password recovery" on the directory.
3. Delegate "Reset user password and force password change at next logon" to the ADConnect
   service account.

## 6. Delegated administration and custom consoles

Delegation lets a named user manage a subset of users and groups. It is enabled on request:
"To enable this tool, you need to send an email to your WALLIX sales contact".

- Delegates are granted through access rules and the user attribute `groupManager`, for example
  `Supplier1;max:10`, `regexp:.*`, `Supplier2;assignableGroups:Google,SalesForce;max:10`.
- The delegated administration tool also grants "Reset factors of administered users".
- A "Custom Admin Console" built on the API can restrict an external provider to managing its
  own group's membership. The public API has no factor-reset call.

## 7. Branding and user communication

A custom theme makes the Trustelem login page recognisable to privileged users, which reduces
the success of look-alike phishing pages.

Themes (`app#/themes`) are "not activate [sic] by default" and are enabled by
support-trustelem@wallix.com. A theme covers the Login, Dashboard and Common files, plus
`favicon.ico`.

## 8. Change management

Most Trustelem changes are console-only. The ones below touch another system or need a
coordinated window.

| Change | Where | Impact |
|--------|-------|--------|
| ADConnect upgrade | agent VMs | none with the documented parallel install, new connector listed first ([02 Directory sync](02-directory-sync-adconnect.md)) |
| Trustelem Connect upgrade | agent VMs | no documented procedure; upgrade one VM at a time while the other serves (*inference*) |
| New Trustelem IP ranges | egress firewall ([01 Tenant setup](01-tenant-setup.md), section 4) | connectors reconnect; restart them after the change |
| Access rule change | console | expected at the next authentication (*inference*, not documented) |
| Factor policy change | console | applies at next enrollment and login |
| SAML certificate rotation | console plus SP re-import | short interruption (section 4) |
| RADIUS secret rotation | Trustelem app model, Bastion, Access Manager | coordinate; do the two Connect listeners one at a time |
| Tenant feature enablement (API, delegation, themes) | WALLIX support or sales | lead time |

## 9. Availability and incident handling

When the tenant is unreachable, new logins that need a Trustelem second factor are expected to
fail (*inference*, step 2); local Bastion accounts such as break-glass keep working, and step 3
is the documented way to lift the RADIUS requirement. WALLIX publishes an
[unavailability](https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability)
history and an [incident log](https://trustelem-doc.wallix.com/books/trustelem-news/page/incidents).
No status page or maintenance calendar is documented.

1. Bastion administrators use the local break-glass account (IP-restricted).
2. Existing Bastion and Access Manager sessions keep running. New native logins are expected to
   fail at the RADIUS step once the Bastion timeout expires (*inference*).
3. If the outage is long, temporarily remove the RADIUS secondary authentication from the AD
   domain on the Bastion (one field, documented rollback). Record the decision.
4. When the tenant is back, re-enable it and verify with `./connect check` and a test login.
