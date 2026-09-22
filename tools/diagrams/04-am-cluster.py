import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(96, 33)
g.box(0, 0, 24, 6, [" Privileged users", " browser HTTPS 443", " (HTML5 RDP/SSH,", "  WebSocket)"])
g.put(24, 2, "---->")
g.box(30, 0, 64, 6, ["  L7 load balancer in front of the farm",
                     "  - HTTPS 443, WebSocket upgrade, health check on 443",
                     "  - X-Forwarded-For + web.proxy.trusted-proxies on AM",
                     "  - source-IP affinity (cookie persistence breaks WAMUT)"])
g.put(45, 5, "+"); g.put(79, 5, "+"); g.vline(45, 6, 7); g.vline(79, 6, 7)
g.box(30, 8, 30, 11, ["  Access Manager node 1", "  Debian appliance, Docker", "  Jetty 11 / Java 17",
                      "  FreeRDP + xterm.js HTML5", "  MariaDB (local instance)", "  Elasticsearch (audit)",
                      "  eth0 users   eth1 HA", "  eth2 admin (SSH 2242)", "  wabam.properties"])
g.box(64, 8, 30, 11, ["  Access Manager node 2", "  same image and version", "  crypto.install.key,",
                      "  db.connections*, and", "  user.admin* copied", "  from node 1",
                      "  eth0 users   eth1 HA", "  eth2 admin (SSH 2242)", "  wabam.properties"])
g.put(45, 8, "+"); g.put(79, 8, "+")
g.put(60, 12, " HA "); g.put(60, 13, "<==>"); g.put(60, 14, " DB ")
g.put(45, 18, "+"); g.put(79, 18, "+"); g.vline(45, 19, 21); g.vline(79, 19, 21)
g.put(47, 19, "REST API 443 (API key)"); g.put(47, 20, "RDP 3389, SSH 22 to proxies")
g.put(81, 19, "SAML/OIDC 443"); g.put(81, 20, "RADIUS 1812")
g.box(30, 22, 30, 5, ["  Bastion cluster", "  (AM Cluster object,", "  identical mode on)"])
g.box(64, 22, 30, 5, ["  Trustelem", "  (SAML/OIDC IdP) and", "  Trustelem Connect RADIUS"])
g.put(45, 22, "+"); g.put(79, 22, "+")
g.put(0, 28, "MariaDB replication between nodes runs on the HA NIC (appliance script since AM 5.0,")
g.put(0, 29, "'--prerequisite-check', /root/sqlreplication/servers_list). Uninstall replication before")
g.put(0, 30, "upgrading a cluster (release note WAB-17588). Enable purge.audit.active on one node only.")
print(g.render())
