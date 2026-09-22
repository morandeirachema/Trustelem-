import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import sequence

print(sequence(
    ["Browser", "LB + Access Mgr", "Trustelem IdP", "Bastion"],
    [
        (0, 1, "GET /wabam/<org>?domain=<DOMAIN>"),
        (1, 0, "302 SAML AuthnRequest (Redirect)"),
        (0, 2, "GET <tenant>.trustelem.com/app/<ID>/sso"),
        ("note", 2, "AD password (ADConnect) + push/TOTP/passkey"),
        (2, 0, "SAML Response: signed assertion, NameID=email, attrs"),
        (0, 1, "POST assertion to the AM ACS"),
        ("note", 1, "verify signature, map Login/Profile, open session"),
        (1, 3, "REST 443 + X-Auth-Key: authorizations of login@DOMAIN"),
        (3, 1, "authorizations (SAML domain, group mapping)"),
        (0, 1, "launch session (WebSocket)"),
        (1, 3, "RDP 3389 / SSH 22 proxy login as login@DOMAIN"),
        ("note", 3, "no re-auth needed"),
    ], col_width=19))
