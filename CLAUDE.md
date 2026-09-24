# CLAUDE.md

Guidance for automated editors working in this repository.

## What this repository is

A documentation workspace for a WALLIX Privileged Access Management design: WALLIX Trustelem
(sold as WALLIX One IDaaS) providing MFA and SSO for a WALLIX Bastion cluster and a WALLIX Access
Manager cluster. The main concern is Trustelem setup, configuration and integration
(`docs/trustelem/`); the architecture set (`docs/architecture/`), runbooks and references support
it. There is no application code: only Markdown, Mermaid sources, three check scripts in `tools/`
and two GitHub Actions workflows.

## Rules

Follow [CONTRIBUTING.md](CONTRIBUTING.md): header block on every document, one home per fact,
verbatim quotes with a link to the source, *inference* and *gap* markers, Mermaid sources in
`tools/diagrams/`, checks before committing, one line in `CHANGELOG.md` per change. No Claude
references in documents or commit messages.

Target versions: Bastion 12.4.3 and Access Manager 6.0.5; the public 12.3.2 and 5.2.4.0 guides are
still cited where their text is unchanged.

## Vendor sources

- Public guides and release notes: listed in [docs/reference/sources.md](docs/reference/sources.md).
- Customer guides behind the doc.wallix.com login: the user downloaded the Bastion 12.4.3 and
  12.0.25 and Access Manager 6.0.5 PDFs to `~/Descargas/WallixDoc`. Extract them to the scratchpad
  with `pdftotext -layout`, cite them as "[Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.1",
  and never commit the PDFs or long excerpts to this public repository.
- Trustelem has no PDFs: its four public books export as HTML at
  `https://trustelem-doc.wallix.com/books/{book}/export/html`.

## Git

- Remote: https://github.com/morandeirachema/Trustelem- (public, branch `main`).
- Commit directly to `main` with plain descriptive messages.
- Research PDFs stay in the scratchpad; `.gitignore` excludes `*.pdf`.
