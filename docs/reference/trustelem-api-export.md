# Exporting the Trustelem configuration with the API

> - **Purpose:** API scripts that snapshot the Trustelem configuration that matters for the PAM
>   integration (users, groups, access rules, alerts, logs) and a nightly job that checks them.
> - **Audience:** Trustelem administrators and the PAM operations team.
> - **Verified:** 2026-09-23, against the Trustelem API page; the handler bodies were not executed
>   against a tenant.
> - **Sources:** [Trustelem API](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api),
>   [07 Operations](../trustelem/07-operations.md).

Trustelem publishes no tenant backup or export feature (see
[07 Operations](../trustelem/07-operations.md)). The API and scripts feature can snapshot the
parts of the configuration that matter for the PAM integration: users, groups, application
permissions (access rules), alerts and 30 days of logs.

The function signatures below are copied from the
[API page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api) as read on
2026-09-23. The handler bodies that combine them are this repository's and were not executed
against a tenant. The console's script editor shows the current `api` object; treat it as the
reference.

Prerequisites:

- The API feature enabled by WALLIX support ("if you don't have access to this feature, please
  contact WALLIX Trustelem support").
- A script created under `https://admin-<tenant>.trustelem.com/app#/api-scripts`.
- An API key restricted to the exporting host's public IP and bound to the script.

## 1. Documented signatures used here

The scripts below rely on these read calls. `listPerms` and `listLogs` have constraints that
shape the scripts.

```ts
listUsers(args: { withGroups?: boolean; withAttributes?: boolean; }): User[];
// User: id, firstName, lastName, UUID?, userPrincipalName?, email, email2?, mobilePhone?,
//       secondaryPhone?, trustelemAdmin?, suspended?, accountExpiration?, primaryDirectory?,
//       allDirectories? (plus groups and attributes when requested)
listGroups(args: {}): Group[];               // Group: id, name, UUID, directoryID?
listApps(args: {}): App[];                   // App: id, name
listPerms(args: { userID?: UserID; groupID?: GroupID; appID?: AppID; }): { perms: Perm[] } | { error: string };
// Perm: appID, groupID, userID, internalZone, externalZone, ldapZone, radiusZone
// ZoneSecurityLevel = '' | 'default' | '1_factor' | '2_factors' | 'forbidden'
getEffectiveUserPermsForApp(args: { appID: AppID; }): { userID, internalZone, externalZone, ldapZone, radiusZone }[];
listLogs(args: { start?: Date, end?: Date, order?: 'fromEnd' | 'fromStart', pageSize?: number, pageToken?: string }): { logs: Log[]; nextPageToken: string } | { error: string; };
// Log: id, date, level, msg, details?, userID?, userEmail, ip, useragent
listAlerts(args: { unreadOnly?: boolean; since?: string; }): Alert[];   // Alert: id, date, msg, userID, read
listSessions(args: { showDeleted?: boolean; since?: string; limit?: number; }): Session[];
```

- `listPerms`: "The research is done on only one id, the priority order is userID, then
  groupID, then appID". Permissions are therefore exported per application.
- `listLogs`: "List all the logs of the 30 previous days". Dates are RFC 3339, pages hold 1000
  logs, and `nextPageToken` gives the next page.

## 2. Script: export permissions (access rules) per application

This script detects user-level exemptions and confirms the rule set of
[chapter 06](../trustelem/06-mfa-and-access-rules.md) every night.

```ts
// script name: export_perms
function handler(req: Request, w: ResponseWriter): void {
  const apps = api.listApps({});
  const out: { app: App; perms: Perm[]; effective: unknown[] }[] = [];
  for (const app of apps) {
    const perms = api.listPerms({ appID: app.id });
    if (isError(perms)) { w.JSON({ error: perms.error, app: app.name }); return; }
    const effective = api.getEffectiveUserPermsForApp({ appID: app.id });
    out.push({ app, perms: perms.perms, effective });
  }
  w.JSON({ generatedAt: new Date().toISOString(), apps: out });
}
```

Deviations to alert on, for the Bastion and Access Manager apps:

- a permission whose `userID` is set (a user-level rule);
- a `radiusZone` or `ldapZone` of `''` (no rule) for a PAM group;
- a web zone of `'1_factor'` for a PAM group.

The API exposes the five documented levels only. The RADIUS-specific *Always allow* and *2nd
factor only* values shown in the console are not in the `ZoneSecurityLevel` type. Check their
API representation in the script editor (gap T6 in the [register](open-questions-and-gaps.md)).

## 3. Script: export users and groups

```ts
// script name: export_identities
function handler(req: Request, w: ResponseWriter): void {
  const users = api.listUsers({ withGroups: true, withAttributes: false });
  const groups = api.listGroups({});
  w.JSON({
    generatedAt: new Date().toISOString(),
    users: users.map(u => ({
      id: u.id, email: u.email, userPrincipalName: u.userPrincipalName,
      primaryDirectory: u.primaryDirectory, suspended: u.suspended,
      accountExpiration: u.accountExpiration, trustelemAdmin: u.trustelemAdmin,
      groups: u.groups
    })),
    groups
  });
}
```

- The `User` datatype has no field describing enrolled factors. The API lists them per user:
  `listAuthTokens(args: { id: UserID; })` returns `AuthToken { id, userID, kind, name }` ("List
  the second factors of a user").
- Calling it for each user lists the users without a second factor before an access rule
  requires one ([chapter 06](../trustelem/06-mfa-and-access-rules.md)).
- Keep only the attributes you need: the export contains personal data.

## 4. Script: export logs and alerts (rolling window)

```ts
// script name: export_logs
function handler(req: Request, w: ResponseWriter): void {
  const input = req.ReadJSON(true);            // { "start": "2026-09-22T00:00:00Z" }
  const all: Log[] = [];
  let token: string | undefined = undefined;
  do {
    const page = api.listLogs({ start: new Date(input.start), pageSize: 1000, pageToken: token, order: 'fromStart' });
    if (isError(page)) { w.JSON({ error: page.error }); return; }
    all.push(...page.logs);
    token = page.nextPageToken;
  } while (token);
  w.JSON({ generatedAt: new Date().toISOString(), logs: all, alerts: api.listAlerts({ since: input.start }) });
}
```

## 5. Calling the scripts

```bash
# run from the allowed IP; the key is stored in the secret manager
TOKEN='<api key>'
BASE='https://admin.trustelem.com/api/script/{script-path-id}'   # copied from the sample command
DATE=$(date -u +%F)
curl -sS -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{}' "$BASE/export_perms"      > "trustelem-perms-$DATE.json"
curl -sS -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{}' "$BASE/export_identities" > "trustelem-identities-$DATE.json"
curl -sS -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d "{\"start\":\"$(date -u -d '1 day ago' +%FT%TZ)\"}" "$BASE/export_logs" > "trustelem-logs-$DATE.json"
```

The endpoint pattern and headers are the documented ones:
`https://admin.trustelem.com/api/script/{script-path-id}/<script>` with `Authorization: Bearer`.
The path segment is the opaque value shown in the script's "sample command" (for example
`46e3xi...gtea`), not the API key.

## 6. Nightly job and checks

1. Run the three calls from a hardened host inside the administration network (the API key's
   allowed IP).
2. Diff `trustelem-perms` against the previous day. Alert on any new user-level permission and
   on any change of zone level for the PAM groups.
3. Diff `trustelem-identities` to catch users added to the administrator groups, suspended
   accounts still in PAM groups, and accounts near `accountExpiration`.
4. Retain the exports for the period the audit policy requires. They are the closest thing to a
   tenant backup. They allow manual re-creation of rules with `setGroupPerm` and `setUserPerm`
   after an administrative error.

## 7. Limits

- Rate limits are not documented (gap T6); keep the job nightly.
- The API cannot export application settings (SAML certificates, connector definitions,
  passkey policy). Record those in the worked example table and in the change log.
- Enrolled factors are readable with `listAuthTokens` but cannot be recreated by the API.
- Restoring is manual: `createUser`, `createGroup`, `addUsersToGroup`, `setGroupPerm` and
  `setUserPerm` exist, but there is no bulk import.
