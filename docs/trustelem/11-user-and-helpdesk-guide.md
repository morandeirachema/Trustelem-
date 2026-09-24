# User and help-desk guide

Date: 2026-09-24. What privileged users see once Trustelem MFA is live, and what the help desk
does when they call. Screens and wording follow the vendor pages cited in chapters 04 to 08;
the help-desk actions follow [06 MFA and access rules](06-mfa-and-access-rules.md) and
[07 Operations](07-operations.md). Bastion log statements are verified against the Bastion
12.4.3 SIEM Logs Guide and Auditor Guide, WALLIX customer documentation behind the
doc.wallix.com login ([doc.wallix.com](https://doc.wallix.com/)).

## 1. Enrolling a second factor

1. Install **WALLIX Authenticator** on the phone (iOS or Android; a Windows desktop version
   exists in the Microsoft Store).
2. Open `https://<tenant>.trustelem.com`, log in with the Active Directory password. If an
   enrollment campaign is running, a window asks to enrol a factor; follow it in the app (the
   exact enrollment screens are not described in the Trustelem books). The window returns at every login until it is done.
3. Optional, for administrators on the web path: a passkey (YubiKey, Windows Hello, Touch ID)
   enrolled by campaign, or re-enrolled from `https://<tenant>.trustelem.com/#security` when
   "User can reset token" allows it.
4. From then on, keep the phone at hand: it receives a push at each privileged login, and
   shows a TOTP code when there is no network ("if the network is up the user receives a push
   notification, otherwise he can use a TOTP", [MFA](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication)).

Help desk: administrators can enrol a user manually or send an enrollment link by e-mail from
the user's entry; a user cannot reset a factor unless the "User can reset token" switch
includes them.

## 2. Logging in through the web portal

1. Open `https://<am-fqdn>/wabam/<org>`.
2. The browser is redirected to the Trustelem login page (the address bar shows
   `<tenant>.trustelem.com`). Enter the AD login and password.
3. Approve the push on the phone, or choose "Use an alternative method" to type the code from
   the app or to use a passkey.
4. The portal opens with the list of authorised sessions and passwords. Launching a session
   never asks for a password again.

Symptoms and causes:

| The user says | Likely cause | Action |
|---------------|--------------|--------|
| "The page says access is refused after the password" (wording varies) | user not in a group with an access rule | check group membership and the app's access rules |
| "No push arrives" | phone offline, app not enrolled, notifications blocked | use the code from the app; re-enrol if needed |
| "After Trustelem I land on an error page" | SAML mismatch (domain name, attributes, certificate) or clock skew | escalate to the PAM team with the time of the attempt |
| "The portal is empty, no sessions" | login does not match a Bastion user (Strip Domain, mapping) | escalate; check `login@DOMAIN` on the Bastion |

## 3. Logging in with a native RDP or SSH client

RDP (`mstsc`):

1. Connect to the Bastion address (or its load-balanced name) on port 3389.
2. The Bastion login screen appears: enter `login@domain` and the AD password.
3. With "Use mobile device" enabled the Bastion expects a push; approve it on the phone (or, if
   the screen asks for a code, type the TOTP from the app).
4. Pick the target from the list.
5. If the connection fails before the login screen because Kerberos is enabled on the Bastion
   RDP proxy and the user does not log in with Kerberos, add
   `enablecredsspsupport:i:0` and `authentication level:i:2` to the `.rdp` file (FreeRDP:
   `/sec:tls`).

SSH (OpenSSH, PuTTY, WALLIX-PuTTY):

1. `ssh {MY_ID}@{BASTION}` opens the target selector (the Bastion login `{MY_ID}` is
   `login@domain` when the domain is not the default one); a direct connection is
   `ssh -l {ACCOUNT}@{DOMAIN}@{DEVICE}+{SERVICE}+{MY_ID} {BASTION}`, or use the connection file
   downloaded from the web UI ([Bastion Users Guide 8.5.3 and 8.5.5](https://pam.wallix.one/documentation/user-doc/bastion_en_user_guide.pdf)).
2. Enter the AD password when prompted.
3. A second prompt appears (keyboard-interactive): approve the push or type the code.

Within the MFA session window (defined by the PAM team, on the same network) the second
factor is not asked again.

Scripts and automation must not use accounts subject to MFA; the PAM team assigns the
`Always allow` exemption to the automation group.

## 4. Lost or replaced phone

1. On the login page choose "Use an alternative method" then "Ask for a rescue code".
2. All Trustelem administrators receive an e-mail; the help desk verifies the caller's identity
   according to the identity-check procedure and records the ticket.
3. An administrator opens **Alerts** in the admin console and clicks "Rescue code".
4. The user has 24 hours to use the one-time code, then enrols the new phone.

## 5. Forgotten Trustelem password

`https://<tenant>.trustelem.com/forgot`, with the factors configured under Security settings >
Password management. Self-service password reset "allows Trustelem users to reset a lost password, even if they are
from Active Directory" once "Password recovery" is enabled on the directory and the connector
account has the reset delegation ([SSPR](https://trustelem-doc.wallix.com/books/trustelem-administration/page/self-service-password-reset));
otherwise AD users go through the normal AD process.

## 6. Help-desk checklist per call

1. Which path: portal, RDP client, SSH client?
2. Exact time and the address the user connected from.
3. Trustelem Logs page: is there an entry for the user at that time? If not, the request never
   reached Trustelem (connector or firewall), or it was an LDAP search for a user without an
   access rule, which "you will not see any logs" for (chapter 08).
4. If there is an entry: user not found, no access rule, no second factor, or rejected push.
5. Bastion evidence for the same time:
   - Audit > Authentication history (RDP and SSH proxy logins only, not the web interface):
     Result and the Diagnosis column. "Authentication attempts with an expired OTP are not
     attributed to a user and are logged as [unknown username]", so search by time and source
     IP as well as by user name ([Bastion 12.4.3 Auditor Guide](https://doc.wallix.com/) 10).
   - For the PAM team or SIEM: the `[wabauth]` lines, `status` (`started`, then `success`,
     `failure` or `canceled`) and `infos`. The `started` line shows which domain identified the
     user (`identified with {domain}({TYPE})`); a failure only says "Authentication failed", so
     the reason comes from the Trustelem entry in item 4
     ([Bastion 12.4.3 SIEM Logs Guide](https://doc.wallix.com/) 2.1).
6. Escalate to the PAM team with items 1 to 5 and [08 Troubleshooting](08-troubleshooting.md).

## 7. Emergency (Trustelem unreachable)

Users cannot obtain a second factor. Existing sessions continue. Only the PAM team's break-glass
account logs in to the Bastion from the administration network. The help desk does not
disable MFA; the decision to temporarily remove the RADIUS secondary authentication belongs to
the PAM team and is recorded.
