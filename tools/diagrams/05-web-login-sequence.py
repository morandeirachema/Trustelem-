import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import sequence

print(sequence(
    ["Browser", "LB + Access Manager", "Trustelem IdP", "Bastion"],
    [
        (0, 1, "GET https://am/wabam/<org>?domain=<DOMAIN>"),
        (1, 0, "302 SAML AuthnRequest (Redirect binding)"),
        (0, 2, "GET <tenant>.trustelem.com/app/<ID>/sso"),
        ("note", 2, "AD password via ADConnect, then push / TOTP / passkey"),
        (2, 0, "SAML Response: signed assertion, NameID=email, uid/email/profile"),
        (0, 1, "POST assertion to AM ACS"),
        ("note", 1, "verify signature, map Login/Profile, open web session"),
        (1, 3, "REST API 443 + X-Auth-Key: authorizations of login@DOMAIN"),
        (3, 1, "authorizations (SAML domain user, group mapping)"),
        (0, 1, "launch session (WebSocket)"),
        (1, 3, "RDP 3389 / SSH 22 proxy connection as login@DOMAIN"),
        ("note", 3, "no re-auth: identity trusted from AM"),
    ], col_width=23))
