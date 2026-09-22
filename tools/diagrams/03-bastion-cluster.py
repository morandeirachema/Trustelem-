import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(90, 30)
g.box(20, 0, 50, 3, ["  Users (native RDP/SSH clients), Access Manager"])
g.put(44, 3, "+"); g.vline(44, 3, 5); g.put(46, 4, "RDP 3389, SSH 22, HTTPS 443 (UI + REST API)")
g.box(20, 6, 50, 4, ["  Front end: L4 load balancer, DNS name, or the", "  AM 'Cluster' (fewest open sessions wins)"])
g.put(44, 6, "+")
g.put(32, 9, "+"); g.put(57, 9, "+"); g.vline(32, 10, 11); g.vline(57, 10, 11)
g.box(10, 12, 32, 12, ["  Bastion node 1", "  role: primary master", "",
                       "  eth0  user + admin services", "  eth1  HA / replication NIC", "",
                       "  MariaDB (all config tables)", "  SSH admin console 2242", "  proxies, vault, recordings",
                       "  local: audit + session data"])
g.box(48, 12, 32, 12, ["  Bastion node 2", "  role: secondary master (M/M)", "  or passive slave (M/S)",
                       "  eth0  user + admin services", "  eth1  HA / replication NIC", "",
                       "  MariaDB (replica)", "  SSH admin console 2242", "  proxies, vault, recordings",
                       "  local: audit + session data"])
g.put(32, 12, "+"); g.put(57, 12, "+")
g.put(42, 16, "<====>"); g.put(42, 17, "3306/7"); g.put(42, 18, "tunnel")
g.put(0, 25, "HA Database Replication = MariaDB replication inside an autossh SSH tunnel. Slaves pull")
g.put(0, 26, "(local 3307 to master 3306). No VIP, no heartbeat: failover is 'bastion-replication")
g.put(0, 27, "--elevate-master' or front-end rerouting. Not replicated: audit/session tables, recording")
g.put(0, 28, "options, licence, network, SNMP, SMTP, SIEM, device certificates.")
print(g.render())
