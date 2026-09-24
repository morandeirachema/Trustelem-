# Standards and compliance mapping

Date: 2026-09-23. Each row gives the citation, what the clause requires, and how the Trustelem
plus Bastion plus Access Manager design meets it or does not. Items marked *uncertain* or
*gap* are not confirmed by a primary source.

## 1. Protocol standards behind the Trustelem integration

### RADIUS (native client path: Bastion to Trustelem Connect)

| Reference | Requirement | Design fit |
|-----------|-------------|------------|
| [RFC 2865](https://www.rfc-editor.org/rfc/rfc2865.html) sections 2.1, 4.4, 5.24 | Access-Challenge and the `State` attribute echoed by the client | Bastion "supports the challenge-response mechanism" and echoes State; Trustelem answers with Access-Challenge for OTP or waits for a push ([Bastion 7.2.5.4](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Trustelem Connect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect)) |
| RFC 2865 sections 5.2 and 2.4 | User-Password is only MD5-XOR obfuscated with the shared secret; transport is UDP | The design uses PAP over UDP 1812 between the Bastion and Trustelem Connect; confidentiality rests on the shared secret and on the network segment |
| [RFC 2869](https://www.rfc-editor.org/rfc/rfc2869.html) section 5.14 Message-Authenticator | HMAC-MD5 over the packet; mandatory only for EAP | *Gap:* neither the Bastion guide nor the Trustelem Connect page mentions Message-Authenticator; ask WALLIX whether the Bastion sends it and whether Connect requires it |
| [CVE-2024-3596 BlastRADIUS](https://nvd.nist.gov/vuln/detail/cve-2024-3596), [blastradius.fail](https://www.blastradius.fail/) | An on-path attacker can turn an Access-Reject into an Access-Accept for non-EAP methods (PAP, CHAP, MS-CHAP) over UDP; "Using MFA or 2FA is not a mitigation either"; mitigation is Message-Authenticator on all packets on both sides, long term RADIUS/TLS | PAP with Message-Authenticator required on both sides mitigates it, but only if Trustelem Connect rejects requests without it and signs its responses. *Gap:* no WALLIX advisory on CVE-2024-3596 was found on the [advisories page](https://www.wallix.com/support-services/alerts/). Compensating control: keep the Bastion-to-Connect hop inside the administration network, ideally the same VLAN or an IPsec path |
| [RFC 6614](https://www.rfc-editor.org/rfc/rfc6614.html) RADIUS/TLS, [RFC 9765](https://www.rfc-editor.org/rfc/rfc9765.html) RADIUS/1.1, [draft-ietf-radext-deprecating-radius](https://datatracker.ietf.org/doc/draft-ietf-radext-deprecating-radius/) | RADIUS over UDP "MUST NOT be used outside of secure networks"; clients must send Message-Authenticator; PAP preferred over CHAP | Trustelem Connect documents RADIUS over UDP only (listeners such as 1812 and 2812), no RadSec (*gap*); the design's PAP choice is aligned with the draft; the "secure network" condition is met by placement, not by the protocol |
| [RFC 2866](https://www.rfc-editor.org/rfc/rfc2866.html) accounting | Accounting Start/Stop | Not used; the Bastion is the system of record for sessions, so this is not a compliance gap |
| [RFC 8044](https://www.rfc-editor.org/rfc/rfc8044.html) | RADIUS data types | The Bastion guide claims RFC 2865 and RFC 8044 compliance |

### SAML 2.0 (web path: Trustelem to Access Manager and Bastion)

| Reference | Requirement | Design fit |
|-----------|-------------|------------|
| [saml-core-2.0-os](https://docs.oasis-open.org/security/saml/v2.0/saml-core-2.0-os.pdf) 1.3.3 and 2.5.1.2 | UTC time values; NotBefore and NotOnOrAfter validity window; the spec sets no numeric skew tolerance | NTP on every node is a hard prerequisite; Access Manager's skew tolerance is not published (*uncertain*); Trustelem: "Verify the time on Access Manager: SAML assertion are valid for a short period" |
| [saml-profiles-2.0-os](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf) 4.1 Web Browser SSO | With HTTP-POST the assertion must be signed; the SP must prevent replay | Trustelem signs with a per-application certificate; Access Manager requires Signed Response and Signed Assertion; replay cache on AM is not documented (*uncertain*); WSA-2026-07-0002 (SAML SP bypass before 5.1.10, 5.2.7, 6.0.4) shows why the patch level matters |
| [saml-bindings-2.0-os](https://docs.oasis-open.org/security/saml/v2.0/saml-bindings-2.0-os.pdf) 3.4 and 3.5 | HTTP-Redirect for AuthnRequests, HTTP-POST for Responses | Matches the Access Manager configuration (Redirect binding to the IdP, POST to the ACS) |

### OpenID Connect (alternative web path)

| Reference | Requirement | Design fit |
|-----------|-------------|------------|
| [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html) 4.1 | Authorization Code grant with client authentication at the token endpoint | Trustelem exposes `/auth`, `/token`, `/userinfo`, RS256 JWKS; Bastion 12.2+ and AM 5.2.4.0+ implement the code flow only |
| [RFC 9700 / BCP 240](https://www.rfc-editor.org/rfc/rfc9700.html) | PKCE for code flows, exact redirect URI matching, no implicit grant | *Gap:* PKCE support on Bastion, Access Manager and the Trustelem provider is not documented; Trustelem still offers the implicit flow, so do not enable it |
| [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) 3.1.3.7, [Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html) | ID token validation (`iss`, `aud`, signature, `exp`, `nonce`); discovery document | Trustelem issuer `https://<tenant>.trustelem.com/app/<ID>` with discovery; the Trustelem page calls it "Discovery 1.1", the current document is Discovery 1.0 with errata |

### Directory and authenticator standards

| Reference | Requirement | Design fit |
|-----------|-------------|------------|
| [RFC 4511](https://www.rfc-editor.org/rfc/rfc4511.html) 4.14, [RFC 4513](https://www.rfc-editor.org/rfc/rfc4513.html) 3 | StartTLS, server identity check | ADConnect uses LDAP or LDAPS to domain controllers; Trustelem Connect LDAP on 2001 supports LDAPS and StartTLS; enable StartTLS on the Bastion ("As Trustelem is compatible, flows are automatically encrypted") |
| [WebAuthn Level 2](https://www.w3.org/TR/webauthn-2/), [Level 3](https://www.w3.org/TR/webauthn-3/) (W3C Recommendation, 2026-08-25) | Origin-bound public-key credentials, phishing resistant | Trustelem second-step passkeys with a policy backed by the FIDO metadata service; web path only, never over RADIUS or LDAP |
| [RFC 6238](https://www.rfc-editor.org/rfc/rfc6238.html) TOTP | Time-based OTP | WALLIX Authenticator falls back to TOTP; TOTP is the RADIUS Access-Challenge answer when push is unavailable |
| [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html) (final July 2025) | AAL2 = two factors, at least one phishing-resistant option offered; AAL3 = phishing-resistant cryptographic authenticator with non-exportable key; "OTP authentication is not phishing-resistant"; "Out-of-band authentication is not phishing-resistant"; re-authentication AAL2 24 h / 1 h idle, AAL3 12 h / 15 min idle | Password plus push or TOTP is AAL2 without phishing resistance; a passkey on the web path is phishing-resistant AAL2 and a device-bound hardware key can reach AAL3 there; the native RADIUS path is capped at non-phishing-resistant AAL2; set Bastion and Access Manager idle timeouts to the AAL limits you claim |

## 2. Regulatory drivers

| Reference | Clause | Requirement | Design fit |
|-----------|--------|-------------|------------|
| [NIS2, Directive (EU) 2022/2555](https://eur-lex.europa.eu/eli/dir/2022/2555/oj) | Art. 21(2)(i), (j) | access control policies; "the use of multi-factor authentication or continuous authentication solutions" | MFA on the web and native paths |
| [Implementing Regulation (EU) 2024/2690](https://eur-lex.europa.eu/eli/reg_impl/2024/2690/oj) | Annex 11.3.2 | policies for privileged and system administration accounts shall "(a) establish strong identification, authentication such as multi-factor authentication, and authorisation procedures for privileged accounts and system administration accounts; (b) set up specific accounts to be used for system administration operations exclusively ... (c) individualise and restrict system administration privileges to the highest extent possible, (d) provide that system administration accounts are only used to connect to system administration systems" | named AD identities via ADConnect and Bastion mappings (a, c); dedicated PAM accounts and groups (b); Bastion as the only route to targets (d) |
| Implementing Regulation (EU) 2024/2690 | Annex 11.4.1, 11.6.1 | "restrict and control the use of system administration systems"; "implement secure authentication procedures and technologies based on access restrictions and the policy on access control" | Bastion and Access Manager are the administration systems, placed in the administration zone; Trustelem access rules are the authentication policy |
| Implementing Regulation (EU) 2024/2690 | Annex 11.7.1, 11.7.2 | "users are authenticated by multiple authentication factors or continuous authentication mechanisms ... where appropriate, in accordance with the classification of the asset to be accessed"; "the strength of authentication is appropriate for the classification of the asset to be accessed" (recital 23 adds that MFA "should be considered ... in particular when users access network and information systems from remote locations or when they access sensitive information or privileged accounts and system administration accounts") | MFA on the web and native paths; passkeys for administrators of the highest-classified assets satisfy the strength requirement, push or TOTP for the rest |
| Implementing Regulation (EU) 2024/2690 | Annex 3.2.3(e) | logs shall include "all privileged access to systems and applications, and activities performed by administrative accounts" | Bastion session recording, audit log and SIEM export; Trustelem SIEM push |
| [DORA, Regulation (EU) 2022/2554](https://eur-lex.europa.eu/eli/reg/2022/2554/oj) and [RTS 2024/1774](https://eur-lex.europa.eu/eli/reg_del/2024/1774/oj/eng) | Art. 9(4)(c) and (d); RTS Art. 21, points (e)(ii) and (f)(ii) | "assignment of privileged, emergency, and administrator access on a need-to-use or an ad-hoc basis for all ICT systems"; "the use of strong authentication methods in accordance with leading practices and techniques for remote access to the financial entity's network, for privileged access, for access to ICT assets supporting critical or important functions or ICT assets that are publicly accessible" | Bastion approvals and time frames give need-to-use access; Trustelem MFA is the strong authentication; shared target accounts are acceptable because the Bastion maps them to individuals and records sessions |
| [ISO/IEC 27001:2022](https://www.iso.org/standard/27001) | A.5.15, 5.16, 5.17, 5.18, 8.2, 8.5, 8.15, 8.16 | access control, identity management, authentication information, access rights, privileged access rights, secure authentication, logging, monitoring (control texts are paywalled and were not re-read) | all covered by the tooling; access reviews remain a process control |
| [IEC 62443-3-3](https://webstore.iec.ch/en/publication/7033) | SR 1.1 (RE 2 and 3), 1.7, 1.13, 2.1 | MFA for untrusted and, at higher levels, all networks; strength of password-based authentication (SR 1.7); approval for untrusted-network access; authorization enforcement (RE wording is paywalled) | Bastion in front of OT jump hosts with Trustelem MFA; RE 3 requires MFA from the OT network too (RADIUS path) |
| [PCI DSS v4.0.1](https://www.pcisecuritystandards.org/document_library/) | 8.4.1, 8.4.2, 8.4.3, 8.5.1 | MFA for administrative, all and remote access to the CDE; MFA not replayable, not bypassable except by documented exception | met when all CDE access passes through Bastion or Access Manager; the break-glass account and TOTP windows need documented exceptions (requirement texts not re-read on 2026-09-24: the standard's PDF sits behind a licence click-through that refuses scripted downloads) |
| [ANSSI PA-022 v3.0](https://messervices.cyber.gouv.fr/documents-guides/anssi-guide-admin_securisee_si_v3-0.pdf) | R6, R27, R30, R31, R36, R37, R38, R39, 13.1, R62, R64 | qualified products where possible; dedicated individual admin accounts; logging; two-factor for administration; trusted certificates from a qualified provider for authentication (R37); centralised authentication; least privilege (R39); bastion placed inside the administration zone; dedicated third-party access chain | satisfied except R6 and R37. R6: Bastion holds BSI BSZ-0020-2025 (12.0.14); the 2019 CSPN is no longer maintained, and no ANSSI qualification was found (*gap*). R37: push, TOTP and passkeys are not qualified X.509 certificates (*gap*); Bastion and Access Manager must sit in the administration zone with hardened admin workstations |
| [ANSSI PG-078 v2.0](https://messervices.cyber.gouv.fr/documents-guides/anssi-guide-authentification_multifacteur_et_mots_de_passe.pdf) | R1, R2, R8, R10, R11, R12, R39 | favour MFA and strong means; do not use SMS as a factor; rate limit; secure channel; limited session lifetime; possession factor on a certified secure element | disable SMS in Trustelem; hardware FIDO keys on the web path; push or TOTP on a phone is the "R39 - -" variant (possession factor without a security component); R11 is the argument for treating RADIUS over UDP as a weak channel |
| [CIS Controls v8.1](https://cas.docs.cisecurity.org/en/latest/source/Controls6/) ([Control 5](https://cas.docs.cisecurity.org/en/latest/source/Controls5/)) | 5.4, 6.3, 6.4, 6.5, 6.7, 6.8 | dedicated admin accounts; MFA for exposed apps, remote access and administrative access; centralised access control; RBAC | met directly by the design |

## 3. Vendor assurance

| Item | Evidence |
|------|----------|
| ANSSI CSPN | ANSSI-CSPN-2019-15 for Bastion 6.0.102.100 (2019-11-22), listed as "Non maintenu" in the [ANSSI catalogue](https://messervices.cyber.gouv.fr/visas/catalogue-produits-services-profils-de-protection-sites-certifies-qualifies-agrees-anssi.pdf) |
| BSI BSZ | [BSZ-0020-2025](https://www.bsi.bund.de/SharedDocs/Zertifikate_BSZ/Bestaetigt/BSZ-0020-2025.html): Bastion 12.0.14, certified 2025-09-29, valid to 2027-09-28; "this certification is also recognized by ANSSI" through the CSPN-BSZ mutual recognition agreement (June 2022, version 3 in May 2024, [ANSSI](https://cyber.gouv.fr/actualites/renouvellement-de-laccord-de-reconnaissance-mutuelle-cspn-bsz-entre-lanssi-et-le-bsi/)); a WALLIX claim, the certificate is not in the ANSSI catalogue ([WALLIX press release](https://www.wallix.com/press/wallix-achieves-dual-certifications-in-germany-and-france-reinforcing-its-position-as-a-trusted-european-cybersecurity/)). The certified branch is 12.0, not 12.3 or 12.4 (*inference*) |
| Common Criteria | none found (*gap*) |
| ISO/IEC 27001:2022 | WALLIX certified by Certi-Trust; the release says WALLIX "gère la sécurité de l'information de sa plateforme SaaS WALLIX One" and lists corporate IT, product development and customer support as audited (*inference* that the SaaS platform is in the certificate scope; ask for the certificate, gap T9) ([press release](https://www.wallix.com/wp-content/uploads/2025/01/250901_-WALLIX-ISO270012022_FINAL_VFR.pdf)); Trustelem is sold as WALLIX One IDaaS, so it falls in scope (*inference*) |
| SecNumCloud | none for WALLIX One IDaaS; WALLIX PAM is offered on the 3DS Outscale cloud, whose SecNumCloud qualification belongs to Outscale (2022) ([press release](https://www.wallix.com/fr/communique-de-presse/wallix-et-3ds-outscale-signent-un-partenariat-et-renforcent-loffre-de-cybersecurite-europeenne/)) |
| Trustelem hosting | "Hosted in European Data Centers" ([product page](https://www.wallix.com/products/idaas/)); provider, country and DR set-up not published (*gap*) |

## 4. Threat model (MITRE ATT&CK)

| Technique | Mitigation | Design |
|-----------|------------|--------|
| [T1078 Valid Accounts](https://attack.mitre.org/techniques/T1078/) | [M1032 MFA](https://attack.mitre.org/mitigations/M1032/), [M1026 Privileged Account Management](https://attack.mitre.org/mitigations/M1026/) | Trustelem MFA; Bastion vault removes standing target credentials |
| [T1021 Remote Services](https://attack.mitre.org/techniques/T1021/) | M1032 on remote service logons | all RDP and SSH through Bastion proxies with RADIUS or SAML MFA; targets accept only Bastion addresses |
| [T1110 Brute Force](https://attack.mitre.org/techniques/T1110/) | M1032 on exposed services | Access Manager is the only exposed web surface; Trustelem external zone rule 2 factors |
| [T1550 Use Alternate Authentication Material](https://attack.mitre.org/techniques/T1550/) | M1026, M1036 (MFA alone does not stop session replay) | credential injection keeps target hashes and tickets away from users; short Access Manager session lifetimes |
| [T1556.006 Modify Authentication Process: MFA](https://attack.mitre.org/techniques/T1556/006/) | M1018, M1032, M1047 (M1026 is listed on the parent T1556) | MFA policy lives in the Trustelem tenant outside the administered systems; the tenant console itself requires two factors |
| [T1621 MFA Request Generation](https://attack.mitre.org/techniques/T1621/) (push fatigue) | M1036, M1032 ("more secure 2FA/MFA mechanisms in replacement of simple push"), M1017 | the RADIUS push-wait path is exposed; mitigate with zone rules, TOTP or password+code on RADIUS, passkeys on the web path, and SIEM detection of repeated requests; number matching in WALLIX Authenticator is not documented (*gap*) |

## 5. Questions for WALLIX raised by this mapping

1. Message-Authenticator support on the Bastion RADIUS client and on Trustelem Connect, and a
   statement on CVE-2024-3596.
2. RadSec or RFC 9765 roadmap for Trustelem Connect.
3. PKCE and exact redirect URI matching on the Bastion and Access Manager OIDC clients and on
   the Trustelem provider.
4. Access Manager SAML clock-skew tolerance and assertion replay cache.
5. Number matching or push rate limiting in WALLIX Authenticator.
6. Certification coverage of Bastion 12.3 and 12.4 versus the certified 12.0.14; ANSSI
   qualification status.
7. Trustelem hosting provider, location, SecNumCloud or HDS status, ISO 27001 certificate
   number and statement of applicability.
