# MFA factors, enrollment and access rules

> - **Purpose:** choose and enable the Trustelem factors, enrol the PAM users, and set the
>   access rules per application and group.
> - **Audience:** Trustelem administrator, security officer, helpdesk lead.
> - **Verified:** 2026-09-24, against the Trustelem documentation books as read on 2026-09-24.
> - **Sources:** [Multi-factors authentication](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication),
>   [Access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules),
>   [Loss of a second factor](https://trustelem-doc.wallix.com/books/trustelem-administration/page/loss-of-a-second-factor),
>   [Trustelem new features](https://trustelem-doc.wallix.com/books/trustelem-news/page/new-features).

This chapter is the repository's home for the access rule values per group (section 7).

## 1. Factors available

For a PAM tenant, give everyone WALLIX Authenticator, the only factor that gives push on the
native RDP/SSH path. Add passkeys for administrators on the web path, keep TOTP as the fallback,
and leave SMS and e-mail off.

| Factor | Notes (verbatim where quoted) | Works over SAML/OIDC | Works over RADIUS/LDAP |
|--------|-------------------------------|----------------------|------------------------|
| WALLIX Authenticator (push + TOTP) | "if the network is up the user receives a push notification, otherwise he can use a TOTP"; desktop version "in the Microsoft store only" and uses WNS | yes | yes (push-wait or TOTP) |
| TOTP authenticator (any app, NFC hardware token) | standard TOTP | yes | yes (Access-Challenge or code appended to the password) |
| Second-step passkey (FIDO2/WebAuthn) | "previously named Security key"; YubiKey, Feitian, Windows Hello, Touch ID/Face ID, password managers, cross-device QR with a 5-minute window | yes | no |
| SMS | "additional cost, not available by default" | yes | implied, not explicit: "You can use a code with LDAP (TOTP or OTP)"; only passkeys are excluded (gap T16) |
| E-mail OTP | "disable by default"; weak | yes | implied, not explicit (same sentence; gap T16) |

## 2. Enable factors

Enable each factor under **Security settings > Authentication factors**, and allow
self-service reset only for a restricted group. "The first part, Manage authentication factors,
has 2 parameters: Login, and User can reset token":

- **Login**: "Users can use the selected factor for a multi factors authentication. An
  administrator can do a manual enrollment for users."
- **User can reset token**: "the defined users can use their dashboard to reset this factor:
  https://mydomain.trustelem.com/#security". Restrict it to a group of users who are allowed to
  re-enrol themselves. For privileged users, prefer administrator-driven re-enrollment after an
  identity check.

## 3. Passkey policy

Set administrator groups to Strict (hardware-bound, certified authenticators), or to Custom
with attestation and clone detection on.

- **Security settings > Passkeys** "contains one policy per class". Second-step passkeys and
  one-step passwordless passkeys are separate classes.
- Levels: Recommended, Strict, Custom.
- Custom rules: User verification; Where the passkey can live; Verify the device's make and
  model; Minimum FIDO certification; Restrict to specific devices; Restrict to specific
  providers; Disable a passkey if cloning is detected.
- Rules are "checked at enrollment" and "checked again at every login".
- A duplicate credential across accounts is refused. The audit event
  `webauthn_duplicate_credential` is "forwarded to your SIEM with the other 2nd factor events".

## 4. Enrollment

Run an enrollment campaign on the PAM groups before any access rule requires two factors.
Three routes exist, all on the same page:

1. **Manual, by an administrator**, from the user's dashboard entry, or by e-mail: "send the
   enrollment link to Trustelem Primary Email or choose another one".
2. **Campaign by group**: "Users in the selected groups will be involved... only if they don't
   already have a 2nd factor. If you select multiple factors, users will have a selector to
   enroll only one of them." Options:
   - "Automatic enroll by email": links are sent automatically.
   - "Automatic enroll during login": "every time users authenticate on Trustelem login page,
     they will have a window asking them to enroll a new factor. They can skip the enrollment,
     but the window will continue to appear".
3. **Self-service reset (re-enrollment)** at `https://<tenant>.trustelem.com/#security`, only for
   the users defined under "User can reset token" (section 2).

Choose the route per population:

- Bastion RADIUS populations may never open the Trustelem login page. The vendor recommends "an
  enrollment campaign by email if possible" for them.
- Access Manager SAML populations: "automatic enroll during login".

Users without an enrolled factor fail. On LDAP, a login and password without WALLIX
Authenticator fail (section 6). On RADIUS there is no enrolled app to receive the push
(*inference*).

## 5. Lost or replaced factor

The user asks for a rescue code, an administrator issues it after an identity check, and the
user re-enrols.

1. On the login page the user selects "Use an alternative method" > "Ask for a rescue code".
   "All administrators receive an email".
2. An administrator checks the user's identity, opens **Alerts** and clicks "Rescue code". "The
   user has 24h to use this one-time rescue code."
3. The user re-enrols.
4. Record the identity check in the ticketing system.

`listAlerts` returns "all the alerts of the 30 previous days", and `markAlertAsRead` clears
them. The Alerts page retention is not documented.

## 6. Access rules

Rules are set per application, for a user, a group or everyone. A user rule always wins over a
group rule, then the most restrictive rule wins. Semantics, verbatim from the
[access rules page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules):

| Protocol | Values |
|----------|--------|
| Web (SAML, OIDC, no-SSO apps), separately for the internal and the external zone | no rule; Default; 1 factor ("login + password OR certificate OR Kerberos"); 2 factors; Forbidden |
| LDAP (no zones) | no rule ("users can't be sourced and can't be authenticated"); 1 factor ("users can be sourced, and only one authentication factor"); 2 factors (push wait "only possible if the app have a timeout long enought", or "login + password and TOTP code sticked together (for instance: mypasswordTOTP)"; "If the user provides login + password and doesn't have WALLIX Authenticator, the authentication will failed"); Forbidden |
| RADIUS (no zones) | no rule; Always allow ("accept the authentication if the login is known, without any verification on the password/2nd factor"); 2nd factor only ("used when you have a radius authentication in addition to another authentication (AD usually)"); 2 factors; Forbidden |

Priority: "1/ A user access rule wins over a group access rule, whether it is more restrictive
or not, a group rule wins over an "everyone" rule. 2/ The most restrictive access rule wins.
In summary: Access forbidden (user) > 2 factors (user) > 1 factor (user) > Access forbidden
(group) > 2 factors (group) > 1 factor (group)".

*Default* and the internal zone come from two tenant settings, the default authentication level
and the internal network list. Both are set on day zero
([chapter 01, section 3](01-tenant-setup.md#3-day-zero-checklist)).

## 7. Rule set for the PAM design

This table is the reference for every rule value in the other chapters.

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

Operating notes:

- A user rule overrides a group rule "whether it is more restrictive or not". Make temporary
  exemptions with a user rule, and review them (list them with the API `listPerms`).
- On LDAP, Trustelem users are invisible to the Bastion until they have an access rule
  ([chapter 04, section 2](04-bastion-integration.md#2-common-prerequisite-the-bastion-application-and-trustelem-connect)).
  Create the rule before testing the Bastion directory.
- Pilot and rollback: on RADIUS, switch the group rule between *Always allow* and *2nd factor
  only*; on the web zones, between *Default* or *1 factor* and *2 factors*. The rollback is a
  console change and needs no appliance change (*inference* from where the rule is evaluated).

## 8. MFA session on RADIUS

An MFA session lets a Bastion RADIUS user skip the second factor for a set duration while on
the same network. "on a Trustelem Bastion application, when you activate Radius, you can also
activate an MFA session". The user authenticates once with the second factor, and "for the
duration defined on Trustelem and as long as he remains on the same network, he will not be
asked to provide his 2nd factor again".

- The example is a GUI login followed by SSH within one hour.
- It requires the Bastion option "Use mobile device for Two-Factor Authentication (2FA)".
- The duration values are not documented, nor what "same network" is based on.
  *Inference:* the Bastion's Framed-IP-Address attribute is the likely input; the Bastion side
  and the load-balancer caveat are in
  [chapter 04, section 3](04-bastion-integration.md#3-scenario-a-ad-users-with-radius-push-as-second-factor-recommended).

Choose the duration per risk: one working session (for example 8 hours) for operators on
managed workstations, shorter for shared or external networks. The web (SAML) path has its own
IdP session. Neither a "remember this browser" option nor push number matching appears in any
of the four Trustelem documentation books (searched on 2026-09-23); treat both as unavailable
unless WALLIX confirms otherwise.
