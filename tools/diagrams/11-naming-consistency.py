import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from asciigrid import Grid

g = Grid(100, 18)
g.box(0, 0, 30, 9, [" Trustelem", " Access Manager app", "", " Domain      = TRUSTELEM", " Login attr  = uid", " script: profile, groups", " metadata -> AM and Bastion"])
g.box(35, 0, 30, 9, [" Access Manager", " SAML Identity Provider", "", " Domain Name = TRUSTELEM", " Login       = uid", " Profile     = profile", " Strip Domain OFF"])
g.box(70, 0, 30, 9, [" Bastion", " SAML auth domain", "", " Domain server = TRUSTELEM", " Username claim= uid", " Group claim   = groups", " mappings on group values"])
g.put(30, 4, "<===>"); g.put(65, 4, "<===>"); g.put(30, 5, "<===>"); g.put(65, 5, "<===>")
g.put(0, 9, "<===> marks values that must be identical on both sides.")
g.put(0, 10, "Assertion goes only to Access Manager (POST to the ACS). Access Manager then calls the Bastion REST")
g.put(0, 11, "API for user jdoe@TRUSTELEM; the Bastion resolves the user in its TRUSTELEM domain and applies the")
g.put(0, 12, "group mappings. Any mismatch in the three boxes produces an empty authorization list, not an error.")
print(g.render())
