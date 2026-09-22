import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(100, 30)
g.box(0, 0, 100, 3, ["   WALLIX Trustelem cloud (SaaS, both sites use the same tenant, agents in each site)"])
g.put(24, 3, "+"); g.put(74, 3, "+"); g.vline(24, 4, 5); g.vline(74, 4, 5)
g.box(0, 6, 48, 18, ["  SITE A  (production)", "",
                     "  LB-A: HTTPS 443 (AM), 22/3389 (Bastion)", "",
                     "  AM-1  <==DB repl==>  AM-2", "",
                     "  Bastion-1 (primary master)", "  Bastion-2 (secondary master)",
                     "     HA Database Replication (M/M)", "",
                     "  ADConnect-A1/A2, Connect-A1/A2", "  Recording storage NFS/SMB (site A)",
                     "  Nightly wabam-backup + Bastion backup", "  shipped to site B (==> arrows)", "", ""])
g.box(52, 6, 48, 18, ["  SITE B  (disaster recovery)", "",
                      "  LB-B: same DNS names on failover", "",
                      "  AM-3 (cold or warm, restored from", "        wabam-backup of site A)", "",
                      "  Bastion-3 (standalone, restored from", "        site A backup; or a slave in", "        Master/Slaves if latency allows)",
                      "", "  ADConnect-B1, Connect-B1 (lower priority)", "  Recording storage (copy of site A)",
                      "  Own licence, SIEM, SMTP, NTP settings", "", ""])
g.put(24, 6, "+"); g.put(74, 6, "+")
g.put(48, 14, "==>"); g.put(48, 15, "==>")
g.put(0, 25, "Bastion audit and session tables are never replicated, so recordings and audit history must be")
g.put(0, 26, "copied at storage level. A DR Bastion refreshed by backup/restore is not real time (RPO = backup")
g.put(0, 27, "interval). Trustelem needs no DR action: agents in site B keep the tenant reachable.")
print(g.render())
