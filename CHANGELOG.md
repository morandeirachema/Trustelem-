# Changelog

Dates are ISO. Each document's header states the versions and sources it was verified against.
Detailed history is in the git log.

## 2026-09-24

### Changed

- Repository refactored: the 1,326-line architecture report split into the
  [architecture set](docs/architecture/README.md); glossary and sources moved to
  `docs/reference/`; every document opens with the Purpose, Audience, Verified and Sources block;
  one home per fact, with links instead of restatements; README reduced to a landing page;
  writing rules moved to [CONTRIBUTING.md](CONTRIBUTING.md).
- Target versions set to Bastion 12.4.3 and Access Manager 6.0.5 after reviewing the customer
  guides (Bastion 12.4.3 and 12.0.25; Access Manager 6.0.5). Bastion HA and Access Manager farm
  runbooks rewritten on them; Access Manager 5.2 facts kept as labelled notes.
- Logging reference rewritten on the Bastion SIEM Logs Guide: transport, full event catalogue,
  verbatim `wabauth` lines, `AuthDomain` and `AuthDomainMapping` event types.

### Added

- `CONTRIBUTING.md`; header, anchor and duplicate-heading checks in `tools/check_docs.py`.
- Vendor meeting script with platform brief, hardware table and indicative timeline.
- External link checker `tools/check_links.py` and a weekly `link-check` workflow.
- Register rows T11 to T16, B9 to B11, A7 and the commercial rows C1 to C4.

### Fixed

- The Access Manager domain name must equal the Bastion *Domain server name*, as both product
  guides say; a same-day change to "Authentication domain name" was reverted.
- The Access Manager RADIUS listener on Trustelem Connect is port 2812, not 1812.
- Every cited claim re-checked against its source (vendor guides, Trustelem books, 69
  third-party sources): paraphrases no longer shown as quotes, about 40 statements marked as
  inference, wrong section citations, sources and product facts corrected.
- Fabrication check after the refactor: all 803 quotations found in the vendor and third-party
  texts; every new or changed prose claim reviewed against its source (no invented facts; about
  30 overstatements, dropped *inference* markers, changed meanings and wrong "home" links fixed).
- Register: B3, B7, B8, A2, A6 closed; B1, B2, B4, B6, A1, A3, A4, A5, A7, T4, T5 and S3
  narrowed with the customer guides; new rows B9 to B12.

## 2026-09-23

### Added

- Trustelem chapters 01 to 12, runbooks, references (Terraform, logging and SIEM, standards,
  SAML naming, API export) and the gaps register.
- `tools/check_docs.py`, the Mermaid parser check and the `docs-check` workflow.

### Changed

- All diagrams converted to Mermaid sources in `tools/diagrams/`.
- Research notes moved to `docs/archive/`.

### Fixed

- Quotations, commands, URL fragments and ticket IDs checked against the downloaded vendor
  texts; official EU texts (NIS2 Implementing Regulation 2024/2690, DORA RTS 2024/1774) quoted.

## 2026-09-22

### Added

- Repository and architecture report with diagrams, access-path coverage, administrator access
  model, OIDC alternative, disaster recovery, sizing, hardening and rollout plan.
