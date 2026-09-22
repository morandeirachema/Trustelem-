import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(90, 19)
g.box(0, 0, 22, 12, [" Bastion node", "", " AD auth domain", " + Secondary auth", "   = RADIUS", "",
                     " 'Use mobile", "  device' = ON", "", " timeout 45-60 s"])
g.box(40, 0, 22, 4, [" Active Directory", " (primary factor)"])
g.put(22, 1, "-- 1. LDAP bind ->"); g.put(22, 2, "<- groups --------")
g.box(40, 6, 22, 5, [" Trustelem Connect", " RADIUS 1812/udp", " relays to cloud"])
g.put(22, 7, "- 2. Access-Req ->"); g.put(22, 9, "<- Access-Accept -")
g.box(70, 6, 16, 5, [" Trustelem", " cloud tenant", " (access rule)"])
g.put(62, 7, "- WSS ->"); g.put(62, 9, "<- OK --")
g.put(77, 10, "+"); g.vline(77, 11, 12); g.put(77, 13, "+")
g.box(70, 13, 16, 3, [" Authenticator"])
g.put(0, 17, "3. The user approves the push (or types a TOTP in the Access-Challenge).")
print(g.render())
