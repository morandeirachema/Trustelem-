import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import sequence

print(sequence(
    ["RDP/SSH client", "Bastion proxy", "Active Dir.", "Trustelem Conn.", "Authenticator"],
    [
        (0, 1, "TCP 3389/22, user@AD + AD password"),
        (1, 2, "LDAP bind (primary factor)"),
        (2, 1, "bind OK + groups"),
        (1, 3, "RADIUS Access-Request (User-Name, NAS-Id=WAB, Framed-IP)"),
        ("note", 3, "relayed to cloud, WSS 443"),
        (3, 4, "push notification"),
        (4, 3, "approve or TOTP code"),
        (3, 1, "RADIUS Access-Accept"),
        ("note", 1, "authz check, target selection, recording"),
        (1, 0, "proxied session to target"),
    ], col_width=17))
