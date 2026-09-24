# Writing and maintaining these documents

> - **Purpose:** the rules every document in this repository follows, so that a reader can trust
>   any page without reading the others first.
> - **Audience:** anyone editing the repository, human or automated.
> - **Verified:** 2026-09-24; the checks below are enforced by `tools/check_docs.py`.
> - **Sources:** this repository's own conventions.

## 1. Document header

Every document under `docs/` (except folder `README.md` indexes and `docs/archive/`) starts with
its title and this block, in this order:

```markdown
# Title

> - **Purpose:** one sentence on what the reader gets from this page.
> - **Audience:** who should read it (PAM architect, Trustelem administrator, Bastion operator...).
> - **Verified:** ISO date, and the product versions or documentation read on that date.
> - **Sources:** the main vendor pages or guides, as links.
```

The check script fails when a label is missing. Keep each item short; details belong in the body.

## 2. One home per fact

A fact is written, with its source, in exactly one document. Other documents link to it instead
of restating it. The owners are:

| Fact | Home |
|------|------|
| Product names, versions verified, target versions, certifications | [architecture overview](docs/architecture/01-overview.md) |
| Trustelem egress destinations (FQDNs, IPs, TLS inspection, proxy) | [tenant setup, section 4](docs/trustelem/01-tenant-setup.md) |
| RADIUS and LDAP listener ports on Trustelem Connect | [Trustelem Connect](docs/trustelem/03-trustelem-connect.md) |
| Network flow and port matrix | [low-level design](docs/architecture/05-low-level-design.md) |
| Timeouts to align, sizing, hardening checklist | [low-level design](docs/architecture/05-low-level-design.md) |
| Names that must match (domain, login attribute, groups) | [SAML assertion and naming](docs/reference/saml-assertion-and-naming.md) |
| Access rule values per group | [MFA and access rules](docs/trustelem/06-mfa-and-access-rules.md) |
| Bastion HA procedures | [Bastion HA runbook](docs/runbooks/bastion-ha-replication.md) |
| Access Manager farm procedures | [Access Manager farm runbook](docs/runbooks/access-manager-farm.md) |
| Log formats and detection rules | [logging and SIEM](docs/reference/logging-and-siem.md) |
| Test IDs and expected results | [test plan](docs/trustelem/10-test-plan.md) |
| Open questions | [gaps register](docs/reference/open-questions-and-gaps.md) |
| Terms | [glossary](docs/reference/glossary.md) |

Two exceptions: the [vendor meeting script](docs/reference/vendor-meeting-script.md) is printed
and read on its own, so it may repeat figures, each with a link to its home; and the landing
[README](README.md) summarises the key facts in one line each, linking to their homes without
repeating figures or sources.

## 3. Sources and claims

- Every technical claim carries a link to its source: the vendor page, guide section, release
  note or standard. Prefer WALLIX primary sources over blogs and partner pages.
- Quotations are verbatim, in double quotes; vendor typos are kept and marked [sic].
- Customer guides behind the [doc.wallix.com](https://doc.wallix.com/) login are cited by title
  and section, for example "[Bastion 12.4.3 Deployment Guide](https://doc.wallix.com/) 5.1".
  Their PDFs and long excerpts never go into this public repository.
- A deduction from the sources is marked *inference*; something the sources do not answer is
  marked *gap* and gets a row in the gaps register.
- Facts that apply only to an older version are kept in a labelled note ("*Access Manager 5.2:*").

## 4. Writing

- Plain English, short sentences, one idea per sentence. Lead each section with the answer.
- Use the vendor's exact names for menus, fields and options, in bold for menu paths and in
  backticks for commands, files, parameters and values.
- Numbers as digits with units ("45 to 60 s"); ranges written "45 to 60".
- No first person, no Claude or tool references in documents or commit messages.

## 5. Diagrams

Diagrams are Mermaid only. Each has one source in `tools/diagrams/*.mmd`, embedded verbatim as a
fenced `mermaid` block. Edit the source and re-paste it; never edit a diagram inline. Use
`{placeholder}` rather than `<placeholder>` inside sequence diagrams.

## 6. Checks and changes

```bash
python3 tools/check_docs.py                  # structure, headers, links and anchors, diagrams
npm install --no-save mermaid@11 jsdom@24    # once, for the diagram parser
node tools/check_mermaid.mjs                 # Mermaid syntax
python3 tools/check_links.py                 # external links, needs Internet access
```

GitHub Actions runs the first two on every push to `main` and on pull requests, and the link
check every Monday. Every change adds a line to [CHANGELOG.md](CHANGELOG.md).
