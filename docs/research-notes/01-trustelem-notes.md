# Research notes 01: WALLIX Trustelem / WALLIX One IDaaS

Working notes gathered on 2026-09-22, mainly from the vendor documentation portal
https://trustelem-doc.wallix.com (books: Trustelem administration, Trustelem applications,
WALLIX Authenticator, Trustelem news), wallix.com pages and press releases, app store
listings and RIPE whois. Facts are tagged verified, inference or gap.

## Product and positioning

- Verified (https://trustelem-doc.wallix.com/books/trustelem-administration/page/summary): "WALLIX Trustelem provides Identity-as-a-Service (IDaaS) including a cloud Single Sign-On (SSO) and Multi-Factor Authentication (MFA)". Two modes: SSO with or without MFA over web protocols, and "LDAP or Radius authentication, with or without MFA, but with no possibilities of SSO". Tenant URLs `https://<tenant>.trustelem.com` (user dashboard) and `https://admin-<tenant>.trustelem.com` (admin console).
- Verified: Trustelem was a French startup founded in 2013, acquired by WALLIX in July 2019 (https://www.actusnews.com/en/wallix/pr/2019/07/03/wallix-signs-the-first-acquisition-under-its-ambition21-plan-with-trustelem-a-french-startup-in-cloud-access-management).
- Verified: current name "WALLIX One IDaaS" (https://www.wallix.com/products/idaas/); 2024 datasheet titled "WALLIX IDaaS / WALLIX One IDaaS" (https://www.wallix.com/wp-content/uploads/2024/01/DATASHEET_2024_WALLIX_IDaaS_EN67.pdf). WALLIX One platform launched 2023-12-14. WALLIX One Console announced 2026-01-27 to orchestrate PAM, IDaaS and IAG (https://www.wallix.com/press/wallix-launches-wallix-one-console-to-boost-operational-efficiency-and-simplify-cybersecurity-for-enterprises-and-organizations/). The doc portal, connectors, download site (dl.trustelem.com) and tenant domains still use the Trustelem name.
- Verified (https://trustelem-doc.wallix.com/books/wallix-authenticator/page/presentation): the MFA-only bundle for Bastion and Access Manager is sold as "WALLIX Authenticator".
- Verified: multi-tenant SaaS "hosted in European Data Centers" (https://www.wallix.com/products/idaas/). Inference from RIPE whois: production IPs 185.4.44.0/24 and 185.4.46.0/24 belong to NBS System CerberHost (France); relay endpoints relay-fr-01/02.wallix.com resolve to Microsoft address space (Azure). Not stated by WALLIX.
- Verified (https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability, .../incidents): availability above 99.99 % every year 2016 to 2022, 99.94 % in 2023 (datacenter migration); incidents logged on 2026-01-05 (storage failure at the hosting provider), 2025-11-27, 2025-10-22, 2024-02-19/20. A reseller cites a 99.9 % SLA; the contractual SLA is not published.
- Verified: WALLIX ISO/IEC 27001:2022 certificate (Certi-Trust, 2025-01-09) covering corporate IT, product development and support, with the WALLIX One SaaS platform managed within that framework (https://www.wallix.com/press/wallix-achieves-iso-iec-270012022-certification-to-maintain-the-highest-level-of-security-for-sensitive-digital-access/). Gap: no SecNumCloud, HDS or ANSSI qualification found for IDaaS.
- No public version numbers for the SaaS; mobile apps: iOS 2.3.17 (2024-08), Android updated 2026-08-14.

## Architecture components

- Admin console tabs (verified, summary page): Users, Groups, Directories, Apps, Services, Access rules, Security settings (General/Internal network, Authentication factors, Passkeys, Password management, Application certificates, IWA), API/scripts, Themes, Dashboard, Logs, Alerts, Sessions.
- Trustelem ADConnect (verified, https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect): installed on a customer VM (Windows Server .exe or Linux .tgz under `/opt/wallix/trustelem-adconnect/`), download https://dl.trustelem.com/adconnect/. "opens a websocket to admin.trustelem.com using port 443 ... encrypted by TLS protocol and with an additional symmetric encryption"; the cloud sends search and authentication requests over that websocket; the connector queries AD via LDAP(S) 389/636 with a read-only service account; "Trustelem does not store any password for Active Directory users". Sync by AD `memberOf` groups, configurable frequency, custom attributes. HA: "The recommendation is 2 VM at least, to have a failover system"; connectors listed in priority order; rolling upgrade. Proxy via `proxy = https://user:pass@proxy_IP:port` in config.ini. Windows service runs as the AD technical user; also used for IWA/Kerberos validation and AD password reset.
- Trustelem Connect (verified, https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect): local "LDAP server / Radius server" forwarding LDAP search/bind and "Radius Access request, Radius Challenge request" to the cloud over the same outbound websocket; one listening port per protocol per application; defaults TCP 2001 (LDAP) and UDP 1812 (RADIUS, 2812 if busy); listen on localhost, `*` or a specific IP; LDAPS/StartTLS with own PEM certificate; Linux runs as user `trustelem` under systemd; download https://dl.trustelem.com/connect/; two VMs recommended. Emulates AD: user DN `CN=<user>,DC=<tenant>,DC=trustelem,DC=com`, groups under `OU=Groups`; local users bind with `mail`, AD-synced users with sAMAccountName, UPN or mail. Also carries outbound SCIM provisioning and SIEM log export.
- WALLIX Authenticator app (verified, https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication): mobile (iOS/Android) and Windows desktop app; push notification when online, TOTP otherwise; Android package `com.trustelem.auth` "WALLIX Authenticator - previously Trustelem Authenticator" (https://play.google.com/store/apps/details?id=com.trustelem.auth); iOS (https://apps.apple.com/us/app/wallix-authenticator/id1122073235); Windows (https://apps.microsoft.com/detail/9n2rjz0ftm07), which needs WNS push URLs allowed.
- Integrated Windows Authentication uses ADConnect on a domain-joined host plus SPN `HTTP/<tenant>.trustelem.com` (https://trustelem-doc.wallix.com/books/trustelem-administration/page/integrated-windows-authentication).
- Not found: Windows credential provider, ADFS adapter, browser extension, password vault.

## Identity sources

- Active Directory via ADConnect (sync, password validation, password reset, IWA).
- Azure AD / Entra ID: app registration with Graph `Directory.Read.All`; optional password validation through a public-client flow, impossible for federated domains (https://trustelem-doc.wallix.com/books/trustelem-administration/page/azure-ad-synchronization).
- Google Workspace: attribute sync only, passwords stored by Trustelem.
- Local Trustelem users: primary email is the login; recommended for partners and backup administrators (https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-local-users).
- SCIM: Trustelem is a SCIM 2.0 client for outbound provisioning through Trustelem Connect (https://trustelem-doc.wallix.com/books/trustelem-administration/page/scim-client); not documented as a SCIM server.
- External IdP inbound federation with just-in-time provisioning (https://trustelem-doc.wallix.com/books/trustelem-administration/page/authentication-with-an-external-idp).
- Gap: no dedicated LDAP-source page; no CSV importer (the API is positioned for that).

## Protocols as identity provider

- SAML 2.0 (verified, https://trustelem-doc.wallix.com/books/trustelem-applications/page/saml-2 and .../export/html): per-app endpoints `https://<tenant>.trustelem.com/app/<ID>/metadata`, `/sso`, `/on_logout`; IdP fields EntityID, ACS, NameID attribute and format, attribute list, RelayState, custom login URL, custom scripting. Signing certificates under Security settings > Application certificates with expiry alerts.
- OpenID Connect (verified, https://trustelem-doc.wallix.com/books/trustelem-applications/page/openid-connect): authorization-code and implicit flows; issuer `https://<tenant>.trustelem.com/app/<ID>`, discovery, `/auth`, `/token`, `/userinfo`, RS256 JWKS; logout through `redirect_uri?logout=<url>`. WALLIX recommends OIDC over SAML for new apps.
- OAuth 2.0 generic client; custom claims by TypeScript scripts (`msg.setAttr`, `msg.addAttr`, `groups`) (https://trustelem-doc.wallix.com/books/trustelem-administration/page/application-scripts).
- RADIUS through Trustelem Connect: Access-Request plus Challenge (password then OTP or push), password and code concatenated, push-wait, or "2nd factor only" when the primary password is checked elsewhere. The Access Manager page specifies PAP; CHAP support and returned attributes are not documented (gap). "Non-systematic MFA" session: no re-prompt for a defined duration on the same network (https://trustelem-doc.wallix.com/books/trustelem-news/page/new-features).
- LDAP, LDAPS and StartTLS through Connect: search and bind, AD-like schema, MFA by push-wait or password plus TOTP concatenated; passkeys unusable over LDAP and RADIUS.
- Kerberos/IWA (internal zone, user portal only). X.509 listed in datasheets, documentation "coming soon".
- Not documented: WS-Federation, CAS, form-based password vaulting.
- Admin API (https://trustelem-doc.wallix.com/books/trustelem-administration/page/api): TypeScript handlers at `https://admin.trustelem.com/api/script/<key>/<script>` with Bearer API keys restricted by IP; objects users, groups, applications, permissions, logs (30 days), alerts, sessions, auth tokens. Enabled by WALLIX support.

## MFA methods

- Verified (https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication): SMS (extra cost, off by default); TOTP (any authenticator app or NFC hardware device); WALLIX Authenticator push with TOTP fallback; second-step passkey (FIDO2/WebAuthn: YubiKey, Feitian, Windows Hello, Touch ID/Face ID, cross-device via QR, password managers); email OTP (weak, off by default). One-step passwordless passkeys are a separate class.
- Passkey policy: Recommended / Strict (hardware only) / Custom (user verification, storage location, attestation, minimum FIDO certification level, allowed models enforced through the FIDO Alliance MDS, clone detection). Duplicate credential across accounts refused with audit event `webauthn_duplicate_credential`.
- Enrollment: per-factor Login and "User can reset token" switches; admin manual enrollment; enrollment campaigns by group with automatic enrol by email or during login; self-service at `https://<tenant>.trustelem.com/#security`.
- Lost factor: one-time rescue code valid 24 h released by an admin from Alerts (https://trustelem-doc.wallix.com/books/trustelem-administration/page/loss-of-a-second-factor).
- Not found: HOTP, voice call, Yubico OTP mode, printed backup codes, hardware token seed import.

## Access rules

- Verified (https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules): rules per application for user, group or everyone; web apps distinguish internal versus external zone by public IP (Security settings > General > Internal network); values no rule, Default, 1 factor, 2 factors, Forbidden. LDAP: 1 factor, 2 factors, Forbidden (also controls whether the user is searchable). RADIUS: Always allow, 2nd factor only, 2 factors, Forbidden. Priority: user rule beats group rule beats everyone, then most restrictive wins. Subscription-wide default authentication level; admin console can require 2 factors.
- Not documented: geolocation, device posture, time windows, risk scoring, browser "remember this device".

## Application catalog

- About 80 templates (https://trustelem-doc.wallix.com/books/trustelem-applications/export/html) including AWS, Google Workspace, Office 365, Salesforce, Slack, GitHub, VPNs (F5 BIG-IP, Pulse Secure, OpenVPN). Generic models: SAML 2, OpenID Connect, OAuth 2, Basic no SSO, LDAP, RADIUS.
- WALLIX Bastion model (https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion): LDAP (port 2001, bind user `trustelem`, base DN from the model, login attribute `mail`, StartTLS) and RADIUS (1812 or 2812, secret from the model). SAML to Bastion since Bastion 12 with the generic SAML2 model (https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml).
- WALLIX Access Manager model (https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager): RADIUS (PAP) and SAML (Login = uid or email, displayname, email, lang). "Access Manager is compatible with SAML (recommanded), LDAP and Radius; The Bastion is compatible with LDAP and Radius" (WALLIX Authenticator book).

## Administration and operations

- Roles: users flagged with administration rights; delegated administration via the `groupManager` attribute (enabled by WALLIX sales) (https://trustelem-doc.wallix.com/books/trustelem-administration/page/delegated-administration).
- Monitoring: dashboard with authentication success and failure counts and connector health, Logs, Alerts, Sessions (kill Trustelem session).
- SIEM export through Trustelem Connect to an on-premise target every 30 s, JSON recommended (https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem).
- Self-service password reset at `/forgot`; AD writeback needs the "Reset user password" delegation on the ADConnect account (https://trustelem-doc.wallix.com/books/trustelem-administration/page/self-service-password-reset).
- Branding through themes enabled by support (https://trustelem-doc.wallix.com/books/trustelem-administration/page/custom-themes).
- Break glass: keep at least one local backup admin not tied to a directory, plus the rescue-code flow.
- Password policy levels None/Medium/High using zxcvbn scores plus a tenant dictionary (https://trustelem-doc.wallix.com/books/trustelem-administration/page/trustelem-password-levels). Gap: brute-force lockout and encryption at rest are not documented.

## Network requirements

- Verified (https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows): all connector traffic outbound only on TCP 443 with TLS; allow `*.trustelem.com`, `relay-fr-01.wallix.com`, `relay-fr-02.wallix.com`; IP fallback 185.4.44.22, 185.4.46.20 to 22; add 185.4.44.114 and 185.4.44.117 active from 2026-09-29; relays 98.66.169.89 and 20.39.241.157. HTTP CONNECT proxy supported; the connector pins the server certificate so TLS inspection must be excluded. Test with `./connect check <sync_id> [http://proxy:3128]`.
- ADConnect to domain controllers TCP 389/636. Applications to Trustelem Connect on 2001/tcp and 1812/udp. Connect to SCIM server and SIEM target.

## Licensing

- No public price list; free trial and sales contact (https://contact.wallix.com/en-gb/free-trial-trustelem-en). SMS at additional cost; WALLIX Authenticator bundle extensible to other apps by licence change; API, delegated administration and themes enabled on request. Reseller pages describe per-user pricing (https://nflo.tech/products/wallix-trustelem/).
