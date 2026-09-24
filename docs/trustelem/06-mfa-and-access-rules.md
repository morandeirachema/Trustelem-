# MFA factors, enrollment and access rules

Date: 2026-09-23. Sources: [Multi-factors authentication](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication),
[Access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules),
[Loss of a second factor](https://trustelem-doc.wallix.com/books/trustelem-administration/page/loss-of-a-second-factor),
[Trustelem new features](https://trustelem-doc.wallix.com/books/trustelem-news/page/new-features).
Quotes are verbatim.

## 1. Factors available

| Factor | Notes (verbatim where quoted) | Works over SAML/OIDC | Works over RADIUS/LDAP |
|--------|-------------------------------|----------------------|------------------------|
| WALLIX Authenticator (push + TOTP) | "if the network is up the user receives a push notification, otherwise he can use a TOTP"; desktop version "in the Microsoft store only" and uses WNS | yes | yes (push-wait or TOTP) |
| TOTP authenticator (any app, NFC hardware token) | standard TOTP | yes | yes (Access-Challenge or code appended to the password) |
| Second-step passkey (FIDO2/WebAuthn) | "previously named Security key"; YubiKey, Feitian, Windows Hello, Touch ID/Face ID, password managers, cross-device QR with a 5-minute window | yes | no |
| SMS | "additional cost, not available by default" | yes | implied, not explicit: "You can use a code with LDAP (TOTP or OTP)"; only passkeys are excluded (gap T16) |
| E-mail OTP | "disable by default"; weak | yes | implied, not explicit (same sentence; gap T16) |

For a PAM tenant: WALLIX Authenticator for everyone (the only factor that gives push on the
native RDP/SSH path), passkeys for administrators on the web path, TOTP as the fallback, SMS
and e-mail off.

## 2. Enable factors

**Security settings > Authentication factors**. "The first part, Manage authentication factors,
has 2 parameters: Login, and User can reset token":

- **Login**: "Users can use the selected factor for a multi factors authentication. An
  administrator can do a manual enrollment for users."
- **User can reset token**: "the defined users can use their dashboard to reset this factor:
  https://mydomain.trustelem.com/#security". Restrict it to a group of users who are allowed to
  re-enrol themselves; for privileged users prefer administrator-driven re-enrollment after an
  identity check.

## 3. Passkey policy

**Security settings > Passkeys** "contains one policy per class" (second-step passkeys and
one-step passwordless passkeys are separate classes). Levels: Recommended, Strict, Custom. The
Custom rules are: User verification; Where the passkey can live; Verify the device's make and
model; Minimum FIDO certification; Restrict to specific devices; Restrict to specific providers;
Disable a passkey if cloning is detected. Rules are "checked at enrollment" and "checked again
at every login". A duplicate credential across accounts is refused and the audit event
`webauthn_duplicate_credential` is "forwarded to your SIEM with the other 2nd factor events".

Recommendation for administrator groups: Strict (hardware-bound, certified authenticators) or
Custom with attestation and clone detection on.

## 4. Enrollment

Three routes, all on the same page:

1. **Manual by an administrator** from the user's dashboard entry, or by e-mail: "send the
   enrollment link to Trustelem Primary Email or choose another one".
2. **Campaign by group**: "Users in the selected groups will be involved... only if they don't
   already have a 2nd factor. If you select multiple factors, users will have a selector to
   enroll only one of them." Options: "Automatic enroll by email" (links sent automatically)
   and "Automatic enroll during login": "every time users authenticate on Trustelem login
   page, they will have a window asking them to enroll a new factor. They can skip the
   enrollment, but the window will continue to appear".
3. **Self-service reset (re-enrollment)** at `https://<tenant>.trustelem.com/#security`, only for
   the users defined under "User can reset token": "the defined users can use their dashboard to
   reset this factor".

Sequence for a PAM roll-out: run the campaign on the PAM groups before any access rule requires
two factors. The vendor recommends "an enrollment campaign by email if possible" for the Bastion
RADIUS populations, who may never open the Trustelem login page, and "automatic enroll during
login" for the Access Manager SAML populations; otherwise users fail: on LDAP "If the user
provides login + password and doesn't have WALLIX Authenticator, the authentication will failed",
and on RADIUS there is no enrolled app to receive the push (*inference*).

## 5. Lost or replaced factor

"Use an alternative method" > "Ask for a rescue code" on the login page; "All administrators
receive an email"; an administrator opens **Alerts** and clicks "Rescue code" after checking
the user's identity; "The user has 24h to use this one-time rescue code." Then the user
re-enrols. Record the identity check in the ticketing system; `listAlerts` returns "all the
alerts of the 30 previous days" (`markAlertAsRead` clears them); the Alerts page retention is
not documented.

## 6. Access rules

Rules are set per application, for a user, a group or everyone. Semantics (verbatim):

| Protocol | Values |
|----------|--------|
| Web (SAML, OIDC, no-SSO apps), separately for the internal and the external zone | no rule; Default; 1 factor ("login + password OR certificate OR Kerberos"); 2 factors; Forbidden |
| LDAP (no zones) | no rule ("users can't be sourced and can't be authenticated"); 1 factor ("users can be sourced, and only one authentication factor"); 2 factors (push wait "only possible if the app have a timeout long enought", or "login + password and TOTP code sticked together (for instance: mypasswordTOTP)"; "If the user provides login + password and doesn't have WALLIX Authenticator, the authentication will failed"); Forbidden |
| RADIUS (no zones) | no rule; Always allow ("accept the authentication if the login is known, without any verification on the password/2nd factor"); 2nd factor only ("used when you have a radius authentication in addition to another authentication (AD usually)"); 2 factors; Forbidden |

Priority: "1/ A user access rule wins over a group access rule, whether it is more restrictive
or not, a group rule wins over an "everyone" rule. 2/ The most restrictive access rule wins.
In summary: Access forbidden (user) > 2 factors (user) > 1 factor (user) > Access forbidden
(group) > 2 factors (group) > 1 factor (group)".

*Default* resolves to "Security settings / General / Default authentication level for users".
The internal zone is "Security settings / General / Internal network. Internal IPs are usually
the public IPs of the company offices."

## 7. Rule set for the PAM design

| Application | Rule target | Web internal | Web external | LDAP | RADIUS |
|-------------|-------------|--------------|--------------|------|--------|
| Access Manager (SAML) | PAM user groups | 2 factors | 2 factors | | |
| Access Manager (SAML) | everyone else | Forbidden | Forbidden | | |
| Access Manager (RADIUS, optional path) | PAM user groups | | | | 2nd factor only |
| Bastion (RADIUS for AD users) | PAM user groups | | | | 2nd factor only |
| Bastion (RADIUS for AD users) | automation exemption group | | | | Always allow |
| Bastion (RADIUS for Bastion-local users) | the few local accounts | | | | 2 factors |
| Bastion (LDAP for Trustelem local users) | partner group | | | 1 factor (plus RADIUS 2nd factor only) | 2nd factor only |
| Trustelem admin console | administrators | 2 factors | 2 factors | | |

Notes:

- A user rule overrides a group rule "whether it is more restrictive or not", so temporary
  exemptions are done with a user rule and must be reviewed (list them with the API
  `listPerms`).
- "Trustelem users will not be found by the Bastion before having an access rule (1 or 2
  factors)" on LDAP ([Bastion app page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion));
  create the rule before testing the Bastion directory.
- Pilot and rollback: on RADIUS change the group rule between *Always allow* and *2nd factor
  only*; on the web zones between *Default* or *1 factor* and *2 factors*. The rollback is a
  console change and needs no appliance change (*inference* from where the rule is evaluated).

## 8. MFA session on RADIUS

"on a Trustelem Bastion application, when you activate Radius, you can also activate an MFA
session"; the user authenticates once with the second factor and "for the duration defined on
Trustelem and as long as he remains on the same network, he will not be asked to provide his
2nd factor again". The example is a GUI login followed by SSH within one hour. It requires the
Bastion option "Use mobile device for Two-Factor Authentication (2FA)". The duration values are
not documented, nor what "same network" is based on; *inference:* the Bastion's
Framed-IP-Address attribute is the likely input.

Choose the duration per risk: one working session (for example 8 hours) for operators on
managed workstations, shorter for shared or external networks. The web (SAML) path has its own
IdP session. Neither a "remember this browser" option nor push number matching appears in any
of the four Trustelem documentation books (searched on 2026-09-23); treat both as unavailable
unless WALLIX confirms otherwise.
