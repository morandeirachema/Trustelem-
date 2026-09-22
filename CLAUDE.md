# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A documentation and architecture workspace for a WALLIX Privileged Access Management (PAM) design:
WALLIX Trustelem (now sold as WALLIX One IDaaS) providing MFA/SSO for a WALLIX Bastion cluster and a
WALLIX Access Manager cluster. There is no application code, build, lint or test tooling. Deliverables
are Markdown reports with ASCII/Mermaid diagrams and links to vendor documentation.

## Conventions for documents in this repo

- Every technical claim must carry a link to its external source (vendor guide, release notes, KB article).
  Prefer primary WALLIX sources over blogs.
- Put today's date (ISO format) in the header of each report and state which product versions it was
  verified against (currently Bastion 12.3.2 and Access Manager 5.2.4.0).
- ASCII diagram boxes must be aligned (equal width borders, consistent padding) so they render cleanly in
  plain Markdown.
- Keep verified facts separate from inferences; mark gaps explicitly rather than guessing.
- No Claude references in commit messages or document bylines.

## Vendor documentation sources

- WALLIX One PAM documentation index: https://pam.wallix.one/documentation/administration/getting-started/documentation.html
- Bastion Functional Administration Guide (PDF): https://pam.wallix.one/documentation/admin-doc/bastion_en_administration_guide.pdf
- Access Manager Administration Guide (PDF): https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf
- Bastion release notes: https://pam.wallix.one/documentation/release-notes/bastion-rn-en.html
- Access Manager release notes: https://pam.wallix.one/documentation/release-notes/am-rn-en.html
- The HTML doc site https://doc.wallix.com/ requires a WALLIX Trustelem SSO login; use the PDFs above instead.
- Useful workflow: download the PDFs to the scratchpad and run `pdftotext -layout` to grep chapters.

## Git

- Remote: https://github.com/morandeirachema/Trustelem- (public repository, branch `main`).
- Commit directly to `main` with plain descriptive messages; the report lives under `docs/`.
- PDFs downloaded for research are ignored by `.gitignore`; keep them in the scratchpad, not the repo.
