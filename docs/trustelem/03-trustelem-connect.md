# Trustelem Connect: the LDAP and RADIUS agent

Date: 2026-09-23. Sources: [LDAP-Radius - Trustelem Connect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect),
[SCIM client](https://trustelem-doc.wallix.com/books/trustelem-administration/page/scim-client),
[connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows),
[on-premise SIEM](https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem),
[access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules).
Quotes are verbatim.

## 1. Role

"a connector, Trustelem Connect, is installed on a local customer server and has the role of
LDAP server / Radius server. When it receives a request (LDAP search, LDAP bind, Radius Access
request, Radius Challenge request) then it sends the request to Trustelem." The same agent also
pushes logs to an on-premise SIEM and performs outbound SCIM provisioning.

"One opened port matches one protocol for one application on Trustelem": a Bastion RADIUS
listener and an Access Manager RADIUS listener are two ports (for example 1812 and 2812).
Default ports: "usually tcp port 2001 for LDAP, and udp port 1812 for Radius".

```mermaid
flowchart LR
    CL["Bastion nodes and<br/>Access Manager nodes<br/>(RADIUS + LDAP clients)"]
    subgraph TC["Trustelem Connect (one VM)"]
        L1[":1812/udp RADIUS, Bastion app"]
        L2[":2812/udp RADIUS, Access Manager app"]
        L3[":2001/tcp LDAP, Bastion app"]
    end
    T["Trustelem cloud<br/>access rules, factors"]
    CL -->|Access-Request / Access-Challenge| L1
    CL -->|Access-Request / Access-Challenge| L2
    CL -->|LDAP bind and search| L3
    TC -->|WebSocket 443 outbound, decision returned| T
    NOTE["One listener per protocol per application;<br/>secrets come from the application model in the console."]
    TC -.- NOTE
```

## 2. Create the service in the console

**Services** tab: "Click on the button + Create a service and copy the service ID." One service
per VM; "The recommendation is 2 VM at least, to have a failover system" (same rule as
ADConnect).

## 3. Install on Windows

1. "Start the setup (Trustelem Connect.exe), and paste your service ID."
2. "If you have a proxy, complete the field HTTP Proxy with the value:
   https://username:password@proxy_IP:proxy_port".
3. "Click on Validate the Configuration".
4. For LDAPS or StartTLS with your own certificate, "on the Trustelem Connect folder, add a
   config.ini file":

```ini
tls_cert="C:\Program Files (x86)\Trustelem\cert.pem"
tls_cert_key="C:\Program Files (x86)\Trustelem\key.pem"
```

5. "Start the service." Then in the console "Refresh your Services page. Turn on the service by
   clicking on No."

## 4. Install on Linux

1. "Install the connector as a service with the setup.sh script launch with root privilege."
2. "edit /opt/wallix/trustelem-connect/config.ini":

```ini
service_id = 2jy34wpcohrhdytr6hutym6qfi2l7nnw
state_dir = run/
# if there is a proxy
proxy = https://username:password@proxy_IP:proxy_port
# optional own certificate for LDAPS / StartTLS (PEM)
tls_cert = run/connector.crt
tls_cert_key = run/connector.key
```

3. "The run folder must have read write rights for the trustelem user."
4. `systemctl start trustelem-connect.service`; "The service will run with the user trustelem".

Config keys documented: `service_id`, `state_dir`, `proxy`, `tls_cert`, `tls_cert_key`,
`outgoing_allowed`, `[target.<name>]` with `addr` and `port`. Listen addresses and ports are
not in the file; they are set per application in the console.

## 5. Add the applications (listeners)

For Bastion and Access Manager use their dedicated app templates (chapters 04 and 05); the
generic procedure is: **Apps** > add an application (generic "Basic no SSO" model when only
LDAP or RADIUS is needed) > "Turn on LDAP and/or Radius" > back on the service page "click on
Add an application +" > "Click on LDAP and/or Radius button(s) to enable the protocol, then
enter the listen address and port" > "If you have setup Trustelem Connect to use LDAPS, then
check LDAPS" > Save.

Listen address: "the listen address can be localhost, all existing IP address on the machine =
*, or a specific IP"; "if you have a dedicated VM for the connector, choose *".

The secrets (LDAP bind DN, bind password, base DN, RADIUS shared secret) "are provided on the
setup of the Trustelem application" and can be shown later with the eye button on the service
page.

Restart the service after adding a target or changing `config.ini`; listener changes made in
the console are pushed to the agent.

## 6. What the LDAP listener exposes

- "If you have to choose between an Active Directory server or a LDAP server, you should choose
  Active Directory. Trustelem tries to replicate how an Active Directory answers."
- User DN `CN=my_user,DC=my_trustelem_domain,DC=trustelem,DC=com`; group DN
  `CN=my_group,OU=Groups,DC=my_trustelem_domain,DC=trustelem,DC=com`.
- "A Trustelem local user must have the login sets to mail"; "A user synchronized from Active
  Directory can have the login sets to sAMAccountName, userPrincipalName or mail".
- Bind account default `trustelem`; base DN `DC=<tenant>,DC=trustelem,DC=com`; user search
  filter `(mail=%u)` in the vendor's OpenVPN example.
- MFA over LDAP: with a *2 factors* access rule the bind succeeds only after a push approval
  ("only possible if the app have a timeout long enought") or with "login + password and TOTP
  code sticked together (for instance: mypasswordTOTP)". "If the user provides login + password
  and doesn't have WALLIX Authenticator, the authentication will failed". Passkeys are not
  usable over LDAP.

## 7. What the RADIUS listener does

- Two-step: "If the application supports Radius in 2 steps (Access Request then Challenge
  request) you can provide login + password then MFA." The Bastion and Access Manager support
  challenge-response.
- One-step: "If the application doesn't support Radius in 2 steps, you can provide login +
  password and code sticked together".
- Push-wait: "login + password then no answer from Trustelem before the validation of a push
  notification". Size the client timeout accordingly.
- Second factor only: with the *2nd factor only* rule the password is ignored, which is what the
  Bastion's "Use mobile device for 2 factor authentication(2FA)" option exploits by "automatically sending the login and
  an empty password".
- Always allow: "accept the authentication if the login is known, without any verification on
  the password/2nd factor" (use only as a deliberate exemption).
- MFA session: on a Bastion app with RADIUS enabled "you can also activate an MFA session";
  during that duration and on the same network the second factor is not requested again
  ([new features](https://trustelem-doc.wallix.com/books/trustelem-news/page/new-features)).
- Not documented: CHAP support (the Access Manager page specifies PAP), attributes returned in
  Access-Accept, RADIUS accounting.

## 8. Connectivity test

`./connect check <your sync id>` or `./connect check <your sync id> http://proxy.example.local:3128`.
Output fields:

| Field | Meaning (verbatim) |
|-------|--------------------|
| `Network: false` | "The connection could not be opened at all: the traffic is blocked or not routed." |
| `Network: true`, `CanTLS: false` | "The connection reaches the server but the TLS session fails: proxy or TLS inspection." |
| `CommOK: true` | "The flows are correct." |
| `RemoteIP` | "The public address your traffic is seen coming from." |

On Windows "open the Trustelem Connect or ADConnect configuration tool and use the connection
test."

## 9. Outbound targets: SIEM and SCIM

Both use the same mechanism: enable outgoing connections and declare a target.

```ini
outgoing_allowed = "true"
[target.siem]
addr = "siem.example.local"
port = "5514"
```

Or with the CLI: `./TrustelemConnect set-target <name> <host:port>` "writes a `[target.<name>]`
section in config.ini and enables outgoing connections"; options `-always-tls`, `-no-tls`,
`-insecure-allow-skip-tls-check`, `-override`. "Restart the service so the new target is
advertised to Trustelem." SIEM configuration itself is in chapter 07.

## 10. RADIUS transport security

RADIUS over UDP obfuscates only the password (MD5 XOR with the shared secret) and, without the
Message-Authenticator attribute on every packet, is exposed to CVE-2024-3596 (BlastRADIUS),
where an on-path attacker can turn an Access-Reject into an Access-Accept
([blastradius.fail](https://www.blastradius.fail/)). Neither the Bastion guide nor the Trustelem
Connect page documents Message-Authenticator, RADIUS/TLS is not offered, and no WALLIX advisory
on the CVE was found ([advisories](https://www.wallix.com/support-services/alerts/)). Until
WALLIX confirms the behaviour, treat the Bastion-to-Connect hop as one that must stay inside a
trusted administration network: same VLAN or host-adjacent placement, no crossing of user
networks, and firewall rules that allow 1812/udp only from the Bastion and Access Manager
addresses. Details and the vendor questions are in
[Standards and compliance](../reference/standards-and-compliance.md).

## 11. Placement and sizing guidance

- Two VMs on separate hosts, ideally one per site; listeners bound to `*` on a dedicated VM.
- Put the VMs on the same network segment as the Bastion and Access Manager nodes so RADIUS
  (UDP) does not cross stateful devices that time out challenge exchanges.
- The vendor gives no throughput numbers ("minimal resources"). Each pending push occupies a
  request for up to the client timeout; keep timeouts at 45 to 60 s and count concurrent logins.
- Manage the VMs through the Bastion once it is live, and log their OS events to the SIEM.
