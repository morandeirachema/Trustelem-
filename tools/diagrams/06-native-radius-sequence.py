import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import sequence

print(sequence(
    ["RDP/SSH client", "Bastion proxy", "Active Dir.", "Trustelem Conn.", "Trustelem cloud", "Authenticator"],
    [
        (0, 1, "TCP 3389 / 22, login user@AD + AD password"),
        (1, 2, "LDAP bind (primary factor)"),
        (2, 1, "bind OK + group membership"),
        (1, 3, "RADIUS Access-Request: User-Name, NAS-Id=WAB, Framed-IP"),
        (3, 4, "forward over WebSocket 443"),
        (4, 5, "push notification"),
        (5, 4, "approve (or TOTP via Access-Challenge)"),
        (4, 3, "accept"),
        (3, 1, "RADIUS Access-Accept"),
        ("note", 1, "authorization check, target selection, recording"),
        (1, 0, "proxied session to target"),
    ], col_width=19))
