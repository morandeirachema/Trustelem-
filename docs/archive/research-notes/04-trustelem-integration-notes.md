# Research notes 04: Trustelem integration with Bastion and Access Manager

Working notes gathered on 2026-09-22 from the Trustelem documentation site
(https://trustelem-doc.wallix.com/), the Bastion 12.3.2 and Access Manager 5.2.4.0
administration guides and third-party integration guides. These notes feed the main
report; facts are tagged verified, inference or gap.

## Trustelem as SAML 2.0 IdP

Access Manager template (verified, https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager):

- Apps > Add > "Access Manager" model. Fields: Root URL (for example `https://wam.example.com/wabam`), Organization identifier (AM > Configuration > Organizations), Domain (must equal the AM authentication domain name), enable SAML.
- SP settings expected on Trustelem: Entity ID `WALLIX-AM`; Sign Messages disabled; Encrypt Messages disabled; Signed Response enabled; Signed Assertion enabled.
- Attributes sent: Login = `uid` for AD users or `email` for Trustelem local users; `displayname`; `email`; `lang`; optional `profile`.
- Profile mapping via a custom attribute script, for example `msg.setAttr("profile","User"); for (let group in groups){ if(group=="admin"){msg.setAttr("profile","Administrator")} }`.
- Download the Trustelem metadata file and import it into Access Manager. Logout: copy the Redirect Binding URI into Redirect Logout URI, replacing `sso` with `on_logout`.
- Caveats: domain must be unique within an organization; a pre-existing AM user with the same login blocks SAML login; time synchronisation is essential; use the SAML tracer browser plugin to inspect assertions; AM logs need DEBUG level for SAML troubleshooting.

Bastion direct SAML (verified, https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion-saml):

- No dedicated Bastion template: use the generic SAML2 model, save, download metadata. Attributes `email`, `displayname`; groups sent by the script `for (let g in groups){ msg.addAttr("groups",g); }`.
- Generic Trustelem SAML endpoints (verified, https://trustelem-doc.wallix.com/books/trustelem-applications/export/html): Entity ID `https://<tenant>.trustelem.com/app/<ID>`, SSO `/app/<ID>/sso`, SLO `/app/<ID>/on_logout`, metadata `/app/<ID>/metadata` (contains the signing certificate).
- Bastion claim mapping: Username = email, Display name = displayname, Email = email, Group = groups. Through Access Manager it requires AM 5.0 or later.
- The Bastion 12 deployment guide lists Trustelem among supported SAML IdPs (verified, https://marketplace-wallix.s3.amazonaws.com/bastion_12.0.2_en_deployment_guide.pdf).
- The Terraform provider mirrors the SAML fields (verified, https://github.com/wallix/terraform-provider-wallix-bastion/blob/main/docs/resources/externalauth_saml.md).

Access Manager side (verified, AM guide chapter 10.3): Entity ID max 256 characters since 5.2.0; known issue in 5.2.x where SAML fails with a missing `SigAlg` when Sign Messages is enabled (release notes). Third-party guides show the WALLIX-AM Entity ID format `https://<host>/wabam/<org>?domain=<DOMAIN>` (https://docs.trustbuilder.com/mfa/wallix-access-manager-saml-2-0-configuration, https://www.ofep.be/wallix-saml-access-manager-bastion-entra-id-guest/).

Gaps: no published clock-skew tolerance; SLO documented only as the logout URIs.

## Trustelem as OpenID Connect provider

- Trustelem OIDC app (verified, https://trustelem-doc.wallix.com/books/trustelem-applications/page/openid-connect): Client ID `trustelem.oidc.xxxx`, client secret, issuer `https://<tenant>.trustelem.com/app/<ID>`, discovery at `/.well-known/openid-configuration`, endpoints `/auth`, `/token`, `/userinfo`, JWKS with RS256, redirect URI and post-logout redirect URI must be declared, authorization-code and implicit flows, minimum scope `email`.
- Bastion OIDC added in 12.1/12.2, dynamic cluster URLs in 12.3 (release notes). Access Manager OIDC added in 5.2.4.0.
- Gap: no Trustelem page documents a WALLIX-specific OIDC template or a groups claim for Bastion.

## Trustelem as RADIUS and LDAP server (Trustelem Connect)

- Architecture (verified, https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect): Trustelem Connect is installed on a customer server and acts as LDAP server and RADIUS server; it forwards over an outbound websocket on TCP 443 to admin.trustelem.com; Windows Server or Linux; recommendation of at least two VMs for failover. Listens on LDAP TCP 2001 and RADIUS UDP 1812 by default (2812 if there is a conflict).
- Console (verified, https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion): Apps > Bastion app > enable RADIUS; Service > Add application > Bastion > listen address; the RADIUS secret is displayed in the Bastion app model.
- Bastion RADIUS options: server, port 1812, timeout (default 5 s; the HID RADIUS guide recommends 45 to 50 s for push, https://www.wallix.com/wp-content/uploads/2020/07/HID_ActivID_Appliance_Wallix_RADIUS_ConfigGuide_FINAL.pdf), secret, "Use mobile device for two-factor authentication" (Trustelem: skips the login and password step by sending login and empty password), "Use primary domain name for 2FA" (sends user@domain). The two options became independent in Bastion 12.2.3 (WAB-16173).
- Three Trustelem scenarios:
  1. AD users: enable "Use mobile device"; Authentication domains > AD domain > Secondary authentication = RADIUS; Trustelem access rule "2nd factor only".
  2. Bastion local users: do not enable "Use mobile device"; Accounts > user > Authentication and backup servers = RADIUS only; username must be recognised by Trustelem (email); rule "2 factors".
  3. Trustelem local users via Trustelem LDAP: enable "Use mobile device"; secondary authentication on the Trustelem LDAP domain; rule "2nd factor only" or "Always allow".
- Trustelem factor behaviour over RADIUS: push notifications, appended codes, or post-password validation; passkeys unsupported over LDAP and RADIUS (verified, https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication).
- Groups: RADIUS carries no groups; AD or the Trustelem LDAP service on port 2001 (group DN `CN=<Group>,OU=Groups,DC=<tenant>,DC=trustelem,DC=com`, login attribute `mail`) remains the authorization source. Access rules with 1 or 2 factors must exist before Bastion can discover users over LDAP.
- MFA cache: for the duration set on Trustelem and while on the same network, the second factor is not asked again (verified, https://trustelem-doc.wallix.com/books/trustelem-news/page/new-features). Bastion sends Framed-IP-Address to support this. Gap: exact location of the duration setting.
- RADIUS HA: several Trustelem Connect VMs; on Bastion, define a second RADIUS external authentication and list both under "Authentication and backup servers" (https://docs.trustbuilder.com/mfa/wallix-bastion-radius-configuration); AM orders authenticators by Priority for HA.

## Trustelem ADConnect and combined design

- ADConnect (verified, https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-synchronization and .../active-directory-users-trustelem-adconnect): Windows or Linux host, not necessarily a domain controller; outbound TCP 443 websocket with TLS plus an extra symmetric encryption layer; LDAP or LDAPS 389/636 to AD with a read-only service account in UPN format; group-based sync scope; adjustable frequency; custom attributes; "Trustelem does not store any password for Active Directory users"; several connectors with priority; zero-downtime upgrade by installing the new version in parallel; same UPN or email merges local and AD accounts. Download from https://dl.trustelem.com/adconnect/; Windows service "Trustelem ADConnect"; Linux config `/opt/wallix/trustelem-adconnect/config.ini`.
- Network flows (verified, https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows): outbound-only TCP 443 to `*.trustelem.com` and `relay-fr-01/02.wallix.com`; IPs 185.4.44.22, 185.4.46.20 to 22, plus 185.4.44.114 and 185.4.44.117 active from 2026-09-29; HTTP CONNECT proxies supported.
- Vendor decision tree (verified, https://trustelem-doc.wallix.com/books/wallix-authenticator/page/setup-instructions): AD users import via ADConnect, enrol factors, deploy Trustelem Connect, RADIUS as second factor on the Bastion AD domain; Access Manager with AD and account mapping uses RADIUS second factor; AD without mapping uses SAML; Trustelem local users use SAML plus LDAP/RADIUS. Prefer Trustelem local users over Bastion local users to keep one identity source.

## WALLIX One naming

- WALLIX One launched 2023-12-14 with One-IDaaS, One-RA and One-PAM (https://www.wallix.com/press/2023/introducing-wallix-one-the-cybersecurity-saas-platform-designed-to-meet-the-digital-and-economic-challenges-of-companies-aiming-to-safeguard-their-access-and-identities/). Current modules: PAM Core, PAM, Remote Access, IDaaS, Enterprise Vault (https://www.wallix.com/products/wallix-one/, https://www.wallix.com/wp-content/uploads/2024/09/DATASHEET_052025_WALLIX_ONE_SaaS_EN.pdf).
- "WALLIX ONE IDaaS (also known as Trustelem)"; tenant URLs `admin-<name>.trustelem.com` and `<name>.trustelem.com` (https://vault-doc.wallix.com/books/enterprise-vault-administration/page/quick-start-guide). The Bastion guide calls the IdP "WALLIX IDaaS".
- IDaaS datasheet: SAML, OIDC, OAuth2, LDAP and RADIUS through connectors, AD/LDAP/Azure AD/G Suite sources, MFA by WALLIX Authenticator push and TOTP, TOTP, email and SMS OTP, U2F/FIDO; EU datacenter (https://www.wallix.com/wp-content/uploads/2024/01/DATASHEET_2024_WALLIX_IDaaS_EN67.pdf).

## MFA policy, operations and caveats

- Access rules (verified, https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules): web = No rule / Default / 1 factor / 2 factors / Forbidden; LDAP = 1 or 2 factors / Forbidden; RADIUS = Always allow / 2nd factor only / 2 factors / Forbidden; most restrictive wins; user rule beats group rule; internal and external IP zones for web authentication.
- Lost factor: user requests a rescue code, admins are alerted, one-time code valid 24 h (https://trustelem-doc.wallix.com/books/trustelem-administration/page/loss-of-a-second-factor).
- Bastion break glass is a credential-recovery e-mail mechanism, not an authentication bypass. Keep a local Bastion administrator with a local password, optionally IP-restricted, as emergency access (inference).
- Fallback when the Trustelem cloud is unreachable is not documented; Trustelem Connect proxies to the cloud so RADIUS and LDAP through it fail as well (inference). Availability history: 99.94 % in 2023, above 99.99 % from 2016 to 2022 (https://trustelem-doc.wallix.com/books/trustelem-news/page/unavailability).
- Logs: Trustelem Logs page, API with 30 days of logs, on-premise SIEM push through Trustelem Connect every 30 s in JSON (https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem, https://trustelem-doc.wallix.com/books/trustelem-administration/page/api). Bastion syslog RFC 5424 (https://docs.fortinet.com/document/fortisiem/7.6.0/external-systems-configuration-guide/717035/wallix-bastion); authentication events `WB_Event="wabauth"` (https://github.com/wallix/Splunk-add-on).
- Certificate rotation: Security settings > Application certificates > Create, assign to the app, update the SP unless it reads the metadata URL, test (https://trustelem-doc.wallix.com/books/trustelem-administration/page/certificate-renewal). AM portal TLS certificate via `wabam-certificate-update` (5.2.0 release notes).
- Native SSH/RDP clients: SAML and OIDC are "not fully integrated" (copy a link into a browser, paste a token), or use OTP session files; SSH keyboard-interactive prompts break automation such as VS Code Remote-SSH (https://github.com/microsoft/vscode-remote-release/issues/11461). RADIUS is the only transparent push/OTP path for the proxies.
- Limits: one value per group mapping, case-insensitive; IPv6 unsupported for SAML and RADIUS on AM; SAML through AM disables direct Bastion SAML; the Entra ID Graph SAML variant is incompatible with AM; passkeys unusable over LDAP/RADIUS; SMS at extra cost.
- Licensing: "WALLIX Authenticator" is the Trustelem offer dedicated to Bastion and Access Manager, extensible by licence change (https://trustelem-doc.wallix.com/books/wallix-authenticator/page/presentation). Per-user subscription, quote only.
