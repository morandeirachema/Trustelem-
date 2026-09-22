import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(100, 8)
g.box(0, 0, 22, 6, [" Trustelem cloud", " admin.trustelem", " .com (WSS 443)"])
g.box(36, 0, 26, 6, [" ADConnect VM 1 (prio 1)", " ADConnect VM 2 (prio 2)", " read-only AD account"])
g.box(76, 0, 22, 6, [" Domain", " controllers", " LDAP/LDAPS 389/636"])
g.put(22, 1, "<-- WSS 443 --"); g.put(22, 3, "<-- WSS 443 --")
g.put(62, 1, "-- LDAP 389 ->"); g.put(62, 3, "-- LDAP 636 ->")
g.put(0, 7, "Outbound only: each agent opens the websocket; the cloud uses the first healthy connector.")
print(g.render())
