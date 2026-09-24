# Caveats and questions for WALLIX

> - **Purpose:** the limits of the design that a PAM architect must accept or work around, and the questions to put to WALLIX before sign-off.
> - **Audience:** PAM architect, security officer, project sponsor.
> - **Verified:** 2026-09-24 against the public Bastion 12.3.2 and Access Manager 5.2.4.0 guides, the Bastion 12.4.3 and Access Manager 6.0.5 customer guides and the Trustelem documentation books.
> - **Sources:** [Bastion Administration Guide 12.3.2](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf), [Access Manager Administration Guide 5.2.4.0](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf), Bastion 12.4.3 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), Access Manager 6.0.5 customer guides on [doc.wallix.com](https://doc.wallix.com/) (login), [open questions and gaps register](../reference/open-questions-and-gaps.md).

## 1. Caveats and gaps

- SAML and OIDC to the Bastion are "supported, but the workflow is not fully integrated" on
  native SSH and RDP clients (copy a link, retrieve a token); in practice native clients use
  RADIUS, Kerberos, SSH keys or the one-time-password session files.
  Source: [Bastion 7.1.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf).
- Configuring SAML on the Bastion for Access Manager makes direct SAML login to the Bastion
  impossible; administrators use LDAP/AD with RADIUS, or local accounts.
  Source: [Bastion 7.3.1](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf).
- IPv6 is unsupported for SAML, LDAP and RADIUS on Access Manager, and both products'
  replication needs IPv4 and nodes "on the same subnet and connected directly or through only one
  router".
  Sources: [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.3, 4.3.5 and 4.3.6, [Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 6 and 6.1, [AM 10.3 and 11](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf),
  [Deployment Guide ch. 5](https://marketplace-wallix.s3.amazonaws.com/bastion_12.0.2_en_deployment_guide.pdf), [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.1.
- Bastion scheduled password rotation runs only on the primary master: "if the primary Bastion
  becomes unavailable, password changes will not run until it is available again". A Bastion
  minor upgrade in HA mode takes the whole cluster out of service (*inference* from the
  procedure). Source: [Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5 and 7.2.
- Passkeys and FIDO2 are unavailable over RADIUS and LDAP, so native-client MFA over RADIUS is
  push or TOTP. Outside Trustelem, the Bastion SSH proxy accepts FIDO2 hardware keys as SSH keys
  ("WALLIX Bastion supports user authentication via SSH using a hardware key (such as a Yubikey)
  that uses the FIDO2 secure authentication standard"); whether RADIUS still runs after such a
  login is gap B10 in the [register](../reference/open-questions-and-gaps.md).
  Sources: [MFA methods](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication),
  [Bastion 12.4.3 Administration Guide](https://doc.wallix.com/) 2.5.
- *Access Manager 5.2:* "Clusters are not compatible with the feature allowing the display of
  the target passwords. However it can be used with an external vault." The 6.0.5 guides no
  longer state this limitation ([Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 3.3); confirm with WALLIX before relying on password
  display through a Bastion cluster.
  Source: [AM 13](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf).
- Trustelem does not document geolocation, device posture, risk scoring or a browser
  "remember this device"; adaptive access is limited to internal/external zones and the RADIUS
  MFA session. Source: [Access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules).
- Gaps confirmed on 2026-09-22: contractual SLA, SAML clock-skew tolerance, RADIUS attributes
  returned by Trustelem, CHAP support on Trustelem RADIUS (the Bastion side is PAP only, known
  limitation WAB-16237), the Access Manager health-check endpoint path, Bastion 12.4 and Access
  Manager 6.0 release notes (behind SSO), and public pricing for the Bastion plus Trustelem
  bundle. The Access Manager replication port and node count are answered by the 6.0.5
  Deployment Guide: 3306/3307 inside an SSH tunnel on 2242, two nodes ([Access Manager 6.0.5 Deployment Guide](https://doc.wallix.com/) 6).

## 2. Questions to put to WALLIX before sign-off

The maintained list is the [open questions and gaps register](../reference/open-questions-and-gaps.md)
and the questions are put to WALLIX with the [vendor meeting script](../reference/vendor-meeting-script.md);
the items below are the sign-off subset and keep their original numbering.

1. Contractual SLA and support hours for WALLIX One IDaaS, and the incident notification
   channel (the public pages give history, not commitments).
2. Maximum tolerated clock skew for SAML assertions on Access Manager and Bastion, and the
   assertion validity Trustelem issues.
3. RADIUS: does Trustelem Connect answer CHAP as well as PAP (the Bastion itself supports only
   PAP, WAB-16237), does it return any attributes in
   Access-Accept, and what happens to a pending push when the Bastion timeout expires first.
4. Whether push approval (not only TOTP) is supported in the Access Manager RADIUS factor chain.
5. Access Manager farm: the path of the health-check endpoint behind the HEALTH_VIEW right, and
   the TLS versions the default HTTP security level allows (the replication port and the two-node
   maximum are answered by the 6.0.5 Deployment Guide 6).
6. Bastion 12.4 and Access Manager 6.0 release notes and compatibility matrix (login required),
   the Debian and Java versions of Access Manager 6.0.5 (the 6.0.5 guides refer to the release
   notes), and the end-of-support dates for 12.3 and 5.2.
7. The supported Bastion DR procedure (the "DRP configuration script" of Deployment Guide 6.4) and the step-by-step `wallix-replication --elevate-master` failover and failback; the latency question is answered by the same-subnet, one-router rule (Deployment Guide 5.1).
8. Trustelem Connect and ADConnect sizing for the expected RADIUS request rate.
9. Whether a Trustelem "remember this browser" or device trust option exists beyond the RADIUS
   MFA session and the internal network zone.
10. Licensing: Access Manager concurrent-user count, Bastion licence per replicated node, and
    the WALLIX Authenticator per-user model for administrators who also need other apps.
11. RADIUS security: Message-Authenticator on the Bastion client (not among the attributes
    Admin Guide 7.2.5.4 lists) and on Trustelem Connect, a
    statement on CVE-2024-3596 (BlastRADIUS), and any RadSec roadmap.
12. PKCE on the Bastion and Access Manager OIDC clients and the Trustelem provider; number
    matching or push rate limiting in WALLIX Authenticator; certification coverage of Bastion
    12.3 and 12.4 versus the BSI-certified 12.0.14 (see the
    [standards and compliance reference](../reference/standards-and-compliance.md)).
13. SCIM provisioning from Trustelem into the Bastion: supported pairing, payload, deprovisioning
    semantics and cluster behaviour (see [SCIM assessment](../trustelem/12-scim-provisioning.md)).
