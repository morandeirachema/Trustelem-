# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A documentation and architecture workspace for a WALLIX Privileged Access Management (PAM) design:
WALLIX Trustelem (now sold as WALLIX One IDaaS) providing MFA/SSO for a WALLIX Bastion cluster and a
WALLIX Access Manager cluster. The main concern is Trustelem setup, configuration and integration;
Bastion and Access Manager content supports that. Trustelem-specific documents live in `docs/trustelem/`. There is no application code, build, lint or test tooling. Deliverables
are Markdown reports with ASCII box diagrams and links to vendor documentation.

## Conventions for documents in this repo

- Every technical claim must carry a link to its external source (vendor guide, release notes, KB article).
  Prefer primary WALLIX sources over blogs.
- Put today's date (ISO format) in the header of each report and state which product versions it was
  verified against (currently Bastion 12.3.2 and Access Manager 5.2.4.0).
- Diagrams are ASCII only (no Mermaid). Draw them with `tools/asciigrid.py` (Grid.box/vline/hline and
  `sequence()`), one script per diagram under `tools/diagrams/`, rendered into `docs/diagrams/*.txt`
  and pasted into the report. Never hand-edit a diagram; edit the script and re-render.
- Keep verified facts separate from inferences; mark gaps explicitly rather than guessing.
- No Claude references in commit messages or document bylines.
- Run `python3 tools/check_docs.py` before committing; it verifies fences, tables, placeholders, links
  and that every rendered diagram matches its script. Add a line to `CHANGELOG.md` for each change.

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
