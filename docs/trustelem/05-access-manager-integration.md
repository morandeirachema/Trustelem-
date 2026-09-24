# Trustelem integration with WALLIX Access Manager

> - **Purpose:** connect Access Manager to Trustelem by SAML (recommended) or RADIUS, with exact
>   field values, and link the federated identity to the Bastion.
> - **Audience:** Access Manager administrator, Trustelem administrator, PAM architect.
> - **Verified:** 2026-09-24, against the Trustelem documentation books as read on 2026-09-24;
>   Access Manager facts against Access Manager 6.0.5 (Administration, Users and Approvers, and
>   Deployment Guides); the Bastion side against Bastion 12.3.2.
> - **Sources:** Trustelem application pages
>   [WALLIX Access Manager](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager)
>   and [WALLIX Bastion SAML](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml),
>   [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) and
>   [Access Manager 6.0.5 Users and Approvers Guide](https://doc.wallix.com/) (login required),
>   [Access Manager release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html),
>   [Trustelem access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules).

Citation convention: the Access Manager guides are customer documentation behind the
doc.wallix.com login, and their section numbers refer to the 6.0.5 editions ("AG" is the
Administration Guide). Quotes without another source are from the Trustelem Access Manager page.

## 1. Options

Use SAML. Use RADIUS only when Access Manager account mapping needs the AD password, as a
fallback path, or for Access Manager local administrators. Trustelem has a dedicated
**Access Manager** application template with both protocols:

| Option | Factors | User experience | When to use |
|--------|---------|-----------------|-------------|
| SAML for AD users (section 2) | Trustelem password check via ADConnect plus any Trustelem factor (push, TOTP, passkey) | redirect to Trustelem, back to the portal, no further prompt; Bastion sessions launch without re-authentication | default choice; "Access Manager is compatible with SAML (recommanded), LDAP and Radius" [sic] ([WALLIX Authenticator](https://trustelem-doc.wallix.com/books/wallix-authenticator/page/presentation)) |
| SAML for Trustelem local users (section 3) | Trustelem password plus a factor | same as above; Login attribute is `email` | partners and contractors without AD accounts |
| RADIUS for AD users (section 5): AD domain in Access Manager, RADIUS as factor 2 | AD password checked by Access Manager, then a Trustelem TOTP | AD password, then the TOTP typed in a second "Password" prompt (section 5) | when Access Manager account mapping needs the AD password, or as a fallback path |
| RADIUS for Access Manager local users (section 6) | local password plus TOTP, or Trustelem password plus TOTP | second "Password" prompt takes the TOTP | Access Manager local administrators |

## 2. SAML for AD users, step by step

Create the Trustelem Access Manager application, import its metadata as a SAML identity provider
in Access Manager, and set the access rule to 2 factors on both zones.

### Trustelem application for SAML

1. **Apps**: create an **Access Manager** application.
2. **Root URL** of Access Manager, for example `https://wam.com/wabam`.
3. **Organization identifier**: "you can find it in: Access Manager → Configuration →
   Organizations". Constraints quoted: "The organization must have a Bastion configured" and
   "The organization must not already have the needed domain used ... a domain is unique in an
   organization."
4. **Domain**: "This domain has to match the Authentication domain name of your Active Directory
   Authentication domain" (on the Bastion).
5. Optional **Custom scripting**, to send an Access Manager profile name in a SAML attribute
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
7. Access rule for the Access Manager app: "you need internal and external set to 2 factors".

### Access Manager SAML identity provider

**Configuration → SAML Identity Providers → +Add**:

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

### Why the service provider settings matter

Keep Signed Response and Signed Assertion ON, and Encrypt Messages and Sign Messages OFF.

- "Disable encryption when configuring SAML to authenticate to WALLIX Bastion through WALLIX
  Access Manager." ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.3.2.1)
- "Disabling the Signed Response and Signed Assertion options allows any user to connect to
  WALLIX Access Manager as an administrator." (AG 4.3.3.2.1)
- The same tab has **Force Authent.** and **Authent. Expir. Delay** ("Define the authentication
  expiration time (in minutes)"). The guide gives no default and no clock-skew tolerance
  (gap A4).
- The Access Manager 5.2.4.0 release notes list known issue WAB-11153: "SAML Authentication can
  fail due to a missing "SigAlg" query param with Signed Messages activated and a "Redirect"
  binding type". That is another reason to leave Sign Messages OFF
  ([release notes](https://pam.wallix.one/documentation/release-notes/am-rn-en.html); the 6.0.5 guides do not mention it).

### Domain name, bindings and metadata

- Domain Name: the same value as the Bastion Domain server name and Authentication domain name
  (`TRUSTELEM`). The Access Manager, Bastion and Trustelem rules are in
  [SAML assertion and naming, section 1.1](../reference/saml-assertion-and-naming.md#11-which-bastion-field-carries-the-domain-name).
- Attribute names "are case-sensitive" (AG 4.3.3.1).
- Access Manager "supports both HTTP Redirect and HTTP POST bindings", with IdP-initiated or
  SP-initiated flows (AG 4.3.3.1, 4.3.3.2).
- The service provider metadata file (Download below **Metadata File**, shown only when
  editing) "is supported by some Identity Providers such as Trustelem, EntraID or Okta"
  (AG 4.3.3.2.4).
- "IPv6 is not supported for SAML authentications." (AG 4.3.3)

### Organization default domain

Set the organization's **Default Domain** to `TRUSTELEM` (**Configuration > Organizations**,
edit the organization) so users reach `https://<am-fqdn>/wabam/<org>` without typing the domain.
The Default Domain "Specifies the domain used when no domain is provided in the request URL"
([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 3.1.1 and 3.1.4;
[AM chapters 8 and 10](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf)).

## 3. SAML for Trustelem local users

Repeat section 2 with the two differences quoted by the vendor:

- Domain: "This domain has to match the Authentication domain name of your Trustelem Active
  Directory Authentication domain", that is the Bastion domain built on Trustelem LDAP
  ([chapter 04, scenario C](04-bastion-integration.md#5-scenario-c-trustelem-local-users-through-trustelem-ldap-plus-radius)).
- Domain tab attribute **Login** = `email` instead of `uid`, because a local Trustelem user's uid
  is its e-mail (vendor reminder quoted in section 9).

## 4. Linking the Access Manager SAML domain to the Bastion

The portal shows authorizations and launches sessions without a second login only when the
Bastion recognises the same federated identity:

- A Bastion SAML external authentication and an **Other IdPs** authentication domain exist
  ([chapter 04, scenario D](04-bastion-integration.md#6-scenario-d-saml-20-to-the-bastion-with-or-without-access-manager)).
- The domain name and the login attribute are identical in Trustelem, Access Manager and the
  Bastion ([SAML assertion and naming, section 1](../reference/saml-assertion-and-naming.md#1-names-that-must-match)).
- The Trustelem Access Manager application carries the `groups` script of chapter 04,
  scenario D.
- On the Access Manager **Bastions** page, **Strip Domain** is OFF for that Bastion
  ([SAML assertion and naming, section 1.2](../reference/saml-assertion-and-naming.md#12-strip-domain)).
- "the Access Manager should be > 5.0". This design uses 6.0.5; its Bastion compatibility is in
  the [architecture overview, section 2](../architecture/01-overview.md#2-product-naming-and-versions).

Source: [WALLIX Bastion SAML page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml).

## 5. RADIUS for AD users

Access Manager checks the AD password as factor 1 and asks Trustelem for a TOTP as factor 2.

### Trustelem application for RADIUS

1. Create the **Access Manager** application. "Let the root url / organization identifier /
   domain fields empty". Enable **Radius**.
2. On the **Service** page, add the **Access Manager** application to Trustelem Connect and
   enable Radius. Choose the port as described in
   [chapter 03, section 1](03-trustelem-connect.md#1-role-and-listeners) (1812, or 2812 when a
   Bastion already uses 1812).
3. Trustelem RADIUS access rule: **2nd factor only**.

### Access Manager RADIUS server and domain

**Configuration/RADIUS Servers**:

| Field | Value (verbatim) |
|-------|------------------|
| Organization | "select the organization where your AD users are" |
| Host | Trustelem Connect host |
| Protocol | **PAP** (Access Manager offers AUTO, PAP and CHAP; "When AUTO is selected, the system first tries CHAP and switches to PAP if CHAP fails.") |
| Authentication Port | 1812 or 2812 |
| Connection Timeout | default "unless you have latency on your network" |
| Login type | simple login |
| Shared Secret | "this secret can be found in the Trustelem Access Manager app model" |
| NAS Identifier | empty |

This design declares both Trustelem Connect VMs as RADIUS servers, each on port 2812, the
Access Manager listener ([chapter 03, section 1](03-trustelem-connect.md#1-role-and-listeners)).
Authenticators with the same factor are tried in Priority order
([farm runbook, section 3.2](../runbooks/access-manager-farm.md#32-install-the-replication)).
Then:

1. **Test Connection**, then **Save**.
2. Edit the AD domain under **Configuration > Domains**: Associated Authenticators = "Active
   Directory Authenticator Factor 1 - Radius Authenticator Factor 2".
3. Set **Factor used for account mapping** to the AD factor: "If LDAP server is also set as the
   account mapping factor, the credentials used with LDAP are used for sessions relying on
   account mapping." ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.4.1).

User experience: "first provide the AD login and password then provide the Trustelem TOTP
code, even if the name of the input is Password again".

### Access Manager RADIUS facts

From the [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.6 unless
stated:

- "WALLIX Access Manager also supports the challenge–response mechanism, allowing multiple
  challenge exchanges during RADIUS authentication, for example, to implement multi-factor
  authentication (MFA)". Push is not named (gap A4).
- The default port is 1812, and no timeout default is given.
- "IPv6 is not supported for RADIUS authentication."
- The factor chain "does not apply to SAML and OIDC" (AG 4.4.1).

### Account mapping for SAML users

SAML users who need account mapping can instead enter a "Target Password Saved for Account
Mapping with SAML and OIDC" in their preferences. "The password is not stored in WALLIX Access
Manager and only lasts for the session."
([Access Manager 6.0.5 Users and Approvers Guide](https://doc.wallix.com/) 3.3.1).

## 6. RADIUS for Access Manager local users

Use the same RADIUS server and edit the **local** domain. Two choices:

- Keep the Access Manager password: "if you want to keep AM user password: Local database
  Factor 1 - Radius Authenticator Factor 2", with the Trustelem rule **2nd factor only**. The
  user types the local password, then the TOTP.
- Use the Trustelem password: "if you want to use Trustelem password: Local database Factor
  Unused - Radius Authenticator Factor 1", with the Trustelem rule **2 factors**.

## 7. Worksheet

Fill this in before the change window.

| Item | Source | Value |
|------|--------|-------|
| Access Manager root URL | load balancer FQDN, path `/wabam` | |
| Organization identifier | AM > Configuration > Organizations | |
| Federated domain name | same on Trustelem app, AM SAML domain and Bastion authentication domain ([naming reference](../reference/saml-assertion-and-naming.md)) | |
| Trustelem metadata file | Trustelem app | |
| Redirect Logout Uri | Redirect Binding Uri with `sso` replaced by `on_logout` | |
| Login attribute | `uid` (AD users) or `email` (Trustelem users) | |
| Profile attribute | `profile` if scripted | |
| Default Profile | User | |
| RADIUS secret | Trustelem AM app model | |
| RADIUS port | 1812 / 2812 / 3812 | |
| Access rules | per group, as in [chapter 06, section 7](06-mfa-and-access-rules.md#7-rule-set-for-the-pam-design) | |

## 8. Verification

Run these checks with a pilot user of each population.

1. Open `https://<am>/wabam/<org>?domain=<DOMAIN>`. The browser is redirected to
   `https://<tenant>.trustelem.com/app/<ID>/sso`.
2. After the password and the second factor, the portal lists the user's Bastion
   authorizations.
3. Launch an RDP and an SSH session: no Bastion prompt appears, and the Bastion audit shows the
   session under `login@DOMAIN`.
4. Log out from the portal: the browser reaches the Trustelem `on_logout` endpoint.
5. Check the profile: a user in the admin group lands with the Administrator profile if the
   script is used.
6. A SAML tracer (browser extension) shows the assertion signed by the current Trustelem
   certificate, and the attributes `uid`/`email`, `displayname`, `email`, `lang`, `profile`.

## 9. Debug

Most SAML failures are copy-and-paste errors, clock drift or a pre-existing user. The vendor
list, verbatim where quoted:

### RADIUS checks

"Verify if the protocol is set to PAP", and remember that the TOTP goes in the second
"Password" field (section 5).

### SAML checks

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

### SAML debug logs

1. Install the **SAML tracer** browser plugin.
2. As a global administrator, set the SAML module to DEBUG on
   **Settings > Application Settings > Logs** tab.
3. Reproduce the problem, then click **Download Logs Archive (ZIP)**.

"The TRACE or ALL modes may expose sensitive information, including passwords." Change the mode
to DEBUG before generating an archive for support
([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 9.7.1). The files are in
`/var/log/wabam` (AG 9.7). Log levels are stored in `wabam.properties` and do not replicate, so
set them on the node that serves the test
([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 6).

Source: [WALLIX Access Manager page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager).
