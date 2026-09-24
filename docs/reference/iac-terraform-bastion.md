# Codifying the Bastion side of the Trustelem integration with Terraform

> - **Purpose:** the Terraform resources and arguments that create the Bastion objects of the
>   Trustelem integration, with illustrative HCL and the options the provider cannot set.
> - **Audience:** Bastion administrators and platform engineers who manage the Bastion cluster as
>   code.
> - **Verified:** 2026-09-24; provider source (`resource_externalauth_radius.go`) checked on 2026-09-23; Bastion
>   12.4.3 customer guides (Functional Administration, Deployment, System Operations), whose
>   sections behind these objects are unchanged from the 12.3.2 Functional Administration Guide.
> - **Sources:** [WALLIX Terraform provider index](https://github.com/wallix/terraform-provider-wallix-bastion/blob/main/docs/index.md),
>   [provider resources](https://github.com/wallix/terraform-provider-wallix-bastion/tree/main/docs/resources),
>   [Bastion 12.3.2 Functional Administration Guide](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
>   Bastion 12.4.3 customer guides behind the [doc.wallix.com](https://doc.wallix.com/) login.

The HCL below is illustrative and follows the documented arguments. Validate it against the
provider version you deploy. Placeholder values (`corp.example.local`, node addresses) are not
those of the [worked example](../trustelem/09-worked-example.md); only its object names are
reused.

## 1. Why codify, and how to connect

Managing the Trustelem objects as code keeps the two cluster nodes identical, gives a
reviewable change history, and reduces the MFA rollback (remove the secondary authentication)
to a one-line change. The objects are:

- an AD external authentication;
- one or two RADIUS external authentications pointing at Trustelem Connect;
- an AD authentication domain with RADIUS as secondary authentication, and its group mappings;
- a SAML external authentication with the Trustelem metadata;
- a SAML authentication domain with its mappings;
- an API key for Access Manager.

Provider facts:

- Required: `ip` and `user`, plus `password` or `token` (API key).
- `api_version` defaults to `v3.12`; the SAML resource requires API v3.12.
- "Bastion 12.0.3+: Full feature support".
- Environment variables: `WALLIX_BASTION_HOST`, `WALLIX_BASTION_USER`, `WALLIX_BASTION_TOKEN`,
  `WALLIX_BASTION_API_VERSION`.

```hcl
provider "wallix-bastion" {
  ip          = "bastion-primary.example.local"   # run against the primary master only
  user        = "terraform"
  token       = var.bastion_api_key
  api_version = "v3.12"
}
```

Run Terraform against the primary master only. In Master/Master mode the Bastion forbids API
provisioning from both nodes at the same time (limitations table in the
[Bastion HA runbook](../runbooks/bastion-ha-replication.md), section 1).

## 2. Resources

Each subsection lists the documented arguments, then an example.

### 2.1 Active Directory external authentication (`externalauth_ldap`)

Arguments: `authentication_name`, `host`, `port`, `timeout`, `ldap_base`, `cn_attribute`,
`login_attribute`. Optional: `is_active_directory`, `login`, `password`, `is_ssl`,
`is_starttls`, `ca_certificate`, `is_protected_user`, `use_primary_auth_domain`.

```hcl
resource "wallix-bastion_externalauth_ldap" "corp_ad" {
  authentication_name = "CORP-AD"
  host                = "dc1.corp.example.local"
  port                = 389
  timeout             = 30
  is_active_directory = true
  is_starttls         = true
  ldap_base           = "dc=corp,dc=example,dc=local"
  login               = "svc-bastion-ldap@corp.example.local"
  password            = var.ad_bind_password
  login_attribute     = "sAMAccountName"
  cn_attribute        = "sAMAccountName"
}
```

### 2.2 RADIUS external authentications to Trustelem Connect (`externalauth_radius`)

Arguments: `authentication_name`, `host`, `port`, `secret`, `timeout`. Optional: `description`,
`use_primary_auth_domain`.

- The GUI option "Use mobile device for 2 factor authentication(2FA)" is not exposed. The
  provider source `resource_externalauth_radius.go` has no such attribute (checked 2026-09-23).
  Set it in the GUI after every apply that recreates the resource
  ([section 3](#3-not-covered-by-the-provider)).
- `use_primary_auth_domain` is the GUI option "Use primary domain name for two-factor
  authentication (2FA)". It "forces the domain name to be mentioned in the login (for example,
  user@domain) during the second authentication"
  ([Admin Guide 7.2.5.4](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf),
  12.3.2 and 12.4.3). The worked example uses sAMAccountName logins and leaves it off. Set it to
  `true` only when Trustelem logins are UPNs
  ([chapter 04](../trustelem/04-bastion-integration.md), section 3).

```hcl
resource "wallix-bastion_externalauth_radius" "trustelem_1" {
  authentication_name     = "Trustelem-RADIUS-1"
  host                    = "trustelem-connect-1.example.local"
  port                    = 1812
  secret                  = var.trustelem_radius_secret
  timeout                 = 50
  use_primary_auth_domain = false   # logins are sAMAccountName (worked example); true only for UPN logins
}

resource "wallix-bastion_externalauth_radius" "trustelem_2" {
  authentication_name     = "Trustelem-RADIUS-2"
  host                    = "trustelem-connect-2.example.local"
  port                    = 1812
  secret                  = var.trustelem_radius_secret
  timeout                 = 50
  use_primary_auth_domain = false   # logins are sAMAccountName (worked example); true only for UPN logins
}
```

### 2.3 AD authentication domain with RADIUS as secondary (`authdomain_ad`)

Arguments: `domain_name`, `auth_domain_name`, `external_auths`, `default_language`,
`default_email_domain`. Optional: `group_attribute`, `display_name_attribute`,
`email_attribute`, `language_attribute`, `is_default`, `secondary_auth`.

```hcl
resource "wallix-bastion_authdomain_ad" "corp" {
  domain_name          = "CORP"
  auth_domain_name     = "corp.example.local"
  external_auths       = [wallix-bastion_externalauth_ldap.corp_ad.authentication_name]
  secondary_auth       = [
    wallix-bastion_externalauth_radius.trustelem_1.authentication_name,
    wallix-bastion_externalauth_radius.trustelem_2.authentication_name,
  ]
  default_language     = "en"
  default_email_domain = "example.com"
  group_attribute      = "memberOf"
  is_default           = true
}
```

Rollback of MFA on the native path is `secondary_auth = []`.

### 2.4 Group mappings (`authdomain_mapping`)

Arguments: `domain_id`, `user_group`, `external_group` (an AD DN, or the SAML group claim
value). Import format: `<domain_id>/<user_group>`.

```hcl
resource "wallix-bastion_authdomain_mapping" "corp_admins" {
  domain_id      = wallix-bastion_authdomain_ad.corp.id
  user_group     = wallix-bastion_usergroup.pam_admins.group_name
  external_group = "CN=PAM-Admins,OU=Groups,DC=corp,DC=example,DC=local"
}
```

### 2.5 SAML external authentication with the Trustelem metadata (`externalauth_saml`)

Arguments: `authentication_name`, `idp_metadata`, `timeout`, and the block
`claim_customization { username (required), displayname, email, group, language }`. Optional:
`description`, `certificate`, `private_key`, `passphrase`. Computed: `sp_entity_id`,
`sp_metadata`, `sp_assertion_consumer_service`, `sp_single_logout_service`, `idp_entity_id`,
`saml_request_url`, `saml_request_method`. The claim values must match the names in the
[SAML naming reference](saml-assertion-and-naming.md).

```hcl
resource "wallix-bastion_externalauth_saml" "trustelem" {
  authentication_name = "Trustelem-SAML"
  idp_metadata        = file("${path.module}/trustelem-metadata.xml")
  timeout             = 900
  claim_customization {
    username    = "uid"          # must equal the Access Manager Login attribute
    displayname = "displayname"
    email       = "email"
    group       = "groups"
  }
}

output "trustelem_sp_entity_id" { value = wallix-bastion_externalauth_saml.trustelem.sp_entity_id }
output "trustelem_sp_acs"       { value = wallix-bastion_externalauth_saml.trustelem.sp_assertion_consumer_service }
```

- Standalone native-SAML design: the two outputs are the values to paste into a Trustelem
  generic SAML2 application (EntityID and Assertion Consumer Service).
- Behind Access Manager: no Bastion application is created
  ([chapter 04](../trustelem/04-bastion-integration.md)).
- Signing certificate rotation: replace the Trustelem metadata file and apply.

### 2.6 SAML authentication domain (`authdomain_saml`)

Arguments: `domain_name`, `auth_domain_name`, `external_auths`, `default_email_domain`,
`default_language`, `label`. Optional: `force_authn`, `is_default`, `secondary_auth`.
Computed: `idp_initiated_url`.

```hcl
resource "wallix-bastion_authdomain_saml" "trustelem" {
  domain_name          = "TRUSTELEM"      # equals the Access Manager SAML domain name
  auth_domain_name     = "TRUSTELEM"
  external_auths       = [wallix-bastion_externalauth_saml.trustelem.authentication_name]
  default_email_domain = "example.com"
  default_language     = "en"
  label                = "Trustelem"
  force_authn          = false
}

resource "wallix-bastion_authdomain_mapping" "saml_admins" {
  domain_id      = wallix-bastion_authdomain_saml.trustelem.id
  user_group     = wallix-bastion_usergroup.pam_admins.group_name
  external_group = "PAM-Admins"            # value sent in the SAML "groups" attribute
}

output "trustelem_idp_initiated_url" { value = wallix-bastion_authdomain_saml.trustelem.idp_initiated_url }
```

### 2.7 API key for Access Manager (`apikey_v2`)

Arguments: `apikey_name`, `profile`, `description`, `ip_limitation`. `profile` and
`ip_limitation` are immutable.

- The provider documentation: "The Bastion API never returns the raw API key value ... always
  reads back as a masked placeholder (********)"; "retrieving the usable secret value requires
  the Bastion web UI (or another out-of-band process) at creation time". Copy the key from the
  web UI when it is created and store it in the secret manager.
- The Bastion guides agree. The **Configuration > API keys** page accepts only "a profile with
  the Read-only profile type". It takes one or more individual IP addresses ("Subnet notations,
  for example 192.0.2.1/24, are not supported"). On edit, "You cannot change the profile or the
  IP limitations". The key is shown once
  ([Bastion 12.4.3 System Operations Guide](https://doc.wallix.com/) 12.1 and 12.2).
- *Bastion 12.0:* API keys carry no profile (12.0.25 System Operations Guide 12.1), so `profile`
  does not apply.

```hcl
resource "wallix-bastion_apikey_v2" "access_manager" {
  apikey_name   = "access-manager"
  profile       = "wallix_access_manager_session_audit"
  description   = "Access Manager farm"
  ip_limitation = "10.10.20.11,10.10.20.12"
}
```

### 2.8 User groups and authorizations

These resources complete the model and are independent of Trustelem:

- `usergroup`: `group_name`, `timeframes`; optional `profile`, `users`, `restrictions`.
- `authorization`: `authorization_name`, `user_group`, `target_group`, `authorize_sessions`,
  `subprotocols`, `approval_required`, `approvers`, `active_quorum`, `is_recorded`,
  `is_critical`, and so on.

## 3. Not covered by the provider

Two parts of the integration stay manual:

- OIDC: no `externalauth_oidc` or `authdomain_oidc` resource exists in the documented set, so
  the OIDC alternative is configured in the GUI.
- The RADIUS option "Use mobile device for 2 factor authentication(2FA)": verify it in the GUI
  after each apply until the provider documents it (closed gap B5 in the
  [register](open-questions-and-gaps.md)).

## 4. Workflow

1. Run `terraform plan` against the primary master in a change window.
2. Apply. *Inference:* the objects replicate to the second node through HA Database
   Replication, as configuration data does.
3. Standalone native SAML only: paste the SP outputs into Trustelem, and download the metadata
   again if the SP entity ID changed.
4. Run the [test plan](../trustelem/10-test-plan.md), sections B and A.
5. Keep the state file in an encrypted backend. It contains the RADIUS secret and the AD bind
   password.
