# Exporting the Trustelem configuration with the API

Date: 2026-09-23. Trustelem publishes no tenant backup or export feature ("not documented",
see [07 Operations](../trustelem/07-operations.md)). The API and scripts feature gives a way to
snapshot the parts of the configuration that matter for the PAM integration: users, groups,
application permissions (access rules), alerts and 30 days of logs. This reference gives the
scripts. The API surface (object names and fields) is the one documented on the
[API page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/api); the
handler bodies below are illustrative and must be adjusted to the exact signatures shown in
the console's script editor, which has autocompletion for the `api` object.

Prerequisites: the API feature enabled by WALLIX support ("if you don't have access to this
feature, please contact WALLIX Trustelem support"); a script created under
`https://admin-<tenant>.trustelem.com/app#/api-scripts`; an API key restricted to the
exporting host's public IP and bound to the script.

## 1. Script: export permissions (access rules)

Purpose: detect user-level exemptions (*Always allow*, *1 factor*) and confirm the rule set of
chapter 06 every night.

```ts
// script name: export_perms
type Output = { generatedAt: string; perms: unknown[] };

function handler(req: Request, w: ResponseWriter): void {
  const result = api.listPerms({});           // documented object: Permissions (listPerms)
  if (isError(result)) { w.JSON({ error: result.error }); return; }
  w.JSON({ generatedAt: new Date().toISOString(), perms: result.perms });
}
```

Fields to expect per permission, from the API page: application, target (user, group or
everyone) and the zone levels `internalZone`, `externalZone`, `ldapZone`, `radiusZone`, each
one of `'' | 'default' | '1_factor' | '2_factors' | 'forbidden'`.

## 2. Script: export users and groups

```ts
// script name: export_identities
function handler(req: Request, w: ResponseWriter): void {
  const users = api.searchUsers({ query: "" });     // Users: search
  if (isError(users)) { w.JSON({ error: users.error }); return; }
  const groups = api.listGroups({});                // Groups
  if (isError(groups)) { w.JSON({ error: groups.error }); return; }
  w.JSON({
    generatedAt: new Date().toISOString(),
    users: users.users.map(u => ({
      id: u.id, email: u.email, login: u.login, directory: u.directory,
      groups: u.groups, factors: u.authFactors, disabled: u.disabled
    })),
    groups: groups.groups
  });
}
```

Keep only the attributes you need; the export contains personal data and must be stored with
the same protection as the SIEM archive.

## 3. Script: export logs and alerts (rolling 30 days)

```ts
// script name: export_logs
function handler(req: Request, w: ResponseWriter): void {
  const input = req.ReadJSON(true);                 // { "from": "2026-09-22T00:00:00Z" }
  let token: string | undefined = undefined;
  const all: unknown[] = [];
  do {
    const page = api.listLogs({ from: input.from, pageSize: 1000, pageToken: token });
    if (isError(page)) { w.JSON({ error: page.error }); return; }
    all.push(...page.logs);
    token = page.nextPageToken;
  } while (token);
  const alerts = api.listAlerts({});
  w.JSON({ generatedAt: new Date().toISOString(), logs: all, alerts: isError(alerts) ? [] : alerts.alerts });
}
```

`listLogs` "List all the logs of the 30 previous days", page size 1000 by default, RFC 3339
dates and a `nextPageToken` for pagination (API page). Record fields: `id, date, level, msg,
details, userID, userEmail, ip, useragent`.

## 4. Calling the scripts

```bash
# run from the allowed IP; the key is stored in the secret manager
TOKEN='<api key>'
BASE='https://admin.trustelem.com/api/script/<key-id>'
DATE=$(date -u +%F)
curl -sS -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{}' "$BASE/export_perms"      > "trustelem-perms-$DATE.json"
curl -sS -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d '{}' "$BASE/export_identities" > "trustelem-identities-$DATE.json"
curl -sS -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" \
  -d "{\"from\":\"$(date -u -d '1 day ago' +%FT%TZ)\"}" "$BASE/export_logs" > "trustelem-logs-$DATE.json"
```

The endpoint pattern and headers are the documented ones:
`https://admin.trustelem.com/api/script/<key>/<script>` with `Authorization: Bearer`.

## 5. Nightly job and checks

1. Run the three calls from a hardened host inside the administration network (the API key's
   allowed IP).
2. Diff `trustelem-perms` against the previous day and alert on any permission whose target is
   a single user, or whose RADIUS zone is `''` or `always allow` for a PAM group.
3. Diff `trustelem-identities` to catch users added to `PAM-Admins` and users without a
   second factor in groups that require one.
4. Retain exports for the period required by the audit policy; they are the closest thing to a
   tenant backup and allow manual re-creation of rules after an administrative error.

## 6. Limits

- Rate limits are not documented; keep the job nightly.
- The API cannot export application settings (SAML certificates, connector definitions,
  passkey policy); record those in the worked example table and in the change log.
- Restoring is manual: the API offers `setGroupPerm`, `createUser` and group operations, so a
  restore script can be written, but there is no bulk import.
