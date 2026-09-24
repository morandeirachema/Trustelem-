# Exporting the Trustelem configuration with the API

Date: 2026-09-23. Trustelem publishes no tenant backup or export feature (see
[07 Operations](../trustelem/07-operations.md)). The API and scripts feature gives a way to
snapshot the parts of the configuration that matter for the PAM integration: users, groups,
application permissions (access rules), alerts and 30 days of logs. The function signatures
below are copied from the [API page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api)
as read on 2026-09-23; the handler bodies that combine them are the author's and were not
executed against a tenant. The console's script editor shows the current `api` object and
must be treated as the reference.

Prerequisites: the API feature enabled by WALLIX support ("if you don't have access to this
feature, please contact WALLIX Trustelem support"); a script created under
`https://admin-<tenant>.trustelem.com/app#/api-scripts`; an API key restricted to the
exporting host's public IP and bound to the script.

## 1. Documented signatures used here

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

"The research is done on only one id, the priority order is userID, then groupID, then
appID" for `listPerms`, so permissions are exported per application. `listLogs`: "List all the
logs of the 30 previous days", RFC 3339 dates, 1000 logs per page, `nextPageToken` for the
next page.

## 2. Script: export permissions (access rules) per application

Purpose: detect user-level exemptions and confirm the rule set of chapter 06 every night.

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

A permission whose `userID` is set is a user-level rule; on the Bastion and Access Manager
apps, a `radiusZone` or `ldapZone` of `''` (no rule) or a web zone of `'1_factor'` for a PAM
group is the deviation to alert on. Note that the API exposes the five documented levels;
the RADIUS-specific *Always allow* and *2nd factor only* values shown in the console are not
listed in the `ZoneSecurityLevel` type, so their API representation must be checked in the
script editor.

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

The `User` datatype has no field describing enrolled factors, but the API lists them per user:
`listAuthTokens(args: { id: UserID; })` returns `AuthToken { id, userID, kind, name }` ("List the
second factors of a user"). Calling it for each user in the export lists the users without a
second factor before an access rule requires one (chapter 06). Keep only the attributes you need; the export contains personal data.

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
`https://admin.trustelem.com/api/script/{script-path-id}/<script>` with `Authorization: Bearer`;
the path segment is the opaque value shown in the script's "sample command" (for example
`46e3xi...gtea`), not the API key.

## 6. Nightly job and checks

1. Run the three calls from a hardened host inside the administration network (the API key's
   allowed IP).
2. Diff `trustelem-perms` against the previous day and alert on any new user-level permission
   and on any change of zone level for the PAM groups.
3. Diff `trustelem-identities` to catch users added to the administrator groups, suspended
   accounts still in PAM groups, and accounts near `accountExpiration`.
4. Retain exports for the period required by the audit policy; they are the closest thing to a
   tenant backup and allow manual re-creation of rules with `setGroupPerm` and `setUserPerm`
   after an administrative error.

## 7. Limits

- Rate limits are not documented; keep the job nightly.
- The API cannot export application settings (SAML certificates, connector definitions,
  passkey policy); enrolled factors are readable with `listAuthTokens` but cannot be recreated
by the API; record those in the worked example table and in the
  change log.
- Restoring is manual: `createUser`, `createGroup`, `addUsersToGroup`, `setGroupPerm` and
  `setUserPerm` exist, but there is no bulk import.
