# Changelog

Dates are ISO. Product versions verified are stated in each document header.

## 2026-09-24

- Added the vendor meeting script (`docs/reference/vendor-meeting-script.md`): platform brief
  with components, integration order, hardware requirements and an indicative timeline, then
  eight question blocks (deployment model and on-premise TOTP, licensing, effort, support and
  roadmap, Bastion, Access Manager, MFA, logging) cross-referenced to the gaps register.
- `tools/check_docs.py` now skips `node_modules`, which the Mermaid check installs locally.
- README: clone and local check instructions at the bottom.
- Gaps register: swept every chapter for gap and inference markers; added T11 (no OIDC template), T12 (no offline mode), T13 (agent sizing), A7 (no syslog forwarder on Access Manager), the SCIM reconciliation question to T5, and a commercial section C1 to C4; matching questions 5.8 and 8.5 in the meeting script.

## 2026-09-23

- Gap closure pass: official texts of Implementing Regulation 2024/2690 and DORA RTS 2024/1774
  read and quoted (an earlier row had attributed recital wording to point 11.7.1); eth1 HA note
  from the Bastion release notes; Terraform RADIUS resource verified from source; absence of a
  Trustelem status page, push number matching and remember-device confirmed in the books.
- Second audit: every command, key, path, URL fragment and ticket ID checked against the vendor
  texts, the Splunk add-on and the Sekoia page; fixed three undocumented console URL fragments,
  the SSH connection syntax in the help-desk guide and a `connect check` expectation; added the
  open questions and gaps register.
- Fabrication review: every quotation checked against the downloaded vendor texts; corrected a
  sentence wrongly attributed to Trustelem (single source of identity), the LDAP two-factor
  wording, two option names, a Trustelem spelling, and rewrote the API export scripts against the
  documented signatures; external standards quotes verified at their source.
- All diagrams converted to Mermaid (`tools/diagrams/*.mmd`); ASCII grid tooling removed;
  `tools/check_docs.py` now verifies Mermaid embedding and `tools/check_mermaid.mjs` parses every
  diagram with the Mermaid library in CI.
- Reference: Trustelem API export scripts (permissions, identities, logs, alerts) as the
  substitute for the missing tenant backup.
- SCIM host scim.wallix.com and Access Manager 6.0 / Bastion 12.4 notes re-checked: still
  unreachable or login-only.
- Trustelem chapter 12: SCIM provisioning assessment (plausible, undocumented, vendor questions).
- Trustelem chapters 09 (worked example), 10 (test plan), 11 (user and help-desk guide).
- Reference: SAML assertion and naming consistency, with the naming diagram.
- Docs check script (`tools/check_docs.py`) and GitHub Actions workflow.
- Research notes moved to `docs/archive/` as superseded material.
- Trustelem chapters 01 to 08 (tenant setup, ADConnect, Trustelem Connect, Bastion and Access
  Manager integration, MFA and access rules, operations, troubleshooting).
- Runbooks (Bastion HA Database Replication, Access Manager farm); references (Terraform for the
  Bastion side, logging and SIEM, standards and compliance).
- README refactored around Trustelem setup, configuration and integration.
- Architecture report: advisory scope corrected (Bastion 12.3.0 to 12.3.6 and 12.4.0),
  certification facts (BSI BSZ-0020-2025), RADIUS transport security note.

## 2026-09-22

- Repository created; architecture report with diagrams; gap review adding access-path
  coverage, administrator access model, OIDC alternative, disaster recovery, sizing, hardening,
  rollout plan, vendor questions and glossary.
