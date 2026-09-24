# Codifying the Bastion side of the Trustelem integration with Terraform

Date: 2026-09-23. Source: the WALLIX Terraform provider documentation
([index](https://github.com/wallix/terraform-provider-wallix-bastion/blob/main/docs/index.md),
[resources](https://github.com/wallix/terraform-provider-wallix-bastion/tree/main/docs/resources))
and the [Bastion 12.3.2 Functional Administration Guide](https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf).
The HCL below is illustrative and follows the documented arguments; validate it against the
provider version you deploy. Placeholder values (`corp.example.local`, node addresses) are
illustrative and are not those of the [worked example](../trustelem/09-worked-example.md),
whose object names this file reuses.

## 1. Why

The Trustelem integration on the Bastion is a handful of objects: an AD external
authentication, one or two RADIUS external authentications pointing at Trustelem Connect, an
AD authentication domain with RADIUS as secondary authentication and group mappings, a SAML
external authentication with the Trustelem metadata, a SAML authentication domain with
mappings, and an API key for Access Manager. Managing them as code makes the two cluster
nodes identical, gives a reviewable change history, and allows the rollback plan (remove the
secondary authentication) to be a one-line change.

Provider facts: required `ip` and `user`; `password` or `token` (API key); `api_version`
default `v3.12`; "Bastion 12.0.3+: Full feature support"; the SAML resource requires API
v3.12. Environment variables `WALLIX_BASTION_HOST`, `WALLIX_BASTION_USER`,
`WALLIX_BASTION_TOKEN`, `WALLIX_BASTION_API_VERSION`.

```hcl
provider "wallix-bastion" {
  ip          = "bastion-primary.example.local"   # run against the primary master only
  user        = "terraform"
  token       = var.bastion_api_key
  api_version = "v3.12"
}
```

Run Terraform against the primary master only: "In Master/Master mode, API provisioning must
not be performed simultaneously from both Bastions" ([Deployment Guide ch. 5](https://marketplace-wallix.s3.amazonaws.com/bastion_12.0.2_en_deployment_guide.pdf)).

## 2. Resources

### Active Directory external authentication (`externalauth_ldap`)

Arguments: `authentication_name`, `host`, `port`, `timeout`, `ldap_base`, `cn_attribute`,
`login_attribute`; optional `is_active_directory`, `login`, `password`, `is_ssl`,
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

### RADIUS external authentications to Trustelem Connect (`externalauth_radius`)

Arguments: `authentication_name`, `host`, `port`, `secret`, `timeout`; optional
`description`, `use_primary_auth_domain`. The GUI option "Use mobile device for 2 factor
authentication(2FA)" is not exposed: the provider source `resource_externalauth_radius.go` has
no such attribute (checked 2026-09-23), so set it in the GUI after every apply that recreates
the resource.

```hcl
resource "wallix-bastion_externalauth_radius" "trustelem_1" {
  authentication_name     = "Trustelem-RADIUS-1"
  host                    = "trustelem-connect-1.example.local"
  port                    = 1812
  secret                  = var.trustelem_radius_secret
  timeout                 = 50
  use_primary_auth_domain = true
}

resource "wallix-bastion_externalauth_radius" "trustelem_2" {
  authentication_name     = "Trustelem-RADIUS-2"
  host                    = "trustelem-connect-2.example.local"
  port                    = 1812
  secret                  = var.trustelem_radius_secret
  timeout                 = 50
  use_primary_auth_domain = true
}
```

### AD authentication domain with RADIUS as secondary (`authdomain_ad`)

Arguments: `domain_name`, `auth_domain_name`, `external_auths`, `default_language`,
`default_email_domain`; optional `group_attribute`, `display_name_attribute`,
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

### Group mappings (`authdomain_mapping`)

Arguments: `domain_id`, `user_group`, `external_group` (an AD DN, or the SAML group claim
value). Import format `<domain_id>/<user_group>`.

```hcl
resource "wallix-bastion_authdomain_mapping" "corp_admins" {
  domain_id      = wallix-bastion_authdomain_ad.corp.id
  user_group     = wallix-bastion_usergroup.pam_admins.group_name
  external_group = "CN=PAM-Admins,OU=Groups,DC=corp,DC=example,DC=local"
}
```

### SAML external authentication with the Trustelem metadata (`externalauth_saml`)

Arguments: `authentication_name`, `idp_metadata`, `timeout`, block
`claim_customization { username (required), displayname, email, group, language }`; optional
`certificate`, `private_key`, `passphrase`; computed `sp_entity_id`, `sp_metadata`,
`sp_assertion_consumer_service`, `sp_single_logout_service`, `idp_entity_id`,
`saml_request_url`.

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

The two outputs are the values to paste into the Trustelem application (EntityID and
Assertion Consumer Service). Rotate the Trustelem signing certificate by replacing the
metadata file and applying.

### SAML authentication domain (`authdomain_saml`)

Arguments: `domain_name`, `auth_domain_name`, `external_auths`, `default_email_domain`,
`default_language`, `label`; optional `force_authn`, `is_default`, `secondary_auth`;
computed `idp_initiated_url`.

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

### API key for Access Manager (`apikey_v2`)

Arguments: `apikey_name`, `profile`, `description`, `ip_limitation`; `profile` and
`ip_limitation` are immutable; "The Bastion API never returns the raw API key value ... always
reads back as a masked placeholder (********)", so capture the key at creation and store it in
the secret manager.

```hcl
resource "wallix-bastion_apikey_v2" "access_manager" {
  apikey_name   = "access-manager"
  profile       = "wallix_access_manager_session_audit"
  description   = "Access Manager farm"
  ip_limitation = "10.10.20.11,10.10.20.12"
}
```

### User groups and authorizations

`usergroup` (`group_name`, `timeframes`, optional `profile`, `users`, `restrictions`) and
`authorization` (`authorization_name`, `user_group`, `target_group`, `authorize_sessions`,
`subprotocols`, `approval_required`, `approvers`, `active_quorum`, `is_recorded`,
`is_critical`, and so on) complete the model; they are independent of Trustelem.

## 3. Not covered by the provider

No `externalauth_oidc` or `authdomain_oidc` resource exists in the documented set, so the OIDC
alternative stays manual. The RADIUS "Use mobile device for 2 factor authentication(2FA)" option should be verified in
the GUI after each apply until the provider documents it.

## 4. Workflow

1. `terraform plan` against the primary master in a change window.
2. Apply; the objects replicate to the second node through HA Database Replication.
3. Paste the SP outputs into Trustelem, download the metadata again if the SP entity ID
   changed, and run the [test plan](../trustelem/10-test-plan.md), sections B and A.
4. Keep the state file in a backend with encryption; it contains the RADIUS secret and the AD
   bind password.
