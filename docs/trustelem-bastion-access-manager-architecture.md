# WALLIX Trustelem MFA for a Bastion cluster and an Access Manager cluster

> - **Purpose:** this report moved; this page maps its old section numbers to the new documents.
> - **Audience:** readers following an old link or an old section number.
> - **Verified:** 2026-09-24.
> - **Sources:** the [architecture set](architecture/README.md), the [glossary](reference/glossary.md) and the [sources](reference/sources.md).

The architecture report was split into focused documents under `docs/architecture/`; start at the [architecture index](architecture/README.md). The glossary and the bibliography moved to `docs/reference/`. Most sections moved as they were. The setup steps of the old section 7, the Trustelem IP list of the old port matrix and the Access Manager log details of the old section 8 now live only in the chapters, runbooks and references that own them, and the new files link there; the revision history is in [CHANGELOG.md](../CHANGELOG.md).

## 1. Where each section went

| Old section | New location |
|-------------|--------------|
| 1. Executive summary | [01-overview.md#1-executive-summary](architecture/01-overview.md#1-executive-summary) |
| 2. Product naming and versions | [01-overview.md#2-product-naming-and-versions](architecture/01-overview.md#2-product-naming-and-versions) |
| 3. Component architecture | [02-components.md](architecture/02-components.md) |
| 3.1 Trustelem / WALLIX One IDaaS | [02-components.md#1-trustelem--wallix-one-idaas](architecture/02-components.md#1-trustelem--wallix-one-idaas) |
| 3.2 WALLIX Bastion | [02-components.md#2-wallix-bastion](architecture/02-components.md#2-wallix-bastion) |
| 3.3 WALLIX Access Manager | [02-components.md#3-wallix-access-manager](architecture/02-components.md#3-wallix-access-manager) |
| 4. High-level design | [03-design-and-flows.md](architecture/03-design-and-flows.md) |
| 4.1 Design decisions | [03-design-and-flows.md#1-design-decisions](architecture/03-design-and-flows.md#1-design-decisions) |
| 4.2 Identity flow, web path | [03-design-and-flows.md#2-identity-flow-web-path](architecture/03-design-and-flows.md#2-identity-flow-web-path) |
| 4.3 Identity flow, native client path | [03-design-and-flows.md#3-identity-flow-native-client-path](architecture/03-design-and-flows.md#3-identity-flow-native-client-path) |
| 4.4 Alternative flows | [03-design-and-flows.md#4-alternative-flows](architecture/03-design-and-flows.md#4-alternative-flows) |
| 4.5 Access path coverage | [03-design-and-flows.md#5-access-path-coverage](architecture/03-design-and-flows.md#5-access-path-coverage) |
| 4.6 Administrator access model | [03-design-and-flows.md#6-administrator-access-model](architecture/03-design-and-flows.md#6-administrator-access-model) |
| 4.7 OpenID Connect as the alternative to SAML | [03-design-and-flows.md#7-openid-connect-as-the-alternative-to-saml](architecture/03-design-and-flows.md#7-openid-connect-as-the-alternative-to-saml) |
| 5. Cluster design | [04-clusters-and-dr.md](architecture/04-clusters-and-dr.md) |
| 5.1 Bastion cluster | [04-clusters-and-dr.md#1-bastion-cluster](architecture/04-clusters-and-dr.md#1-bastion-cluster) |
| 5.2 Access Manager cluster (farm) | [04-clusters-and-dr.md#2-access-manager-cluster-farm](architecture/04-clusters-and-dr.md#2-access-manager-cluster-farm) |
| 5.3 Failure modes | [04-clusters-and-dr.md#3-failure-modes](architecture/04-clusters-and-dr.md#3-failure-modes) |
| 5.4 Disaster recovery and multi-site | [04-clusters-and-dr.md#4-disaster-recovery-and-multi-site](architecture/04-clusters-and-dr.md#4-disaster-recovery-and-multi-site) |
| 6. Low-level design | [05-low-level-design.md](architecture/05-low-level-design.md) |
| 6.1 Naming and mapping rules | [05-low-level-design.md#1-naming-and-mapping-rules](architecture/05-low-level-design.md#1-naming-and-mapping-rules) |
| 6.2 Certificates, keys and secrets | [05-low-level-design.md#2-certificates-keys-and-secrets](architecture/05-low-level-design.md#2-certificates-keys-and-secrets) |
| 6.3 Network flows and ports | [05-low-level-design.md#3-network-flows-and-ports](architecture/05-low-level-design.md#3-network-flows-and-ports) |
| 6.4 Timeouts to align | [05-low-level-design.md#4-timeouts-to-align](architecture/05-low-level-design.md#4-timeouts-to-align) |
| 6.5 Sizing | [05-low-level-design.md#5-sizing](architecture/05-low-level-design.md#5-sizing) |
| 6.6 Security hardening checklist | [05-low-level-design.md#6-security-hardening-checklist](architecture/05-low-level-design.md#6-security-hardening-checklist) |
| 7. Setup runbook | [06-deployment-and-rollout.md](architecture/06-deployment-and-rollout.md) |
| 7.1 Prerequisites | [06-deployment-and-rollout.md#1-prerequisites](architecture/06-deployment-and-rollout.md#1-prerequisites) |
| 7.2 Trustelem tenant | [06-deployment-and-rollout.md#2-trustelem-tenant](architecture/06-deployment-and-rollout.md#2-trustelem-tenant) |
| 7.3 Bastion cluster | [06-deployment-and-rollout.md#3-bastion-cluster](architecture/06-deployment-and-rollout.md#3-bastion-cluster) |
| 7.4 Access Manager farm | [06-deployment-and-rollout.md#4-access-manager-farm](architecture/06-deployment-and-rollout.md#4-access-manager-farm) |
| 7.5 Acceptance tests | [06-deployment-and-rollout.md#5-acceptance-tests](architecture/06-deployment-and-rollout.md#5-acceptance-tests) |
| 7.6 Rollout and rollback | [06-deployment-and-rollout.md#6-rollout-and-rollback](architecture/06-deployment-and-rollout.md#6-rollout-and-rollback) |
| 8. Operations | [07-operations.md](architecture/07-operations.md) |
| 8.1 Monitoring and logging | [07-operations.md#1-monitoring-and-logging](architecture/07-operations.md#1-monitoring-and-logging) |
| 8.2 Rotation and lifecycle | [07-operations.md#2-rotation-and-lifecycle](architecture/07-operations.md#2-rotation-and-lifecycle) |
| 8.3 Upgrades and backups | [07-operations.md#3-upgrades-and-backups](architecture/07-operations.md#3-upgrades-and-backups) |
| 9. Caveats and gaps | [08-caveats-and-questions.md#1-caveats-and-gaps](architecture/08-caveats-and-questions.md#1-caveats-and-gaps) |
| 9.1 Questions to put to WALLIX before sign-off | [08-caveats-and-questions.md#2-questions-to-put-to-wallix-before-sign-off](architecture/08-caveats-and-questions.md#2-questions-to-put-to-wallix-before-sign-off) |
| 10. Glossary | [glossary.md](reference/glossary.md) |
| 11. Sources | [sources.md](reference/sources.md) |
