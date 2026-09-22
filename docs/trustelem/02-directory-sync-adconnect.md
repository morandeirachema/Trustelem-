# Active Directory synchronisation with Trustelem ADConnect

Date: 2026-09-23. Source: [Active Directory users - Trustelem ADConnect](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-users-trustelem-adconnect)
and [Active Directory synchronization](https://trustelem-doc.wallix.com/books/trustelem-administration/page/active-directory-synchronization).
Quotes are verbatim.

## 1. How it works

"During the setup, Trustelem ADConnect opens a websocket to admin.trustelem.com using port
443. Note: with the websocket, information is encrypted by TLS protocol and with an additional
symmetric encryption." The cloud sends search and authentication requests down that socket;
"Trustelem ADConnect sends the request to Active Directory using LDAP(S) with the service
account running the connector"; "thanks to this connector Trustelem does not store any password
for Active Directory users."

```
+--------------------+              +------------------------+              +--------------------+
| Trustelem cloud    |<-- WSS 443 --| ADConnect VM 1 (prio 1)|-- LDAP 389 ->| Domain             |
| admin.trustelem    |              | ADConnect VM 2 (prio 2)|              | controllers        |
| .com (WSS 443)     |<-- WSS 443 --| read-only AD account   |-- LDAP 636 ->| LDAP/LDAPS 389/636 |
|                    |              |                        |              |                    |
+--------------------+              +------------------------+              +--------------------+

Outbound only: each agent opens the websocket; the cloud uses the first healthy connector.
```

## 2. Prerequisites (verbatim)

- "Prepare a VM, Windows Server or Linux, with minimal resources for the OS".
- "If you have only one VM which is down, the link to your AD is down too.. The recommendation
  is 2 VM at least, to have a failover system".
- Download from https://dl.trustelem.com/adconnect/ (.exe or .tgz).
- "If the VM isn't a Windows Server in the AD domain, you need to open the flow from the VM to a
  DC - tcp port 389 or 636".
- Outbound TCP 443 to `*.trustelem.com` (see chapter 01 for the full list).
- "A service account with "read only" rights should be created on your Active Directory". Use
  the UPN form (`connector@ADdomain`). For self-service password reset the same account also
  needs the "Reset user password and force password change at next logon" delegation
  ([SSPR page](https://trustelem-doc.wallix.com/books/trustelem-administration/page/self-service-password-reset)).

## 3. Register the directory in the console

1. **Directories**: "Click on Create and select Active Directory."
2. "Give a name to the new directory, and optionally a description."
3. "Ensure Use a connector is checked."
4. "Write down the synchronization ID, then click on Save."

## 4. Install on Windows Server

1. "launch the installation software and paste the synchronization ID then click on Validate
   the Configuration".
2. "Open Windows Services Manager (you can click on Configure the service). Select Trustelem
   ADConnect. Right-click, select Properties."
3. "On General tab, make sure that Startup type is set to Automatic (Delayed Start)."
4. "On Log On tab, select This account and enter the technical user's credentials."
5. If the machine is not in the AD domain, "you can't use the Log On tab of the service. Create a
   config.ini file in Trustelem setup directory":

```ini
ldap_addr = ldap://ad_fqdn_or_ip
ldap_port = 389
# use the UPN
ldap_user = connector@ADdomain
ldap_password = xxxx
```

   LDAPS variant:

```ini
ldap_addr = ldaps://ad_fqdn_or_ip
# or, to verify the certificate (place it in the Trustelem setup directory):
ldap_addr = ldaps://ad_fqdn_or_ip?tls_verify
ldap_port = 636
```

6. "Launch the service. Note: if you used a config.ini file (machine not in the AD domain), the
   4th led will be red."

## 5. Install on Linux

1. "launch the installation software from the .tgz file, using ./setup.sh with root rights".
2. "edit /opt/wallix/trustelem-adconnect/config.ini file containing the synchronization id":

```ini
sync_id = 2jy34wpcohrhdytr6hutym6qfi2l7nnw
state_dir = run/
ldap_addr = ldap://ad_fqdn_or_ip
ldap_port = 389
# use the UPN
ldap_user = connector@ADdomain
ldap_password = xxxx
# if there is a proxy
proxy = https://username:password@proxy_IP:proxy_port
```

3. For LDAPS with verification, "make sure the certificate is signed by a known CA. Check that
   the certificate is signed by a CA listed in /etc/ssl/certs", either by linking it
   (`ln -nsf /path/to/public.crt /etc/ssl/certs/my-ca-name.crt`) or by adding to
   `/lib/systemd/system/trustelem-adconnect.service`:

```ini
[Service]
Type = simple
ExecStart = ...
Environment = "SSL_CERT_FILE=/path/to/public.crt"
```

4. `systemctl start trustelem-adconnect.service`.

Config keys: `sync_id`, `state_dir`, `ldap_addr` (with optional `?tls_verify`), `ldap_port`,
`ldap_user`, `ldap_password`, `proxy`. Log settings and log file locations are not documented.

## 6. Activate and configure the synchronisation

1. "Get back to the Trustelem admin dashboard, Directory tab. Refresh the page: the connector
   should show up in the table. Once the connector is up, check the IP address, the server name
   and the service account (to avoid spoofing), then activate the connector by pushing the
   "No" button."
2. "Setup the appropriate synchronization frequency (nota: a high frequency increases the load
   of your domain controllers)." The list of values is not documented.
3. "Select the groups to be synchronized." Scope by AD group; "Domain users" cannot be used
   ("it is not a real group").
4. Optional: "By checking Advanced options, you can define a list of Custom attributes (title,
   memberOf,objectGUID,userPrincipalName...) to import with the users." Import
   `userPrincipalName` and `sAMAccountName` when the Bastion or Access Manager login must be
   one of them; the SAML `uid` attribute sent to Access Manager comes from the imported login.
5. Repeat the install on the second VM with the same synchronization ID; in the directory's
   connector list order them by priority.

## 7. Upgrades without interruption

"Install the latest release of the connector in parallel with your current connector. In the
directory tab of the Trustelem administration console, select the relevant directory and
ensure the new connector is listed first in order to be used in priority. Ensure that the new
connector is working fine by checking its usage statistics, then you can disable the previous
connector in the administration console. Finally, you can uninstall the previous connector from
your server and then it can be deleted from the Trustelem administration console."

## 8. Health and troubleshooting

Health: the Dashboard shows "number of users by directories (the led indicates if the directory
synchronization works, needs attention or doesn't work)"; the connector table shows IP, server
name, service account, usage statistics and a Server Link status behind the "i" icon.

Connector not visible in the console:

- "ping admin.trustelem.com on the machine running the connector to verify the outgoing flows"
  (the network-flows page adds that ping alone is not a valid test; use `connect check`).
- "verify the synchronization ID", "verify the proxy setup".
- "if the VM is a Windows machine, verify that you clicked on Validate on Trustelem ADConnect
  program".

No groups listed in "Sync groups": open the "i" icon; if Server Link shows an error, "verify the
flows from the VM running the connector to the Active Directory; verify the service account
used for Trustelem AD Connect (UserPrincipalName and password); verify if you have a
replication delay between the DC"; otherwise "verify if the service account has the right to
search groups on Active Directory; try to refresh the page".

Group missing users: "If your group is Domain users, it's normal, it can't be used because it
is not a real group"; check that the service account can read the user objects and that DC
replication has completed.

## 9. Security notes

- The service account is read-only; do not reuse it for Trustelem Connect or for the Bastion
  AD bind.
- Prefer LDAPS with `?tls_verify` (or the Windows Log On tab on a domain-joined host).
- The connector pins the Trustelem server certificate; exclude `*.trustelem.com` from TLS
  inspection.
- Two connectors on different hosts, patched on the vendor's rolling procedure above.
