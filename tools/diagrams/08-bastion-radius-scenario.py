import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(96, 16)
g.box(0, 0, 22, 12, [" Bastion node", "", " AD auth domain", " + Secondary auth", "   = RADIUS", "",
                     " 'Use mobile", "  device' = ON", "", " timeout 45-60 s"])
g.box(36, 0, 22, 4, [" Active Directory", " (primary factor)"])
g.put(22, 1, "-- 1. LDAP bind ->"); g.put(22, 2, "<- groups --------")
g.box(36, 6, 22, 5, [" Trustelem Connect", " RADIUS 1812/udp", " relays to cloud"])
g.put(22, 7, "-- 2. Access-Req ->"); g.put(22, 9, "<- Access-Accept --")
g.box(66, 6, 16, 5, [" Trustelem", " cloud tenant", " (access rule)"])
g.put(58, 7, "-WSS 443->"); g.put(58, 9, "<- push OK")
g.put(73, 11, "+"); g.vline(73, 12, 12)
g.box(66, 13, 16, 3, [" Authenticator"])
g.put(0, 13, "3. The user approves the push (or types a TOTP in the Access-Challenge).")
print(g.render())
