import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(108, 34)
g.box(20, 0, 66, 9, ["        WALLIX Trustelem cloud tenant (SaaS, EU datacenters)",
                     "   admin-<tenant>.trustelem.com   |   <tenant>.trustelem.com",
                     "",
                     "   Users, Groups, Directories, Apps, Services, Access rules,",
                     "   Security settings, Application certificates, Logs, API",
                     "",
                     "   SAML 2.0 IdP      OIDC provider      RADIUS + LDAP backend"])
g.put(86, 3, "443"); g.put(86, 4, "<-->"); g.put(86, 5, "push")
g.box(90, 1, 16, 7, [" WALLIX", " Authenticator", " app: iOS,", " Android,", " Windows"])
g.put(23, 8, "+"); g.put(66, 8, "+")
g.vline(23, 9, 13); g.vline(66, 9, 13)
g.put(25, 10, "WebSocket TLS 443"); g.put(25, 11, "outbound only, cert pinned")
g.put(68, 10, "WebSocket TLS 443"); g.put(68, 11, "outbound only, cert pinned")
g.box(0, 14, 44, 8, ["  Trustelem ADConnect (2 VMs, priority)",
                     "  Windows service or Linux daemon",
                     "  - syncs users/groups from AD (memberOf)",
                     "  - validates AD passwords (never stored)",
                     "  - IWA/Kerberos, AD password reset",
                     "  - LDAP/LDAPS 389/636 to domain ctrls"])
g.put(23, 14, "+")
g.box(46, 14, 44, 8, ["  Trustelem Connect (2 VMs, failover)",
                      "  Windows or Linux, runs as 'trustelem'",
                      "  - RADIUS server  UDP 1812 (2812 if busy)",
                      "  - LDAP server TCP 2001 (LDAPS/StartTLS)",
                      "  - SCIM client, SIEM log push every 30 s",
                      "  - relays RADIUS requests to the cloud"])
g.put(66, 14, "+")
g.vline(10, 22, 24); g.put(10, 21, "+"); g.put(10, 25, "+")
g.put(12, 22, "LDAP/LDAPS 389/636"); g.put(12, 23, "read-only bind account")
g.box(0, 25, 26, 4, [" Active Directory", " (source of truth)"])
g.vline(56, 22, 24); g.put(56, 21, "+"); g.put(56, 25, "+")
g.vline(78, 22, 24); g.put(78, 21, "+"); g.put(78, 25, "+")
g.put(58, 22, "RADIUS 1812/udp"); g.put(58, 23, "PAP + challenge")
g.put(80, 22, "RADIUS 1812/udp"); g.put(80, 23, "PAP")
g.box(46, 25, 20, 4, [" Bastion nodes", " (RADIUS client)"]); g.box(68, 25, 20, 4, [" Access Manager", " (RADIUS client)"])
g.put(0, 31, "Passkeys and FIDO2 keys work only on the web (SAML/OIDC) path. Over LDAP and RADIUS the second")
g.put(0, 32, "factor is a push approval, a TOTP, or a password+code concatenation.")
print(g.render())
