# Trustelem integration with WALLIX Access Manager

Date: 2026-09-23. Sources: the Trustelem application page
[WALLIX Access Manager](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager),
the [WALLIX Bastion SAML page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml),
the [Access Manager 5.2.4.0 Administration Guide](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)
and the [Trustelem access rules page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules).
Quotes are verbatim from those pages.

## 1. Options

Trustelem has a dedicated **Access Manager** application template with two protocols:

| Option | Factors | User experience | When to use |
|--------|---------|-----------------|-------------|
| SAML for AD users | Trustelem password check via ADConnect plus any Trustelem factor (push, TOTP, passkey) | redirect to Trustelem, back to the portal, no further prompt; Bastion sessions launch without re-authentication | default choice; "Access Manager is compatible with SAML (recommanded), LDAP and Radius" [sic] ([WALLIX Authenticator](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/presentation)) |
| SAML for Trustelem local users | Trustelem password plus a factor | same as above; Login attribute is `email` | partners and contractors without AD accounts |
| RADIUS for AD users (AD domain in Access Manager, RADIUS as factor 2) | AD password checked by Access Manager, then a Trustelem TOTP | "first provide the AD login and password then provide the Trustelem TOTP code, even if the name of the input is Password again" | when Access Manager account mapping needs the AD password, or as a fallback path |
| RADIUS for Access Manager local users | local password plus TOTP, or Trustelem password plus TOTP | second "Password" prompt takes the TOTP | Access Manager local administrators |

## 2. SAML for AD users, step by step

Trustelem side:

1. **Apps**, create an **Access Manager** application.
2. **Root URL** of Access Manager, for example `https://wam.com/wabam`.
3. **Organization identifier**: "you can find it in: Access Manager → Configuration →
   Organizations". Constraints quoted: "The organization must have a Bastion configured" and
   "The organization must not already have the needed domain used ... a domain is unique in an
   organization."
4. **Domain**: "This domain has to match the Authentication domain name of your Active Directory
   Authentication domain" (on the Bastion).
5. Optional **Custom scripting** to send an Access Manager profile name in a SAML attribute
   named `profile`:

```javascript
//Define a default profile attribute which matches the name of the Access Manager profile
msg.setAttr("profile","User")
//Change the default profile depending on the email address
if(user.email=="rose.keler@trustelem.demo"){msg.setAttr("profile","Auditor")}
//Change the default profile depending on Trustelem groups
for (let group in groups) {
  if(group=="Trustelem admin group name"){msg.setAttr("profile","Administrator")}
}
```

6. Save and **download the metadata file**.

Access Manager side, **Configuration → SAML Identity Providers → +Add**:

| Tab | Field | Value (verbatim) |
|-----|-------|------------------|
| General | Organization | the one whose identifier was used on Trustelem |
| General | Name | free |
| Service Provider | WALLIX-AM Entity ID | `WALLIX-AM` |
| Service Provider | Sign Messages | OFF |
| Service Provider | Encrypt Messages | OFF |
| Service Provider | Signed Response | ON |
| Service Provider | Signed Assertion | ON |
| Identity Provider | metadata | "Import the Trustelem metadata file" |
| Identity Provider | Redirect Logout Uri | "Copy the Redirect Binding Uri and paste it in Redirect Logout Uri, replacing « sso » by « on_logout »" |
| Domain | Domain Name | "the domain for federated users : still the same value used on the Bastion and on Trustelem setup" |
| Domain | Default Profile | "Usually it is User" and "You can let No Default Profile if Trustelem is in charge of the profile." |
| Domain | Login | `uid` |
| Domain | Display Name Attribute | `displayname` |
| Domain | Email Attribute | `email` |
| Domain | Language Attribute | `lang` |
| Domain | Profile Attribute | empty, or `profile` if the script sends it |

Trustelem access rule for the Access Manager app: "you need internal and external set to
2 factors".

Why these SP settings matter (Admin Guide 10.3.2): Encrypt Messages "is required to disabled"
for the Bastion workflow, and "By disabling the attributes Signed Response and Signed
Assertion, any user will be able to connect to Access Manager as an administrator." Keep both
ON. A known issue (WAB-11153) drops the `SigAlg` parameter when Sign Messages is ON with the
Redirect binding, which is
another reason to leave it OFF ([release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html)).

## 3. SAML for Trustelem local users

Identical to section 2 with two differences quoted by the vendor:

- Domain: "This domain has to match the Authentication domain name of your Trustelem Active
  Directory Authentication domain" (the Bastion domain built on Trustelem LDAP, see
  `04-bastion-integration.md` scenario C).
- Domain tab attribute **Login → email** instead of `uid`. "reminder: a local Trustelem user
  must have an uid set to email".

## 4. Linking the Access Manager SAML domain to the Bastion

For the portal to show authorizations and launch sessions without a second login, the
Bastion must recognise the same federated identity:

- Bastion SAML external authentication and an **Other IdPs** authentication domain exist
  (see `04-bastion-integration.md` scenario D).
- "AM Domain Name = Bastion Authentication domain name" and "AM Login = Bastion Username".
- The same `groups` script is set on the Trustelem Access Manager application:
  `for (let g in groups){ msg.addAttr("groups",g); }`.
- On the Access Manager **Bastions** page, **Strip Domain** is OFF for that Bastion so that
  `login@domain` is preserved ([Admin Guide 10.3.2](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)).
- "the Access Manager should be > 5.0".

Sources: [WALLIX Bastion SAML page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml).

## 5. RADIUS for AD users

Trustelem side: create the **Access Manager** application, "Let the root url / organization
identifier / domain fields empty", enable **Radius**; on the **Service** page add the
**Access Manager** application to Trustelem Connect and enable Radius; "If you don't already
have a Bastion using it, you can let the default port 1812. Otherwise, you can use 2812, 3812...".

Access Manager side, **Configuration/RADIUS Servers**:

| Field | Value (verbatim) |
|-------|------------------|
| Organization | "select the organization where your AD users are" |
| Host | Trustelem Connect host |
| Protocol | **PAP** |
| Authentication Port | 1812 or 2812 |
| Connection Timeout | default "unless you have latency on your network" |
| Login type | simple login |
| Shared Secret | "this secret can be found in the Trustelem Access Manager app model" |
| NAS Identifier | empty |

Then **Test Connection**, **Save**, and edit the AD domain under **Configuration > Domains**:
Associated Authenticators = "Active Directory Authenticator Factor 1 - Radius Authenticator
Factor 2". Trustelem RADIUS access rule: **2nd factor only**.

User experience: "first provide the AD login and password then provide the Trustelem TOTP
code, even if the name of the input is Password again".

## 6. RADIUS for Access Manager local users

Same RADIUS server; edit the **local** domain:

- "if you want to keep AM user password: Local database Factor 1 - Radius Authenticator
  Factor 2", Trustelem rule **2nd factor only**; the user types the local password then the TOTP.
- "if you want to use Trustelem password: Local database Factor Unused - Radius Authenticator
  Factor 1", Trustelem rule **2 factors**.

## 7. Worksheet

| Item | Source | Value |
|------|--------|-------|
| Access Manager root URL | load balancer FQDN, path `/wabam` | |
| Organization identifier | AM > Configuration > Organizations | |
| Federated domain name | same on Trustelem app, AM SAML domain and Bastion authentication domain | |
| Trustelem metadata file | Trustelem app | |
| Redirect Logout Uri | Redirect Binding Uri with `sso` replaced by `on_logout` | |
| Login attribute | `uid` (AD users) or `email` (Trustelem users) | |
| Profile attribute | `profile` if scripted | |
| Default Profile | User | |
| RADIUS secret | Trustelem AM app model | |
| RADIUS port | 1812 / 2812 / 3812 | |
| Access rules | web internal+external *2 factors*; RADIUS *2nd factor only* | |

## 8. Verification

1. Open `https://<am>/wabam/<org>?domain=<DOMAIN>`; the browser is redirected to
   `https://<tenant>.trustelem.com/app/<ID>/sso`.
2. After password and second factor, the portal lists the Bastion authorizations of the user.
3. Launch an RDP and an SSH session: no Bastion prompt; the Bastion audit shows the session
   under `login@DOMAIN`.
4. Log out from the portal: the browser reaches the Trustelem `on_logout` endpoint.
5. Check the profile: a user in the admin group lands with the Administrator profile if the
   script is used.
6. SAML tracer (browser extension) shows the assertion signed by the current Trustelem
   certificate and the attributes `uid`/`email`, `displayname`, `email`, `lang`, `profile`.

## 9. Debug (vendor list, verbatim where quoted)

RADIUS: "Verify if the protocol is set to PAP" and remember the TOTP-in-password-field
behaviour.

SAML:

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
- Then: install the **SAML tracer** browser plugin, and as a global administrator set the
  SAML module to DEBUG in the **Settings > Logs** tab, reproduce, and download the log archive.
  TRACE and ALL "may expose sensitive information, including passwords"; switch back to DEBUG
  before generating an archive for support ([Admin Guide 15.2](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)).

Source: [WALLIX Access Manager page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager).
