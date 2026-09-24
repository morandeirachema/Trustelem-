# Changelog

Dates are ISO. Product versions verified are stated in each document header.

## 2026-09-24

- Deep audit and sync, cross-references: every meeting question now cites its register row or
  is marked as a design confirmation; new rows T14 (log retention) and T15 (hardware TOTP
  tokens); T1, T4, T5, A5, B1 and A1 extended; closed rows S1, S2 and B5 moved to a *Closed*
  section; register rows put in numeric order; report 9.1 and 7.5 point to the register and the
  test plan; README tree, dates, counts and CI wording corrected; archive notes indexed; stale
  `tools/__pycache__` file removed from git.
- Deep audit and sync, diagrams: the Access Manager RADIUS listener is port 2812 everywhere (it
  was 1812 in three diagrams, the port matrix and the runbook); component names unified across
  the eleven diagrams; the TOTP path drawn through the client and the Access-Challenge instead of
  the app; Master/Master failover by front-end rerouting and `--elevate-master` only for
  Master/Slaves; DR diagram per-node settings moved off the storage box; the Bastion field that
  must equal the Access Manager domain name is the Authentication domain name (Domain server name
  set identical); new gap B7 and meeting question 6.6 on which Bastion domain the Access Manager
  domain name matches; Access Manager to Trustelem 443 back-channel row added to the port matrix.
- Added the vendor meeting script (`docs/reference/vendor-meeting-script.md`): platform brief
  with components, integration order, hardware requirements and an indicative timeline, then
  eight question blocks (deployment model and on-premise TOTP, licensing, effort, support and
  roadmap, Bastion, Access Manager, MFA, logging) cross-referenced to the gaps register.
- `tools/check_docs.py` now skips `node_modules`, which the Mermaid check installs locally.
- README: clone and local check instructions at the bottom.
- Added `tools/check_links.py` (external link check, per-host serialised, retries, placeholder
  and code-span exclusion, login-gated and bot-blocking hosts reported as warnings) and a weekly
  `link-check` GitHub Actions workflow. First run over 120 URLs: one wrong link fixed in the
  meeting script (Trustelem Connect page), RFC links moved to the static
  `rfc-editor.org/rfc/rfcNNNN.html` renderings because the `info` pages timed out.
- Public release-notes pages re-read: they stop at Bastion 12.3.2 and Access Manager 5.2.4.0,
  so B1 and A1 stay open (noted in the register).
- Gaps register: swept every chapter for gap and inference markers; added T11 (no OIDC template), T12 (no offline mode), T13 (agent sizing), A7 (no syslog forwarder on Access Manager), the SCIM reconciliation question to T5, and a commercial section C1 to C4; matching questions 5.8 and 8.5 in the meeting script.

## 2026-09-23

- Mermaid labels shortened so boxes no longer overlap text (six diagram sources, README, report,
  SAML reference).
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
