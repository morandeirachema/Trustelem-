import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(100, 9)
g.box(0, 0, 22, 7, [" Bastion nodes", " Access Manager", " nodes", "", " RADIUS + LDAP", " clients"])
g.box(40, 0, 30, 7, [" Trustelem Connect VM", "", " :1812/udp  Bastion app", " :2812/udp  Access Mgr app", " :2001/tcp  LDAP (Bastion)", " relays each request"])
g.box(84, 0, 16, 7, [" Trustelem", " cloud", "", " access rules,", " factors"])
g.put(22, 2, "- Access-Request ->"); g.put(22, 3, "<- Accept/Challenge")
g.put(22, 4, "- LDAP bind ------>"); g.put(22, 5, "<- bind result ----")
g.put(70, 2, "- WSS 443 -->"); g.put(70, 3, "<-- decision ")
g.put(0, 8, "One listener per protocol per application; secrets come from the application model in the console.")
print(g.render())
