# Architecture

The design of WALLIX Trustelem (WALLIX One IDaaS) MFA for a WALLIX Bastion cluster and a WALLIX
Access Manager cluster, split by question. Each document carries its own sources; terms are in
the [glossary](../reference/glossary.md) and the bibliography in [sources](../reference/sources.md).

| Document | What it answers |
|----------|-----------------|
| [01 Overview](01-overview.md) | What is the design, which products and versions, which target versions, which certifications? |
| [02 Components](02-components.md) | What does Trustelem, the Bastion and Access Manager each provide, with which protocols and factors? |
| [03 Design and flows](03-design-and-flows.md) | Which design decisions, how a login flows on the web and native paths, which factor protects each access path, how administrators log in? |
| [04 Clusters and DR](04-clusters-and-dr.md) | How do the Bastion pair and the Access Manager farm replicate and fail over, and how does a second site recover? |
| [05 Low-level design](05-low-level-design.md) | Which names must match, which certificates and secrets exist, which ports to open, which timeouts to align, how to size and harden? |
| [06 Deployment and rollout](06-deployment-and-rollout.md) | What must be ready first, in which order to build, how to sign off, how to roll out and roll back? |
| [07 Operations](07-operations.md) | What to monitor, how to rotate secrets and handle users, how to upgrade and back up? |
| [08 Caveats and questions](08-caveats-and-questions.md) | What are the known limits, and what must WALLIX answer before sign-off? |

Recommended reading order:

1. Everyone: 01, then 03.
2. PAM architect: 02, 04, 05 and 08.
3. Build team: 05, 06, then the [Trustelem chapters](../trustelem/README.md) and the
   [runbooks](../runbooks/bastion-ha-replication.md) that 06 points to.
4. Operations team: 07, with the [logging and SIEM reference](../reference/logging-and-siem.md).
