# Trustelem Connect: the LDAP and RADIUS agent

> - **Purpose:** install two Trustelem Connect agents and publish the LDAP and RADIUS listeners
>   that the Bastion and Access Manager use for Trustelem MFA.
> - **Audience:** Trustelem administrator, system and network administrators of the agent VMs.
> - **Verified:** 2026-09-24, against the Trustelem documentation books as read on 2026-09-24.
> - **Sources:** [LDAP-Radius - Trustelem Connect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/ldap-radius-trustelem-connect),
>   [SCIM client](https://trustelem-doc.wallix.com/books/trustelem-administration/page/scim-client),
>   [connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows),
>   [on-premise SIEM](https://trustelem-doc.wallix.com/books/trustelem-administration/page/on-premise-siem),
>   [access rules](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules),
>   [MFA](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication),
>   [Bastion app page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion).

All quotes without another source are from the LDAP-Radius Trustelem Connect page. This
chapter is the repository's home for the RADIUS and LDAP listener ports.

## 1. Role and listeners

Trustelem Connect is a local LDAP and RADIUS server that forwards every request to the
Trustelem cloud. "a connector, Trustelem Connect, is installed on a local customer server and
has the role of LDAP server / Radius server. When it receives a request (LDAP search, LDAP bind,
Radius Access request, Radius Challenge request) then it sends the request to Trustelem." The
same agent also pushes logs to an on-premise SIEM and performs outbound SCIM provisioning
(section 9).

Each application gets its own port per protocol: "One opened port matches one protocol for one
application on Trustelem". A Bastion RADIUS listener and an Access Manager RADIUS listener are
therefore two ports, for example 1812 and 2812. Default ports: "usually tcp port 2001 for LDAP,
and udp port 1812 for Radius". The application pages say what to do when 1812 is taken:

| Listener | Port rule | Source |
|----------|-----------|--------|
| RADIUS, Bastion application | 1812, "but if you don't know if it is already used on the machine running the connector, choose 2812 instead" | [Bastion app page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-bastion) |
| RADIUS, Access Manager application | "If you don't already have a Bastion using it, you can let the default port 1812. Otherwise, you can use 2812, 3812..." | [Access Manager app page](https://trustelem-doc.wallix.com/books/trustelem-applications/page/wallix-access-manager) |

This design uses 1812/udp for the Bastion, 2812/udp for Access Manager and 2001/tcp for the
Bastion LDAP listener:

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

**Services** tab: "Click on the button + Create a service and copy the service ID."

- The page does not say whether both VMs share one service ID or each has its own
  (*inference:* one per VM, as here).
- Redundancy follows the ADConnect rule: "The recommendation is 2 VM at least, to have a
  failover system".

## 3. Install on Windows

Both installers are published at https://dl.trustelem.com/connect/: "Download Trustelem Connect
on the VM (.exe or .tgz depending of the OS)" [sic]. The `.exe` is used here, the `.tgz` in
section 4. The Windows installer takes the service ID and an optional proxy.

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

5. "Start the service." Then in the console: "Refresh your Services page. Turn on the service by
   clicking on No."

## 4. Install on Linux

On Linux the service ID, proxy and certificate go in one `config.ini` file.

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
4. `systemctl start trustelem-connect.service`. "The service will run with the user trustelem".

Documented configuration keys:

- `service_id`, `state_dir`, `proxy`, `tls_cert`, `tls_cert_key`, `outgoing_allowed`.
- `[target.<name>]` with `addr` and `port` (SIEM page, which spells the section
  `[targert.choose_a_name]` [sic]), or `addr = host:port` alone (SCIM page).

Listen addresses and ports are not in the file. They are set per application in the console
(section 5).

## 5. Add the applications (listeners)

Each application opens its listeners on the service page. For Bastion and Access Manager use
their dedicated app templates ([chapter 04](04-bastion-integration.md) and
[chapter 05](05-access-manager-integration.md)). The generic procedure:

1. **Apps**: add an application. Use the generic "Basic no SSO" model when only LDAP or RADIUS
   is needed.
2. "Turn on LDAP and/or Radius".
3. Back on the service page, "click on Add an application +".
4. "Click on LDAP and/or Radius button(s) to enable the protocol, then enter the listen address
   and port".
5. "If you have setup Trustelem Connect to use LDAPS, then check LDAPS".
6. Save.

Listen address: "the listen address can be localhost, all existing IP address on the machine =
*, or a specific IP"; "if you have a dedicated VM for the connector, choose *".

Secrets: the LDAP bind DN, bind password, base DN and RADIUS shared secret "are provided on the
setup of the Trustelem application". The eye button on the service page shows them later.

Restart the service after adding a target or changing `config.ini`. *Inference:* listener
changes made in the console reach the agent without a restart.

## 6. What the LDAP listener exposes

The listener imitates an Active Directory. "If you have to choose between an Active Directory
server or a LDAP server, you should choose Active Directory. Trustelem tries to replicate how an
Active Directory answers."

| Item | Value |
|------|-------|
| User DN | `CN=my_user,DC=my_trustelem_domain,DC=trustelem,DC=com` |
| Group DN | `CN=my_group,OU=Groups,DC=my_trustelem_domain,DC=trustelem,DC=com` |
| Login of a Trustelem local user | "A Trustelem local user must have the login sets to mail" |
| Login of an AD user | "A user synchronized from Active Directory can have the login sets to sAMAccountName, userPrincipalName or mail" |
| Bind account | default `trustelem`; bind DN `cn=trustelem,DC=<tenant>,DC=trustelem,DC=com` |
| Base DN | `DC=<tenant>,DC=trustelem,DC=com` |
| User search filter | `(mail=%u)` |

The bind DN, base DN and filter come from the vendor's OpenVPN example
([Trustelem applications export, OpenVPN chapter](https://trustelem-doc.wallix.com/books/trustelem-applications/export/html)).

MFA over LDAP depends on the LDAP access rule; the *2 factors* behaviour (push wait or TOTP
appended to the password) is in
[chapter 06, section 6](06-mfa-and-access-rules.md#6-access-rules). Passkeys are not usable
over LDAP ([MFA](https://trustelem-doc.wallix.com/books/trustelem-administration/page/multi-factors-authentication)).

## 7. What the RADIUS listener does

The RADIUS listener accepts a password and a second factor in one or two steps, or waits for a
push. The modes, from the
[access rules page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/access-rules):

- **Two steps:** "If the application supports Radius in 2 steps (Access Request then Challenge
  request) you can provide login + password then MFA." The Bastion (Admin Guide 7.2.5.4) and
  Access Manager ("supports the challenge-response mechanism",
  [Access Manager 6.0.5 Administration Guide](https://doc.wallix.com/) 4.3.6 and
  [Access Manager 5.2.4.0 Administration Guide](https://pam.wallix.one/documentation/admin-doc/am-admin-guide_en.pdf) 11)
  support it;
  see [chapter 04, section 3](04-bastion-integration.md#3-scenario-a-ad-users-with-radius-push-as-second-factor-recommended)
  and [chapter 05, section 5](05-access-manager-integration.md#5-radius-for-ad-users).
- **One step:** "If the application doesn't support Radius in 2 steps, you can provide login +
  password and code sticked together".
- **Push wait:** "login + password then no answer from Trustelem before the validation of a push
  notification". Size the client timeout accordingly.
- **Second factor only:** with the *2nd factor only* rule the password is ignored. The Bastion
  option "Use mobile device for 2 factor authentication(2FA)" relies on this
  ([chapter 04, section 3](04-bastion-integration.md#3-scenario-a-ad-users-with-radius-push-as-second-factor-recommended)).
- **Always allow:** accepts a known login without any check; use it only as a deliberate
  exemption. The rule values are in [chapter 06, section 6](06-mfa-and-access-rules.md#6-access-rules).
- **MFA session:** a Bastion app with RADIUS can skip the second factor for a while on the same
  network; see [chapter 06, section 8](06-mfa-and-access-rules.md#8-mfa-session-on-radius).

Not documented: CHAP support (the Access Manager page specifies PAP), attributes returned in
Access-Accept, RADIUS accounting.

## 8. Connectivity test

Run the check on each agent after installation and after every firewall or proxy change.

- Linux: `./connect check <your sync id>` or
  `./connect check <your sync id> http://proxy.example.local:3128`. `<your sync id>` is the
  vendor's generic name; for Trustelem Connect it is the `service_id` of section 2.
- Windows: "open the Trustelem Connect or ADConnect configuration tool and use the connection
  test."

Output fields ([connectors network flows](https://trustelem-doc.wallix.com/books/trustelem-administration/page/connectors-network-flows)):

| Field | Meaning (verbatim) |
|-------|--------------------|
| `Network: false` | "The connection could not be opened at all: the traffic is blocked or not routed." |
| `Network: true`, `CanTLS: false` | "The connection reaches the server but the TLS session fails: proxy or TLS inspection." |
| `CommOK: true` | "The flows are correct." |
| `RemoteIP` | "The public address your traffic is seen coming from." |

The destinations to open are in
[chapter 01, section 4](01-tenant-setup.md#4-network-prerequisites-for-every-connector).

## 9. Outbound targets: SIEM and SCIM

SIEM export and SCIM provisioning use the same mechanism: enable outgoing connections and
declare a target.

```ini
outgoing_allowed = "true"
[target.siem]
addr = "siem.example.local"
port = "5514"
```

The CLI does the same: `./TrustelemConnect set-target <name> <host:port>` "writes a
`[target.<name>]` section in config.ini and enables outgoing connections". Options:
`-always-tls`, `-no-tls`, `-insecure-allow-skip-tls-check`, `-override`. "Restart the service
so the new target is advertised to Trustelem." The SIEM configuration itself is in
[chapter 07](07-operations.md).

## 10. RADIUS transport security

Keep the RADIUS hop inside a trusted administration network. RADIUS over UDP obfuscates only
the password (MD5 XOR with the shared secret), and without Message-Authenticator it is exposed to CVE-2024-3596 (BlastRADIUS)
([blastradius.fail](https://www.blastradius.fail/)). Neither the Bastion guide nor the Trustelem Connect page
documents Message-Authenticator, and RADIUS/TLS is not offered. The analysis, the missing WALLIX
advisory and the vendor questions are in
[Standards and compliance](../reference/standards-and-compliance.md).

Until WALLIX confirms the behaviour:

- Place the agents in the same VLAN as the Bastion and Access Manager nodes, or host-adjacent.
- Do not let the RADIUS hop cross user networks.
- Allow 1812/udp only from the Bastion addresses and 2812/udp only from the Access Manager
  addresses.

## 11. Placement and sizing

- Two VMs on separate hosts, ideally one per site. Bind the listeners to `*` on a dedicated VM.
- Recommendation: the same network segment as the Bastion and Access Manager nodes
  (section 10) also keeps RADIUS (UDP) away from stateful devices that could time out challenge
  exchanges.
- The vendor gives no throughput numbers ("minimal resources"). *Inference:* each pending push
  holds a request for up to the client timeout, so count concurrent logins when sizing.
- Manage the VMs through the Bastion once it is live, and send their OS events to the SIEM.
